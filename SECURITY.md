# Security

This repository is an offline retrieval prototype. The optional provider path can transmit the question and retrieved context to a configured endpoint; do not use it with private documents without the required review and approval.

Please do not open a public issue containing API keys, private documents, or sensitive security details. Revoke exposed credentials immediately, then contact the repository owner through a private GitHub channel with the repository name, affected revision, and a minimal reproduction. There is no security response SLA for this learning repository.

The repository-authored demo files are not organizational policy or legal advice; the external
PPN snapshot is source material, not advice or an authorization. Treat all retrieved documents as
untrusted content. Synthetic prompt-injection and document-poisoning fixtures live under
`tests/fixtures/adversarial/`; run `python scripts/evaluate_adversarial.py` for the offline
boundary and fail-closed checks. Those checks do not establish model-backed adversarial
resistance.
