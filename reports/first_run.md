# Offline baseline run

Report set generated on 2026-08-24 UTC (see each JSON artifact for its exact timestamp).
Configuration: local TF-IDF baseline, deterministic word-window chunking, top-k = 3, with locally
checksum-verified extracted text. The corpus contains three
repository-authored demo teaching artifacts and one separately classified UK Cabinet Office PPN
017 text snapshot. The PPN source record, OGL v3.0 metadata, extracted-text SHA-256, and recorded
raw-source SHA-256 are in [`../data/corpus_manifest.json`](../data/corpus_manifest.json) and
[`../data/documents/README.md`](../data/documents/README.md).

## Retrieval result

The run evaluated 15 hand-authored cases: 13 answerable and 2 unanswerable. Four `public` cases
exercise the PPN snapshot; the `dev` and `held_out` cases also include the repository-authored
demo files. These are descriptive results for this tiny fixed label set, not evidence of broad
retrieval or RAG quality.

| Metric | Result |
|---|---:|
| Questions | 15 |
| Answerable questions | 13 |
| Unanswerable questions | 2 |
| Source hit@3 | 1.00 |
| Mean reciprocal rank | 1.00 |
| Source precision@3 | 0.654 |
| Source recall@3 | 1.00 |
| Exact expected-citation hit@3 | 1.00 |
| Exact citation precision@3 | 0.359 |
| Exact citation recall@3 | 1.00 |
| Retrieval no-evidence rate | 1.00 |
| Case pass rate | 1.00 |

The `public` split has four answerable PPN cases. Its source precision@3 is 1.00 and exact
citation precision@3 is 0.333; both recall figures and hit@3 are 1.00. The `held_out` split has
four answerable demo cases and two out-of-corpus questions: source precision@3 is 0.542 and exact
citation precision@3 is 0.417, with both recall figures and hit@3 at 1.00. The `dev` split has
source precision@3 of 0.467 and exact citation precision@3 of 0.333. These small-set precision
figures show why hit@k alone would be misleading.

The source and citation figures are retrieval-label checks. The retrieval no-evidence figure is
not an abstention-correctness result; abstention correctness belongs only to pending claim
annotations. The run did not call a provider and
does not measure generated-answer correctness, claim support, citation completeness, prompt-
injection resistance, latency, or cost. The two unanswerable cases have no positive lexical match;
this is not a general out-of-domain detector.

## Separate generation and adversarial checks

`reports/generation_validation.json` records 5/5 expected outcomes for a structural provider-
output gate: valid retrieved citation, missing citation, wrong citation, instruction-like output,
and malformed content. No model was called. This does not establish entailment or generation
quality.

`reports/adversarial_results.json` records 2/2 deterministic fixture-control checks for synthetic
prompt-injection and document-poisoning text: fixture presence, explicit untrusted prompt
boundaries, and rejection of representative unsafe output. No model was called, so this is not a
prompt-injection-resistance result.

## Evidence-contract status

The versioned claim annotation set is intentionally **pending human review**. It contains six
held-out fixtures across four case types (answerable, unanswerable, adversarial, and ambiguous).
Unsupported-claim and citation-error examples are failure modes within those types. There are 31
unresolved review items: 26 claim-label fields and five evidence-reference reviews. No claim
support, citation completeness/precision, unsupported-claim, or abstention result is reported;
the claim report emits `null` rates until an approved reviewer supplies labels and identity.
Pending evidence references also keep claim review incomplete. Raw-source and public-licence
verification remain out-of-band and are not reproducible in this workspace.
See [`../docs/annotation_protocol.md`](../docs/annotation_protocol.md) and
[`claim_evaluation.json`](claim_evaluation.json). The claim report is scoped to the same
manifest metadata but does not copy retrieval or Project 4 results.

The generated JSON reports record the corpus manifest SHA-256, current git revision, generation
timestamp, configuration, and working-tree status. Regenerated reports currently record
`working_tree_dirty: true` because the tracked report artifacts are changed in this checkout; the
revision is context, not a claim that an immutable release was evaluated.

Regenerate the artifacts with:

```bash
python scripts/verify_corpus_manifest.py
python scripts/evaluate_retrieval.py
python scripts/validate_generation.py
python scripts/evaluate_claims.py
python scripts/evaluate_adversarial.py
```
