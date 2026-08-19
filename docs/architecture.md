# Architecture

## Corpus and manifest

1. Read versioned Markdown/text files from the local corpus directory.
2. When `data/corpus_manifest.json` is present, require every indexed file to be listed.
3. Validate the explicit source-type enum and manifest status/blocker. Public/external entries
   must include an absolute URL, publisher, licence, revision, retrieval date, a recorded
   raw-source SHA-256, and an extracted-text SHA-256. Compare each local file's digest with the
   recorded snapshot checksum. Raw-source and public-licence verification are out-of-band and not
   reproducible here; raw PDFs are not fetched at runtime.
4. Attach the manifest entry to each `DocumentChunk`, including its source type, publication/PDF
   URL, publisher, licence, revision, retrieval date, and extraction metadata where recorded.
   URL fields are metadata only; the loader never downloads them.
5. Split each source into deterministic overlapping word windows and keep the source filename,
   chunk identifier, and provenance with every chunk.
6. Fit a local TF-IDF matrix as the retrieval baseline. The checked-in corpus contains three
   repository-authored demo files and one separately classified external PPN 017 text snapshot.

The manifest's demo entries intentionally have `null` external provenance fields because they
are repository-authored teaching artifacts. The PPN entry records publication/PDF metadata, OGL
v3.0 terms URL, February 2025 revision, retrieval date, extracted-text SHA-256, and a recorded raw
source SHA-256. Only the extracted text is checksum-verified locally; the repository MIT licence
does not apply to or replace the PPN's source terms.

## Query path

1. Transform the question with the same vectorizer.
2. Rank chunks by cosine similarity, with deterministic source/chunk tie breakers; omit zero-score
   matches.
3. Return top-k matches with score and citation identifiers.
4. Use evidence-only mode when no provider is configured or retrieval has no positive evidence.
5. If an optional OpenAI-compatible endpoint is configured, send the question and retrieved
   context as quoted, explicitly untrusted data.
6. Accept provider output only when it is non-empty plain text, contains at least one exact
   citation from the current retrieved set, contains no citation outside that set, and does not
   match the small set of obvious instruction-exfiltration patterns.
7. On a provider/network error, malformed response, unsafe content, or invalid citation, return
   the deterministic evidence-only draft.
8. Display the answer and retrieved evidence with plain-text rendering.

The generation gate validates identifiers and a few structural hazards. It is not a claim-
entailment, citation-precision, or prompt-injection guarantee. Claim support, citation
completeness/precision, unsupported claims, and abstention correctness are separate, pending
human-review dimensions defined in [`annotation_protocol.md`](annotation_protocol.md).

## Trust boundaries

- Documents are untrusted content. Delimiters and system instructions tell a provider not to
  follow document text, but a prompt is not a security boundary and no model-backed resistance
  result is claimed.
- User questions are also quoted data; text that looks like a role message is not promoted to a
  system instruction.
- The optional endpoint is external and may receive the question and retrieved document text.
  Do not index sensitive data without appropriate approval.
- The no-key path does not contact a provider and remains a local retrieval/evidence-only mode.
- `safe_plain_text` removes ANSI, control, bidi, and zero-width formatting characters before
  display or prompt quoting. Streamlit uses `st.text`, never document-controlled Markdown/HTML.
- Synthetic prompt-injection and document-poisoning fixtures are separate from the production-
  like demo corpus. Offline fixture checks verify boundaries and deterministic rejection cases,
  not adversarial model behavior.
- The application is a demonstration and does not provide authorization, legal advice, or a
  decision.
- Project 3's corpus and evaluation reports are not a shared Project 4 index or result; the
  versioned boundary is documented in [`project_boundaries.md`](project_boundaries.md).
