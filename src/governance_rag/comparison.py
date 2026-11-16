"""Retriever comparison and abstention analysis for the challenge question set.

The functions implement the protocol written into ``evaluation/challenge_questions.json``
before any result was computed. Everything is deterministic: identical inputs give
byte-identical reports, so a committed report can be checked for staleness in CI.
"""

from __future__ import annotations

import math
from statistics import median
from typing import Any, Protocol

from .retrieval import RetrievedChunk

DECIMALS = 4


class Retriever(Protocol):
    def retrieve(
        self, query: str, top_k: int = 3, *, min_score: float = 0.0
    ) -> list[RetrievedChunk]: ...


def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, DECIMALS) if denominator else None


def first_relevant_rank(citations: list[str], expected: list[str]) -> int | None:
    """1-based rank of the first retrieved citation that is an expected one."""
    expected_set = set(expected)
    for rank, citation in enumerate(citations, start=1):
        if citation in expected_set:
            return rank
    return None


def evaluate_questions(
    questions: list[dict[str, Any]], retriever: Retriever, top_k: int = 3
) -> list[dict[str, Any]]:
    """Retrieve for every question and record ranks and the top-1 score."""
    rows: list[dict[str, Any]] = []
    for item in questions:
        results = retriever.retrieve(str(item["question"]), top_k=top_k)
        citations = [result.chunk.citation for result in results]
        expected = [str(citation) for citation in item.get("expected_citations") or []]
        answerable = bool(item.get("answerable"))
        rows.append(
            {
                "id": item.get("id"),
                "split": item.get("split", "all"),
                "design": item.get("design", "original"),
                "answerable": answerable,
                "label_status": item.get("label_status", "original_set"),
                "question": item["question"],
                "expected_citations": expected,
                "retrieved": [
                    {"citation": result.chunk.citation, "score": round(result.score, DECIMALS)}
                    for result in results
                ],
                "top1_score": round(results[0].score, DECIMALS) if results else 0.0,
                "first_relevant_rank": (
                    first_relevant_rank(citations, expected) if answerable else None
                ),
            }
        )
    return rows


def retrieval_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Chunk-level hit@1, hit@3 and MRR@3 over answerable questions."""
    answerable = [row for row in rows if row["answerable"]]
    ranks = [row["first_relevant_rank"] for row in answerable]
    count = len(answerable)
    return {
        "answerable_questions": count,
        "hit_at_1": _rate(sum(rank == 1 for rank in ranks), count),
        "hit_at_3": _rate(sum(rank is not None for rank in ranks), count),
        "mrr_at_3": (
            round(sum(1 / rank for rank in ranks if rank) / count, DECIMALS) if count else None
        ),
    }


def mcnemar_exact(
    first: list[dict[str, Any]], second: list[dict[str, Any]], max_rank: int
) -> dict[str, Any]:
    """Exact two-sided McNemar test for a paired hit@k comparison.

    Only discordant questions (one retriever hits, the other misses) carry
    information; under the null each is a fair coin flip. Added after the
    protocol was written, so it is reported as a post-hoc check.
    """

    def hit(row: dict[str, Any]) -> bool:
        rank = row["first_relevant_rank"]
        return rank is not None and rank <= max_rank

    pairs = [
        (hit(a), hit(b))
        for a, b in zip(first, second, strict=True)
        if a["answerable"] and b["answerable"]
    ]
    only_first = sum(a and not b for a, b in pairs)
    only_second = sum(b and not a for a, b in pairs)
    discordant = only_first + only_second
    tail = sum(math.comb(discordant, k) for k in range(min(only_first, only_second) + 1))
    p_value = min(1.0, 2 * tail / 2**discordant) if discordant else 1.0
    return {
        "metric": f"hit@{max_rank}",
        "paired_questions": len(pairs),
        "only_first_hits": only_first,
        "only_second_hits": only_second,
        "p_value_two_sided": round(p_value, DECIMALS),
    }


def answers(row: dict[str, Any], threshold: float) -> bool:
    """The protocol's decision rule: answer when top-1 is positive and >= threshold."""
    return row["top1_score"] > 0 and row["top1_score"] >= threshold


