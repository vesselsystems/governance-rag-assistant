# Governance RAG Assistant

A research-minded GenAI portfolio project following the AI Career Training Plan's third project:

> RAG chatbot over a policy/governance document set.

The assistant retrieves evidence from a small, versioned governance corpus, returns citations, evaluates retrieval quality on a hand-built question set, and supports an optional OpenAI-compatible generation endpoint. Without an API key it still runs in **evidence-only mode**, which makes the retrieval and safety behavior testable and reproducible.

## Why this is professionally useful

- It treats RAG as an evaluated system, not a chatbot demo.
- Every response is tied to a source chunk.
- The default local TF-IDF index is deterministic and cheap; it is a baseline that can later be compared with embedding retrieval.
- The corpus is explicitly marked as original demo guidance. Replace it with public policy or documentation after reviewing its license and provenance.
- The evaluation set measures hit@k and reciprocal rank before generation is introduced.

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

Then open the local Streamlit URL. For a real LLM-backed answer, set an OpenAI-compatible key and optionally a model/base URL:

```bash
# PowerShell example
$env:OPENAI_API_KEY = "..."
$env:OPENAI_MODEL = "your-model"
streamlit run app.py
```

Without `OPENAI_API_KEY`, the app displays a grounded evidence draft instead of inventing an answer.

## Architecture

```text
Markdown corpus
      │
      ▼
clean + chunk + metadata
      │
      ▼
TF-IDF retrieval baseline ──► top-k evidence + citations
      │                                  │
      └── evaluation set                 └── optional LLM generation
                                             │
                                             ▼
                                    Streamlit answer interface
```

## Responsible-use controls

- The demo corpus is not legal advice and is not an organizational policy.
- The assistant is instructed to answer only from retrieved evidence.
- No-answer behavior is explicit when retrieval returns no evidence.
- Source provenance, citation coverage, prompt-injection tests, and unsupported-answer review are documented.
- Secrets are read from environment variables and are not committed.

## Project structure

```text
.
├── app.py
├── data/documents/                 # versioned demo governance documents
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

## Research extensions

1. Compare TF-IDF with sentence-transformer embeddings on the same evaluation set.
2. Add a labeled answer set and measure citation precision/recall and unsupported-claim rate.
3. Add adversarial prompt-injection and document-poisoning tests.
4. Measure latency, token/cost usage, and answer quality across models.
5. Replace the demo corpus with a licensed public policy/documentation collection.
