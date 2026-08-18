# Offline baseline run

Run date: 2026-08-18. Configuration: local TF-IDF baseline, deterministic word-window
chunking, top-k = 3, with the SHA-256-verified corpus manifest. The corpus contains three
repository-authored demo teaching artifacts and one separately marked UK Cabinet Office PPN 017
text snapshot. The PPN source record, OGL v3.0 terms, extracted-text SHA-256, and raw PDF
SHA-256 are in [`../data/corpus_manifest.json`](../data/corpus_manifest.json) and
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
| Unanswerable no-evidence rate | 1.00 |
| Case pass rate | 1.00 |

The `public` split has four answerable PPN cases. Its source precision@3 is 1.00 and exact
citation precision@3 is 0.333; both recall figures and hit@3 are 1.00. The `held_out` split has
four answerable demo cases and two out-of-corpus questions: source precision@3 is 0.542 and exact
citation precision@3 is 0.417, with both recall figures and hit@3 at 1.00. The `dev` split has
source precision@3 of 0.467 and exact citation precision@3 of 0.333. These small-set precision
figures show why hit@k alone would be misleading.

The source and citation figures are retrieval-label checks. The run did not call a provider and
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

Regenerate the artifacts with:

```bash
python scripts/verify_corpus_manifest.py
python scripts/evaluate_retrieval.py
python scripts/validate_generation.py
python scripts/evaluate_adversarial.py
```
