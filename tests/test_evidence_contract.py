import json
from pathlib import Path

import pytest

from governance_rag.annotations import (
    PARTIALLY_REVIEWED,
    PENDING_REVIEW,
    evaluate_claim_annotations,
    load_annotation_set,
    validate_annotation_fixture_binding,
    validate_annotation_set,
    validate_declared_schema,
)

ROOT = Path(__file__).parents[1]


def _reviewed_label(label: str) -> dict[str, str]:
    return {"label": label, "status": "reviewed", "reviewer_id": "reviewer-1"}


def _pending_label() -> dict[str, None | str]:
    return {"label": None, "status": PENDING_REVIEW}


def _sample_annotation_set() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "review_status": "reviewed",
        "reviewer": {"id": "reviewer-1", "status": "reviewed"},
        "fixture_binding": {
            "fixture_file": "evaluation/evidence_contract_cases.json",
            "algorithm": "sha256-canonical-json-v1",
        },
        "cases": [
            {
                "case_id": "sample-01",
                "split": "held_out",
                "case_type": "answerable",
                "question": "What belongs in an approval record?",
                "answer": "The record states its intended use. [demo.md#0]",
                "review_scope": [
                    "claim_support",
                    "citation_completeness",
                    "citation_precision",
                ],
                "fixture_sha256": "a" * 64,
                "abstention_correctness": _reviewed_label("not_applicable"),
                "claims": [
                    {
                        "claim_id": "sample-01-claim-1",
                        "claim_text": "The record states its intended use.",
                        "claim_support": _reviewed_label("supported"),
                        "citation_completeness": _reviewed_label("complete"),
                        "citation_precision": _reviewed_label("incorrect"),
                        "unsupported_claim": _reviewed_label("no"),
                        "evidence_references": [
                            {
                                "citation": "[not-retrieved.md#9]",
                                "source": "not-retrieved.md",
                                "chunk_id": "9",
                                "status": "reviewed",
                                "reviewer_id": "reviewer-1",
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_checked_in_claim_annotations_are_explicitly_pending() -> None:
    annotation_set = load_annotation_set(ROOT / "evaluation" / "claim_annotations.json")
    report = evaluate_claim_annotations(annotation_set)

    assert annotation_set["review_status"] == PENDING_REVIEW
    assert annotation_set["reviewer"]["id"] is None
    assert {case["case_type"] for case in annotation_set["cases"]} == {
        "answerable",
        "unanswerable",
        "adversarial",
        "ambiguous",
    }
    assert report["reviewer_labels"]["count"] == 0
    assert report["pending_review"]["status"] == PENDING_REVIEW
    assert report["pending_review"]["counts"]["cases"] == len(annotation_set["cases"])
    assert report["measured_metrics"]["claim_support"]["rate"] is None
    assert report["measured_metrics"]["citation_precision"]["rate"] is None
    assert report["measured_metrics"]["unsupported_claims"]["rate"] is None


def test_reviewed_labels_are_measured_without_treating_citation_as_support() -> None:
    report = evaluate_claim_annotations(_sample_annotation_set())
    metrics = report["measured_metrics"]

    assert metrics["claim_support"]["rate"] == 1.0
    assert metrics["citation_completeness"]["rate"] == 1.0
    assert metrics["citation_precision"]["rate"] == 0.0
    assert metrics["unsupported_claims"]["rate"] == 0.0
    assert metrics["claim_review_completion_rate"] == 1.0
    assert report["pending_review"]["counts"]["label_fields"] == 0
    assert report["reviewer_labels"]["count"] == 5
    assert report["measured_metrics"]["review_completion"]["rate"] == 1.0
    assert report["reviewed_evidence_references"]["count"] == 1


def test_pending_unknown_question_is_not_counted_as_correct_abstention() -> None:
    annotation_set = _sample_annotation_set()
    case = annotation_set["cases"][0]
    case["case_id"] = "unknown-01"
    case["case_type"] = "unanswerable"
    case["question"] = "What is the international travel reimbursement limit?"
    case["answer"] = "I could not find supporting evidence in the indexed documents."
    case["claims"] = []
    case["abstention_correctness"] = _pending_label()
    annotation_set["review_status"] = PENDING_REVIEW
    annotation_set["reviewer"] = {"id": None, "status": PENDING_REVIEW}

    report = evaluate_claim_annotations(annotation_set)

    assert report["measured_metrics"]["abstention_correctness"]["rate"] is None
    assert report["pending_review"]["counts"]["label_fields"] == 1
    assert report["pending_review"]["counts"]["evidence_references"] == 0
    assert report["rows"][0]["review_status"] == PENDING_REVIEW


def test_pending_evidence_reference_blocks_claim_completion() -> None:
    annotation_set = _sample_annotation_set()
    reference = annotation_set["cases"][0]["claims"][0]["evidence_references"][0]
    reference["status"] = PENDING_REVIEW
    reference.pop("reviewer_id")
    annotation_set["review_status"] = PARTIALLY_REVIEWED
    annotation_set["reviewer"] = {"id": "reviewer-1", "status": PARTIALLY_REVIEWED}

    report = evaluate_claim_annotations(annotation_set)

    assert report["measured_metrics"]["fully_reviewed_claims"] == 0
    assert report["measured_metrics"]["pending_evidence_reference_count"] == 1
    assert report["pending_review"]["counts"]["evidence_references"] == 1
    assert report["pending_review"]["counts"]["review_items"] == 1


def test_invalid_unsupported_claim_label_fails_closed() -> None:
    annotation_set = _sample_annotation_set()
    annotation_set["cases"][0]["claims"][0]["unsupported_claim"] = _reviewed_label(
        "unsupported"
    )

    with pytest.raises(ValueError, match="unsupported_claim.label"):
        validate_annotation_set(annotation_set)


def test_reviewed_label_requires_reviewer_identity() -> None:
    annotation_set = _sample_annotation_set()
    annotation_set["reviewer"] = {"id": None, "status": PENDING_REVIEW}
    annotation_set["review_status"] = PENDING_REVIEW
    annotation_set["cases"][0]["claims"][0]["claim_support"] = {
        "label": "supported",
        "status": "reviewed",
    }

    with pytest.raises(ValueError, match="claim_support requires reviewer_id"):
        validate_annotation_set(annotation_set)


def test_declared_schema_and_manual_validator_reject_extra_properties() -> None:
    annotation_set = _sample_annotation_set()
    schema_path = ROOT / "evaluation" / "claim_annotations.schema.json"
    validate_declared_schema(annotation_set, schema_path)
    annotation_set["unexpected"] = True

    with pytest.raises(ValueError, match="unknown fields"):
        validate_annotation_set(annotation_set)
    with pytest.raises(ValueError, match="(?i)additional properties"):
        validate_declared_schema(annotation_set, schema_path)


def test_fixture_binding_rejects_immutable_question_changes() -> None:
    annotation_set = load_annotation_set(ROOT / "evaluation" / "claim_annotations.json")
    fixtures = json.loads(
        (ROOT / "evaluation" / "evidence_contract_cases.json").read_text(encoding="utf-8")
    )
    fixtures[0]["question"] = "Changed after annotation"

    with pytest.raises(ValueError, match="immutable fields|fixture_sha256"):
        validate_annotation_fixture_binding(annotation_set, fixtures)


def test_annotation_schema_fixture_mentions_pending_status() -> None:
    schema = json.loads(
        (ROOT / "evaluation" / "claim_annotations.schema.json").read_text(encoding="utf-8")
    )

    assert schema["properties"]["review_status"]["enum"]
    assert PENDING_REVIEW in schema["properties"]["review_status"]["enum"]
    assert "claim_support" in schema["$defs"]["claim"]["required"]
    assert "citation_completeness" in schema["$defs"]["claim"]["required"]
    assert "citation_precision" in schema["$defs"]["claim"]["required"]
    assert "unsupported_claim" in schema["$defs"]["claim"]["required"]
    assert "evidence_references" in schema["$defs"]["claim"]["required"]
