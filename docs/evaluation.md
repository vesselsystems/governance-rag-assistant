# Offline evaluation

## Retrieval set and provenance

`evaluation/questions.json` is a small, hand-authored label set over the three repository-authored
demo files and the verified UK Cabinet Office PPN 017 snapshot. The `dev` cases are smoke
questions, `public` cases exercise the external snapshot, and the `held_out` cases use different
phrasings plus deliberately out-of-corpus questions. This is a repeatable regression set, not an
independent benchmark. Corpus provenance and the separate source licences are recorded in
[`data/corpus_manifest.json`](../data/corpus_manifest.json) and
[`data/documents/README.md`](../data/documents/README.md).

Each answerable record may include:

- `expected_source`: the source document expected in the retrieved set;
- `expected_citations`: exact chunk identifiers such as `[model_risk_review_playbook.md#1]`.

An unanswerable record sets `answerable` to `false` and has no expected source. The local TF-IDF
retriever treats a query with no positive lexical match as having no evidence; that is a narrow
abstention check, not a complete out-of-domain detector.

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
- **unanswerable no-evidence/abstention rate:** fraction of explicitly unanswerable records
  for which retrieval returned no chunks;
- **case pass rate:** all labels on a record pass; unanswerable records pass only when no chunks
  are returned.

Precision and recall here describe retrieval labels, not answer claims. They are not estimates of
production performance. The report includes rows and split summaries so denominators remain
inspectable.

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
- The manifest verifies the exact local text bytes before indexing; it never downloads source
  URLs.
- Questions were authored with knowledge of the demo and PPN documents, including held-out
  labels.
- Results can change if documents, chunk settings, stop-word behavior, or labels change.
- Tiny hand-authored sets cannot support broad quality or safety claims.
- Any future external snapshot needs a verified URL, publisher, licence/permission, revision,
  retrieval date, extracted-text checksum, and (when applicable) raw-source checksum before it is
  indexed. The PPN snapshot's OGL terms remain separate from the repository MIT licence.
