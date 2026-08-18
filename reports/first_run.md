# First retrieval evaluation

Configuration: local TF-IDF baseline, deterministic word-window chunking, top-k = 3.

| Metric | Result |
|---|---:|
| Questions | 5 |
| Hit@3 | 1.00 |
| Mean reciprocal rank | 1.00 |

All five labeled questions retrieved the expected source document at rank 1 in this small demo corpus.

## Limits

This result is a smoke test, not evidence of general RAG quality. The corpus is small, the questions were written alongside the documents, and the evaluation measures retrieval—not answer faithfulness. Next research steps are to add held-out questions, embedding retrieval, citation precision/recall, unsupported-claim review, prompt-injection cases, and latency/cost measurements.
