"""Apply a fully terminal human-review queue to the claim annotations."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from governance_rag.annotations import (
    CLAIM_LABEL_FIELDS,
    PARTIALLY_REVIEWED,
    PENDING_REVIEW,
    REVIEWED,
    load_annotation_set,
)

try:  # Direct execution puts scripts/ on sys.path.
    from validate_reviews import _read_json, _validate_schema, validate_review_queue
except ModuleNotFoundError:  # pragma: no cover - depends on how the script is imported
    _validator_spec = importlib.util.spec_from_file_location(
        "_review_queue_validator", Path(__file__).with_name("validate_reviews.py")
    )
    if _validator_spec is None or _validator_spec.loader is None:
        raise ImportError("Could not load scripts/validate_reviews.py")
    _validator = importlib.util.module_from_spec(_validator_spec)
    _validator_spec.loader.exec_module(_validator)
    _read_json = _validator._read_json
    _validate_schema = _validator._validate_schema
    validate_review_queue = _validator.validate_review_queue

TERMINAL_QUEUE_STATUSES = frozenset({"approved", "rejected"})


def _review_notes(item: dict[str, Any]) -> str:
    evidence = "\n".join(f"- {reference}" for reference in item["evidence_refs"])
    return (
        f"Queue decision: {item['decision']}\n"
        f"Rationale: {item['rationale']}\n"
        f"Review evidence refs:\n{evidence}"
    )


def _find_claim(
    annotation_set: dict[str, Any], case_id: str, claim_id: str
) -> dict[str, Any]:
    for case in annotation_set["cases"]:
        if case["case_id"] == case_id:
            for claim in case["claims"]:
                if claim["claim_id"] == claim_id:
                    return claim
            break
    raise ValueError(f"Queue item refers to missing annotation claim {case_id}/{claim_id}")


def _find_case(annotation_set: dict[str, Any], case_id: str) -> dict[str, Any]:
    for case in annotation_set["cases"]:
        if case["case_id"] == case_id:
            return case
    raise ValueError(f"Queue item refers to missing annotation case {case_id}")


def _find_reference(claim: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    parts = item["item_id"].split("/")
    try:
        reference_index = int(parts[-1])
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid evidence-reference queue ID: {item['item_id']}") from error
    references = claim["evidence_references"]
    if reference_index < 0 or reference_index >= len(references):
        raise ValueError(f"Queue item refers to missing evidence reference: {item['item_id']}")
    reference = references[reference_index]
    if item["evidence_refs"] != [reference["citation"]]:
        raise ValueError(f"Queue evidence does not match annotation reference: {item['item_id']}")
    return reference


def _annotation_review_items(annotation_set: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for case in annotation_set["cases"]:
        records.append(case["abstention_correctness"])
        for claim in case["claims"]:
            records.extend(claim[field] for field in CLAIM_LABEL_FIELDS)
            records.extend(claim["evidence_references"])
    return records


def _set_top_level_review_state(annotation_set: dict[str, Any]) -> None:
    records = _annotation_review_items(annotation_set)
    pending = any(record["status"] == PENDING_REVIEW for record in records)
    reviewed = any(record["status"] == REVIEWED for record in records)
    if pending:
        status = PARTIALLY_REVIEWED if reviewed else PENDING_REVIEW
    else:
        status = REVIEWED

    reviewer_ids = {
        record.get("reviewer_id") for record in records if record.get("reviewer_id")
    }
    if len(reviewer_ids) > 1:
        reviewers = ", ".join(sorted(reviewer_ids))
        raise ValueError(
            "Cannot set annotation reviewer identity mechanically: multiple reviewer IDs "
            f"remain ({reviewers})"
        )
    reviewer_id = next(iter(reviewer_ids), None)
    if status != PENDING_REVIEW and reviewer_id is None:
        raise ValueError("Cannot set annotation reviewer identity: no reviewed item has a reviewer")
    annotation_set["review_status"] = status
    annotation_set["reviewer"] = {"id": reviewer_id, "status": status}


def apply_terminal_queue(
    queue: dict[str, Any], annotation_set: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, int]]:
    """Return an updated annotation copy and counts, without mutating the input."""
    candidate = copy.deepcopy(annotation_set)
    counts = {"claim_label": 0, "evidence_reference": 0, "external_source_license": 0}
    for item in queue["items"]:
        if item["status"] not in TERMINAL_QUEUE_STATUSES:
            raise ValueError(
                "Refusing to apply review queue: every queue item must be terminal "
                "(approved or rejected)"
            )
        item_type = item["item_type"]
        counts[item_type] += 1
        if item_type == "external_source_license":
            continue

        if item_type == "claim_label":
            case = _find_case(candidate, item["case_id"])
            record = (
                case[item["field"]]
                if item["claim_id"] is None
                else _find_claim(candidate, item["case_id"], item["claim_id"])[item["field"]]
            )
            record.update(
                label=item["decision"],
                status=REVIEWED,
                reviewer_id=item["reviewer"],
                notes=_review_notes(item),
            )
        elif item_type == "evidence_reference":
            claim = _find_claim(candidate, item["case_id"], item["claim_id"])
            reference = _find_reference(claim, item)
            reference.update(
                status=REVIEWED,
                reviewer_id=item["reviewer"],
                notes=_review_notes(item),
            )
        else:  # validate_review_queue normally makes this unreachable.
            raise ValueError(f"Unsupported queue item type: {item_type}")

    _set_top_level_review_state(candidate)
    return candidate, counts


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
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=None,
        help="Optional evidence-contract fixture path for a temporary annotation copy",
    )
    parser.add_argument("--manifest", type=Path, default=root / "data" / "corpus_manifest.json")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Atomically replace the annotation file; without this flag, only validate/dry-run",
    )
    return parser


def _load_annotations(
    annotation_path: Path,
    annotation_schema: Path,
    fixtures_path: Path | None,
) -> tuple[dict[str, Any], Path | None]:
    try:
        return (
            load_annotation_set(
                annotation_path,
                schema_path=annotation_schema,
                fixtures_path=fixtures_path,
            ),
            fixtures_path,
        )
    except ValueError as error:
        if fixtures_path is not None or "Could not read annotation fixtures" not in str(error):
            raise
        raw_annotation = _read_json(annotation_path, "annotation set")
        binding = (
            raw_annotation.get("fixture_binding") if isinstance(raw_annotation, dict) else None
        )
        fixture_file = binding.get("fixture_file") if isinstance(binding, dict) else None
        fallback = (
            Path(__file__).parents[1] / fixture_file
            if isinstance(fixture_file, str)
            else None
        )
        if fallback is None or not fallback.is_file():
            raise
        return (
            load_annotation_set(
                annotation_path,
                schema_path=annotation_schema,
                fixtures_path=fallback,
            ),
            fallback,
        )


def _validate_candidate(
    candidate: dict[str, Any],
    annotation_path: Path,
    annotation_schema: Path,
    fixtures_path: Path | None,
) -> None:
    """Validate an in-memory candidate through the existing annotation loader."""
    annotation_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{annotation_path.name}.", suffix=".tmp", dir=annotation_path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(candidate, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        load_annotation_set(
            temporary_path,
            schema_path=annotation_schema,
            fixtures_path=fixtures_path,
        )
    finally:
        temporary_path.unlink(missing_ok=True)


def _atomic_write(path: Path, value: dict[str, Any]) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        queue = _read_json(args.queue, "review queue")
        _validate_schema(queue, args.schema)
        annotation_set, fixtures_path = _load_annotations(
            args.annotations,
            args.annotation_schema,
            args.fixtures,
        )
        manifest = _read_json(args.manifest, "corpus manifest")
        counts = validate_review_queue(queue, annotation_set, manifest)

        pending_items = [item for item in queue["items"] if item["status"] == "pending"]
        external = next(
            item for item in queue["items"] if item["item_type"] == "external_source_license"
        )
        if pending_items:
            external_message = (
                "; external source/license item is not terminal"
                if external["status"] not in TERMINAL_QUEUE_STATUSES
                else ""
            )
            raise ValueError(
                f"Refusing to apply review queue: {len(pending_items)} pending queue item(s) remain"
                f"{external_message}; no annotation was changed"
            )
        if external["status"] not in TERMINAL_QUEUE_STATUSES:
            raise ValueError(
                "Refusing to apply review queue: external source/license item is not terminal "
                f"(status={external['status']!r}); no annotation was changed"
            )

        candidate, applied = apply_terminal_queue(queue, annotation_set)
        _validate_candidate(candidate, args.annotations, args.annotation_schema, fixtures_path)
        if args.write:
            _atomic_write(args.annotations, candidate)
    except (OSError, TypeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    action = "wrote" if args.write else "dry-run; would write"
    print(f"validated terminal review queue: {counts['total_items']} items")
    print(
        f"applied claim-label: {applied['claim_label']}; "
        f"evidence-reference: {applied['evidence_reference']}; "
        f"external source/license: {applied['external_source_license']}"
    )
    print(f"annotation review status: {candidate['review_status']}")
    print(f"{action}: {args.annotations}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
