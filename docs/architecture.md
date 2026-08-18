# Architecture

## Indexing

1. Read versioned Markdown/text files (the current files are original demo guidance).
2. Split each source into deterministic overlapping word windows.
3. Keep the source filename and chunk identifier with every chunk.
4. Fit a local TF-IDF matrix as the retrieval baseline.

## Query path

1. Transform the question with the same vectorizer.
2. Rank chunks by cosine similarity and discard zero-score matches.
3. Return top-k matches with scores and citation identifiers.
4. Use the evidence-only mode when no provider is configured.
5. If an optional OpenAI-compatible endpoint is configured, send the question and retrieved
   context with instructions to answer only from that context.
6. Accept provider output only when it is non-empty and every citation-shaped token is an exact
   identifier from the retrieved set.
7. On a provider/network error, malformed response, empty content, or invalid citation, return
   the deterministic evidence-only draft.
8. Display the retrieved evidence beside the answer for inspection.

The citation gate validates identifier membership. It is not a claim-entailment or citation
precision test, and it does not prove that a provider followed the prompt.

## Trust boundaries

- Documents are untrusted content. The prompt asks the optional provider not to follow
  instructions found in retrieved text; adversarial prompt-injection resistance has not been
  established by this demo.
- The optional endpoint is external and may receive the question and retrieved document text.
  Do not index sensitive data without appropriate approval.
- The no-key path does not contact a provider and remains a local retrieval/evidence-only mode.
- The application is a demonstration and does not provide authorization, legal advice, or a
  decision.
