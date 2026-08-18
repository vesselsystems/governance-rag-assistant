"""Deterministic TF-IDF retrieval baseline with citations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from .corpus import DocumentChunk, load_corpus


@dataclass(frozen=True)
class RetrievedChunk:
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
    def from_directory(cls, directory: Path) -> "TfidfRetriever":
        return cls(load_corpus(directory))

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        """Return the highest-scoring non-empty matches."""
        if not query.strip() or top_k < 1:
            return []
        query_vector = self.vectorizer.transform([query])
        scores = (self.matrix @ query_vector.T).toarray().ravel()
        ranked = np.argsort(-scores)[:top_k]
        return [
            RetrievedChunk(self.chunks[index], float(scores[index]))
            for index in ranked
            if scores[index] > 0
        ]
