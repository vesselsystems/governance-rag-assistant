# Governance RAG Assistant

[![CI](https://github.com/vesselsystems/governance-rag-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/vesselsystems/governance-rag-assistant/actions/workflows/ci.yml)

A retrieval-first question-answering assistant over AI-governance documents, for procurement and compliance reviewers who need the source paragraph rather than a summary.

## Why I built it

Someone asks "can suppliers use AI to write their bids?" A fluent paragraph is no use to them unless they can check it against the policy text. I also wanted to find out where lexical retrieval breaks down, not just where it works.

## What it does

The first benchmark was saturated. On the original 15 hand-written questions both retrievers find the right chunk in the top 3 every time, because those questions reuse the documents' own wording. So I wrote a harder set before any results existed: 32 questions, 18 paraphrases that avoid the answer's key words, 2 lexical traps, 12 unanswerable.

| Retriever | Original hit@3 | Challenge hit@3 | Challenge hit@1 | Challenge MRR |
|---|---:|---:|---:|---:|
| TF-IDF (default) | 1.00 | 0.65 | 0.30 | 0.47 |
| BM25 | 1.00 | 0.65 | 0.55 | 0.58 |

Paraphrase questions drop top-3 retrieval from 100% to 65%, and every miss is a vocabulary mismatch — "apply" versus "applies", "phone" versus "Helpdesk". BM25 wins five paired questions and loses none (exact McNemar p = 0.06), which is suggestive but not settled. Score thresholds cannot separate unanswerable on-topic questions from answerable ones: median top-1 similarity is actually higher for unanswerable (0.18) than answerable (0.15).

## How it works

- The corpus is the UK Cabinet Office's PPN 017 plus three documents I wrote, 23 chunks total. A manifest records each file's SHA-256 and the loader refuses anything missing from it or changed.
- Documents are split into 180-word windows with a 40-word overlap, each keeping a citation ID like `[ppn_017_…txt#3]`.
- With no API key set, the answer is the retrieved passages themselves, so the default path cannot invent anything.
- If an OpenAI-compatible endpoint is configured, the draft is accepted only when every citation in it belongs to the retrieved set. Anything else falls back to evidence-only. The gate fails closed.
- Streamlit renders everything through `st.text` after stripping control and bidi characters, so document text cannot inject markup.

<!-- TODO: add screenshot of the app answering a question in evidence-only mode with the citation visible -->

## Run it

Requires Python 3.11+.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
streamlit run app.py
```

To compare the retrievers yourself: `python scripts/compare_retrievers.py`.

## Tests and CI

63 tests plus Ruff. CI also re-runs the evaluation and fails if the committed comparison report no longer matches the code.

```bash
pytest
ruff check .
python scripts/compare_retrievers.py --check
```

## Limits and what's next

Twenty-three chunks is a small corpus, and the challenge labels are drafted but not yet human-verified. No generated answer has been evaluated for faithfulness, latency, or cost. For on-topic questions the corpus cannot answer, the app shows related but non-answering passages instead of abstaining.

Next: verify the labels and re-run the comparison, add an embedding or hybrid retriever, and replace threshold abstention with an answerability check that has to quote support.

## License

MIT for the code and the documents I wrote. PPN 017 is a UK Cabinet Office publication recorded as Open Government Licence v3.0.
