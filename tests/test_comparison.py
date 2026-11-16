"""BM25 correctness, comparison metrics, threshold rule, and challenge-set integrity."""

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

from governance_rag.comparison import (
    decision_metrics,
    first_relevant_rank,
    mcnemar_exact,
    retrieval_metrics,
    select_threshold,
)
from governance_rag.corpus import DocumentChunk
from governance_rag.retrieval import Bm25Retriever, TfidfRetriever, tokenize

ROOT = Path(__file__).resolve().parents[1]
CHALLENGE = json.loads((ROOT / "evaluation" / "challenge_questions.json").read_text("utf-8"))


def _chunk(source: str, text: str, chunk_id: str = "0") -> DocumentChunk:
    return DocumentChunk(chunk_id=chunk_id, source=source, text=text)


# --- BM25 -------------------------------------------------------------------


def test_bm25_matches_hand_computed_scores() -> None:
    # N=3, lengths 2/3/1, avgdl=2; df(alpha)=2, df(gamma)=1; k1=1.5, b=0.75.
    retriever = Bm25Retriever(
        [_chunk("a.md", "alpha beta"), _chunk("b.md", "alpha gamma gamma"), _chunk("c.md", "delta")]
    )
    idf_alpha = math.log(1 + (3 - 2 + 0.5) / (2 + 0.5))
    idf_gamma = math.log(1 + (3 - 1 + 0.5) / (1 + 0.5))
    norm_b = 1.5 * (1 - 0.75 + 0.75 * 3 / 2)
    expected_b = idf_alpha * 2.5 / (1 + norm_b) + idf_gamma * 2 * 2.5 / (2 + norm_b)
    expected_a = idf_alpha * 2.5 / (1 + 1.5)

    results = retriever.retrieve("alpha gamma", top_k=3)

    assert [result.chunk.source for result in results] == ["b.md", "a.md"]
    assert results[0].score == pytest.approx(expected_b, rel=1e-9)
    assert results[1].score == pytest.approx(expected_a, rel=1e-9)


def test_bm25_rare_terms_outweigh_common_terms() -> None:
    retriever = Bm25Retriever(
        [_chunk("common.md", "policy policy"), _chunk("rare.md", "policy helpdesk")]
        + [_chunk(f"filler{i}.md", "policy text") for i in range(4)]
    )
    scores = dict(zip((c.source for c in retriever.chunks), retriever.score("policy helpdesk")))
    assert scores["rare.md"] > scores["common.md"]


def test_bm25_normalises_for_chunk_length() -> None:
    retriever = Bm25Retriever(
        [_chunk("short.md", "audit filler"), _chunk("long.md", "audit " + "filler " * 20)]
    )
    short, long = retriever.score("audit")
    assert short > long > 0


def test_bm25_returns_nothing_without_a_usable_query_term() -> None:
    retriever = Bm25Retriever([_chunk("a.md", "governance record")])
    assert retriever.retrieve("") == []
    assert retriever.retrieve("the and of") == []  # only stop words
    assert retriever.retrieve("sourdough") == []  # unseen term
    assert retriever.retrieve("governance", top_k=0) == []


def test_bm25_breaks_ties_like_the_tfidf_baseline() -> None:
    chunks = [
        _chunk("b.md", "same text"),
        _chunk("a.md", "same text"),
        _chunk("a.md", "same text", "1"),
    ]
    bm25 = [r.chunk.citation for r in Bm25Retriever(chunks).retrieve("same text", top_k=3)]
    tfidf = [r.chunk.citation for r in TfidfRetriever(chunks).retrieve("same text", top_k=3)]
    assert bm25 == tfidf == ["[a.md#0]", "[a.md#1]", "[b.md#0]"]


def test_bm25_rejects_invalid_settings() -> None:
    with pytest.raises(ValueError):
        Bm25Retriever([])
    with pytest.raises(ValueError):
        Bm25Retriever([_chunk("a.md", "text")], b=1.5)
    with pytest.raises(ValueError):
        Bm25Retriever([_chunk("a.md", "text")]).retrieve("text", min_score=-1)


