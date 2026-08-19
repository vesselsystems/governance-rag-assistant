# Project 3 / Project 4 corpus boundary

Project 3 (`03_governance_rag_assistant`) owns the local governance corpus, its
`data/corpus_manifest.json`, deterministic chunk identifiers, retrieval labels, and evidence
contract annotations. The Project 3 index is intentionally not a shared or global corpus.

Project 4 (`04_responsible_ai_capstone`) owns its own application and data/index lifecycle. It
must not import Project 3 files, reuse Project 3 chunk identifiers, or copy Project 3 retrieval,
generation, or claim-evaluation results. A Project 3 report is scoped to the manifest hash and
configuration recorded in that report and cannot be presented as a Project 4 result.

If a future integration is approved, use an explicit versioned adapter rather than a filesystem
shortcut. The minimum contract is:

```text
EvidenceContract/v1
  corpus_manifest_sha256: 64-hex digest
  corpus_id: string
  source: string
  chunk_id: string
  citation: "[source#chunk_id]"
  text: string
  provenance: manifest metadata with locally checked extracted-text checksum
```

An adapter must validate this contract, preserve source licence/provenance, and keep evaluation
splits and report metadata separate. No adapter is implemented or exercised by this phase. This
boundary is also why the Project 3 claim report explicitly says that retrieval metrics are
reported separately and does not emit or copy any Project 4 result.
