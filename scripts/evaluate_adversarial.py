"""Run deterministic prompt-boundary and document-poisoning fixture checks."""

from __future__ import annotations

import json
from pathlib import Path

from governance_rag.evaluation import evaluate_adversarial_fixtures

if __name__ == "__main__":
    root = Path(__file__).parents[1]
    cases = json.loads(
        (root / "evaluation" / "adversarial_questions.json").read_text(encoding="utf-8")
    )
    rows, metrics = evaluate_adversarial_fixtures(cases, root)
    report = {"metrics": metrics, "rows": rows}
    report_dir = root / "reports"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "adversarial_results.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2))
    for row in rows:
        print(f"{'PASS' if row['passed'] else 'FAIL'}: {row['id']}")
    if not all(row["passed"] for row in rows):
        raise SystemExit("adversarial fixture checks failed")
