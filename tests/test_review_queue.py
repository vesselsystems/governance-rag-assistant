import copy
import importlib.util
import json
from pathlib import Path

import pytest

from governance_rag.annotations import load_annotation_set

ROOT = Path(__file__).parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "validate_reviews", ROOT / "scripts" / "validate_reviews.py"
)
assert _SPEC and _SPEC.loader
_REVIEWS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_REVIEWS)
_validate_schema = _REVIEWS._validate_schema
validate_review_queue = _REVIEWS.validate_review_queue


def _inputs() -> tuple[dict, dict, dict]:
    queue = json.loads((ROOT / "evaluation" / "review_queue.json").read_text(encoding="utf-8"))
    annotations = load_annotation_set(
        ROOT / "evaluation" / "claim_annotations.json",
        schema_path=ROOT / "evaluation" / "claim_annotations.schema.json",
    )
    manifest = json.loads((ROOT / "data" / "corpus_manifest.json").read_text(encoding="utf-8"))
    return queue, annotations, manifest


def test_checked_in_review_queue_has_declared_scope_and_blockers() -> None:
    queue, annotations, manifest = _inputs()
    _validate_schema(queue, ROOT / "evaluation" / "review_queue.schema.json")

    counts = validate_review_queue(queue, annotations, manifest)

    assert counts == {
        "total_items": 32,
        "claim_label_decisions": 26,
        "evidence_reference_decisions": 5,
        "external_source_license_reviews": 1,
        "pending_items": 32,
        "pending_blockers": 32,
    }
    assert all(item["status"] == "pending" for item in queue["items"])
    assert all(item["decision"] is None for item in queue["items"])


def test_queue_rejects_duplicate_and_unknown_case_ids() -> None:
    queue, annotations, manifest = _inputs()
    queue["items"][1]["item_id"] = queue["items"][0]["item_id"]
    with pytest.raises(ValueError, match="duplicate item_id"):
        validate_review_queue(queue, annotations, manifest)

    queue, annotations, manifest = _inputs()
    queue["items"][0]["item_id"] = "claim-label/not-an-annotation-case/abstention_correctness"
    with pytest.raises(ValueError, match="does not match an annotation case"):
        validate_review_queue(queue, annotations, manifest)


def test_queue_rejects_pending_as_complete_summary() -> None:
    queue, annotations, manifest = _inputs()
    queue["summary"]["status"] = "complete"
    with pytest.raises(ValueError, match="pending-as-complete"):
        validate_review_queue(queue, annotations, manifest)


def test_pending_queue_rejects_manually_reviewed_label() -> None:
    queue, annotations, manifest = _inputs()
    record = annotations["cases"][0]["abstention_correctness"]
    record.update(label="correct", status="reviewed", reviewer_id="reviewer-1")

    with pytest.raises(ValueError, match="pending queue item.*pending annotation"):
        validate_review_queue(queue, annotations, manifest)


def test_pending_queue_rejects_manually_reviewed_evidence_reference() -> None:
    queue, annotations, manifest = _inputs()
    record = annotations["cases"][0]["claims"][0]["evidence_references"][0]
    record.update(status="reviewed", reviewer_id="reviewer-1")

    with pytest.raises(ValueError, match="pending queue item.*pending annotation"):
        validate_review_queue(queue, annotations, manifest)


def test_terminal_queue_item_may_bind_to_pending_annotation() -> None:
    queue, annotations, manifest = _inputs()
    item = queue["items"][0]
    item.update(
        {
            "status": "approved",
            "decision": "correct",
            "reviewer": "reviewer-1",
            "reviewed_at_utc": "2026-01-01T00:00:00Z",
            "rationale": "Synthetic test review.",
        }
    )
    queue["summary"]["pending_items"] -= 1

    counts = validate_review_queue(queue, annotations, manifest)

    assert counts["pending_items"] == 31


def test_queue_rejects_manifest_document_metadata_drift() -> None:
    queue, annotations, manifest = _inputs()
    manifest["documents"][3]["revision"] = "Changed after queue creation"

    with pytest.raises(ValueError, match="manifest_document_sha256"):
        validate_review_queue(queue, annotations, manifest)


def test_completed_item_requires_evidence_and_valid_utc_time() -> None:
    queue, annotations, manifest = _inputs()
    item = queue["items"][0]
    item.update(
        {
            "status": "approved",
            "decision": "correct",
            "reviewer": "reviewer-1",
            "reviewed_at_utc": "2026-01-01T00:00:00Z",
            "rationale": "Reviewed against the fixture.",
            "evidence_refs": [],
        }
    )
    with pytest.raises(ValueError, match="evidence"):
        validate_review_queue(queue, annotations, manifest)

    queue, annotations, manifest = _inputs()
    item = queue["items"][0]
    item.update(
        {
            "status": "approved",
            "decision": "correct",
            "reviewer": "reviewer-1",
            "reviewed_at_utc": "2026-02-30T00:00:00Z",
            "rationale": "Reviewed against the fixture.",
        }
    )
    with pytest.raises(ValueError, match="valid UTC timestamp"):
        validate_review_queue(queue, annotations, manifest)


def test_schema_rejects_missing_required_queue_field() -> None:
    queue, _, _ = _inputs()
    malformed = copy.deepcopy(queue)
    del malformed["items"][0]["question"]
    with pytest.raises(ValueError, match="JSON Schema validation"):
        _validate_schema(malformed, ROOT / "evaluation" / "review_queue.schema.json")


def test_schema_requires_manifest_document_digest() -> None:
    queue, _, _ = _inputs()
    malformed = copy.deepcopy(queue)
    del malformed["manifest_document_sha256"]

    with pytest.raises(ValueError, match="JSON Schema validation"):
        _validate_schema(malformed, ROOT / "evaluation" / "review_queue.schema.json")
