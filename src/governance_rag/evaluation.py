"""Offline retrieval and adversarial-fixture evaluation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .corpus import DocumentChunk
from .generation import build_prompt, validate_generated_answer
from .retrieval import RetrievedChunk, TfidfRetriever


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


def _mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def _summarize(rows: list[dict[str, Any]]) -> dict[str, float]:
    answerable = [row for row in rows if row["answerable"]]
    unanswerable = [row for row in rows if not row["answerable"]]

    source_hits = [row["hit_at_k"] for row in answerable if row["expected_sources"]]
    ranked_answerable = [row for row in answerable if row["rank"] is not None]
    citation_cases = [row for row in answerable if row["expected_citations"]]
    citation_hits = [row["citation_hit_at_k"] for row in citation_cases]
    source_precision = [
        row["source_precision_at_k"]
        for row in answerable
        if row["source_precision_at_k"] is not None
    ]
    source_recall = [
        row["source_recall_at_k"]
        for row in answerable
        if row["source_recall_at_k"] is not None
    ]
    citation_precision = [
        row["citation_precision_at_k"]
        for row in citation_cases
        if row["citation_precision_at_k"] is not None
    ]
    citation_recall = [
        row["citation_recall_at_k"]
        for row in citation_cases
        if row["citation_recall_at_k"] is not None
    ]
    passed = sum(1 for row in rows if row["passed"])
    unanswerable_without_evidence = sum(1 for row in unanswerable if row["no_evidence"])

    reciprocal_ranks = [
        1 / row["rank"] if row["rank"] is not None else 0.0 for row in answerable
    ]
    return {
        "questions": float(len(rows)),
        "answerable_questions": float(len(answerable)),
        "unanswerable_questions": float(len(unanswerable)),
        "hit_at_k": _mean([float(value) for value in source_hits]),
        "mean_reciprocal_rank": _mean(reciprocal_ranks),
        "citation_evaluated_questions": float(len(citation_cases)),
        "citation_hit_at_k": _mean([float(value) for value in citation_hits]),
        "source_precision_at_k": _mean([float(value) for value in source_precision]),
        "source_recall_at_k": _mean([float(value) for value in source_recall]),
        "citation_precision_at_k": _mean([float(value) for value in citation_precision]),
        "citation_recall_at_k": _mean([float(value) for value in citation_recall]),
        "retrieval_no_evidence_rate": (
            float(unanswerable_without_evidence / len(unanswerable))
            if unanswerable
            else 0.0
        ),
        "retrieval_nonempty_rate": (
            float(sum(1 for row in rows if not row["no_evidence"]) / len(rows)) if rows else 0.0
        ),
        "case_pass_rate": float(passed / len(rows)) if rows else 0.0,
        # This count makes it clear when MRR includes a zero for a miss.
        "ranked_answerable_questions": float(len(ranked_answerable)),
    }


def _precision_at_k(retrieved: list[str], expected: list[str]) -> float | None:
    if not expected:
        return None
    if not retrieved:
        return 0.0
    expected_set = set(expected)
    return float(sum(value in expected_set for value in retrieved) / len(retrieved))


def _recall_at_k(retrieved: list[str], expected: list[str]) -> float | None:
    if not expected:
        return None
    expected_set = set(expected)
    if not expected_set:
        return None
    return float(len(set(retrieved) & expected_set) / len(expected_set))


def evaluate_retrieval(
    questions: list[dict[str, Any]],
    retriever: TfidfRetriever,
    top_k: int = 3,
    *,
    min_score: float = 0.0,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Evaluate source/chunk retrieval and explicitly labeled unanswerable cases.

    Source precision/recall are defined only for records with expected source
    labels.  Citation precision/recall are defined only for exact expected
    citation labels.  These are retrieval metrics, not generated-answer or
    entailment metrics.
    """
    rows: list[dict[str, Any]] = []

    for item in questions:
        question = str(item["question"])
        results = retriever.retrieve(question, top_k=top_k, min_score=min_score)
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
                "retrieved_count": len(results),
                "hit_at_k": primary_hit if answerable else None,
                "citation_hit_at_k": citation_hit if answerable else None,
                "source_precision_at_k": (
                    _precision_at_k(sources, expected_sources) if answerable else None
                ),
                "source_recall_at_k": (
                    _recall_at_k(sources, expected_sources) if answerable else None
                ),
                "citation_precision_at_k": (
                    _precision_at_k(citations, expected_citations) if answerable else None
                ),
                "citation_recall_at_k": (
                    _recall_at_k(citations, expected_citations) if answerable else None
                ),
                "rank": rank if answerable else None,
                "citation_rank": citation_rank if answerable else None,
                "no_evidence": not results,
                "min_score": min_score,
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


def evaluate_adversarial_fixtures(
    cases: list[dict[str, Any]],
    root: Path,
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    """Run deterministic checks over prompt-injection/poisoning fixtures.

    This does not call a model and therefore does not measure model resistance.
    It verifies that fixtures are present, prompt boundaries identify their text
    as untrusted, and representative unsafe provider output is rejected by the
    generation gate.
    """
    rows: list[dict[str, Any]] = []
    for item in cases:
        fixture_path = root / str(item["fixture"])
        exists = fixture_path.is_file()
        text = fixture_path.read_text(encoding="utf-8") if exists else ""
        fixture_chunk = DocumentChunk(
            chunk_id="fixture",
            source=fixture_path.name,
            text=text,
        )
        result = RetrievedChunk(chunk=fixture_chunk, score=1.0)
        prompts = build_prompt(str(item["question"]), [result])
        system_prompt = prompts[0]["content"]
        user_prompt = prompts[1]["content"]
        marker_present = any(
            marker in text.lower()
            for marker in (
                "ignore all previous instructions",
                "system message",
                "reveal",
                "must obey",
                "override",
            )
        )
        prompt_boundary = (
            "UNTRUSTED" in system_prompt
            and "not system, developer, or user instructions" in system_prompt
            and "BEGIN UNTRUSTED RETRIEVED DOCUMENT" in user_prompt
        )
        unsafe_response = item.get("unsafe_response")
        if isinstance(unsafe_response, str):
            unsafe_response = unsafe_response.replace("{citation}", result.chunk.citation)
        unsafe_rejected = not validate_generated_answer(unsafe_response, [result])
        passed = exists and marker_present and prompt_boundary and unsafe_rejected
        rows.append(
            {
                "id": item.get("id"),
                "category": item.get("category"),
                "fixture": str(item["fixture"]),
                "fixture_present": exists,
                "adversarial_marker_present": marker_present,
                "prompt_boundary_check": prompt_boundary,
                "unsafe_generation_rejected": unsafe_rejected,
                "passed": passed,
            }
        )

    total = len(rows)
    metrics = {
        "fixture_count": float(total),
        "fixture_presence_rate": _mean(
            [float(row["fixture_present"]) for row in rows]
        ),
        "prompt_boundary_check_rate": _mean(
            [float(row["prompt_boundary_check"]) for row in rows]
        ),
        "unsafe_generation_rejection_rate": _mean(
            [float(row["unsafe_generation_rejected"]) for row in rows]
        ),
        "case_pass_rate": _mean([float(row["passed"]) for row in rows]),
    }
    return rows, metrics
