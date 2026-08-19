"""Claim-level evidence-contract annotations and pending-review accounting.

The annotation file is a review template, not an entailment oracle.  Structural
citation membership and retrieval labels never become claim labels.  A label or
evidence reference is measured only after an identified reviewer marks it as
``reviewed``; unresolved work remains pending and is reported explicitly.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

ANNOTATION_SCHEMA_VERSION = "1.0"
PENDING_REVIEW = "pending_human_review"
REVIEWED = "reviewed"
PARTIALLY_REVIEWED = "partially_reviewed"
REVIEW_STATUSES = frozenset({PENDING_REVIEW, REVIEWED})
SET_REVIEW_STATUSES = frozenset({PENDING_REVIEW, PARTIALLY_REVIEWED, REVIEWED})
CASE_TYPES = frozenset({"answerable", "unanswerable", "adversarial", "ambiguous"})
FIXTURE_BINDING_ALGORITHM = "sha256-canonical-json-v1"

CLAIM_LABEL_FIELDS = (
    "claim_support",
    "citation_completeness",
    "citation_precision",
    "unsupported_claim",
)
ALL_LABEL_FIELDS = (*CLAIM_LABEL_FIELDS, "abstention_correctness")
REVIEW_SCOPE_FIELDS = frozenset(ALL_LABEL_FIELDS)
LABEL_VALUES = {
    "claim_support": frozenset(
        {"supported", "partially_supported", "unsupported", "not_applicable"}
    ),
    "citation_completeness": frozenset({"complete", "incomplete", "not_applicable"}),
    "citation_precision": frozenset({"precise", "imprecise", "incorrect", "not_applicable"}),
    "unsupported_claim": frozenset({"yes", "no", "not_applicable"}),
    "abstention_correctness": frozenset({"correct", "incorrect", "not_applicable"}),
}
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_CITATION_RE = re.compile(r"^\[([^\]\[#\r\n]+)#([^\]\[#\r\n]+)\]$")


def _fail(path: str, message: str) -> None:
    raise ValueError(f"{path}: {message}")


def _ensure_object(value: Any, *, path: str, allowed: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(path, "must be an object")
    unknown = sorted(set(value) - allowed)
    if unknown:
        _fail(path, "unknown fields: " + ", ".join(unknown))
    return value


def _non_blank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_notes(value: Any, *, path: str) -> None:
    if value is not None and not isinstance(value, str):
        _fail(path, "must be a string or null")


def _validate_reviewer(value: Any, *, path: str) -> None:
    reviewer = _ensure_object(value, path=path, allowed={"id", "status"})
    reviewer_id = reviewer.get("id")
    status = reviewer.get("status")
    if reviewer_id is not None and not _non_blank(reviewer_id):
        _fail(path, "id must be a non-empty string or null")
    if status not in SET_REVIEW_STATUSES:
        _fail(path, "status must describe pending, partial, or completed review")
    if status == PENDING_REVIEW and reviewer_id is not None:
        _fail(path, "pending reviewer status requires a null id")
    if status != PENDING_REVIEW and not _non_blank(reviewer_id):
        _fail(path, "partial or completed reviewer status requires a reviewer id")


def _validate_label(value: Any, *, field: str, path: str) -> None:
    label_record = _ensure_object(
        value,
        path=f"{path}.{field}",
        allowed={"label", "status", "reviewer_id", "notes"},
    )
    if "label" not in label_record:
        _fail(path, f"{field}.label is required; use null while review is pending")
    label = label_record["label"]
    status = label_record.get("status")
    if status not in REVIEW_STATUSES:
        _fail(path, f"{field}.status must be 'pending_human_review' or 'reviewed'")
    if label is not None and label not in LABEL_VALUES[field]:
        allowed = ", ".join(sorted(LABEL_VALUES[field]))
        _fail(path, f"{field}.label must be one of {allowed}, or null")

    reviewer_id = label_record.get("reviewer_id")
    if reviewer_id is not None and not _non_blank(reviewer_id):
        _fail(path, f"{field}.reviewer_id must be a non-empty string or null")
    if label is None:
        if status != PENDING_REVIEW:
            _fail(path, f"{field} with a null label must remain pending_human_review")
        if reviewer_id is not None:
            _fail(path, f"{field} cannot identify a reviewer while pending")
    else:
        if status != REVIEWED:
            _fail(path, f"{field} with a label must have reviewed status")
        if not _non_blank(reviewer_id):
            _fail(path, f"{field} requires reviewer_id when status is reviewed")
    _validate_notes(label_record.get("notes"), path=f"{path}.{field}.notes")


def _validate_evidence_reference(value: Any, path: str) -> None:
    reference = _ensure_object(
        value,
        path=path,
        allowed={"citation", "source", "chunk_id", "status", "reviewer_id", "notes"},
    )
    required = {"citation", "source", "chunk_id", "status"}
    missing = sorted(required - set(reference))
    if missing:
        _fail(path, "missing fields: " + ", ".join(missing))
    citation = reference["citation"]
    source = reference["source"]
    chunk_id = reference["chunk_id"]
    match = _CITATION_RE.fullmatch(citation) if isinstance(citation, str) else None
    if match is None:
        _fail(path, "citation must match [source#chunk_id] exactly")
    if not _non_blank(source):
        _fail(path, "source must be a non-empty string")
    if not _non_blank(chunk_id):
        _fail(path, "chunk_id must be a non-empty string")
    if source != match.group(1) or chunk_id != match.group(2):
        _fail(path, "citation must agree with source and chunk_id")
    status = reference["status"]
    if status not in REVIEW_STATUSES:
        _fail(path, "status must be pending_human_review or reviewed")
    reviewer_id = reference.get("reviewer_id")
    if reviewer_id is not None and not _non_blank(reviewer_id):
        _fail(path, "reviewer_id must be a non-empty string or null")
    if status == PENDING_REVIEW:
        if reviewer_id is not None:
            _fail(path, "pending evidence references cannot identify a reviewer")
    elif not _non_blank(reviewer_id):
        _fail(path, "reviewed evidence references require reviewer_id")
    _validate_notes(reference.get("notes"), path=f"{path}.notes")


def _validate_fixture_binding(value: Any) -> None:
    binding = _ensure_object(
        value,
        path="annotation_set.fixture_binding",
        allowed={"fixture_file", "algorithm"},
    )
    if not _non_blank(binding.get("fixture_file")):
        _fail("annotation_set.fixture_binding.fixture_file", "must be a non-empty string")
    if binding.get("algorithm") != FIXTURE_BINDING_ALGORITHM:
        _fail(
            "annotation_set.fixture_binding.algorithm",
            f"must be {FIXTURE_BINDING_ALGORITHM!r}",
        )


def _validate_case_immutable_fields(case: dict[str, Any], path: str) -> None:
    if not _non_blank(case.get("split")):
        _fail(path, "split must be a non-empty string")
    if not isinstance(case.get("case_type"), str) or case.get("case_type") not in CASE_TYPES:
        _fail(
            path,
            "case_type must identify answerable, unanswerable, adversarial, or ambiguous",
        )
    if not _non_blank(case.get("question")):
        _fail(path, "question must be a non-empty string")
    answer = case.get("answer")
    if answer is not None and not isinstance(answer, str):
        _fail(path, "answer must be a string or null")
    review_scope = case.get("review_scope")
    if not isinstance(review_scope, list) or not review_scope:
        _fail(path, "review_scope must be a non-empty list")
    if any(not isinstance(item, str) for item in review_scope):
        _fail(path, "review_scope entries must be strings")
    if len(review_scope) != len(set(review_scope)):
        _fail(path, "review_scope must not contain duplicates")
    if any(item not in REVIEW_SCOPE_FIELDS for item in review_scope):
        _fail(path, "review_scope contains an unknown review dimension")
    fixture_hash = case.get("fixture_sha256")
    if not isinstance(fixture_hash, str) or not _SHA256_RE.fullmatch(fixture_hash):
        _fail(path, "fixture_sha256 must be 64 hexadecimal characters")
    _validate_notes(case.get("notes"), path=f"{path}.notes")


def _iter_review_items(cases: list[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for case in cases:
        yield case["abstention_correctness"]
        for claim in case["claims"]:
            for field in CLAIM_LABEL_FIELDS:
                yield claim[field]
            yield from claim["evidence_references"]


def _contains_pending(cases: list[dict[str, Any]]) -> bool:
    for item in _iter_review_items(cases):
        if item.get("status") == PENDING_REVIEW:
            return True
    return False


def _contains_reviewed(cases: list[dict[str, Any]]) -> bool:
    return any(item.get("status") == REVIEWED for item in _iter_review_items(cases))


# Keep the original private helper name for callers that used it in tests; its
# definition now includes evidence-reference statuses as well as labels.
def _annotation_contains_pending(cases: list[dict[str, Any]]) -> bool:
    return _contains_pending(cases)


def validate_annotation_set(
    value: Any,
    fixture_cases: Any | None = None,
) -> None:
    """Validate the strict annotation contract and optionally its fixture binding."""
    annotation = _ensure_object(
        value,
        path="annotation_set",
        allowed={
            "schema_version",
            "review_status",
            "reviewer",
            "fixture_binding",
            "cases",
            "notes",
        },
    )
    if annotation.get("schema_version") != ANNOTATION_SCHEMA_VERSION:
        _fail("annotation_set.schema_version", f"must be {ANNOTATION_SCHEMA_VERSION!r}")
    review_status = annotation.get("review_status")
    if review_status not in SET_REVIEW_STATUSES:
        _fail("annotation_set.review_status", "must describe pending, partial, or completed review")
    _validate_reviewer(annotation.get("reviewer"), path="annotation_set.reviewer")
    _validate_fixture_binding(annotation.get("fixture_binding"))
    _validate_notes(annotation.get("notes"), path="annotation_set.notes")

    reviewer = annotation["reviewer"]
    reviewer_id = reviewer["id"]
    if review_status == PENDING_REVIEW:
        if reviewer["status"] != PENDING_REVIEW or reviewer_id is not None:
            _fail("annotation_set", "pending review requires pending reviewer status and null id")
    elif reviewer["status"] != review_status or not _non_blank(reviewer_id):
        _fail("annotation_set", "reviewer status and identity must match set review_status")

    cases = annotation.get("cases")
    if not isinstance(cases, list):
        _fail("annotation_set.cases", "must be a list")
    case_ids: set[str] = set()
    for case_index, case_value in enumerate(cases):
        case_path = f"annotation_set.cases[{case_index}]"
        case = _ensure_object(
            case_value,
            path=case_path,
            allowed={
                "case_id",
                "split",
                "case_type",
                "question",
                "answer",
                "review_scope",
                "fixture_sha256",
                "abstention_correctness",
                "claims",
                "notes",
            },
        )
        case_id = case.get("case_id")
        if not _non_blank(case_id):
            _fail(case_path, "case_id must be a non-empty string")
        if case_id in case_ids:
            _fail(case_path, f"duplicate case_id {case_id!r}")
        case_ids.add(case_id)
        _validate_case_immutable_fields(case, case_path)
        _validate_label(
            case.get("abstention_correctness"),
            field="abstention_correctness",
            path=case_path,
        )
        claims = case.get("claims")
        if not isinstance(claims, list):
            _fail(case_path, "claims must be a list; use an empty list for an abstention")
        claim_ids: set[str] = set()
        for claim_index, claim_value in enumerate(claims):
            claim_path = f"{case_path}.claims[{claim_index}]"
            claim = _ensure_object(
                claim_value,
                path=claim_path,
                allowed={
                    "claim_id",
                    "claim_text",
                    "claim_support",
                    "citation_completeness",
                    "citation_precision",
                    "unsupported_claim",
                    "evidence_references",
                    "notes",
                },
            )
            claim_id = claim.get("claim_id")
            if not _non_blank(claim_id):
                _fail(claim_path, "claim_id must be a non-empty string")
            if claim_id in claim_ids:
                _fail(claim_path, f"duplicate claim_id {claim_id!r} in case")
            claim_ids.add(claim_id)
            if not _non_blank(claim.get("claim_text")):
                _fail(claim_path, "claim_text must be a non-empty string")
            _validate_notes(claim.get("notes"), path=f"{claim_path}.notes")
            for field in CLAIM_LABEL_FIELDS:
                _validate_label(claim.get(field), field=field, path=claim_path)
            references = claim.get("evidence_references")
            if not isinstance(references, list):
                _fail(claim_path, "evidence_references must be a list")
            for reference_index, reference in enumerate(references):
                _validate_evidence_reference(
                    reference,
                    f"{claim_path}.evidence_references[{reference_index}]",
                )

    pending = _contains_pending(cases)
    reviewed = _contains_reviewed(cases)
    if review_status == REVIEWED and pending:
        _fail(
            "annotation_set.review_status",
            "reviewed sets cannot contain pending labels or references",
        )
    if review_status == PARTIALLY_REVIEWED and (not pending or not reviewed):
        _fail(
            "annotation_set.review_status",
            "partially reviewed sets require both reviewed and pending items",
        )
    if review_status == PENDING_REVIEW and reviewed:
        _fail(
            "annotation_set.review_status",
            "pending sets cannot contain reviewed labels or evidence references",
        )
    if fixture_cases is not None:
        validate_annotation_fixture_binding(annotation, fixture_cases)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _reference_immutable_payload(reference: Any, *, path: str) -> dict[str, str]:
    if not isinstance(reference, dict):
        _fail(path, "must be an object")
    for field in ("citation", "source", "chunk_id"):
        if not _non_blank(reference.get(field)):
            _fail(path, f"{field} must be a non-empty string")
    citation = reference["citation"]
    match = _CITATION_RE.fullmatch(citation)
    if match is None:
        _fail(path, "citation must match [source#chunk_id] exactly")
    if reference["source"] != match.group(1) or reference["chunk_id"] != match.group(2):
        _fail(path, "citation must agree with source and chunk_id")
    return {
        "citation": citation,
        "source": reference["source"],
        "chunk_id": reference["chunk_id"],
    }


def _fixture_claims(fixture: dict[str, Any], *, path: str) -> list[dict[str, Any]]:
    claims = fixture.get("claims")
    if not isinstance(claims, list):
        _fail(path, "fixture claims must be a list")
    result: list[dict[str, Any]] = []
    for index, claim_value in enumerate(claims):
        claim_path = f"{path}.claims[{index}]"
        if not isinstance(claim_value, dict):
            _fail(claim_path, "must be an object")
        claim_id = claim_value.get("claim_id")
        claim_text = claim_value.get("claim_text")
        if not _non_blank(claim_id) or not _non_blank(claim_text):
            _fail(claim_path, "claim_id and claim_text must be non-empty strings")
        references = claim_value.get("evidence_references")
        if not isinstance(references, list):
            _fail(claim_path, "evidence_references must be a list")
        result.append(
            {
                "claim_id": claim_id,
                "claim_text": claim_text,
                "evidence_references": [
                    _reference_immutable_payload(
                        reference,
                        path=f"{claim_path}.evidence_references",
                    )
                    for reference in references
                ],
            }
        )
    return result


def _fixture_immutable_payload(fixture: Any, *, path: str) -> dict[str, Any]:
    if not isinstance(fixture, dict):
        _fail(path, "must be an object")
    answer = fixture.get("answer", fixture.get("candidate_answer"))
    if not isinstance(fixture.get("case_id"), str):
        _fail(path, "case_id must be a string")
    if not _non_blank(fixture.get("split")):
        _fail(path, "split must be a non-empty string")
    if not isinstance(fixture.get("case_type"), str) or fixture.get("case_type") not in CASE_TYPES:
        _fail(path, "case_type is not one of the four allowed case types")
    if not _non_blank(fixture.get("question")):
        _fail(path, "question must be a non-empty string")
    if answer is not None and not isinstance(answer, str):
        _fail(path, "answer must be a string or null")
    review_scope = fixture.get("review_scope")
    if not isinstance(review_scope, list) or not review_scope:
        _fail(path, "review_scope must be a non-empty list")
    if any(not isinstance(item, str) for item in review_scope):
        _fail(path, "review_scope entries must be strings")
    if len(review_scope) != len(set(review_scope)) or any(
        item not in REVIEW_SCOPE_FIELDS for item in review_scope
    ):
        _fail(path, "review_scope contains duplicate or unknown dimensions")
    claims = _fixture_claims(fixture, path=path)
    case_references = fixture.get("evidence_references")
    if not isinstance(case_references, list):
        _fail(path, "evidence_references must be a list")
    return {
        "case_id": fixture["case_id"],
        "split": fixture["split"],
        "case_type": fixture["case_type"],
        "question": fixture["question"],
        "answer": answer,
        "review_scope": review_scope,
        "claims": claims,
        "evidence_references": [
            _reference_immutable_payload(reference, path=f"{path}.evidence_references")
            for reference in case_references
        ],
    }


def _annotation_immutable_payload(case: dict[str, Any], *, path: str) -> dict[str, Any]:
    claims = []
    for index, claim in enumerate(case["claims"]):
        claims.append(
            {
                "claim_id": claim["claim_id"],
                "claim_text": claim["claim_text"],
                "evidence_references": [
                    _reference_immutable_payload(
                        reference,
                        path=f"{path}.claims[{index}].evidence_references",
                    )
                    for reference in claim["evidence_references"]
                ],
            }
        )
    return {
        "case_id": case["case_id"],
        "split": case["split"],
        "case_type": case["case_type"],
        "question": case["question"],
        "answer": case["answer"],
        "review_scope": case["review_scope"],
        "claims": claims,
        "evidence_references": [
            reference
            for claim in claims
            for reference in claim["evidence_references"]
        ],
    }


def canonical_fixture_hash(fixture: Any) -> str:
    """Return the stable hash used to bind an annotation case to its fixture."""
    return hashlib.sha256(
        _canonical_json(_fixture_immutable_payload(fixture, path="fixture")).encode("utf-8")
    ).hexdigest()


def validate_annotation_fixture_binding(
    annotation_set: dict[str, Any], fixture_cases: Any
) -> None:
    """Require annotations to match immutable fixture content exactly.

    Labels and evidence-reference review statuses are intentionally excluded from
    the hash so reviewers can resolve them.  IDs, wording, evidence identifiers,
    split/type/question/answer, and review scope are immutable and must match.
    """
    validate_annotation_set(annotation_set)
    if not isinstance(fixture_cases, list):
        _fail("fixture_cases", "must be a JSON list")
    fixtures_by_id: dict[str, dict[str, Any]] = {}
    for index, fixture in enumerate(fixture_cases):
        payload = _fixture_immutable_payload(fixture, path=f"fixture_cases[{index}]")
        case_id = payload["case_id"]
        if case_id in fixtures_by_id:
            _fail("fixture_cases", f"duplicate case_id {case_id!r}")
        fixtures_by_id[case_id] = fixture

    annotations_by_id = {case["case_id"]: case for case in annotation_set["cases"]}
    if set(annotations_by_id) != set(fixtures_by_id):
        _fail("annotation_set", "annotation and fixture case IDs differ")
    for case_id, fixture in fixtures_by_id.items():
        annotation = annotations_by_id[case_id]
        expected = _fixture_immutable_payload(fixture, path=f"fixture_cases[{case_id!r}]")
        observed = _annotation_immutable_payload(
            annotation,
            path=f"annotation_set.cases[{case_id!r}]",
        )
        if observed != expected:
            _fail(
                f"annotation_set.cases[{case_id!r}]",
                "immutable fields do not match the evidence-contract fixture",
            )
        expected_hash = canonical_fixture_hash(fixture)
        if annotation["fixture_sha256"].lower() != expected_hash:
            _fail(
                f"annotation_set.cases[{case_id!r}].fixture_sha256",
                "does not match the immutable fixture content",
            )


def validate_declared_schema(value: Any, schema_path: Path) -> None:
    """Validate an instance with the declared Draft 2020-12 JSON Schema."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError as error:  # pragma: no cover - exercised in minimal installs
        raise ValueError(
            "jsonschema is required to validate claim annotations; install the dev dependencies"
        ) from error
    try:
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"Could not read annotation schema {schema_path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Annotation schema {schema_path} is not valid JSON") from error
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as error:
        raise ValueError(f"Annotation schema {schema_path} is invalid") from error
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "annotation_set"
        raise ValueError(f"{location}: JSON Schema validation failed: {error.message}")


