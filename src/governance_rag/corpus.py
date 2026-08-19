"""Load, verify, and chunk the versioned document corpus.

The loader is intentionally local-only.  A manifest can describe a future external
snapshot, but this module never downloads a URL or treats a URL as proof of a license.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

MANIFEST_FILENAME = "corpus_manifest.json"
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
REPOSITORY_AUTHORED_DEMO = "repository_authored_demo"

# These are deliberately explicit rather than accepting an arbitrary value that
# happens to contain "external".  Keep additions reviewed because source_type
# controls which provenance requirements are applied to a document.
KNOWN_EXTERNAL_SOURCE_TYPES = frozenset(
    {
        "official_external",
        "public",
        "public_external",
        "external",
        "external_public",
        "public_source",
    }
)
SOURCE_TYPES = frozenset({REPOSITORY_AUTHORED_DEMO, *KNOWN_EXTERNAL_SOURCE_TYPES})
PUBLIC_SOURCE_TYPES = KNOWN_EXTERNAL_SOURCE_TYPES

# Statuses describe what this local loader can reproduce.  External-source and
# licence verification are deliberately not represented as an active status.
LOCAL_TEXT_CHECKSUM_VERIFIED = "local_text_checksum_verified"
BLOCKED_MANIFEST_STATUSES = frozenset({"blocked", "invalid"})
ACTIVE_MANIFEST_STATUSES = frozenset({LOCAL_TEXT_CHECKSUM_VERIFIED})
MANIFEST_STATUSES = frozenset({*ACTIVE_MANIFEST_STATUSES, *BLOCKED_MANIFEST_STATUSES})

DEFAULT_VERIFICATION_SCOPE = {
    "local_text_checksum": "local_checksum_verified",
    "raw_source": "out_of_band_not_reproducible",
    "public_license": "out_of_band_not_reproducible",
}
_VERIFICATION_SCOPE_STATUSES = {
    "local_text_checksum": frozenset({"local_checksum_verified"}),
    "raw_source": frozenset({"out_of_band_not_reproducible"}),
    "public_license": frozenset({"out_of_band_not_reproducible"}),
}
_REQUIRED_DOCUMENT_FIELDS = (
    "path",
    "source_type",
    "url",
    "publisher",
    "license",
    "revision",
    "retrieval_date",
)
_MANIFEST_KEYS = frozenset({
    "schema_version",
    "corpus_id",
    "status",
    "blocker",
    "verification_scope",
    "documents",
})


def _validate_public_url(value: str, *, path: str, field: str) -> None:
    """Require a real HTTP(S) URL for source metadata, without fetching it."""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Manifest {field} for {path!r} must be an absolute HTTP(S) URL")


@dataclass(frozen=True)
class DocumentProvenance:
    """Provenance recorded for one local document snapshot.

    ``None`` is deliberate for fields that are not applicable or have not been
    recorded.  Callers should not infer an external license or authority from a
    metadata field.  ``raw_source_sha256``/``raw_pdf_sha256`` records a digest
    supplied from the out-of-band acquisition record; this loader does not have
    the raw artifact and cannot reproduce that check.  The loader does verify the
    checked-in extracted-text bytes and never fetches a source URL.
    """

    path: str
    url: str | None
    publisher: str | None
    license: str | None
    revision: str | None
    retrieval_date: str | None
    sha256: str
    notes: str | None = None
    source_type: str = REPOSITORY_AUTHORED_DEMO
    pdf_url: str | None = None
    license_url: str | None = None
    raw_pdf_sha256: str | None = None
    raw_sha256: str | None = None
    raw_source_sha256: str | None = None
    extraction_method: str | None = None

    @property
    def extracted_sha256(self) -> str:
        """Return the digest of the indexed/extracted text bytes."""
        return self.sha256

    @property
    def raw_source_digest(self) -> str | None:
        """Return the canonical recorded digest for the raw source bytes."""
        return self.raw_source_sha256 or self.raw_sha256 or self.raw_pdf_sha256

    @classmethod
    def from_mapping(cls, value: Any) -> "DocumentProvenance":
        """Parse and validate one manifest document entry.

        Public/external entries are deliberately stricter than repository-authored
        demo artifacts.  A URL alone is never treated as provenance: the publisher,
        licence, revision, retrieval date, and both raw and extracted digests must
        be recorded before a public snapshot can be indexed.
        """
        if not isinstance(value, dict):
            raise ValueError("Each manifest document must be an object")
        missing = [field for field in _REQUIRED_DOCUMENT_FIELDS if field not in value]
        if missing:
            raise ValueError(f"Manifest document is missing fields: {', '.join(missing)}")
        if "sha256" not in value and "extracted_sha256" not in value:
            raise ValueError("Manifest document is missing fields: sha256")

        path = value["path"]
        if not isinstance(path, str) or not path.strip():
            raise ValueError("Manifest document path must be a non-empty string")
        source_type = value["source_type"]
        if not isinstance(source_type, str) or not source_type.strip():
            raise ValueError(f"Manifest source_type for {path!r} must be a non-empty string")
        if source_type not in SOURCE_TYPES:
            allowed = ", ".join(sorted(SOURCE_TYPES))
            raise ValueError(
                f"Manifest source_type for {path!r} must be one of {allowed}; "
                f"got {source_type!r}"
            )
        sha256 = value.get("sha256", value.get("extracted_sha256"))
        if not isinstance(sha256, str) or not _SHA256_RE.fullmatch(sha256):
            raise ValueError(f"Manifest sha256 for {path!r} must be 64 hexadecimal characters")
        raw_pdf_sha256 = value.get("raw_pdf_sha256")
        if raw_pdf_sha256 is not None and (
            not isinstance(raw_pdf_sha256, str) or not _SHA256_RE.fullmatch(raw_pdf_sha256)
        ):
            raise ValueError(
                f"Manifest raw_pdf_sha256 for {path!r} must be 64 hexadecimal characters or null"
            )
        raw_sha256 = value.get("raw_sha256")
        raw_source_sha256 = value.get("raw_source_sha256")
        for field_name, digest in (
            ("raw_sha256", raw_sha256),
            ("raw_source_sha256", raw_source_sha256),
        ):
            if digest is not None and (
                not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest)
            ):
                raise ValueError(
                    f"Manifest {field_name} for {path!r} must be 64 hexadecimal characters or null"
                )
        raw_digests = {
            digest.lower()
            for digest in (raw_pdf_sha256, raw_sha256, raw_source_sha256)
            if digest is not None
        }
        if len(raw_digests) > 1:
            raise ValueError(
                f"Manifest raw-source digests for {path!r} disagree; record one digest"
            )

        for field_name in (
            "url",
            "publisher",
            "license",
            "revision",
            "retrieval_date",
            "notes",
            "source_type",
            "pdf_url",
            "license_url",
            "extraction_method",
        ):
            field_value = value.get(field_name)
            if field_value is not None and not isinstance(field_value, str):
                raise ValueError(
                    f"Manifest field {field_name!r} for {path!r} must be a string or null"
                )
        for field_name in ("url", "pdf_url", "license_url"):
            field_value = value.get(field_name)
            if field_value is not None:
                _validate_public_url(field_value, path=path, field=field_name)
        retrieval_date = value.get("retrieval_date")
        if retrieval_date is not None:
            try:
                date.fromisoformat(retrieval_date)
            except ValueError as error:
                raise ValueError(
                    f"Manifest retrieval_date for {path!r} must be an ISO date or null"
                ) from error

        document = cls(
            path=path,
            url=value["url"],
            publisher=value["publisher"],
            license=value["license"],
            revision=value["revision"],
            retrieval_date=retrieval_date,
            sha256=sha256.lower(),
            notes=value.get("notes"),
            source_type=source_type,
            pdf_url=value.get("pdf_url"),
            license_url=value.get("license_url"),
            raw_pdf_sha256=(
                (raw_pdf_sha256 or (raw_source_sha256 if value.get("pdf_url") else None)).lower()
                if (raw_pdf_sha256 or (raw_source_sha256 if value.get("pdf_url") else None))
                is not None
                else None
            ),
            raw_sha256=(raw_sha256.lower() if raw_sha256 is not None else None),
            raw_source_sha256=(
                (
                    raw_source_sha256
                    or raw_sha256
                    or raw_pdf_sha256
                ).lower()
                if (raw_source_sha256 or raw_sha256 or raw_pdf_sha256) is not None
                else None
            ),
            extraction_method=value.get("extraction_method"),
        )
        validate_source_metadata(document)
        return document

    def as_dict(self) -> dict[str, str | None]:
        """Return a JSON-serializable manifest entry."""
        return {
            "path": self.path,
            "source_type": self.source_type,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "publisher": self.publisher,
            "license": self.license,
            "license_url": self.license_url,
            "revision": self.revision,
            "retrieval_date": self.retrieval_date,
            "sha256": self.sha256,
            "extracted_sha256": self.extracted_sha256,
            "raw_source_sha256": self.raw_source_digest,
            "raw_pdf_sha256": self.raw_pdf_sha256,
            "raw_sha256": self.raw_sha256,
            "extraction_method": self.extraction_method,
            "notes": self.notes,
        }


def validate_source_metadata(document: DocumentProvenance) -> None:
    """Validate the source classification and metadata without network access.

    Repository-authored demos must not carry external provenance fields.  Known
    external classifications require enough metadata to identify the source and
    record both digests.  The raw-source digest and licence fields are records;
    this function does not verify a raw artifact or contact a licence URL.
    """
    if document.source_type not in SOURCE_TYPES:
        raise ValueError(
            f"Manifest source_type for {document.path!r} is not a known classification"
        )

    raw_digest = document.raw_source_digest
    if document.source_type == REPOSITORY_AUTHORED_DEMO:
        external_fields = {
            "url": document.url,
            "pdf_url": document.pdf_url,
            "publisher": document.publisher,
            "license": document.license,
            "license_url": document.license_url,
            "revision": document.revision,
            "retrieval_date": document.retrieval_date,
            "raw_source_sha256": raw_digest,
        }
        present = [field for field, value in external_fields.items() if value is not None]
        if present:
            raise ValueError(
                f"Repository-authored manifest source {document.path!r} cannot carry "
                f"external metadata: {', '.join(present)}"
            )
        return

    required_text = {
        "url": document.url,
        "publisher": document.publisher,
        "license": document.license,
        "revision": document.revision,
        "retrieval_date": document.retrieval_date,
    }
    missing = [field for field, value in required_text.items() if not isinstance(value, str)]
    blank = [
        field
        for field, value in required_text.items()
        if isinstance(value, str) and not value.strip()
    ]
    if missing or blank:
        fields = ", ".join(missing + blank)
        raise ValueError(
            f"External manifest source {document.path!r} is missing required metadata: {fields}"
        )
    _validate_public_url(document.url, path=document.path, field="url")
    if raw_digest is None:
        raise ValueError(
            f"External manifest source {document.path!r} requires raw_source_sha256 "
            "(or legacy raw_sha256/raw_pdf_sha256)"
        )
    if not _SHA256_RE.fullmatch(raw_digest):
        raise ValueError(
            f"Manifest raw-source digest for {document.path!r} must be 64 "
            "hexadecimal characters"
        )
    if not _SHA256_RE.fullmatch(document.extracted_sha256):
        raise ValueError(
            f"Manifest extracted-text digest for {document.path!r} must be 64 "
            "hexadecimal characters"
        )


# Backwards-compatible import name; the stricter validator now covers every
# known external source type and repository-authored classification.
def validate_public_source_metadata(document: DocumentProvenance) -> None:
    validate_source_metadata(document)


def _validate_manifest_gate(status: str, blocker: str | None) -> None:
    """Reject manifests that are blocked, invalid, or internally inconsistent."""
    if status in BLOCKED_MANIFEST_STATUSES:
        detail = blocker or "no blocker reason was recorded"
        raise ValueError(f"Corpus manifest is {status} and cannot be indexed: {detail}")
    if status not in ACTIVE_MANIFEST_STATUSES:
        raise ValueError(f"Corpus manifest status {status!r} is not indexable")
    if blocker is not None:
        raise ValueError(
            "Corpus manifest has a blocker and cannot be indexed while status is active"
        )


def _parse_verification_scope(value: Any) -> dict[str, str]:
    """Parse the intentionally limited, non-overclaiming verification scope."""
    if value is None:
        return dict(DEFAULT_VERIFICATION_SCOPE)
    if not isinstance(value, dict):
        raise ValueError("Corpus manifest verification_scope must be an object")
    expected_keys = set(DEFAULT_VERIFICATION_SCOPE)
    if set(value) != expected_keys:
        missing = sorted(expected_keys - set(value))
        unknown = sorted(set(value) - expected_keys)
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unknown:
            details.append("unknown " + ", ".join(unknown))
        raise ValueError("Corpus manifest verification_scope: " + "; ".join(details))
    parsed: dict[str, str] = {}
    for field_name, allowed in _VERIFICATION_SCOPE_STATUSES.items():
        field_value = value[field_name]
        if field_value not in allowed:
            options = ", ".join(sorted(allowed))
            raise ValueError(
                f"Corpus manifest verification_scope.{field_name} must be one of {options}"
            )
        parsed[field_name] = field_value
    return parsed


@dataclass(frozen=True)
class CorpusManifest:
    """A provenance manifest for a reproducible local corpus snapshot."""

    schema_version: int
    corpus_id: str
    status: str
    blocker: str | None
    documents: tuple[DocumentProvenance, ...]
    path: Path
    verification_scope: dict[str, str] = field(
        default_factory=lambda: dict(DEFAULT_VERIFICATION_SCOPE)
    )

    @classmethod
    def from_path(cls, path: Path) -> "CorpusManifest":
        """Read and validate a manifest without accessing any remote URL."""
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except OSError as error:
            raise ValueError(f"Could not read corpus manifest {path}") from error
        except json.JSONDecodeError as error:
            raise ValueError(f"Corpus manifest {path} is not valid JSON") from error

        if not isinstance(raw, dict):
            raise ValueError("Corpus manifest must be a JSON object")
        unknown_fields = sorted(set(raw) - _MANIFEST_KEYS)
        if unknown_fields:
            raise ValueError(
                "Corpus manifest contains unknown fields: " + ", ".join(unknown_fields)
            )
        schema_version = raw.get("schema_version")
        if schema_version != 1:
            raise ValueError("Unsupported corpus manifest schema_version; expected 1")
        corpus_id = raw.get("corpus_id")
        status = raw.get("status")
        if not isinstance(corpus_id, str) or not corpus_id.strip():
            raise ValueError("Corpus manifest corpus_id must be a non-empty string")
        if not isinstance(status, str) or not status.strip():
            raise ValueError("Corpus manifest status must be a non-empty string")
        if status not in MANIFEST_STATUSES:
            allowed = ", ".join(sorted(MANIFEST_STATUSES))
            raise ValueError(
                f"Corpus manifest status must be one of {allowed}; got {status!r}"
            )
        blocker = raw.get("blocker")
        if blocker is not None and (
            not isinstance(blocker, str) or not blocker.strip()
        ):
            raise ValueError("Corpus manifest blocker must be a non-empty string or null")
        _validate_manifest_gate(status, blocker)
        verification_scope = _parse_verification_scope(raw.get("verification_scope"))
        raw_documents = raw.get("documents")
        if not isinstance(raw_documents, list) or not raw_documents:
            raise ValueError("Corpus manifest documents must be a non-empty list")
        documents = tuple(DocumentProvenance.from_mapping(item) for item in raw_documents)
        paths = [document.path for document in documents]
        if len(paths) != len(set(paths)):
            raise ValueError("Corpus manifest document paths must be unique")
        return cls(
            schema_version=schema_version,
            corpus_id=corpus_id,
            status=status,
            blocker=blocker,
            documents=documents,
            path=path,
            verification_scope=verification_scope,
        )

    def for_path(self, path: Path, directory: Path) -> DocumentProvenance | None:
        """Return the manifest entry corresponding to a local corpus path."""
        resolved = path.resolve()
        for document in self.documents:
            candidate = _resolve_manifest_document(document, self.path, directory)
            if candidate.resolve() == resolved:
                return document
        return None


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file, reading it in bounded chunks."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path) -> CorpusManifest:
    """Load a manifest explicitly for callers that need provenance inspection."""
    return CorpusManifest.from_path(path)


def _resolve_manifest_document(
    document: DocumentProvenance,
    manifest_path: Path,
    directory: Path,
) -> Path:
    """Resolve a manifest path relative to either data/ or the corpus directory."""
    relative = Path(document.path)
    candidates = [manifest_path.parent / relative, directory / relative]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    # Return the first candidate so the error names the manifest's natural path.
    return candidates[0]


def verify_manifest(
    manifest: CorpusManifest,
    directory: Path,
    *,
    verify_checksums: bool = True,
) -> dict[Path, DocumentProvenance]:
    """Verify local text bytes for an active manifest without network access.

    This is deliberately a local checksum operation, not raw-source or licence
    verification: URL fields and recorded raw digests are metadata only and are
    never fetched or independently reproduced here.
    """
    _validate_manifest_gate(manifest.status, manifest.blocker)
    for document in manifest.documents:
        validate_source_metadata(document)
    resolved_directory = directory.resolve()
    entries: dict[Path, DocumentProvenance] = {}
    for document in manifest.documents:
        path = _resolve_manifest_document(document, manifest.path, directory)
        resolved = path.resolve()
        if resolved_directory not in resolved.parents:
            raise ValueError(f"Manifest path escapes the corpus directory: {document.path!r}")
        if not path.is_file():
            raise ValueError(f"Manifest document does not exist locally: {document.path!r}")
        if path.suffix.lower() not in {".md", ".txt"}:
            raise ValueError(f"Manifest document is not Markdown/text: {document.path!r}")
        if verify_checksums and sha256_file(path) != document.sha256:
            raise ValueError(
                f"Checksum mismatch for {document.path!r}; update the manifest only after review"
            )
        if resolved in entries:
            raise ValueError(f"Manifest resolves multiple entries to {path}")
        entries[resolved] = document

    discovered = {path.resolve() for path in _discover_files(directory)}
    untracked = sorted(discovered - set(entries))
    if untracked:
        names = ", ".join(path.name for path in untracked)
        raise ValueError(f"Corpus files are missing from the manifest: {names}")
    return entries


def _discover_files(directory: Path) -> list[Path]:
    return [
        path
        for path in sorted(directory.glob("**/*"))
        if path.is_file()
        and path.name.lower() != "readme.md"
        and path.suffix.lower() in {".md", ".txt"}
    ]


@dataclass(frozen=True)
class DocumentChunk:
    """A retrievable piece of a source document."""

    chunk_id: str
    source: str
    text: str
    provenance: DocumentProvenance | None = None

    @property
    def citation(self) -> str:
        return f"[{self.source}#{self.chunk_id}]"


def chunk_text(
    text: str,
    source: str,
    chunk_words: int = 180,
    overlap_words: int = 40,
    provenance: DocumentProvenance | None = None,
) -> list[DocumentChunk]:
    """Create deterministic word-window chunks while retaining source metadata."""
    words = text.split()
    if not words:
        return []
    if chunk_words < 1:
        raise ValueError("chunk_words must be positive")
    if overlap_words < 0 or overlap_words >= chunk_words:
        raise ValueError("overlap_words must be non-negative and smaller than chunk_words")

    chunks: list[DocumentChunk] = []
    step = chunk_words - overlap_words
    for index, start in enumerate(range(0, len(words), step)):
        window = words[start : start + chunk_words]
        if not window:
            break
        chunks.append(
            DocumentChunk(
                chunk_id=str(index),
                source=source,
                text=" ".join(window),
                provenance=provenance,
            )
        )
        if start + chunk_words >= len(words):
            break
    return chunks


def load_corpus(
    directory: Path,
    *,
    manifest_path: Path | None = None,
    verify_checksums: bool = True,
) -> list[DocumentChunk]:
    """Load Markdown/text documents and attach checksum-checked manifest metadata.

    If ``data/corpus_manifest.json`` exists next to ``directory``, it is used
    automatically.  A manifest makes untracked or modified snapshot files fail
    closed.  Custom directories without a manifest remain supported for tests
    and local experiments.
    """
    directory = Path(directory)
    if manifest_path is None:
        candidate = directory.parent / MANIFEST_FILENAME
        manifest_path = candidate if candidate.is_file() else None

    manifest: CorpusManifest | None = None
    manifest_entries: dict[Path, DocumentProvenance] = {}
    if manifest_path is not None:
        manifest = load_manifest(Path(manifest_path))
        manifest_entries = verify_manifest(
            manifest,
            directory,
            verify_checksums=verify_checksums,
        )
        files = [Path(path) for path in manifest_entries]
        discovered = {path.resolve() for path in _discover_files(directory)}
        untracked = sorted(discovered - set(manifest_entries))
        if untracked:
            names = ", ".join(path.name for path in untracked)
            raise ValueError(f"Corpus files are missing from the manifest: {names}")
    else:
        files = _discover_files(directory)

    chunks: list[DocumentChunk] = []
    for path in sorted(files):
        provenance = manifest_entries.get(path.resolve()) if manifest else None
        chunks.extend(
            chunk_text(
                path.read_text(encoding="utf-8"),
                source=path.name,
                provenance=provenance,
            )
        )
    if not chunks:
        raise ValueError(f"No .md or .txt documents found in {directory}")
    return chunks
