import json
from pathlib import Path

import pytest

import governance_rag.generation as generation
from governance_rag.corpus import chunk_text
from governance_rag.evaluation import evaluate_retrieval
from governance_rag.generation import NO_EVIDENCE, answer_question, evidence_only_draft
from governance_rag.retrieval import RetrievedChunk, TfidfRetriever

ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "data" / "documents"


def _results() -> list[RetrievedChunk]:
    retriever = TfidfRetriever.from_directory(CORPUS)
    return retriever.retrieve("What belongs in an approval record?", top_k=3)


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def test_chunking_retains_source_and_rejects_bad_overlap() -> None:
    chunks = chunk_text("one two three four five", "demo.md", chunk_words=3, overlap_words=1)

    assert chunks
    assert all(chunk.source == "demo.md" for chunk in chunks)
    assert chunks[0].citation == "[demo.md#0]"
    with pytest.raises(ValueError, match="overlap_words"):
        chunk_text("one two three", "demo.md", chunk_words=2, overlap_words=2)


def test_retriever_returns_governance_evidence() -> None:
    retriever = TfidfRetriever.from_directory(CORPUS)
    results = retriever.retrieve("What belongs in an approval record?", top_k=3)

    assert results
    assert results[0].chunk.source == "model_risk_review_playbook.md"


def test_evaluation_questions_cover_held_out_and_unanswerable_cases() -> None:
    retriever = TfidfRetriever.from_directory(CORPUS)
    questions = json.loads(
        (ROOT / "evaluation" / "questions.json").read_text(encoding="utf-8")
    )
    rows, metrics = evaluate_retrieval(questions, retriever)

    assert len(rows) == len(questions)
    assert metrics["hit_at_k"] >= 0.8
    assert metrics["citation_hit_at_k"] >= 0.8
    assert metrics["source_precision_at_k"] >= 0.0
    assert metrics["source_recall_at_k"] >= 0.8
    assert metrics["citation_recall_at_k"] >= 0.8
    assert metrics["unanswerable_no_evidence_rate"] == 1.0
    assert metrics["by_split"]["held_out"]["unanswerable_questions"] == 2.0
    assert metrics["by_split"]["public"]["questions"] == 4.0
    assert metrics["by_split"]["public"]["case_pass_rate"] == 1.0


def test_no_evidence_is_explicit() -> None:
    assert evidence_only_draft([]) == NO_EVIDENCE


def test_malformed_provider_output_falls_back(monkeypatch) -> None:
    results = _results()
    malformed = b'{"choices": [{"message": {"content": null}}]}'
    monkeypatch.setattr(generation, "urlopen", lambda *args, **kwargs: _FakeResponse(malformed))

    answer, mode = answer_question(
        "What belongs in an approval record?",
        results,
        api_key="test-key",
        model="test-model",
    )

    assert answer == evidence_only_draft(results)
    assert mode == "evidence-only (LLM fallback)"


def test_invalid_provider_citations_fall_back(monkeypatch) -> None:
    results = _results()
    payload = json.dumps(
        {
            "choices": [
                {"message": {"content": "The record needs more detail [not-retrieved.md#9]"}}
            ]
        }
    ).encode("utf-8")
    monkeypatch.setattr(generation, "urlopen", lambda *args, **kwargs: _FakeResponse(payload))

    answer, mode = answer_question(
        "What belongs in an approval record?",
        results,
        api_key="test-key",
        model="test-model",
    )

    assert not generation.validate_citations(
        "The record needs more detail [not-retrieved.md#9]", results
    )
    assert answer == evidence_only_draft(results)
    assert mode == "evidence-only (LLM fallback)"


def test_provider_failure_falls_back(monkeypatch) -> None:
    results = _results()

    def fail(*args, **kwargs):
        raise OSError("provider unavailable")

    monkeypatch.setattr(generation, "urlopen", fail)

    answer, mode = answer_question(
        "What belongs in an approval record?",
        results,
        api_key="test-key",
        model="test-model",
    )

    assert answer == evidence_only_draft(results)
    assert mode == "evidence-only (LLM fallback)"


def test_valid_retrieved_citation_allows_llm_mode(monkeypatch) -> None:
    results = _results()
    citation = results[0].chunk.citation
    payload = json.dumps(
        {"choices": [{"message": {"content": f"The record has required fields. {citation}"}}]}
    ).encode("utf-8")
    monkeypatch.setattr(generation, "urlopen", lambda *args, **kwargs: _FakeResponse(payload))

    answer, mode = answer_question(
        "What belongs in an approval record?",
        results,
        api_key="test-key",
        model="test-model",
    )

    assert answer == f"The record has required fields. {citation}"
    assert mode == "llm"


def test_zero_score_evidence_never_calls_provider(monkeypatch) -> None:
    result = RetrievedChunk(chunk=chunk_text("unrelated", "demo.md")[0], score=0.0)

    def unexpected_call(*args, **kwargs):
        raise AssertionError("provider should not be called for zero-score evidence")

    monkeypatch.setattr(generation, "generate_openai_compatible", unexpected_call)

    answer, mode = answer_question(
        "What is not in this corpus?",
        [result],
        api_key="test-key",
        model="test-model",
    )

    assert answer == NO_EVIDENCE
    assert mode == "evidence-only"


def test_no_evidence_never_calls_provider(monkeypatch) -> None:
    def unexpected_call(*args, **kwargs):
        raise AssertionError("provider should not be called without evidence")

    monkeypatch.setattr(generation, "generate_openai_compatible", unexpected_call)

    answer, mode = answer_question(
        "What is not in this corpus?",
        [],
        api_key="test-key",
        model="test-model",
    )

    assert answer == NO_EVIDENCE
    assert mode == "evidence-only"