def test_tokenizer_matches_tfidf_vocabulary() -> None:
    text = "The approval record shows AI-enabled data, e.g. lineage."
    vocabulary = TfidfRetriever([_chunk("a.md", text)]).vectorizer.get_feature_names_out()
    unigrams = {term for term in vocabulary if " " not in term}
    assert set(tokenize(text)) == unigrams


# --- comparison metrics -------------------------------------------------------


def _row(answerable: bool, rank: int | None, top1: float, split: str = "dev") -> dict:
    return {
        "answerable": answerable,
        "first_relevant_rank": rank,
        "top1_score": top1,
        "split": split,
    }


def test_first_relevant_rank_uses_any_expected_citation() -> None:
    assert first_relevant_rank(["[x#0]", "[y#1]", "[y#2]"], ["[y#2]", "[y#1]"]) == 2
    assert first_relevant_rank(["[x#0]"], ["[y#1]"]) is None


def test_retrieval_metrics_ignore_unanswerable_rows() -> None:
    rows = [_row(True, 1, 0.5), _row(True, 3, 0.4), _row(True, None, 0.2), _row(False, None, 0.9)]
    metrics = retrieval_metrics(rows)
    assert metrics["answerable_questions"] == 3
    assert metrics["hit_at_1"] == round(1 / 3, 4)
    assert metrics["hit_at_3"] == round(2 / 3, 4)
    assert metrics["mrr_at_3"] == round((1 + 1 / 3) / 3, 4)


def test_decision_metrics_count_both_error_types() -> None:
    rows = [_row(True, 1, 0.5), _row(True, None, 0.1), _row(False, None, 0.3), _row(False, None, 0)]
    metrics = decision_metrics(rows, threshold=0.2)
    assert metrics["false_abstentions"] == 1  # answerable 0.1 < 0.2
    assert metrics["false_answers"] == 1  # unanswerable 0.3 >= 0.2
    assert metrics["answered_with_wrong_evidence"] == 0
    assert metrics["balanced_accuracy"] == 0.5


def test_select_threshold_maximises_balanced_accuracy_with_low_tie_break() -> None:
    separable = [_row(True, 1, 0.6), _row(True, 1, 0.5), _row(False, None, 0.2)]
    assert select_threshold(separable) == 0.5
    # No threshold separates these; every candidate ties at 0.5, so take the lowest.
    inseparable = [_row(True, 1, 0.2), _row(False, None, 0.2)]
    assert select_threshold(inseparable) == 0.0


def test_mcnemar_exact_matches_the_binomial_tail() -> None:
    first = [_row(True, None, 0)] * 5 + [_row(True, 1, 0)] * 3
    second = [_row(True, 1, 0)] * 5 + [_row(True, 1, 0)] * 3
    result = mcnemar_exact(first, second, max_rank=1)
    assert (result["only_first_hits"], result["only_second_hits"]) == (0, 5)
    assert result["p_value_two_sided"] == 0.0625  # 2 * 0.5**5
    assert mcnemar_exact(first[:3], first[:3], max_rank=1)["p_value_two_sided"] == 1.0


# --- challenge set integrity --------------------------------------------------


def test_challenge_labels_reference_real_chunks() -> None:
    corpus = TfidfRetriever.from_directory(ROOT / "data" / "documents")
    citations = {chunk.citation for chunk in corpus.chunks}
    for item in CHALLENGE["questions"]:
        assert set(item["expected_citations"]) <= citations, item["id"]


def test_challenge_set_is_well_formed() -> None:
    protocol = CHALLENGE["protocol"]
    questions = CHALLENGE["questions"]
    assert {"threshold_rule", "retriever_settings", "top_k"} <= set(protocol)
    assert len({item["id"] for item in questions}) == len(questions)
    for item in questions:
        assert item["split"] in {"dev", "test"}
        assert item["design"] in protocol["design_values"]
        assert item["label_status"] in protocol["label_status_values"]
        assert bool(item["expected_citations"]) == item["answerable"], item["id"]
        assert item["rationale"].strip()
    for split in ("dev", "test"):
        kinds = {item["answerable"] for item in questions if item["split"] == split}
        assert kinds == {True, False}, f"{split} needs answerable and unanswerable questions"


def test_committed_comparison_report_is_current() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "compare_retrievers.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
