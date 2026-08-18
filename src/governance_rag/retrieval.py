"""Deterministic TF-IDF retrieval baseline with citations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

from .corpus import DocumentChunk, load_corpus


@dataclass(frozen=True)
class RetrievedChunk:
    """A retrieved chunk and its local cosine-similarity score."""

    chunk: DocumentChunk
    score: float


class TfidfRetriever:
    """Small local retrieval index suitable for a reproducible baseline."""

    def __init__(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            raise ValueError("Retriever requires at least one chunk")
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform([chunk.text for chunk in chunks])

    @classmethod
    def from_directory(
        cls,
        directory: Path,
        *,
        manifest_path: Path | None = None,
        verify_checksums: bool = True,
    ) -> "TfidfRetriever":
        """Build an index from a local corpus, optionally verifying its manifest."""
        return cls(
            load_corpus(
                directory,
                manifest_path=manifest_path,
                verify_checksums=verify_checksums,
            )
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        *,
        min_score: float = 0.0,
    ) -> list[RetrievedChunk]:
        """Return the highest-scoring non-empty matches.

        ``min_score`` is an optional explicit abstention threshold.  The default
        keeps the original lexical baseline behavior: zero-score chunks are
        omitted, while any positive match is inspectable.  Ties use source and
        chunk identifiers as deterministic secondary keys.
        """
        if not query.strip() or top_k < 1:
            return []
        if min_score < 0:
            raise ValueError("min_score must be non-negative")
        query_vector = self.vectorizer.transform([query])
        scores = (self.matrix @ query_vector.T).toarray().ravel()
        ranked = sorted(
            range(len(self.chunks)),
            key=lambda index: (
                -float(scores[index]),
                self.chunks[index].source,
                self.chunks[index].chunk_id,
            ),
        )[:top_k]
        return [
            RetrievedChunk(self.chunks[index], float(scores[index]))
            for index in ranked
            if scores[index] > 0 and scores[index] >= min_score
        ]
