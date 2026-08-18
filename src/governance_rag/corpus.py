"""Load, verify, and chunk the versioned document corpus.

The loader is intentionally local-only.  A manifest can describe a future external
snapshot, but this module never downloads a URL or treats a URL as proof of a license.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

MANIFEST_FILENAME = "corpus_manifest.json"
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_REQUIRED_DOCUMENT_FIELDS = (
    "path",
    "url",
    "publisher",
    "license",
    "revision",
    "retrieval_date",
    "sha256",
)


@dataclass(frozen=True)
class DocumentProvenance:
    """Provenance recorded for one local document snapshot.

    ``None`` is deliberate for fields that are not applicable or have not been
    verified.  Callers should not infer an external license or authority from a
    missing value.  ``raw_pdf_sha256`` records the source bytes used to create a
    text snapshot; the loader verifies the checked-in text hash and never fetches
    the PDF URL.
    """

    path: str
    url: str | None
    publisher: str | None
    license: str | None
    revision: str | None
    retrieval_date: str | None
    sha256: str
    notes: str | None = None
    source_type: str | None = None
    pdf_url: str | None = None
    license_url: str | None = None
    raw_pdf_sha256: str | None = None
    extraction_method: str | None = None

    @classmethod
    def from_mapping(cls, value: Any) -> "DocumentProvenance":
        """Parse and validate one manifest document entry."""
        if not isinstance(value, dict):
            raise ValueError("Each manifest document must be an object")
        missing = [field for field in _REQUIRED_DOCUMENT_FIELDS if field not in value]
        if missing:
            raise ValueError(f"Manifest document is missing fields: {', '.join(missing)}")

        path = value["path"]
        if not isinstance(path, str) or not path.strip():
            raise ValueError("Manifest document path must be a non-empty string")
        sha256 = value["sha256"]
        if not isinstance(sha256, str) or not _SHA256_RE.fullmatch(sha256):
            raise ValueError(f"Manifest sha256 for {path!r} must be 64 hexadecimal characters")
        raw_pdf_sha256 = value.get("raw_pdf_sha256")
        if raw_pdf_sha256 is not None and (
            not isinstance(raw_pdf_sha256, str) or not _SHA256_RE.fullmatch(raw_pdf_sha256)
        ):
            raise ValueError(
                f"Manifest raw_pdf_sha256 for {path!r} must be 64 hexadecimal characters or null"
            )

        for field in (
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
            field_value = value.get(field)
            if field_value is not None and not isinstance(field_value, str):
                raise ValueError(f"Manifest field {field!r} for {path!r} must be a string or null")
        retrieval_date = value.get("retrieval_date")
        if retrieval_date is not None:
            try:
                date.fromisoformat(retrieval_date)
            except ValueError as error:
                raise ValueError(
                    f"Manifest retrieval_date for {path!r} must be an ISO date or null"
                ) from error

        return cls(
            path=path,
            url=value["url"],
            publisher=value["publisher"],
            license=value["license"],
            revision=value["revision"],
            retrieval_date=retrieval_date,
            sha256=sha256.lower(),
            notes=value.get("notes"),
            source_type=value.get("source_type"),
            pdf_url=value.get("pdf_url"),
            license_url=value.get("license_url"),
            raw_pdf_sha256=(raw_pdf_sha256.lower() if raw_pdf_sha256 is not None else None),
            extraction_method=value.get("extraction_method"),
        )

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
            "raw_pdf_sha256": self.raw_pdf_sha256,
            "extraction_method": self.extraction_method,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class CorpusManifest:
    """A provenance manifest for a reproducible local corpus snapshot."""

    schema_version: int
    corpus_id: str
    status: str
    blocker: str | None
    documents: tuple[DocumentProvenance, ...]
    path: Path

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
        schema_version = raw.get("schema_version")
        if schema_version != 1:
            raise ValueError("Unsupported corpus manifest schema_version; expected 1")
        corpus_id = raw.get("corpus_id")
        status = raw.get("status")
        if not isinstance(corpus_id, str) or not corpus_id.strip():
            raise ValueError("Corpus manifest corpus_id must be a non-empty string")
        if not isinstance(status, str) or not status.strip():
            raise ValueError("Corpus manifest status must be a non-empty string")
        blocker = raw.get("blocker")
        if blocker is not None and not isinstance(blocker, str):
            raise ValueError("Corpus manifest blocker must be a string or null")
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
    """Verify that manifest entries point to local files with recorded hashes.

    This is deliberately a verification operation, not an ingestion operation:
    URL fields are metadata only and are never fetched.
    """
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
    """Load Markdown/text documents and attach verified manifest metadata.

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
