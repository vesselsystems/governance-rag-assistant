"""Validate the human-review queue without creating any review outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance_rag.annotations import (
    CLAIM_LABEL_FIELDS,
    LABEL_VALUES,
    PENDING_REVIEW,
    load_annotation_set,
)

QUEUE_STATUSES = frozenset({"pending", "approved", "rejected"})
_ITEM_TYPES = frozenset({"claim_label", "evidence_reference", "external_source_license"})
_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


def _error(message: str) -> None:
    raise ValueError(message)


def _read_json(path: Path, description: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"Could not read {description}: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"{description} is not valid JSON: {path}") from error


def _validate_schema(value: Any, schema_path: Path) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as error:  # pragma: no cover - covered by installation checks
        raise ValueError("jsonschema is required; install the dev dependencies") from error
    schema = _read_json(schema_path, "review queue schema")
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as error:
        raise ValueError(f"Review queue schema is invalid: {schema_path}") from error
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "review_queue"
        _error(f"{location}: JSON Schema validation failed: {error.message}")


def _require_object(value: Any, path: str, fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        _error(f"{path} must be an object")
    unknown = sorted(set(value) - fields)
    if unknown:
        _error(f"{path} has unknown fields: {', '.join(unknown)}")
    missing = sorted(fields - set(value))
    if missing:
        _error(f"{path} is missing required fields: {', '.join(missing)}")
    return value


def _reference_citations(claim: dict[str, Any]) -> list[str]:
    references = claim.get("evidence_references")
    if not isinstance(references, list):
        _error(f"claim {claim.get('claim_id')!r} evidence_references must be a list")
    return [reference["citation"] for reference in references]


def _ppn_manifest_record(manifest: dict[str, Any]) -> dict[str, Any]:
    documents = manifest.get("documents") if isinstance(manifest, dict) else None
    if not isinstance(documents, list):
        _error("corpus manifest documents must be a list")
    for document in documents:
        if (
            isinstance(document, dict)
            and document.get("path")
            == "documents/ppn_017_improving_transparency_of_ai_use_in_procurement.txt"
        ):
            return document
    _error("corpus manifest is missing the PPN 017 document")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_manifest_document_hash(document: dict[str, Any]) -> str:
    """Return the stable digest for a complete manifest document record."""
    return hashlib.sha256(_canonical_json(document).encode("utf-8")).hexdigest()


def _annotation_record_for_item(
    annotation_set: dict[str, Any], item: dict[str, Any]
) -> dict[str, Any] | None:
    if item["item_type"] == "external_source_license":
        return None
    case = next(case for case in annotation_set["cases"] if case["case_id"] == item["case_id"])
    if item["item_type"] == "claim_label":
        if item["claim_id"] is None:
            return case[item["field"]]
        claim = next(
            claim for claim in case["claims"] if claim["claim_id"] == item["claim_id"]
        )
        return claim[item["field"]]
    if item["item_type"] == "evidence_reference":
        claim = next(
            claim for claim in case["claims"] if claim["claim_id"] == item["claim_id"]
        )
        reference_index = int(item["item_id"].rsplit("/", 1)[1])
        return claim["evidence_references"][reference_index]
    return None


def _expected_items(
    annotation_set: dict[str, Any], manifest: dict[str, Any]
) -> list[dict[str, Any]]:
    """Build immutable queue rows directly from the checked-in annotation evidence."""
    items: list[dict[str, Any]] = []
    for case in annotation_set["cases"]:
        case_id = case["case_id"]
        items.append(
            {
                "item_id": f"claim-label/{case_id}/abstention_correctness",
                "item_type": "claim_label",
                "case_id": case_id,
                "claim_id": None,
                "field": "abstention_correctness",
                "question": (
                    f"Review abstention_correctness for case {case_id}: {case['question']}"
                ),
                # The fixture record is evidence even when the candidate answer has no citation.
                "evidence_refs": [f"evaluation/evidence_contract_cases.json#{case_id}"],
            }
        )
        for claim in case["claims"]:
            claim_id = claim["claim_id"]
            citations = _reference_citations(claim)
            for field in CLAIM_LABEL_FIELDS:
                items.append(
                    {
                        "item_id": f"claim-label/{case_id}/{claim_id}/{field}",
                        "item_type": "claim_label",
                        "case_id": case_id,
                        "claim_id": claim_id,
                        "field": field,
                        "question": (
                            f"Review {field} for claim {claim_id}: {claim['claim_text']}"
                        ),
                        "evidence_refs": citations,
                    }
                )
            for reference_index, citation in enumerate(citations):
                items.append(
                    {
                        "item_id": f"evidence-reference/{case_id}/{claim_id}/{reference_index}",
                        "item_type": "evidence_reference",
                        "case_id": case_id,
                        "claim_id": claim_id,
                        "field": "citation_entailment",
                        "question": (
                            f"Does evidence reference {citation} entail/support claim "
                            f"{claim_id}: {claim['claim_text']}?"
                        ),
                        "evidence_refs": [citation],
                    }
                )

    documents = manifest.get("documents") if isinstance(manifest, dict) else None
    if not isinstance(documents, list):
        _error("corpus manifest documents must be a list")
    ppn_index = next(
        (
            index
            for index, document in enumerate(documents)
            if isinstance(document, dict)
            and document.get("path")
            == "documents/ppn_017_improving_transparency_of_ai_use_in_procurement.txt"
        ),
        None,
    )
    if ppn_index is None:
        _error("corpus manifest is missing the PPN 017 document")
    ppn = _ppn_manifest_record(manifest)
    evidence_refs = [f"data/corpus_manifest.json#documents[{ppn_index}]"]
    for field in ("url", "license_url"):
        if isinstance(ppn.get(field), str) and ppn[field].strip():
            evidence_refs.append(ppn[field])
    items.append(
        {
            "item_id": "external-source-license/ppn-017",
            "item_type": "external_source_license",
            "case_id": None,
            "claim_id": None,
            "field": "source_and_license",
            "question": (
                "Has the external PPN 017 snapshot's source provenance and reuse licence "
                "been reviewed before redistribution or consequential use?"
            ),
            "evidence_refs": evidence_refs,
        }
    )
    return items


def _validate_timestamp(value: Any, path: str) -> None:
    if not isinstance(value, str) or not _TIMESTAMP_RE.fullmatch(value):
        _error(f"{path} must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError(f"{path} is not a valid UTC timestamp") from error
    if parsed.tzinfo != timezone.utc:
        _error(f"{path} must be UTC")


def _validate_item_state(item: dict[str, Any], expected: dict[str, Any], path: str) -> None:
    status = item["status"]
    if status not in QUEUE_STATUSES:
        _error(f"{path}.status must be pending, approved, or rejected")
    if item["evidence_refs"] != expected["evidence_refs"]:
        _error(f"{path}.evidence_refs do not match bound annotation/corpus evidence")
    for field in ("reviewer", "reviewed_at_utc", "rationale"):
        value = item[field]
        if value is not None and (not isinstance(value, str) or not value.strip()):
            _error(f"{path}.{field} must be a non-blank string or null")

    if status == "pending":
        if any(
            item[field] is not None
            for field in ("decision", "reviewer", "reviewed_at_utc", "rationale")
        ):
            _error(f"{path}: pending items cannot contain a decision or review outcome")
        return

    missing = [
        field
        for field in ("decision", "reviewer", "reviewed_at_utc", "rationale", "evidence_refs")
        if item[field] is None
        or (isinstance(item[field], str) and not item[field].strip())
        or (field == "evidence_refs" and not item[field])
    ]
    if missing:
        _error(
            f"{path}: {status} requires reviewer, time, rationale, decision, and evidence "
            f"({', '.join(missing)})"
        )
    _validate_timestamp(item["reviewed_at_utc"], f"{path}.reviewed_at_utc")

    if item["item_type"] == "claim_label":
        allowed = LABEL_VALUES[item["field"]]
        if item["decision"] not in allowed:
            _error(f"{path}.decision must be a valid {item['field']} label")
    elif item["item_type"] == "evidence_reference" and item["decision"] not in {
        "entailed",
        "partially_entailed",
        "not_entailed",
        "citation_incorrect",
    }:
        _error(f"{path}.decision is not a supported citation-entailment decision")
    elif item["item_type"] == "external_source_license" and item["decision"] not in {
        "verified",
        "not_verified",
        "needs_follow_up",
    }:
        _error(f"{path}.decision is not a supported source/license decision")


def validate_review_queue(
    queue: Any,
    annotation_set: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, int]:
    """Validate queue structure, immutable bindings, state transitions, and counts."""
    fields = {
        "schema_version", "annotation_file", "corpus_manifest", "manifest_document_sha256",
        "review_status", "items", "summary", "notes",
    }
    root = _require_object(queue, "review_queue", fields)
    if root.get("schema_version") != "1.0":
        _error("review_queue.schema_version must be '1.0'")
    if root.get("annotation_file") != "evaluation/claim_annotations.json":
        _error("review_queue.annotation_file must bind claim_annotations.json")
    if root.get("corpus_manifest") != "data/corpus_manifest.json":
        _error("review_queue.corpus_manifest must bind corpus_manifest.json")
    expected_manifest_digest = canonical_manifest_document_hash(_ppn_manifest_record(manifest))
    observed_manifest_digest = root["manifest_document_sha256"]
    if (
        not isinstance(observed_manifest_digest, str)
        or not re.fullmatch(r"[0-9a-fA-F]{64}", observed_manifest_digest)
        or observed_manifest_digest.lower() != expected_manifest_digest
    ):
        _error(
            "review_queue.manifest_document_sha256 does not match the canonical PPN manifest "
            "document record"
        )
    if root.get("review_status") not in {"pending", "complete"}:
        _error("review_queue.review_status must be pending or complete")
    if not isinstance(root.get("items"), list):
        _error("review_queue.items must be a list")

    expected = _expected_items(annotation_set, manifest)
    expected_by_id = {item["item_id"]: item for item in expected}
    seen: set[str] = set()
    item_fields = {
        "item_id", "item_type", "case_id", "claim_id", "field", "question", "evidence_refs",
        "decision", "reviewer", "reviewed_at_utc", "rationale", "status",
    }
    counts = {"claim_label": 0, "evidence_reference": 0, "external_source_license": 0}
    pending = 0
    for index, raw_item in enumerate(root["items"]):
        path = f"review_queue.items[{index}]"
        item = _require_object(raw_item, path, item_fields)
        item_id = item.get("item_id")
        if not isinstance(item_id, str) or not item_id.strip():
            _error(f"{path}.item_id must be a non-blank string")
        if item_id in seen:
            _error(f"{path}: duplicate item_id {item_id!r}")
        seen.add(item_id)
        if item_id not in expected_by_id:
            _error(f"{path}.item_id {item_id!r} does not match an annotation case/evidence item")
        bound = expected_by_id[item_id]
        for field in ("item_type", "case_id", "claim_id", "field", "question"):
            if item[field] != bound[field]:
                _error(f"{path}.{field} does not match bound annotation evidence")
        if item["item_type"] not in _ITEM_TYPES:
            _error(f"{path}.item_type is invalid")
        _validate_item_state(item, bound, path)
        annotation_record = _annotation_record_for_item(annotation_set, item)
        if item["status"] == "pending" and annotation_record is not None:
            if annotation_record["status"] != PENDING_REVIEW:
                _error(
                    f"{path}: pending queue item must bind to a pending annotation "
                    "label/evidence record"
                )
        counts[item["item_type"]] += 1
        pending += item["status"] == "pending"

    missing = sorted(set(expected_by_id) - seen)
    if missing:
        _error("review_queue is missing queue IDs: " + ", ".join(missing))
    if len(seen) != len(expected_by_id):
        _error("review_queue contains an unexpected number of unique items")

    summary_fields = {
        "status", "total_items", "claim_label_decisions", "evidence_reference_decisions",
        "external_source_license_reviews", "pending_items",
    }
    summary = _require_object(root.get("summary"), "review_queue.summary", summary_fields)
    expected_counts = {
        "total_items": len(expected),
        "claim_label_decisions": counts["claim_label"],
        "evidence_reference_decisions": counts["evidence_reference"],
        "external_source_license_reviews": counts["external_source_license"],
        "pending_items": pending,
    }
    for field, value in expected_counts.items():
        if summary.get(field) != value:
            _error(f"review_queue.summary.{field} must be {value}, got {summary.get(field)!r}")
    expected_summary_status = "pending" if pending else "complete"
    if summary.get("status") != expected_summary_status:
        _error(
            "review_queue.summary.status is a pending-as-complete summary"
            if pending and summary.get("status") == "complete"
            else f"review_queue.summary.status must be {expected_summary_status}"
        )
    if root["review_status"] != expected_summary_status:
        _error(f"review_queue.review_status must be {expected_summary_status}")
    return {**expected_counts, "pending_blockers": pending}


def _parser() -> argparse.ArgumentParser:
    root = Path(__file__).parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, default=root / "evaluation" / "review_queue.json")
    parser.add_argument(
        "--schema", type=Path, default=root / "evaluation" / "review_queue.schema.json"
    )
    parser.add_argument(
        "--annotations", type=Path, default=root / "evaluation" / "claim_annotations.json"
    )
    parser.add_argument(
        "--annotation-schema",
        type=Path,
        default=root / "evaluation" / "claim_annotations.schema.json",
    )
    parser.add_argument("--manifest", type=Path, default=root / "data" / "corpus_manifest.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        queue = _read_json(args.queue, "review queue")
        _validate_schema(queue, args.schema)
        annotation_set = load_annotation_set(args.annotations, schema_path=args.annotation_schema)
        manifest = _read_json(args.manifest, "corpus manifest")
        counts = validate_review_queue(queue, annotation_set, manifest)
    except (ValueError, TypeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"review queue: {counts['total_items']} items")
    print(f"claim-label decisions: {counts['claim_label_decisions']}")
    print(f"evidence-reference decisions: {counts['evidence_reference_decisions']}")
    print(f"external source/license reviews: {counts['external_source_license_reviews']}")
    print(f"pending items: {counts['pending_items']}")
    if counts["pending_blockers"]:
        print(f"pending blockers: {counts['pending_blockers']} human decisions remain")
    else:
        print("pending blockers: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
