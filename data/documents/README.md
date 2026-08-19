# Corpus status and provenance

This directory contains two clearly separated source types:

- **Repository-authored demo guidance:** `ai_data_governance_policy.md`,
  `incident_response_guide.md`, and `model_risk_review_playbook.md`. These are short teaching
  artifacts written for this repository. They are not an organisation's approved policy, legal
  advice, or evidence of an external standard. Their manifest entries have no upstream URL,
  publisher, revision, or external licence claim.
- **External source snapshot:**
  `ppn_017_improving_transparency_of_ai_use_in_procurement.txt`, extracted from a UK Cabinet
  Office publication record described below. It is indexed as public source material, not as
  repository-authored guidance.

The checked-in [`../corpus_manifest.json`](../corpus_manifest.json) records the SHA-256 checksum
of every local text file. The loader verifies those bytes locally and never downloads a manifest
URL. The repository MIT licence does **not** license or replace the terms for the external PPN
snapshot; the PPN entry has its own Open Government Licence v3.0 metadata. Raw-source and public-
licence verification are out-of-band and not reproducible in this workspace.

## External source record

The external text was acquired and extracted on **2026-08-18** from the publication and PDF
metadata recorded below. The raw PDF is not checked into this repository; the acquisition-record
raw-source SHA-256 is retained as a lookup value, not independently verified by the local loader.

- **Publication:** [PPN 017: Improving transparency of AI use in procurement](https://www.gov.uk/government/publications/ppn-017-improving-transparency-of-ai-use-in-procurement)
- **PDF:** [PPN 017 PDF](https://assets.publishing.service.gov.uk/media/67af7ba0e270ceae39f9e279/PPN_017_Improving_transparency_of_AI_use_in_procurement.pdf)
- **Publisher:** UK Cabinet Office
- **Revision:** Updated February 2025
- **Terms:** [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
- **Extracted-text SHA-256 (locally checked):** `95cba453a3c44ea0641334365603c083b8f54fd227f501c91b17fc3825509ac1`
- **Recorded raw-source SHA-256:** `cb67e1910da3005a0160c0f2dcc3e8fdcc5de2a1fcc636ad2f6609199d73d62e`
- **Extraction:** `pdftotext -layout -enc UTF-8 (Xpdf 4.06)`; the checked-in file is the command output,
  with no added summary or editorial content.

The publisher page states that content is available under OGL v3.0 except where otherwise stated.
The public-licence terms and raw PDF digest are not independently verified or reproducible in this
workspace; review the linked licence and source record before redistributing or relying on the snapshot.

## Adding another public or official snapshot

No new snapshot is added in the evidence-contract phase. Do not copy a document into this
directory until its reuse terms and exact source can be verified. The complete fail-closed
staging and update procedure is [`../../docs/ingestion_update.md`](../../docs/ingestion_update.md).
Add a manifest entry with all of these fields:

- local `path` for the exact text snapshot and a `source_type` distinguishing it from demo files;
- publication `url`, direct `pdf_url` when applicable, and `publisher`;
- the source's `license` and `license_url` (or a documented permission statement);
- immutable `revision` (release, update, commit, or other publisher identifier);
- `retrieval_date` in ISO `YYYY-MM-DD` form;
- lowercase extracted-text `sha256` and, when applicable, recorded `raw_source_sha256`;
- the extraction method in `extraction_method` when the source was converted to text.

Keep each source's terms separate from the repository's code licence. Run
`python scripts/verify_corpus_manifest.py` before an evaluation run. The validator requires
public-source URL, publisher, licence, revision, retrieval date, a recorded raw-source SHA-256,
and extracted-text SHA-256 metadata. It fails closed on untracked or modified local files and
locally verifies only the extracted-text bytes. It never downloads a URL.
