# Governance RAG Assistant

[![CI](https://github.com/vesselsystems/governance-rag-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/vesselsystems/governance-rag-assistant/actions/workflows/ci.yml)

A small, offline-first governance-document retrieval-augmented assistant. It indexes Markdown
with deterministic TF-IDF retrieval, shows source chunks, and uses an optional OpenAI-compatible
endpoint only when explicitly configured.

This is an evaluation exercise, not evidence of broad RAG quality. The no-key path is
provider-neutral: it uses the local index and returns an evidence-only draft. If an optional
provider fails, returns malformed or unsafe data, or cites a chunk that was not retrieved, the
app returns that evidence-only draft.

## Corpus status and provenance

The indexed corpus deliberately keeps source types separate: three **repository-authored demo
teaching artifacts** and one **official external snapshot** from the UK Cabinet Office,
[PPN 017: Improving transparency of AI use in procurement](https://www.gov.uk/government/publications/ppn-017-improving-transparency-of-ai-use-in-procurement).
The demo files are not an organization's policy or legal advice. The PPN snapshot is public source
material with its own [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
terms; the code's MIT licence is not silently applied to it.

[`data/corpus_manifest.json`](data/corpus_manifest.json) records the verified source and revision,
per-file extracted-text SHA-256 checksums, the PPN PDF URL and raw PDF SHA-256, publisher, licence
terms URL, and retrieval date. The loader verifies every local snapshot against those checksums,
attaches the metadata to retrieved chunks, and never downloads manifest URLs. See
[`data/documents/README.md`](data/documents/README.md) for the complete source record and
replacement checklist.

## Quick start

```bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python scripts/verify_corpus_manifest.py
python scripts/evaluate_retrieval.py
python scripts/validate_generation.py
python scripts/evaluate_adversarial.py
streamlit run app.py
```

Without credentials, the app remains local and displays retrieved evidence. An optional
OpenAI-compatible endpoint can be configured as follows:

```powershell
$env:OPENAI_API_KEY = "..."
$env:OPENAI_MODEL = "your-model"
streamlit run app.py
```

`OPENAI_BASE_URL` is optional. Do not send sensitive documents to an endpoint without the
necessary review and approval.

## Architecture and safety boundary

```text
Demo Markdown + verified official PPN snapshot + manifest
        │
        ▼
clean + deterministic word chunks
        │
        ▼
local TF-IDF baseline ──► top-k chunks + citation IDs
        │                                │
        └── offline evaluation            └── optional provider
                                               │
                          structural validation gate
                                               │
                         valid output or evidence-only fallback
```

Retrieved documents are untrusted data. The optional provider prompt uses explicit boundaries
and says not to execute document instructions; prompt-injection resistance is **not** inferred
from that prompt. Synthetic prompt-injection and document-poisoning fixtures are kept outside
the normal corpus under `tests/fixtures/adversarial/`. Offline checks verify the boundary and
that representative unsafe provider output is rejected, but they do not measure a model's
adversarial robustness.

The UI renders answers and retrieved documents with Streamlit `st.text`, not Markdown or HTML.
Control and terminal-formatting characters are removed by `safe_plain_text` before display or
provider quoting. This is a rendering safeguard, not a content trust decision.

## Evaluation

`evaluation/questions.json` is a small, hand-authored set with `dev`, `public`, and manually
held-out splits. It includes questions labeled against the three demo files and the verified PPN
snapshot, plus explicitly unanswerable questions. The set is a repeatable regression check, not
an independently collected benchmark.

Run `python scripts/evaluate_retrieval.py` to regenerate `reports/retrieval_results.json`. The
report defines and separates:

- source hit@3 and mean reciprocal rank;
- source precision/recall@3 where source labels are present;
- exact expected-citation hit, precision, and recall@3 where chunk labels are present;
- the rate of unanswerable cases with no lexical evidence.

`python scripts/validate_generation.py` separately exercises the provider-output gate with valid,
missing-citation, wrong-citation, instruction-like, and malformed cases. It does not call a model
and does not measure claim entailment, citation completeness, or generated-answer quality.

`python scripts/evaluate_adversarial.py` separately checks the synthetic fixtures, untrusted
prompt delimiters, and rejection of representative unsafe output. It is a static/offline safety
check, not a score for prompt-injection resistance.

All reports are descriptive results for this tiny fixed corpus and label set. They must not be
read as production quality, safety, latency, or cost evidence. See [`docs/evaluation.md`](docs/evaluation.md)
and [`reports/first_run.md`](reports/first_run.md).

## Responsible-use limits

- Treat the demo files as teaching material, and the PPN file as a source snapshot—not as
  organizational policy, legal advice, or a decision authority.
- No-key mode is the default and does not require a provider account.
- Empty or zero-score retrieval returns an explicit no-evidence response.
- Provider errors, malformed output, unsafe output, and ungrounded citation output fail closed to
  evidence-only mode.
- Identifier validation does not prove that a cited chunk supports every claim.
- Human review is needed before using the pattern for consequential decisions.

## Project structure

```text
.
├── app.py
├── data/
│   ├── corpus_manifest.json           # checksums, source provenance, and licence metadata
│   └── documents/                     # demo guidance plus the separately marked PPN snapshot
├── docs/architecture.md
├── docs/evaluation.md
├── evaluation/
│   ├── questions.json
│   ├── generation_cases.json
│   └── adversarial_questions.json
├── reports/
├── scripts/
├── src/governance_rag/
│   ├── corpus.py
│   ├── evaluation.py
│   ├── generation.py
│   └── retrieval.py
└── tests/
```

## Next experiments

1. Compare retrieval methods on the same labeled set and pre-register any abstention threshold.
2. Have reviewers label claim support and citation completeness for generated answers.
3. Expand adversarial fixtures and run model-backed tests in an approved isolated environment.
4. Measure provider-specific quality, latency, and cost separately from retrieval metrics.
5. Review the external PPN snapshot's source terms before any redistribution or consequential use.

## License

The code and repository-authored documentation are released under the [MIT License](LICENSE)
where applicable. The PPN text snapshot is external source material recorded under the source's
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/);
MIT does not cover or replace those terms. See [`data/corpus_manifest.json`](data/corpus_manifest.json)
and [`data/documents/README.md`](data/documents/README.md).
