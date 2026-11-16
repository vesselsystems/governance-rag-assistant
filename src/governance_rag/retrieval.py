"""Deterministic lexical retrievers (TF-IDF and BM25) with citations."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

from .corpus import DocumentChunk, load_corpus

# Same token pattern and stop-word list as the TF-IDF baseline, so a comparison
# isolates the scoring function rather than tokenization differences.
_TOKEN_PATTERN = re.compile(r"(?u)\b\w\w+\b")


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens of two or more characters, minus English stop words."""
    return [
        token
        for token in _TOKEN_PATTERN.findall(text.lower())
        if token not in ENGLISH_STOP_WORDS
    ]


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


class Bm25Retriever:
    """Okapi BM25 over the same chunks, as a second lexical baseline.

    Differences from the TF-IDF baseline are deliberate and few: term frequency
    saturates (``k1``) and long chunks are length-normalised (``b``); there are no
    bigrams. Scores are unbounded and depend on query length, so they are not
    comparable to cosine scores and any abstention threshold must be chosen per
    retriever. ``k1`` and ``b`` are the common defaults and are not tuned here.
    """

    def __init__(self, chunks: list[DocumentChunk], *, k1: float = 1.5, b: float = 0.75) -> None:
        if not chunks:
            raise ValueError("Retriever requires at least one chunk")
        if k1 < 0 or not 0 <= b <= 1:
            raise ValueError("BM25 requires k1 >= 0 and 0 <= b <= 1")
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self._term_counts = [Counter(tokenize(chunk.text)) for chunk in chunks]
        self._lengths = [sum(counts.values()) for counts in self._term_counts]
        self._average_length = sum(self._lengths) / len(self._lengths) or 1.0
        document_frequency: Counter[str] = Counter()
        for counts in self._term_counts:
            document_frequency.update(counts.keys())
        total = len(chunks)
        # Lucene's non-negative IDF variant: a term in every chunk still scores >= 0.
        self._idf = {
            term: math.log(1 + (total - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    @classmethod
    def from_directory(
        cls,
        directory: Path,
        *,
        manifest_path: Path | None = None,
        verify_checksums: bool = True,
    ) -> "Bm25Retriever":
        return cls(
            load_corpus(directory, manifest_path=manifest_path, verify_checksums=verify_checksums)
        )

    def score(self, query: str) -> list[float]:
        """BM25 score of every chunk; each distinct query term contributes once."""
        terms = [term for term in dict.fromkeys(tokenize(query)) if term in self._idf]
        scores: list[float] = []
        for counts, length in zip(self._term_counts, self._lengths):
            norm = self.k1 * (1 - self.b + self.b * length / self._average_length)
            total = 0.0
            for term in terms:
                frequency = counts.get(term, 0)
                if frequency:
                    total += self._idf[term] * frequency * (self.k1 + 1) / (frequency + norm)
            scores.append(total)
        return scores

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        *,
        min_score: float = 0.0,
    ) -> list[RetrievedChunk]:
        """Same contract as :meth:`TfidfRetriever.retrieve`, including tie-breaking."""
        if not query.strip() or top_k < 1:
            return []
        if min_score < 0:
            raise ValueError("min_score must be non-negative")
        scores = self.score(query)
        ranked = sorted(
            range(len(self.chunks)),
            key=lambda index: (
                -scores[index],
                self.chunks[index].source,
                self.chunks[index].chunk_id,
            ),
        )[:top_k]
        return [
            RetrievedChunk(self.chunks[index], scores[index])
            for index in ranked
            if scores[index] > 0 and scores[index] >= min_score
        ]
