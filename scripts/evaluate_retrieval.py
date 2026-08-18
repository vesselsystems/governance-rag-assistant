"""Run the labeled retrieval evaluation and write report artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from governance_rag.evaluation import evaluate_retrieval
from governance_rag.retrieval import TfidfRetriever

if __name__ == "__main__":
    root = Path(__file__).parents[1]
    retriever = TfidfRetriever.from_directory(root / "data" / "documents")
    questions = json.loads((root / "evaluation" / "questions.json").read_text(encoding="utf-8"))
    rows, metrics = evaluate_retrieval(questions, retriever, top_k=3)

    report_dir = root / "reports"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "retrieval_results.json").write_text(
        json.dumps({"metrics": metrics, "rows": rows}, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2))
    for row in rows:
        print(f"{'PASS' if row['passed'] else 'FAIL'}: {row['question']}")
