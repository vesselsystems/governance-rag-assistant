"""Retrieval evaluation before generation."""

from __future__ import annotations

from typing import Any

from .retrieval import TfidfRetriever


def evaluate_retrieval(
    questions: list[dict[str, Any]],
    retriever: TfidfRetriever,
    top_k: int = 3,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    """Compute hit@k and reciprocal rank using expected source labels."""
    rows: list[dict[str, Any]] = []
    hits = 0
    reciprocal_ranks: list[float] = []

    for item in questions:
        results = retriever.retrieve(str(item["question"]), top_k=top_k)
        sources = [result.chunk.source for result in results]
        expected = str(item["expected_source"])
        rank = next((index + 1 for index, source in enumerate(sources) if source == expected), None)
        if rank is not None:
            hits += 1
            reciprocal_ranks.append(1 / rank)
        else:
            reciprocal_ranks.append(0.0)
        rows.append(
            {
                "question": item["question"],
                "expected_source": expected,
                "retrieved_sources": sources,
                "hit_at_k": rank is not None,
                "rank": rank,
            }
        )

    total = len(questions)
    return rows, {
        "questions": float(total),
        "hit_at_k": float(hits / total) if total else 0.0,
        "mean_reciprocal_rank": sum(reciprocal_ranks) / total if total else 0.0,
    }
