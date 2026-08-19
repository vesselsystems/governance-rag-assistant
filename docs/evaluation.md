# Offline evaluation

## Retrieval set and provenance

`evaluation/questions.json` is a small, hand-authored label set over the three repository-authored
demo files and the locally stored UK Cabinet Office PPN 017 text snapshot. The `dev` cases are
smoke questions, `public` cases exercise the external-source text, and the `held_out` cases use
different phrasings plus deliberately out-of-corpus questions. This is a repeatable regression
set, not an independent benchmark. The extracted text is locally checksum-verified; raw-source
and public-licence verification are out-of-band and not reproducible here. Corpus provenance and
the separate source licences are recorded in
[`data/corpus_manifest.json`](../data/corpus_manifest.json) and
[`data/documents/README.md`](../data/documents/README.md).

Each answerable record may include:

- `expected_source`: the source document expected in the retrieved set;
- `expected_citations`: exact chunk identifiers such as `[model_risk_review_playbook.md#1]`.

An unanswerable record sets `answerable` to `false` and has no expected source. The local TF-IDF
retriever treats a query with no positive lexical match as having no evidence; that is a narrow
retrieval no-evidence check, not a complete out-of-domain detector or abstention judgment.

## Retrieval metrics

Run `python scripts/evaluate_retrieval.py` to regenerate
`reports/retrieval_results.json`. At `top_k=3`, the report contains:

- **source hit@k:** whether any expected source appears in the retrieved set;
- **mean reciprocal rank:** reciprocal rank of the expected source, or expected citation when
  only a citation label is provided, with zero for a miss;
- **source precision/recall@k:** overlap with the labeled expected source set, defined only for
  source-labeled answerable records;
- **exact citation hit/precision/recall@k:** overlap with labeled chunk identifiers, defined
  only for records with `expected_citations`;
- **`retrieval_no_evidence_rate`:** fraction of explicitly unanswerable records for which
  retrieval returned no chunks. This is a retrieval observation, not an abstention-correctness
  judgment; abstention correctness remains a pending claim-annotation dimension.
- **case pass rate:** all retrieval labels on a record pass; unanswerable records pass only when
  no chunks are returned. This is a structural retrieval regression, not abstention correctness.

Precision and recall here describe retrieval labels, not answer claims. They are not estimates of
production performance. The report includes rows and split summaries so denominators remain
inspectable. `reports/retrieval_results.json` also records the manifest SHA-256, code revision
when available, timestamp, and configuration. Its `scope` is retrieval-only; it does not contain
claim-quality results.

## Evidence-contract fixtures and claim review

`evaluation/evidence_contract_cases.json` is a separate held-out fixture set with four case
types: answerable, unanswerable, adversarial, and ambiguous. Unsupported-claim and citation-error
examples are failure-mode fixtures within those four types, not extra case categories. It is not
included in the retrieval denominator. `evaluation/claim_annotations.json` is the corresponding
schema-versioned annotation template. Every reviewer label and evidence-reference status is
intentionally `pending_human_review`; no claim is independently labeled in this repository. See
[`annotation_protocol.md`](annotation_protocol.md) for the protocol and label definitions.

Run `python scripts/evaluate_claims.py` to validate the declared JSON Schema with `jsonschema`,
run the strict manual-validator parity checks, bind immutable annotation content to the fixture
file, and emit `reports/claim_evaluation.json`. The report keeps three things distinct:

- `measured_metrics`: rates computed only from resolved human labels;
- `reviewer_labels`: the resolved labels and reviewer identifiers, if any; and
- `pending_review`: unresolved cases, claims, labels, and evidence references.

With the checked-in pending template, claim support, citation completeness/precision, unsupported
claim, and abstention rates are `null` rather than invented results. Pending evidence references
also prevent a claim from becoming fully reviewed. A structurally accepted citation still requires
claim-level review. These metrics are not retrieval metrics and are not copied to Project 4.

## Separate generation validation

The offline retrieval script never calls a model and does not score generated answers. Run
`python scripts/validate_generation.py` to exercise the deterministic provider-output gate using
`evaluation/generation_cases.json`. It covers a valid retrieved citation, missing citation,
wrong citation, instruction-like output, and malformed content. The report is a structural gate
check only; it does not measure claim entailment, citation completeness, refusal quality, model
quality, latency, cost, or provider behavior.

The optional provider path is fail-closed: network errors, malformed responses, control/bidi text,
obvious instruction-exfiltration output, citation-free answers, and citations outside the current
retrieved set return evidence-only mode. Even a structurally valid citation does not prove that
the cited chunk supports every claim.

## Adversarial fixtures

`evaluation/adversarial_questions.json` points to synthetic prompt-injection and document-
poisoning fixtures under `tests/fixtures/adversarial/`. Run
`python scripts/evaluate_adversarial.py` to verify that the fixtures exist, prompt construction
labels retrieved text as untrusted, and representative unsafe outputs are rejected. This is an
offline control test; it intentionally does **not** claim prompt-injection resistance because no
model is called.

## Reproducibility and limits

- Retrieval is local, deterministic TF-IDF with fixed word-window chunking and deterministic tie
  breaking.
- The manifest verifies the exact local text bytes before indexing; raw-source and public-licence
  checks are recorded as out-of-band/not reproducible here, and source URLs are never downloaded.
- Questions were authored with knowledge of the demo and PPN documents, including held-out
  labels.
- Results can change if documents, chunk settings, stop-word behavior, or labels change.
- Tiny hand-authored sets cannot support broad quality or safety claims.
- Any future external snapshot needs a recorded absolute URL, publisher, licence/permission,
  revision, retrieval date, extracted-text checksum, and raw-source checksum before it is indexed;
  source and licence review remains out-of-band. The
  fail-closed procedure is documented in [`ingestion_update.md`](ingestion_update.md). The PPN
  snapshot's OGL terms remain separate from the repository MIT licence.
- Project 3's corpus/index and reports are intentionally separate from Project 4; see
  [`project_boundaries.md`](project_boundaries.md). No Project 3 result is a Project 4 result.
