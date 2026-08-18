# Architecture

## Indexing

1. Read versioned Markdown/text files.
2. Split each source into deterministic overlapping word windows.
3. Store the source filename and chunk identifier with every chunk.
4. Fit a local TF-IDF matrix as the retrieval baseline.

## Query path

1. Transform the question with the same vectorizer.
2. Rank chunks by cosine similarity.
3. Return top-k non-zero matches with scores and citations.
4. Use evidence-only mode by default.
5. If an approved OpenAI-compatible endpoint is configured, send only the retrieved context and constrained instructions to the model.
6. Display the evidence alongside the answer so a reviewer can inspect it.

## Trust boundaries

- Documents are untrusted content; instructions inside documents must not override the system prompt.
- The optional LLM endpoint is external and may receive the question and retrieved document text. Do not index sensitive data without approval.
- The application is a demonstration and does not provide authorization, legal advice, or a decision.
