# Offline retrieval evaluation run

Configuration: local TF-IDF baseline, deterministic word-window chunking, top-k = 3.
The corpus contains original demo guidance written for this repository; it has no external
provenance claim.

| Metric | Result |
|---|---:|
| Questions | 11 |
| Answerable questions | 9 |
| Unanswerable questions | 2 |
| Source hit@3 | 1.00 |
| Mean reciprocal rank | 1.00 |
| Exact expected-citation hit@3 | 1.00 |
| Unanswerable no-evidence rate | 1.00 |
| Case pass rate | 1.00 |

The `dev` split has five answerable cases. The manually authored `held_out` split has four
answerable paraphrases and two out-of-corpus questions. These results describe this small,
fixed label set and lexical configuration only. They are not evidence of general retrieval or
RAG quality.

The source and citation figures are retrieval checks: they show that labeled documents or
chunk identifiers appeared in the retrieved set. The run did not call a provider and does not
measure generated-answer correctness, claim support, citation completeness, prompt-injection
resistance, latency, or cost. Provider fallback and citation-identifier handling are covered
by unit tests, but that is not a broad citation or safety evaluation.

The machine-readable rows and split summaries are in
[`retrieval_results.json`](retrieval_results.json). Re-run `python scripts/evaluate_retrieval.py`
to regenerate them after changing the corpus, chunking, or labels.
