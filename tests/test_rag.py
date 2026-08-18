import json
from pathlib import Path

from governance_rag.corpus import chunk_text
from governance_rag.evaluation import evaluate_retrieval
from governance_rag.generation import NO_EVIDENCE, evidence_only_draft
from governance_rag.retrieval import TfidfRetriever

ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "data" / "documents"


def test_chunking_retains_source_and_rejects_bad_overlap() -> None:
    chunks = chunk_text("one two three four five", "demo.md", chunk_words=3, overlap_words=1)

    assert chunks
    assert all(chunk.source == "demo.md" for chunk in chunks)
    assert chunks[0].citation == "[demo.md#0]"


def test_retriever_returns_governance_evidence() -> None:
    retriever = TfidfRetriever.from_directory(CORPUS)
    results = retriever.retrieve("What belongs in an approval record?", top_k=3)

    assert results
    assert results[0].chunk.source == "model_risk_review_playbook.md"


def test_evaluation_questions_have_retrieval_signal() -> None:
    retriever = TfidfRetriever.from_directory(CORPUS)
    questions = json.loads(
        (ROOT / "evaluation" / "questions.json").read_text(encoding="utf-8")
    )
    rows, metrics = evaluate_retrieval(questions, retriever)

    assert len(rows) == len(questions)
    assert metrics["hit_at_k"] >= 0.8


def test_no_evidence_is_explicit() -> None:
    assert evidence_only_draft([]) == NO_EVIDENCE