def load_annotation_set(
    path: Path,
    *,
    schema_path: Path | None = None,
    fixtures_path: Path | None = None,
) -> dict[str, Any]:
    """Load, validate, and bind a versioned annotation set to its fixture file."""
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"Could not read annotation set {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Annotation set {path} is not valid JSON") from error
    if schema_path is None:
        candidate = Path(path).parent / "claim_annotations.schema.json"
        schema_path = candidate if candidate.is_file() else None
    if schema_path is not None:
        validate_declared_schema(value, Path(schema_path))
    validate_annotation_set(value)

    if fixtures_path is None:
        project_root = Path(path).resolve().parent.parent
        candidate = (project_root / value["fixture_binding"]["fixture_file"]).resolve()
        if project_root not in candidate.parents:
            raise ValueError("Annotation fixture path escapes the project root")
        fixtures_path = candidate
    try:
        fixtures = json.loads(Path(fixtures_path).read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"Could not read annotation fixtures {fixtures_path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Annotation fixtures {fixtures_path} are not valid JSON") from error
    validate_annotation_fixture_binding(value, fixtures)
    return value


def _label(value: dict[str, Any]) -> str | None:
    """Return a resolved label, keeping pending values as ``None``."""
    label = value.get("label")
    return label if value.get("status") == REVIEWED else None


