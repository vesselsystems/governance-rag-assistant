"""Offline retrieval evaluation, including abstention and chunk checks."""

from __future__ import annotations

from typing import Any

from .retrieval import TfidfRetriever


def _as_strings(value: Any) -> list[str]:
    """Normalize a scalar or list label from the JSON evaluation set."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _expected_citations(item: dict[str, Any], expected_sources: list[str]) -> list[str]:
    raw_citations = item.get("expected_citations", item.get("expected_citation"))
    citations = _as_strings(raw_citations)
    if citations:
        return citations

    # Accept a compact chunk label for small hand-authored sets.  An explicit
    # citation remains preferable because it cannot be ambiguous across files.
    raw_chunks = item.get("expected_chunks", item.get("expected_chunk"))
    chunks = _as_strings(raw_chunks)
    if chunks and expected_sources:
        return [f"[{source}#{chunk}]" for source in expected_sources for chunk in chunks]
    return []


def _summarize(rows: list[dict[str, Any]]) -> dict[str, float]:
    answerable = [row for row in rows if row["answerable"]]
    unanswerable = [row for row in rows if not row["answerable"]]

    source_hits = [row["hit_at_k"] for row in answerable if row["expected_sources"]]
    ranked_answerable = [row for row in answerable if row["rank"] is not None]
    citation_cases = [row for row in answerable if row["expected_citations"]]
    citation_hits = [row["citation_hit_at_k"] for row in citation_cases]
    passed = sum(1 for row in rows if row["passed"])
    correct_abstentions = sum(1 for row in unanswerable if row["no_evidence"])

    reciprocal_ranks = [
        1 / row["rank"] if row["rank"] is not None else 0.0 for row in answerable
    ]
    return {
        "questions": float(len(rows)),
        "answerable_questions": float(len(answerable)),
        "unanswerable_questions": float(len(unanswerable)),
        "hit_at_k": float(sum(source_hits) / len(source_hits)) if source_hits else 0.0,
        "mean_reciprocal_rank": (
            sum(reciprocal_ranks) / len(answerable) if answerable else 0.0
        ),
        "citation_evaluated_questions": float(len(citation_cases)),
        "citation_hit_at_k": (
            float(sum(citation_hits) / len(citation_hits)) if citation_hits else 0.0
        ),
        "unanswerable_no_evidence_rate": (
            float(correct_abstentions / len(unanswerable)) if unanswerable else 0.0
        ),
        "case_pass_rate": float(passed / len(rows)) if rows else 0.0,
        # This count makes it clear when MRR includes a zero for a miss.
        "ranked_answerable_questions": float(len(ranked_answerable)),
    }


def evaluate_retrieval(
    questions: list[dict[str, Any]],
    retriever: TfidfRetriever,
    top_k: int = 3,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Evaluate source retrieval, expected chunks, and unanswerable cases.

    Existing records with ``expected_source`` remain valid.  New records can set
    ``answerable`` to ``false`` and omit labels, or add ``expected_citations``
    for an exact chunk-level check.  Retrieval metrics do not assess generated
    answer correctness or citation entailment.
    """
    rows: list[dict[str, Any]] = []

    for item in questions:
        question = str(item["question"])
        results = retriever.retrieve(question, top_k=top_k)
        sources = [result.chunk.source for result in results]
        citations = [result.chunk.citation for result in results]
        expected_source_value = item.get("expected_source")
        expected_sources = _as_strings(expected_source_value)
        expected_citations = _expected_citations(item, expected_sources)
        explicit_answerable = item.get("answerable")
        answerable = (
            bool(explicit_answerable)
            if explicit_answerable is not None
            else bool(expected_sources or expected_citations)
        )
        split = str(item.get("split", "default"))

        source_rank = next(
            (
                index + 1
                for index, source in enumerate(sources)
                if source in expected_sources
            ),
            None,
        )
        citation_rank = next(
            (
                index + 1
                for index, citation in enumerate(citations)
                if citation in expected_citations
            ),
            None,
        )
        source_hit = source_rank is not None if expected_sources else None
        citation_hit = citation_rank is not None if expected_citations else None
        # Keep hit@k compatible with source-labeled cases, while allowing a
        # citation-only record to use its exact chunk as the primary label.
        primary_hit = source_hit if expected_sources else citation_hit
        rank = source_rank if expected_sources else citation_rank
        checks = [check for check in (source_hit, citation_hit) if check is not None]
        passed = all(checks) if answerable and checks else not answerable and not results

        rows.append(
            {
                "id": item.get("id"),
                "split": split,
                "question": item["question"],
                "answerable": answerable,
                "expected_source": expected_source_value,
                "expected_sources": expected_sources,
                "expected_citations": expected_citations,
                "retrieved_sources": sources,
                "retrieved_citations": citations,
                "hit_at_k": primary_hit if answerable else None,
                "citation_hit_at_k": citation_hit if answerable else None,
                "rank": rank if answerable else None,
                "citation_rank": citation_rank if answerable else None,
                "no_evidence": not results,
                "passed": passed,
            }
        )

    metrics: dict[str, Any] = _summarize(rows)
    splits = sorted({str(row["split"]) for row in rows})
    metrics["by_split"] = {
        split: _summarize([row for row in rows if row["split"] == split])
        for split in splits
    }
    return rows, metrics
