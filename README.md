# Governance RAG Assistant

[![CI](https://github.com/vesselsystems/governance-rag-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/vesselsystems/governance-rag-assistant/actions/workflows/ci.yml)

A small, offline-first governance-document retrieval-augmented
assistant. It indexes Markdown with deterministic TF-IDF retrieval, shows source chunks, and
uses an optional OpenAI-compatible endpoint only when explicitly configured.

This is an evaluation exercise, not evidence of broad RAG quality. The no-key path is
provider-neutral: it uses the local index and returns an evidence-only draft. If an optional
provider fails, returns malformed data, or cites a chunk that was not retrieved, the app also
returns that evidence-only draft.

## Corpus status

The three indexed documents are **original demo guidance written for this repository**. They
are not an organization's policy, legal advice, or a sourced public-policy collection. No
external provenance, license, or authority is claimed for the current corpus. See
[`data/documents/README.md`](data/documents/README.md) before replacing it with material from
elsewhere.

## Quick start

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python scripts/evaluate_retrieval.py
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

## Architecture

```text
Original demo Markdown
        │
        ▼
clean + deterministic word chunks
        │
        ▼
local TF-IDF baseline ──► top-k chunks + citation IDs
        │                                │
        └── offline evaluation            └── optional provider
                                               │
                         valid response + retrieved citations only
                                               │
                                  otherwise evidence-only fallback
```

The citation check compares citation identifiers in provider output with the identifiers in
the current retrieved set. It does **not** establish that every claim is supported or measure
citation precision/recall.

## Offline evaluation

`evaluation/questions.json` contains a small development set and a manually authored
`held_out` set. The held-out records include answerable paraphrases with expected chunk
citations and two questions intentionally outside this corpus. The split is useful for a
repeatable check, but it is not an independently collected benchmark.

Run:

```bash
python scripts/evaluate_retrieval.py
```

The report separates:

- source hit@3 and mean reciprocal rank, which measure retrieval labels;
- exact expected-chunk/citation hit@3, which measures whether the labeled chunk was retrieved;
- the rate at which the unanswerable examples produced no lexical evidence.

These are retrieval and abstention checks only. They do not measure generated-answer quality,
claim entailment, citation completeness, prompt-injection resistance, latency, or cost. See
[`docs/evaluation.md`](docs/evaluation.md) and [`reports/first_run.md`](reports/first_run.md)
for limitations and the recorded local run.

## Responsible-use limits

- Treat the corpus as teaching material, not organizational policy or legal advice.
- No-key mode is the default and does not require a provider account.
- Empty retrieval returns an explicit no-evidence response.
- Provider errors and malformed or ungrounded citation output fail closed to evidence-only mode.
- The prompt asks the provider not to follow instructions in retrieved documents, but this
  repository does not claim to have completed adversarial prompt-injection testing.
- Human review is needed before using the pattern for consequential decisions.

## Project structure

```text
.
├── app.py
├── data/documents/                 # original demo governance guidance
├── docs/architecture.md
├── docs/evaluation.md
├── evaluation/questions.json
├── reports/first_run.md
├── scripts/evaluate_retrieval.py
├── src/governance_rag/
│   ├── corpus.py
│   ├── evaluation.py
│   ├── generation.py
│   └── retrieval.py
└── tests/
```

## Next experiments

1. Add independently sourced, licensed documents with URL, retrieval date, license, checksum,
   and version metadata.
2. Compare retrieval methods on the same labeled set.
3. Have reviewers label claim support and citation completeness for generated answers.
4. Add adversarial prompt-injection/document-poisoning cases rather than treating the prompt
   instruction as a tested guarantee.
5. Measure provider-specific quality, latency, and cost separately from retrieval metrics.

## License

The code and documentation are released under the [MIT License](LICENSE). The current demo corpus is original material in this repository; any future external documents need their own provenance and license review.
