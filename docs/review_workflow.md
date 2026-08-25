# Human-review workflow

> **STATUS: PENDING.** The checked-in queue contains no human outcomes.

`evaluation/review_queue.json` is the tracked work list for the six held-out evidence-contract
cases. It contains **32 total items**: **31 claim-review items** (26 claim-label decisions and
5 evidence-reference citation/entailment decisions), plus one separate review of the external
PPN 017 source and licence. The queue is bound by `scripts/validate_reviews.py` to
`claim_annotations.json`, `evidence_contract_cases.json`, and `data/corpus_manifest.json`. Its
`manifest_document_sha256` pins the complete canonical JSON of the bound PPN manifest document
record, so metadata drift invalidates the queue. Do not edit annotations or regenerate reports as
part of queue review.

## Review a queue item

1. Inspect the exact candidate answer, claim wording, cited chunk, fixture record, and (for PPN)
   manifest/source record. Do not fetch URLs during review or silently repair a candidate answer.
2. Make one decision for one item. Claim-label decisions use the labels defined in
   [`annotation_protocol.md`](annotation_protocol.md). Evidence-reference decisions use
   `entailed`, `partially_entailed`, `not_entailed`, or `citation_incorrect`. The PPN item uses
   `verified`, `not_verified`, or `needs_follow_up`.
3. Update only the item being reviewed. Keep every other item pending. Use an approved
   pseudonymous reviewer ID; do not record an email address, token, or personal information.
4. A completed item must have `status` `approved` or `rejected`, a non-empty `decision`,
   `reviewer`, `reviewed_at_utc`, `rationale`, and `evidence_refs`. The timestamp must be UTC in
   `YYYY-MM-DDTHH:MM:SSZ` form (fractional seconds are also accepted). A pending item has
   `status: "pending"` and `decision`, `reviewer`, `reviewed_at_utc`, and `rationale` set to
   `null`; it has no outcome.
5. Preserve `item_id`, `question`, and `evidence_refs`: they are immutable bindings to existing
   evidence. Disputed items should be independently reviewed and adjudicated under the existing
   annotation protocol rather than overwritten to make a report complete.

Every queue item has these exact workflow fields:

```json
{
  "item_id": "...",
  "question": "...",
  "evidence_refs": ["..."],
  "decision": null,
  "reviewer": null,
  "reviewed_at_utc": null,
  "rationale": null,
  "status": "pending"
}
```

The queue also carries binding/type fields (`item_type`, `case_id`, `claim_id`, and `field`) so
that IDs and scope cannot drift from the annotation set. A pending queue item must still point to
a pending annotation label or evidence-reference record; terminal queue items may point to a
still-pending annotation because the apply step consumes that pre-write state. `evidence_refs` for
an abstention points to its fixture record; it is still evidence for the review and must not be
removed.

## Validate

Run:

```bash
python scripts/validate_reviews.py
```

The validator checks JSON Schema, duplicate and missing IDs/fields, immutable evidence bindings,
the PPN manifest-document digest, queue/annotation pending-state consistency, valid UTC timestamps,
completed-item requirements, and summary counts. It prints the total, 31 claim-review plus one
external-item scope counts, pending count, and pending blockers. A pending item cannot be represented
as complete in the summary. Keep the queue pending until all decisions are genuinely reviewed.

## Apply terminal outcomes

After the queue is genuinely complete, validate and preview the mechanical annotation update:

```bash
python scripts/apply_review_queue.py
```

The preview is a dry-run and does not mutate `evaluation/claim_annotations.json`. Write the
validated update atomically only when the queue and external source/licence review are terminal:

```bash
python scripts/apply_review_queue.py --write
```

**Warning:** after a successful `--write` apply, run `python scripts/evaluate_claims.py` to
regenerate the claim report. Do not regenerate that report before applying terminal outcomes;
the apply script does not regenerate reports.
