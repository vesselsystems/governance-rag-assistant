# Contributing

This repository favors inspectable evidence and provider-neutral tests.

Before opening a change:

1. Create an isolated Python 3.11+ environment and install `.[dev]`.
2. Run `pytest` and `ruff check .`.
3. Verify `data/corpus_manifest.json` and update the evaluation labels and recorded results when
   corpus or chunking changes.
4. Document publication/PDF URLs, publisher, licence or permission, revision, retrieval date,
   extracted-text checksum, and (when applicable) raw-source checksum before adding external
   documents; a `null` licence must not be turned into a claim of reuse rights. Keep source terms
   separate from the repository MIT licence.
5. Run the retrieval, generation-validation, adversarial-fixture, and manifest smoke scripts.
6. Never commit API keys, private documents, or personal information.

Generation changes should include a test for malformed, unsupported, unsafe, or ungrounded provider
output where relevant. Keep generated-answer validation separate from retrieval metrics.
