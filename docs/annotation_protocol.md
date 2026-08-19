# Project 3 evidence-contract annotation protocol

> **STATUS: PENDING HUMAN REVIEW.** The checked-in annotation set contains no
> independently labeled claims, citations, or abstentions. Fixture intent and
> retrieval labels are not substitutes for reviewer judgments.

## Purpose and unit of review

The evidence contract is a claim-level review of a candidate answer against the exact
retrieved evidence shown with it. Retrieval hit/precision/recall and the structural provider
output gate are measured separately; neither one establishes claim support. A reviewer may
review the answerable, unanswerable, adversarial, and ambiguous held-out fixtures in
`evaluation/evidence_contract_cases.json`. Unsupported-claim and citation-error examples are
failure modes within those four case types, not additional categories. The corresponding
`evaluation/claim_annotations.json` is a versioned, all-pending template.

One annotation case contains:

- the immutable question, split, case type, candidate answer, review scope, and fixture hash;
- one abstention label for whether refusing/no-evidence behavior was correct;
- zero or more atomic claims with immutable IDs and wording; and
- one label object for each claim dimension plus exact evidence references whose review status is
  tracked separately.

A candidate answer may be structurally valid while still containing an unsupported claim or an
imprecise citation. Do not infer a label from the presence of a citation token. The annotation
case copies the immutable fixture fields and stores a `sha256-canonical-json-v1` hash; loading or
reporting fails closed if either the fields or hash differ.

## Schema and statuses

`evaluation/claim_annotations.schema.json` is the declared Draft 2020-12 JSON Schema for
schema version `1.0`; CI validates it with the explicit `jsonschema` development dependency.
`src/governance_rag/annotations.py` then performs strict parity checks, including recursive
additional-property rejection and citation/source/chunk consistency. Every label is an object with
`label` and `status`:

- `label: null`, `status: pending_human_review` means no reviewer judgment exists;
- a non-null label requires `status: reviewed` and a non-empty reviewer identity; and
- `not_applicable` is a reviewed decision about a dimension, not a missing label.

The set-level reviewer `id` is `null` while review is pending. A partial or completed set
requires a non-blank approved pseudonymous reviewer identifier and matching status; do not put
email addresses, tokens, or other secrets in annotation files. `review_status` is
`pending_human_review`, `partially_reviewed`, or `reviewed`.

## Label definitions

### Claim support (`claim_support`)

- **supported:** the cited evidence entails the complete claim as written;
- **partially_supported:** evidence supports only a material subset or requires a narrower
  wording;
- **unsupported:** the evidence does not entail the claim, contradicts it, or the answer adds a
  material fact not present in the indexed source; and
- **not_applicable:** use only when the claim dimension genuinely cannot apply, with a note.

### Citation completeness (`citation_completeness`)

- **complete:** every substantive claim has at least one citation reference;
- **incomplete:** one or more substantive claims lack a citation; and
- **not_applicable:** only for a reviewed response with no substantive claim, such as a pure
  reviewed abstention.

### Citation precision (`citation_precision`)

- **precise:** the cited chunk is the smallest/useful evidence reference and supports the claim;
- **imprecise:** the citation is in the retrieved set but is too broad, indirect, or only partly
  relevant;
- **incorrect:** the citation is not retrieved, points to the wrong source/chunk, or does not
  support the claim; and
- **not_applicable:** only with an explicit reviewer note.

### Abstention correctness (`abstention_correctness`)

- **correct:** the answer abstains when the indexed evidence cannot support the question, or
  answers when the evidence supports it;
- **incorrect:** it answers without support, or abstains despite sufficient evidence; and
- **not_applicable:** only when the case has no abstention decision to review.

### Unsupported claims (`unsupported_claim`)

Use **yes** when the claim is unsupported as written and **no** when the evidence supports the
claim. This is intentionally redundant with claim support: it makes unsupported-claim counts
and error analysis queryable without pretending that a structural citation check is entailment.

## Evidence references and review procedure

1. Freeze the run inputs named in the report metadata: corpus manifest SHA-256, code revision
   when available, timestamp, and configuration.
2. Inspect the exact retrieved chunk text and citation identifier. Do not fetch a URL during
   annotation and do not add a new source to the corpus as part of review.
3. Split the answer into independently checkable substantive claims. Preserve the candidate
   wording in `claim_text`; do not silently repair it.
4. Add each cited reference as `{citation, source, chunk_id, status}`. An absent, wrong, or
   overly broad reference remains visible so citation errors can be labeled; it is not silently
   removed. A pending reference is unresolved review work.
5. Assign every applicable label, add a short note for partial/incorrect decisions, and record
   the approved reviewer identifier. A second reviewer should independently label disputed
   cases before adjudication.
6. Change the set and reviewer statuses only when the required review is actually complete.
   Every evidence-reference status is part of that completion decision. Never replace pending
   values with `no`, `incorrect`, or zero merely to make a report run.

Run `python scripts/evaluate_claims.py` to validate the declared schema and manual contract,
verify immutable fixture bindings, and emit `reports/claim_evaluation.json`. Its
`measured_metrics` contain only resolved reviewer labels; `reviewer_labels` lists those labels
separately; and `pending_review` lists every unresolved case, claim, label, and evidence reference.
With the checked-in template, rates that require labels are `null`, not scores, and pending
references prevent claim completion.

This protocol is an evaluation control, not evidence that the assistant is safe, accurate, or fit
for consequential decisions.
