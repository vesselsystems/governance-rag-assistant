# Corpus status and provenance

This directory contains two clearly separated source types:

- **Repository-authored demo guidance:** `ai_data_governance_policy.md`,
  `incident_response_guide.md`, and `model_risk_review_playbook.md`. These are short teaching
  artifacts written for this repository. They are not an organisation's approved policy, legal
  advice, or evidence of an external standard. Their manifest entries have no upstream URL,
  publisher, revision, or external licence claim.
- **Official external snapshot:**
  `ppn_017_improving_transparency_of_ai_use_in_procurement.txt`, extracted from the verified UK
  Cabinet Office PDF described below. It is indexed as public source material, not as repository-
  authored guidance.

The checked-in [`../corpus_manifest.json`](../corpus_manifest.json) records the SHA-256 checksum
of every local text file. The loader verifies those bytes locally and never downloads a manifest
URL. The repository MIT licence does **not** license or replace the terms for the external PPN
snapshot; the PPN entry has its own Open Government Licence v3.0 metadata.

## Verified external snapshot

The external text was downloaded and extracted on **2026-08-18** from the official publication and
PDF. The raw PDF was verified against the supplied observed digest before extraction. The PDF is
not checked into this repository; the raw digest is recorded so a future source check can detect a
different download.

- **Publication:** [PPN 017: Improving transparency of AI use in procurement](https://www.gov.uk/government/publications/ppn-017-improving-transparency-of-ai-use-in-procurement)
- **PDF:** [PPN 017 PDF](https://assets.publishing.service.gov.uk/media/67af7ba0e270ceae39f9e279/PPN_017_Improving_transparency_of_AI_use_in_procurement.pdf)
- **Publisher:** UK Cabinet Office
- **Revision:** Updated February 2025
- **Terms:** [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
- **Extracted-text SHA-256:** `95cba453a3c44ea0641334365603c083b8f54fd227f501c91b17fc3825509ac1`
- **Raw PDF SHA-256:** `cb67e1910da3005a0160c0f2dcc3e8fdcc5de2a1fcc636ad2f6609199d73d62e`
- **Extraction:** `pdftotext -layout -enc UTF-8 (Xpdf 4.06)`; the checked-in file is the command output,
  with no added summary or editorial content.

The publisher page states that content is available under OGL v3.0 except where otherwise stated.
Review the linked licence and source page before redistributing or relying on the snapshot.

## Adding another public or official snapshot

Do not copy a document into this directory until its reuse terms and exact source can be verified.
Add a manifest entry with all of these fields:

- local `path` for the exact text snapshot and a `source_type` distinguishing it from demo files;
- publication `url`, direct `pdf_url` when applicable, and `publisher`;
- the source's `license` and `license_url` (or a documented permission statement);
- immutable `revision` (release, update, commit, or other publisher identifier);
- `retrieval_date` in ISO `YYYY-MM-DD` form;
- lowercase extracted-text `sha256` and, when applicable, `raw_pdf_sha256`;
- the extraction method in `extraction_method` when the source was converted to text.

Keep each source's terms separate from the repository's code licence. Run
`python scripts/verify_corpus_manifest.py` before an evaluation run.
