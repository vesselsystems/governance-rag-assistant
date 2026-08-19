"""Summarize claim annotations without turning pending review into a result."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from governance_rag.annotations import (
    CASE_TYPES,
    evaluate_claim_annotations,
    load_annotation_set,
    validate_annotation_fixture_binding,
)
from governance_rag.reporting import build_run_metadata

if __name__ == "__main__":
    root = Path(__file__).parents[1]
    annotation_path = root / "evaluation" / "claim_annotations.json"
    schema_path = root / "evaluation" / "claim_annotations.schema.json"
    manifest_path = root / "data" / "corpus_manifest.json"
    annotation_set = load_annotation_set(annotation_path, schema_path=schema_path)
    contract_cases_path = root / "evaluation" / "evidence_contract_cases.json"
    try:
        contract_cases = json.loads(contract_cases_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(
            f"Could not load evidence-contract fixtures: {contract_cases_path}"
        ) from error
    if not isinstance(contract_cases, list):
        raise SystemExit("Evidence-contract fixtures must be a JSON list")
    if any(
        not isinstance(case, dict)
        or not isinstance(case.get("case_id"), str)
        or case.get("case_type") not in CASE_TYPES
        for case in contract_cases
    ):
        raise SystemExit("Evidence-contract fixtures have an invalid case_id or case_type")
    try:
        validate_annotation_fixture_binding(annotation_set, contract_cases)
    except ValueError as error:
        raise SystemExit(f"Evidence-contract fixture binding failed: {error}") from error
    fixture_types = Counter(case["case_type"] for case in contract_cases)
    evaluation = evaluate_claim_annotations(annotation_set)
    report = {
        "metadata": build_run_metadata(
            root,
            manifest_path=manifest_path,
            config={
                "annotation_file": annotation_path.relative_to(root).as_posix(),
                "fixture_file": contract_cases_path.relative_to(root).as_posix(),
                "schema_file": schema_path.relative_to(root).as_posix(),
                "schema_validation": "jsonschema_draft_2020_12_and_manual_validator",
                "fixture_binding": "immutable_content_and_sha256",
                "retrieval_metrics_included": False,
                "human_review_required": True,
            },
        ),
        "scope": {
            "name": "claim_level_evidence_contract",
            "claim_metrics_require_reviewed_labels": True,
            "retrieval_metrics": "reported separately; not copied into this report",
            "generation_quality": "not measured",
        },
        "fixture_inventory": {
            "status": "fixture_inventory_only; not reviewer labels or quality results",
            "case_count": len(contract_cases),
            "by_case_type": dict(sorted(fixture_types.items())),
            "failure_modes": {
                "unsupported_claim": "failure-mode fixture within its declared case_type",
                "citation_error": "failure-mode fixture within its declared case_type",
            },
        },
        **evaluation,
    }
    report_dir = root / "reports"
    report_dir.mkdir(exist_ok=True)
    report_path = report_dir / "claim_evaluation.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report["measured_metrics"], indent=2))
    print(f"reviewer_labels: {report['reviewer_labels']['count']}")
    pending = report["pending_review"]
    print(f"pending_review: {pending['status']} ({pending['counts']['label_fields']} fields)")
    print(f"wrote: {report_path}")