def _metric(
    records: Iterable[dict[str, Any]],
    *,
    positive_labels: frozenset[str],
) -> dict[str, Any]:
    labels: list[str] = []
    pending = 0
    not_applicable = 0
    for record in records:
        resolved = _label(record)
        if resolved is None:
            pending += 1
        elif resolved == "not_applicable":
            not_applicable += 1
        else:
            labels.append(resolved)
    counts = dict(sorted(Counter(labels).items()))
    return {
        "reviewed": len(labels),
        "pending": pending,
        "not_applicable": not_applicable,
        "label_counts": counts,
        "positive_count": sum(label in positive_labels for label in labels),
        "rate": (
            float(sum(label in positive_labels for label in labels) / len(labels))
            if labels
            else None
        ),
    }


def evaluate_claim_annotations(annotation_set: dict[str, Any]) -> dict[str, Any]:
    """Summarize labels while counting unresolved evidence references as pending."""
    validate_annotation_set(annotation_set)
    claims: list[tuple[str, str, dict[str, Any]]] = []
    abstentions: list[tuple[str, dict[str, Any]]] = []
    rows: list[dict[str, Any]] = []
    reviewer_labels: list[dict[str, Any]] = []
    reviewed_evidence_references: list[dict[str, Any]] = []
    pending_fields: list[dict[str, Any]] = []
    fully_reviewed_claims = 0
    total_claims = 0
    reviewed_label_count = 0
    pending_label_count = 0
    reviewed_evidence_reference_count = 0
    pending_evidence_reference_count = 0

    reviewer = annotation_set["reviewer"]
    default_reviewer_id = reviewer.get("id")
    for case in annotation_set["cases"]:
        case_id = case["case_id"]
        abstention = case["abstention_correctness"]
        abstentions.append((case_id, abstention))
        case_pending = _label(abstention) is None
        if case_pending:
            pending_label_count += 1
            pending_fields.append(
                {
                    "case_id": case_id,
                    "claim_id": None,
                    "field": "abstention_correctness",
                    "status": PENDING_REVIEW,
                }
            )
        else:
            reviewed_label_count += 1
            reviewer_labels.append(
                {
                    "case_id": case_id,
                    "claim_id": None,
                    "field": "abstention_correctness",
                    "label": _label(abstention),
                    "reviewer_id": abstention.get("reviewer_id", default_reviewer_id),
                }
            )

        case_claims = case["claims"]
        total_claims += len(case_claims)
        for claim in case_claims:
            claim_id = claim["claim_id"]
            claims.append((case_id, claim_id, claim))
            claim_pending = False
            for field in CLAIM_LABEL_FIELDS:
                label_record = claim[field]
                resolved = _label(label_record)
                if resolved is None:
                    pending_label_count += 1
                    claim_pending = True
                    pending_fields.append(
                        {
                            "case_id": case_id,
                            "claim_id": claim_id,
                            "field": field,
                            "status": PENDING_REVIEW,
                        }
                    )
                else:
                    reviewed_label_count += 1
                    reviewer_labels.append(
                        {
                            "case_id": case_id,
                            "claim_id": claim_id,
                            "field": field,
                            "label": resolved,
                            "reviewer_id": label_record.get(
                                "reviewer_id", default_reviewer_id
                            ),
                        }
                    )

            for reference_index, reference in enumerate(claim["evidence_references"]):
                if reference["status"] == PENDING_REVIEW:
                    pending_evidence_reference_count += 1
                    claim_pending = True
                    pending_fields.append(
                        {
                            "case_id": case_id,
                            "claim_id": claim_id,
                            "field": "evidence_references",
                            "reference_index": reference_index,
                            "citation": reference["citation"],
                            "status": PENDING_REVIEW,
                        }
                    )
                else:
                    reviewed_evidence_reference_count += 1
                    reviewed_evidence_references.append(
                        {
                            "case_id": case_id,
                            "claim_id": claim_id,
                            "reference_index": reference_index,
                            "citation": reference["citation"],
                            "reviewer_id": reference.get("reviewer_id", default_reviewer_id),
                        }
                    )
            if not claim_pending:
                fully_reviewed_claims += 1
            case_pending = case_pending or claim_pending

        rows.append(
            {
                "case_id": case_id,
                "split": case["split"],
                "case_type": case["case_type"],
                "claim_count": len(case_claims),
                "pending_evidence_references": sum(
                    reference["status"] == PENDING_REVIEW
                    for claim in case_claims
                    for reference in claim["evidence_references"]
                ),
                "review_status": PENDING_REVIEW if case_pending else REVIEWED,
                "reviewer_id": default_reviewer_id,
            }
        )

    support_records = [claim[2]["claim_support"] for claim in claims]
    completeness_records = [claim[2]["citation_completeness"] for claim in claims]
    precision_records = [claim[2]["citation_precision"] for claim in claims]
    unsupported_records = [claim[2]["unsupported_claim"] for claim in claims]
    abstention_records = [record for _, record in abstentions]
    claim_support = _metric(support_records, positive_labels=frozenset({"supported"}))
    resolved_support = [
        _label(record)
        for record in support_records
        if _label(record) is not None and _label(record) != "not_applicable"
    ]
    claim_support["supported_or_partially_supported_rate"] = (
        float(sum(label in {"supported", "partially_supported"} for label in resolved_support))
        / len(resolved_support)
        if resolved_support
        else None
    )

    required_review_items = (
        reviewed_label_count
        + pending_label_count
        + reviewed_evidence_reference_count
        + pending_evidence_reference_count
    )
    reviewed_review_items = reviewed_label_count + reviewed_evidence_reference_count
    metrics = {
        "cases": len(annotation_set["cases"]),
        "claims": total_claims,
        "reviewed_label_count": reviewed_label_count,
        "pending_label_count": pending_label_count,
        "reviewed_evidence_reference_count": reviewed_evidence_reference_count,
        "pending_evidence_reference_count": pending_evidence_reference_count,
        "fully_reviewed_claims": fully_reviewed_claims,
        "claim_review_completion_rate": (
            float(fully_reviewed_claims / total_claims) if total_claims else None
        ),
        "review_completion": {
            "required_items": required_review_items,
            "reviewed_items": reviewed_review_items,
            "pending_items": required_review_items - reviewed_review_items,
            "rate": (
                float(reviewed_review_items / required_review_items)
                if required_review_items
                else None
            ),
        },
        "claim_support": claim_support,
        "citation_completeness": _metric(
            completeness_records,
            positive_labels=frozenset({"complete"}),
        ),
        "citation_precision": _metric(
            precision_records,
            positive_labels=frozenset({"precise"}),
        ),
        "abstention_correctness": _metric(
            abstention_records,
            positive_labels=frozenset({"correct"}),
        ),
        "unsupported_claims": _metric(
            unsupported_records,
            positive_labels=frozenset({"yes"}),
        ),
    }

    pending_case_ids = [row["case_id"] for row in rows if row["review_status"] != REVIEWED]
    pending_claim_ids = sorted(
        {item["claim_id"] for item in pending_fields if item["claim_id"] is not None}
    )
    return {
        "review_status": annotation_set["review_status"],
        "measured_metrics": metrics,
        "reviewer_labels": {
            "status": "reviewed_labels_only",
            "count": len(reviewer_labels),
            "entries": reviewer_labels,
        },
        "reviewed_evidence_references": {
            "status": "reviewed_references_only",
            "count": len(reviewed_evidence_references),
            "entries": reviewed_evidence_references,
        },
        "pending_review": {
            "status": PENDING_REVIEW if pending_fields else REVIEWED,
            "case_ids": pending_case_ids,
            "claim_ids": pending_claim_ids,
            "pending_fields": pending_fields,
            "counts": {
                "cases": len(pending_case_ids),
                "claims": len(pending_claim_ids),
                "label_fields": pending_label_count,
                "evidence_references": pending_evidence_reference_count,
                "review_items": len(pending_fields),
            },
        },
        "rows": rows,
    }
