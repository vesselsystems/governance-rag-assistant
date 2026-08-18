"""Load and chunk the versioned document corpus."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentChunk:
    """A retrievable piece of a source document."""

    chunk_id: str
    source: str
    text: str

    @property
    def citation(self) -> str:
        return f"[{self.source}#{self.chunk_id}]"


def chunk_text(
    text: str,
    source: str,
    chunk_words: int = 180,
    overlap_words: int = 40,
) -> list[DocumentChunk]:
    """Create deterministic word-window chunks while retaining source metadata."""
    words = text.split()
    if not words:
        return []
    if overlap_words >= chunk_words:
        raise ValueError("overlap_words must be smaller than chunk_words")

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
            )
        )
        if start + chunk_words >= len(words):
            break
    return chunks


def load_corpus(directory: Path) -> list[DocumentChunk]:
    """Load Markdown/text documents, skipping the corpus README."""
    chunks: list[DocumentChunk] = []
    for path in sorted(directory.glob("**/*")):
        if not path.is_file() or path.name.lower() == "readme.md":
            continue
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        chunks.extend(
            chunk_text(
                path.read_text(encoding="utf-8"),
                source=path.name,
            )
        )
    if not chunks:
        raise ValueError(f"No .md or .txt documents found in {directory}")
    return chunks
