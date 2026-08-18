# Offline evaluation

## What is in the set

`evaluation/questions.json` is a small, hand-authored label set over the current original demo
corpus. The five `dev` cases are the initial smoke questions. The `held_out` cases were added
as different phrasings and include four answerable questions with expected chunk citations and
two questions whose topics are not in the corpus.

This is a transparent regression set, not an independent benchmark. The corpus is small and
there is no claim that these examples represent production traffic or general RAG quality.

Each answerable record may include:

- `expected_source`: the source document expected in the retrieved set;
- `expected_citations`: exact chunk identifiers such as `[model_risk_review_playbook.md#1]`.

An unanswerable record sets `answerable` to `false` and has no expected source. The local TF-IDF
retriever treats a query with no non-zero lexical match as having no evidence; that is a narrow
check, not a complete out-of-domain detector.

## Retrieval and abstention metrics

Run `python scripts/evaluate_retrieval.py` to regenerate
`reports/retrieval_results.json`.

- **Hit@3:** for answerable, source-labeled records, whether the expected source appears in the
  top three chunks.
- **Mean reciprocal rank:** the reciprocal rank of the expected source (or expected citation
  when a record has no source label), with zero for a miss.
- **Citation hit@3:** for records with `expected_citations`, whether an exact expected chunk
  appears in the top three. This checks retrieval of an identifier, not whether generated prose
  is supported by it.
- **Unanswerable no-evidence rate:** the fraction of `answerable: false` records for which the
  retriever returns no chunks.
- **Case pass rate:** all labels on a record must pass; unanswerable records pass only when no
  chunks are returned.

The JSON also reports the same retrieval summaries by `split`. Metrics are descriptive results
for this set and configuration, not estimates of deployment performance.

## Generation is separate

The offline script does not call a model and does not score generated answers. The provider
boundary has unit tests for malformed responses, provider exceptions, invalid citation IDs,
valid retrieved citations, and no-evidence behavior. Those tests verify fallback and identifier
handling only; they are not a citation-quality, claim-entailment, or prompt-injection study.

Generation quality would require separately labeled answers and human or task-specific review
for claim support, citation completeness, refusal quality, and harmful failure modes. Those
measurements are not reported here.

## Reproducibility and limits

- Retrieval is local, deterministic TF-IDF with fixed word-window chunking.
- Questions were authored with knowledge of the demo documents, including the held-out labels.
- Results can change if documents, chunk settings, stop-word behavior, or labels change.
- The corpus has no external provenance in this repository. Replacing it requires recording
  provenance and license information before making stronger source claims.
