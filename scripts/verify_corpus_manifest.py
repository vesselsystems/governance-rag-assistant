"""Verify local corpus files against their provenance manifest."""

from __future__ import annotations

import json
from pathlib import Path

from governance_rag.corpus import PUBLIC_SOURCE_TYPES, load_manifest, verify_manifest
from governance_rag.reporting import build_run_metadata

if __name__ == "__main__":
    root = Path(__file__).parents[1]
    manifest = load_manifest(root / "data" / "corpus_manifest.json")
    entries = verify_manifest(manifest, root / "data" / "documents")
    external_documents = [
        entry for entry in manifest.documents if entry.source_type in PUBLIC_SOURCE_TYPES
    ]
    result = {
        "metadata": build_run_metadata(
            root,
            manifest_path=root / "data" / "corpus_manifest.json",
            config={"operation": "local_manifest_verification", "network_access": False},
        ),
        "corpus_id": manifest.corpus_id,
        "status": manifest.status,
        "source_metadata_contract": "passed",
        "network_access": False,
        "blocker": manifest.blocker,
        "verification_scope": manifest.verification_scope,
        "local_text_checksum_verification": "passed",
        "raw_source_hashes_recorded": sum(
            entry.raw_source_digest is not None for entry in manifest.documents
        ),
        "raw_source_verification": "out_of_band_not_reproducible",
        "public_license_verification": "out_of_band_not_reproducible",
        "checksum_verified_documents": len(entries),
        "checksum_verified_external_documents": len(external_documents),
        "checksum_verified_paths": sorted(entry.path for entry in manifest.documents),
    }
    print(json.dumps(result, indent=2))
