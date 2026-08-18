"""Verify local corpus files against their provenance manifest."""

from __future__ import annotations

import json
from pathlib import Path

from governance_rag.corpus import load_manifest, verify_manifest

if __name__ == "__main__":
    root = Path(__file__).parents[1]
    manifest = load_manifest(root / "data" / "corpus_manifest.json")
    entries = verify_manifest(manifest, root / "data" / "documents")
    external_documents = [
        entry for entry in manifest.documents if entry.source_type == "official_external"
    ]
    result = {
        "corpus_id": manifest.corpus_id,
        "status": manifest.status,
        "blocker": manifest.blocker,
        "verified_documents": len(entries),
        "verified_external_documents": len(external_documents),
        "verified_paths": sorted(entry.path for entry in manifest.documents),
    }
    print(json.dumps(result, indent=2))
