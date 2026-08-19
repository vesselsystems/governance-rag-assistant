"""Run the labeled offline retrieval evaluation and write report artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from governance_rag.corpus import PUBLIC_SOURCE_TYPES, load_manifest, verify_manifest
from governance_rag.evaluation import evaluate_retrieval
from governance_rag.reporting import build_run_metadata
from governance_rag.retrieval import TfidfRetriever

if __name__ == "__main__":
    root = Path(__file__).parents[1]
    manifest = load_manifest(root / "data" / "corpus_manifest.json")
    checksum_verified_entries = verify_manifest(manifest, root / "data" / "documents")
    retriever = TfidfRetriever.from_directory(root / "data" / "documents")
    questions = json.loads((root / "evaluation" / "questions.json").read_text(encoding="utf-8"))
    rows, metrics = evaluate_retrieval(questions, retriever, top_k=3)

    report_dir = root / "reports"
    report_dir.mkdir(exist_ok=True)
    report = {
        "metadata": build_run_metadata(
            root,
            manifest_path=root / "data" / "corpus_manifest.json",
            config={
                "evaluation_file": "evaluation/questions.json",
                "top_k": 3,
                "min_score": 0.0,
            },
        ),
        "scope": {
            "name": "retrieval_labels",
            "generation_metrics": "not measured",
            "claim_metrics": "not measured; pending human annotation",
        },
        "corpus": {
            "corpus_id": manifest.corpus_id,
            "status": manifest.status,
            "verification_scope": manifest.verification_scope,
            "checksum_verified_documents": len(checksum_verified_entries),
            "checksum_verified_external_documents": sum(
                entry.source_type in PUBLIC_SOURCE_TYPES for entry in manifest.documents
            ),
            "raw_source_verification": "out_of_band_not_reproducible",
            "public_license_verification": "out_of_band_not_reproducible",
        },
        "measured_metrics": metrics,
        "metrics": metrics,
        "rows": rows,
    }
    (report_dir / "retrieval_results.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2))
    for row in rows:
        print(f"{'PASS' if row['passed'] else 'FAIL'}: {row['question']}")
    if not all(row["passed"] for row in rows):
        raise SystemExit("retrieval evaluation failed")
