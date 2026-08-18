# Evaluation plan

## Retrieval metrics included now

- **Hit@3:** whether the expected source document appears in the top three retrieved chunks.
- **Mean reciprocal rank:** rewards the expected source appearing near the top.

The labeled question set is intentionally small and transparent. It demonstrates the evaluation pattern but is not a statistically sufficient benchmark.

## Generation metrics to add next

- Citation precision: cited chunks actually support the claim.
- Citation recall: important claims have evidence.
- Unsupported-claim rate: claims not entailed by the corpus.
- Refusal quality: the assistant declines questions outside the corpus.
- Prompt-injection resistance: malicious instructions in documents do not control the assistant.
- Latency and cost per answer.

Human review should remain part of the evaluation for consequential use cases.
