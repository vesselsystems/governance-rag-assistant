# Contributing

This repository favors inspectable evidence and provider-neutral tests.

Before opening a change:

1. Create an isolated Python 3.11+ environment and install `.[dev]`.
2. Run `pytest` and `ruff check .`.
3. Update the evaluation labels and recorded results when corpus or chunking changes.
4. Document provenance and licensing before adding external documents.
5. Never commit API keys, private documents, or personal information.

Generation changes should include a test for malformed, unsupported, or ungrounded provider output where relevant.