def decision_metrics(rows: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    """Answer/abstain error rates for one threshold."""
    answerable = [row for row in rows if row["answerable"]]
    unanswerable = [row for row in rows if not row["answerable"]]
    false_abstentions = sum(not answers(row, threshold) for row in answerable)
    false_answers = sum(answers(row, threshold) for row in unanswerable)
    wrong_evidence = sum(
        answers(row, threshold) and row["first_relevant_rank"] is None for row in answerable
    )
    answer_rate = _rate(len(answerable) - false_abstentions, len(answerable))
    abstain_rate = _rate(len(unanswerable) - false_answers, len(unanswerable))
    balanced = (
        round((answer_rate + abstain_rate) / 2, DECIMALS)
        if answer_rate is not None and abstain_rate is not None
        else None
    )
    return {
        "threshold": round(threshold, DECIMALS),
        "answerable": len(answerable),
        "unanswerable": len(unanswerable),
        "false_abstentions": false_abstentions,
        "false_answers": false_answers,
        "answered_with_wrong_evidence": wrong_evidence,
        "false_abstention_rate": _rate(false_abstentions, len(answerable)),
        "false_answer_rate": _rate(false_answers, len(unanswerable)),
        "balanced_accuracy": balanced,
    }


def select_threshold(dev_rows: list[dict[str, Any]]) -> float:
    """Pre-registered rule: maximise dev balanced accuracy; ties go to the lower value."""
    candidates = sorted({0.0, *(row["top1_score"] for row in dev_rows if row["top1_score"] > 0)})

    def key(threshold: float) -> tuple[float, float]:
        balanced = decision_metrics(dev_rows, threshold)["balanced_accuracy"]
        return (balanced if balanced is not None else -1.0, -threshold)

    return max(candidates, key=key)


def score_distribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Top-1 score spread for answerable versus unanswerable questions."""

    def spread(values: list[float]) -> dict[str, float | None]:
        if not values:
            return {"min": None, "median": None, "max": None}
        return {
            "min": round(min(values), DECIMALS),
            "median": round(median(values), DECIMALS),
            "max": round(max(values), DECIMALS),
        }

    return {
        "answerable": spread([row["top1_score"] for row in rows if row["answerable"]]),
        "unanswerable": spread([row["top1_score"] for row in rows if not row["answerable"]]),
    }


def compare(
    challenge: list[dict[str, Any]],
    regression: list[dict[str, Any]],
    retriever: Retriever,
    top_k: int = 3,
) -> dict[str, Any]:
    """Every number the report shows for one retriever."""
    rows = evaluate_questions(challenge, retriever, top_k=top_k)
    regression_rows = evaluate_questions(regression, retriever, top_k=top_k)
    dev = [row for row in rows if row["split"] == "dev"]
    test = [row for row in rows if row["split"] == "test"]
    threshold = select_threshold(dev)
    designs = sorted({row["design"] for row in rows if row["answerable"]})
    answerable_rows = [row for row in rows if row["answerable"]]
    verified = [row for row in rows if row["label_status"] in {"human_verified", "human_corrected"}]
    return {
        "regression_set": retrieval_metrics(regression_rows),
        "challenge_dev": retrieval_metrics(dev),
        "challenge_test": retrieval_metrics(test),
        # The dev split only selects the abstention threshold; no ranking setting was
        # tuned on it, so pooling both splits is legitimate for ranking metrics.
        "challenge_all": retrieval_metrics(answerable_rows),
        "challenge_by_design": {
            design: retrieval_metrics([row for row in rows if row["design"] == design])
            for design in designs
        },
        "challenge_human_verified_only": (
            retrieval_metrics(verified) if verified else "no human-verified labels yet"
        ),
        "abstention": {
            "selected_threshold_from_dev": round(threshold, DECIMALS),
            "dev": decision_metrics(dev, threshold),
            "test": decision_metrics(test, threshold),
            "test_without_threshold": decision_metrics(test, 0.0),
            "score_distribution_dev": score_distribution(dev),
            "score_distribution_test": score_distribution(test),
        },
        "rows": rows,
    }
