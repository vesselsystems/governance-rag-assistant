"""Validate representative provider-output cases without calling a model."""

from __future__ import annotations

import json
from pathlib import Path

from governance_rag.generation import validate_generated_answer
from governance_rag.reporting import build_run_metadata
from governance_rag.retrieval import TfidfRetriever

if __name__ == "__main__":
    root = Path(__file__).parents[1]
    retriever = TfidfRetriever.from_directory(root / "data" / "documents")
    cases = json.loads(
        (root / "evaluation" / "generation_cases.json").read_text(encoding="utf-8")
    )
    results = retriever.retrieve("What belongs in an approval record?", top_k=3)
    if not results:
        raise SystemExit("generation validation requires a deterministic retrieval result")

    rows: list[dict[str, object]] = []
    for case in cases:
        response = case.get("response")
        if isinstance(response, str):
            response = response.replace("{citation}", results[0].chunk.citation)
        valid = validate_generated_answer(response, results)
        expected = bool(case["expected_valid"])
        rows.append(
            {
                "id": case.get("id"),
                "expected_valid": expected,
                "observed_valid": valid,
                "passed": valid == expected,
            }
        )

    metrics = {
        "cases": len(rows),
        "passed": sum(1 for row in rows if row["passed"]),
        "case_pass_rate": (
            sum(1 for row in rows if row["passed"]) / len(rows) if rows else 0.0
        ),
        "scope": "structural provider-output validation only; no model was called",
    }
    report = {
        "metadata": build_run_metadata(
            root,
            manifest_path=root / "data" / "corpus_manifest.json",
            config={
                "evaluation_file": "evaluation/generation_cases.json",
                "retrieval_question": "What belongs in an approval record?",
                "top_k": 3,
            },
        ),
        "scope": {
            "name": "structural_generation_gate",
            "claim_metrics": "not measured; pending human annotation",
            "retrieval_metrics": "not measured by this script",
        },
        "measured_metrics": metrics,
        "metrics": metrics,
        "rows": rows,
    }
    report_dir = root / "reports"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "generation_validation.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2))
    for row in rows:
        print(f"{'PASS' if row['passed'] else 'FAIL'}: {row['id']}")
    if not all(row["passed"] for row in rows):
        raise SystemExit("generation validation failed")
