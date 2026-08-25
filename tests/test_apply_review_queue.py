import importlib.util
import json
from pathlib import Path

from governance_rag.annotations import load_annotation_set

ROOT = Path(__file__).parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "apply_review_queue", ROOT / "scripts" / "apply_review_queue.py"
)
assert _SPEC and _SPEC.loader
_APPLY = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APPLY)


def _copy_inputs(tmp_path: Path) -> tuple[Path, Path]:
    evaluation = tmp_path / "evaluation"
    evaluation.mkdir()
    annotation_path = evaluation / "claim_annotations.json"
    queue_path = evaluation / "review_queue.json"
    annotation_path.write_text(
        (ROOT / "evaluation" / "claim_annotations.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    queue_path.write_text(
        (ROOT / "evaluation" / "review_queue.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return annotation_path, queue_path


def _terminal_queue() -> dict:
    queue = json.loads((ROOT / "evaluation" / "review_queue.json").read_text(encoding="utf-8"))
    decisions = {
        "claim_support": "supported",
        "citation_completeness": "complete",
        "citation_precision": "precise",
        "unsupported_claim": "no",
        "abstention_correctness": "correct",
    }
    for item in queue["items"]:
        item.update(
            {
                "decision": (
                    decisions[item["field"]]
                    if item["item_type"] == "claim_label"
                    else "entailed"
                    if item["item_type"] == "evidence_reference"
                    else "verified"
                ),
                "reviewer": "reviewer-1",
                "reviewed_at_utc": "2026-01-01T00:00:00Z",
                "rationale": "Synthetic test review.",
                "status": "approved",
            }
        )
    queue["review_status"] = "complete"
    queue["summary"]["status"] = "complete"
    queue["summary"]["pending_items"] = 0
    return queue


def _args(annotation_path: Path, queue_path: Path, *extra: str) -> list[str]:
    return [
        "--queue",
        str(queue_path),
        "--annotations",
        str(annotation_path),
        "--annotation-schema",
        str(ROOT / "evaluation" / "claim_annotations.schema.json"),
        "--fixtures",
        str(ROOT / "evaluation" / "evidence_contract_cases.json"),
        "--manifest",
        str(ROOT / "data" / "corpus_manifest.json"),
        *extra,
    ]


def test_pending_queue_is_refused_without_annotation_mutation(tmp_path: Path, capsys) -> None:
    annotation_path, queue_path = _copy_inputs(tmp_path)
    original = annotation_path.read_bytes()

    assert _APPLY.main(_args(annotation_path, queue_path)) == 1

    assert annotation_path.read_bytes() == original
    assert "pending queue item" in capsys.readouterr().err


def test_terminal_queue_dry_run_does_not_mutate_annotation(tmp_path: Path, capsys) -> None:
    annotation_path, queue_path = _copy_inputs(tmp_path)
    queue_path.write_text(json.dumps(_terminal_queue(), indent=2), encoding="utf-8")
    original = annotation_path.read_bytes()

    assert _APPLY.main(_args(annotation_path, queue_path)) == 0

    assert annotation_path.read_bytes() == original
    assert "dry-run" in capsys.readouterr().out


def test_terminal_queue_write_updates_annotation_copy(tmp_path: Path) -> None:
    annotation_path, queue_path = _copy_inputs(tmp_path)
    original = load_annotation_set(
        annotation_path,
        schema_path=ROOT / "evaluation" / "claim_annotations.schema.json",
        fixtures_path=ROOT / "evaluation" / "evidence_contract_cases.json",
    )
    queue_path.write_text(json.dumps(_terminal_queue(), indent=2), encoding="utf-8")

    assert _APPLY.main(_args(annotation_path, queue_path, "--write")) == 0

    updated = load_annotation_set(
        annotation_path,
        schema_path=ROOT / "evaluation" / "claim_annotations.schema.json",
        fixtures_path=ROOT / "evaluation" / "evidence_contract_cases.json",
    )
    assert updated["review_status"] == "reviewed"
    assert updated["reviewer"] == {"id": "reviewer-1", "status": "reviewed"}
    assert updated["fixture_binding"] == original["fixture_binding"]
    for before_case, after_case in zip(original["cases"], updated["cases"]):
        assert before_case["case_id"] == after_case["case_id"]
        assert before_case["question"] == after_case["question"]
        for before_claim, after_claim in zip(before_case["claims"], after_case["claims"]):
            assert before_claim["claim_id"] == after_claim["claim_id"]
            assert [
                {key: reference[key] for key in ("citation", "source", "chunk_id")}
                for reference in before_claim["evidence_references"]
            ] == [
                {key: reference[key] for key in ("citation", "source", "chunk_id")}
                for reference in after_claim["evidence_references"]
            ]
            assert all(
                after_claim[field]["status"] == "reviewed"
                and after_claim[field]["reviewer_id"] == "reviewer-1"
                and "Synthetic test review." in after_claim[field]["notes"]
                for field in _APPLY.CLAIM_LABEL_FIELDS
            )
            assert all(
                reference["status"] == "reviewed"
                and reference["reviewer_id"] == "reviewer-1"
                and "entailed" in reference["notes"]
                for reference in after_claim["evidence_references"]
            )
        assert before_case["abstention_correctness"]["label"] is None
        assert after_case["abstention_correctness"]["label"] == "correct"
        assert after_case["abstention_correctness"]["status"] == "reviewed"
