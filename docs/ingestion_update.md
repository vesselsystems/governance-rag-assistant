# Public-source ingestion and update procedure

> **Fail-closed procedure:** this repository does not download source URLs at runtime and this
> phase does not add a raw dataset. A URL in `data/corpus_manifest.json` is metadata, not a fetch
> instruction.

The indexed corpus remains the four local text snapshots whose extracted bytes pass the checked-in
manifest checksums. Do not claim a larger corpus, a new revision, or new evaluation results until
the steps below have been completed and reviewed. Raw-source and public-licence verification is
out-of-band and not reproducible in this workspace. Do not commit raw PDFs, browser artifacts,
private data, credentials, or `.env` files.

## Before an update

1. Obtain authorization and confirm that the public source may be used. Acquisition must happen
   outside the application/runtime path; no script in this repository performs the download.
2. Record the publication URL, direct raw URL when applicable, publisher, licence/permission
   statement, immutable revision, and retrieval date (`YYYY-MM-DD`). These are source-record
   fields, not proof that this offline workspace verified the remote source or licence.
3. Preserve the exact raw-source SHA-256 in the out-of-band acquisition record. If a text extraction
   is required, record the tool, version/options, and exact extracted-text SHA-256. The raw artifact
   is not automatically suitable for commit.
4. Check that the intended local `.md`/`.txt` snapshot contains no secrets or personal data and
   that its licence terms are separate from the repository MIT licence.

## Staged update and validation

1. Place the candidate extracted text in a temporary, ignored staging directory. Review the
   source terms and extracted text out-of-band before admission; do not put an unreviewed file
   under `data/documents/`.
2. After that review, copy the approved candidate into `data/documents/` and add one manifest
   entry with a value from the explicit source-type enum (`repository_authored_demo`,
   `official_external`, `public`, `public_external`, `external`, `external_public`, or
   `public_source`; normally `"official_external"`) and all required fields: URL, publisher, licence, revision,
   date, extracted `sha256` (or `extracted_sha256`), and recorded `raw_source_sha256` (legacy
   `raw_pdf_sha256`/`raw_sha256` is accepted for compatibility).
3. Run `python scripts/verify_corpus_manifest.py`. The loader validates the source-type and
   metadata contract, checks local extracted bytes, rejects an untracked document, rejects path
   escapes, and never contacts a URL. A missing field, invalid URL/date/digest, missing file, or
   checksum mismatch stops the update.
4. Have the source owner/reviewer sign off on the manifest change and any new evaluation labels
   before indexing it; the local script must not report that remote PDF or licence review as
   reproduced verification.
5. Only after the local verifier passes and review is complete, update the manifest hash and
   regenerate the explicitly scoped reports. Record the new manifest hash and code revision in
   the report metadata.
6. If any step fails, remove the candidate and its manifest entry and keep the last checksum-valid
   corpus. Never update a digest to make a modified file pass without source/reviewer approval.

## Replacement and rollback

A replacement is a new snapshot: retain the old revision in version control, use a new revision
and retrieval date, recompute both recorded digests, and rerun all checks. If source terms, raw
acquisition, extraction, or review cannot be completed, set the change aside rather than marking
remote verification as reproducible. Reports from one manifest must not be copied to another corpus
or to Project 4.
