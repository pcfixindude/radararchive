"""MRMS visual review sample-set annotations and candidate readiness — local advisory only."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from backend.app.services.mrms_visual_review_sample_set import (
    load_visual_review_sample_set,
)
from backend.app.services.storage import LocalStorage

ANNOTATIONS_JSON = "dev/mrms_visual_review_sample_annotations.json"
READINESS_MD = "dev/mrms_visual_review_sample_readiness.md"

SUGGESTED_READINESS_COMMAND = "make mrms-visual-review-readiness"

STATUS_UNREVIEWED = "unreviewed"
STATUS_ACCEPTABLE = "acceptable"
STATUS_QUESTIONABLE = "questionable"
STATUS_REJECTED = "rejected"

ALLOWED_STATUSES = {
    STATUS_UNREVIEWED,
    STATUS_ACCEPTABLE,
    STATUS_QUESTIONABLE,
    STATUS_REJECTED,
}

ISSUE_MISSING_ARTIFACT = "missing_artifact"
ISSUE_STALE = "stale"
ISSUE_WRONG_MODE = "wrong_mode"
ISSUE_SUSPICIOUS_VISUAL = "suspicious_visual"
ISSUE_NEEDS_FOLLOWUP = "needs_followup"

ALLOWED_ISSUE_TAGS = {
    ISSUE_MISSING_ARTIFACT,
    ISSUE_STALE,
    ISSUE_WRONG_MODE,
    ISSUE_SUSPICIOUS_VISUAL,
    ISSUE_NEEDS_FOLLOWUP,
}

READINESS_NOT_READY = "not_ready"
READINESS_NEEDS_REVIEW = "needs_review"
READINESS_CANDIDATE_READY = "candidate_ready"


class SampleAnnotationValidationError(ValueError):
    """Raised when sample annotation input fails validation."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _annotations_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(ANNOTATIONS_JSON)


def _readiness_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(READINESS_MD)


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_advisory_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "does_not_download_or_decode": True,
        "no_external_notifications": True,
        "candidate_ready_is_not_production_authorization": True,
        "prototype": True,
    }


def build_sample_key(*, timestamp: Optional[str], layer: Optional[str]) -> str:
    return f"{timestamp or 'unknown'}|{layer or 'unknown'}"


def infer_auto_issue_tags(entry: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    if entry.get("missing_artifacts"):
        tags.append(ISSUE_MISSING_ARTIFACT)
    if entry.get("stale_visual_review"):
        tags.append(ISSUE_STALE)
    if entry.get("selection_reason") == "missing_artifacts":
        if ISSUE_NEEDS_FOLLOWUP not in tags:
            tags.append(ISSUE_NEEDS_FOLLOWUP)
    return tags


def validate_annotation_input(
    *,
    sample_key: str,
    status: str,
    operator_notes: Optional[str] = None,
    reviewer_label: Optional[str] = None,
    issue_tags: Optional[list[str]] = None,
) -> None:
    if not (sample_key or "").strip():
        raise SampleAnnotationValidationError("sample_key is required")
    normalized_status = (status or "").strip().lower()
    if normalized_status not in ALLOWED_STATUSES:
        raise SampleAnnotationValidationError(
            f"status must be one of: {', '.join(sorted(ALLOWED_STATUSES))}"
        )
    if normalized_status != STATUS_UNREVIEWED and not (operator_notes or "").strip():
        if normalized_status in {STATUS_QUESTIONABLE, STATUS_REJECTED}:
            raise SampleAnnotationValidationError(
                "operator_notes is required for questionable or rejected samples"
            )
    for tag in issue_tags or []:
        normalized_tag = str(tag).strip().lower()
        if normalized_tag and normalized_tag not in ALLOWED_ISSUE_TAGS:
            raise SampleAnnotationValidationError(
                f"issue tag must be one of: {', '.join(sorted(ALLOWED_ISSUE_TAGS))}"
            )


def load_sample_annotations(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_annotations_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def save_sample_annotations(storage: LocalStorage, payload: dict[str, Any]) -> dict[str, Any]:
    json_path = _annotations_json_path(storage)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    payload = {
        **payload,
        "json_path": json_path,
        "readiness_markdown_path": _readiness_md_path(storage),
        "suggested_command": SUGGESTED_READINESS_COMMAND,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return payload


def _default_annotations_document(sample_set: Optional[dict[str, Any]]) -> dict[str, Any]:
    return {
        "updated_at": _utc_now(),
        "sample_set_created_at": (sample_set or {}).get("created_at"),
        "sample_set_entry_count": int((sample_set or {}).get("entry_count", 0)),
        "annotations": {},
        "latest_readiness": None,
    }


def upsert_sample_annotation(
    storage: LocalStorage,
    *,
    sample_key: str,
    status: str = STATUS_UNREVIEWED,
    operator_notes: Optional[str] = None,
    reviewer_label: Optional[str] = None,
    issue_tags: Optional[list[str]] = None,
) -> dict[str, Any]:
    sample_set = load_visual_review_sample_set(storage)
    if sample_set is None or not (sample_set.get("entries") or []):
        raise SampleAnnotationValidationError(
            "visual review sample set is required before recording annotations"
        )

    entries_by_key = {
        build_sample_key(timestamp=item.get("timestamp"), layer=item.get("layer")): item
        for item in (sample_set.get("entries") or [])
    }
    normalized_key = sample_key.strip()
    entry = entries_by_key.get(normalized_key)
    if entry is None:
        raise SampleAnnotationValidationError(f"sample_key not found in current sample set: {sample_key}")

    validate_annotation_input(
        sample_key=normalized_key,
        status=status,
        operator_notes=operator_notes,
        reviewer_label=reviewer_label,
        issue_tags=issue_tags,
    )

    normalized_status = status.strip().lower()
    normalized_tags = sorted(
        {
            str(tag).strip().lower()
            for tag in (issue_tags or [])
            if str(tag).strip().lower() in ALLOWED_ISSUE_TAGS
        }
    )
    auto_tags = infer_auto_issue_tags(entry)
    merged_tags = sorted(set(normalized_tags) | set(auto_tags))

    document = load_sample_annotations(storage) or _default_annotations_document(sample_set)
    annotations = dict(document.get("annotations") or {})
    reviewed_at = _utc_now() if normalized_status != STATUS_UNREVIEWED else None
    record = {
        "sample_key": normalized_key,
        "timestamp": entry.get("timestamp"),
        "layer": entry.get("layer"),
        "tile_mode": entry.get("tile_mode"),
        "primary_artifact_path": entry.get("primary_artifact_path"),
        "status": normalized_status,
        "operator_notes": (operator_notes or "").strip() or None,
        "reviewed_at": reviewed_at,
        "reviewer_label": (reviewer_label or "").strip() or None,
        "issue_tags": merged_tags,
        "auto_issue_tags": auto_tags,
        **_safety_fields(),
    }
    annotations[normalized_key] = record
    document["updated_at"] = _utc_now()
    document["sample_set_created_at"] = sample_set.get("created_at")
    document["sample_set_entry_count"] = int(sample_set.get("entry_count", 0))
    document["annotations"] = annotations
    readiness = compute_readiness_summary(storage, sample_set=sample_set, annotations=annotations)
    document["latest_readiness"] = readiness
    saved = save_sample_annotations(storage, document)
    save_readiness_markdown(storage, readiness)
    return record


def compute_readiness_summary(
    storage: LocalStorage,
    *,
    sample_set: Optional[dict[str, Any]] = None,
    annotations: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    sample_set = sample_set or load_visual_review_sample_set(storage)
    if sample_set is None:
        return {
            "computed_at": _utc_now(),
            "readiness_level": READINESS_NOT_READY,
            "readiness_reason": "no_sample_set",
            "total_selected_samples": 0,
            "reviewed_samples": 0,
            "unreviewed_samples": 0,
            "acceptable_count": 0,
            "questionable_count": 0,
            "rejected_count": 0,
            "missing_artifact_samples": 0,
            "stale_samples": 0,
            "needs_followup_samples": 0,
            "suspicious_visual_samples": 0,
            "entry_summaries": [],
            "markdown_path": _readiness_md_path(storage),
            "annotations_path": _annotations_json_path(storage),
            "suggested_command": SUGGESTED_READINESS_COMMAND,
            **_safety_fields(),
        }

    entries = list(sample_set.get("entries") or [])
    if annotations is None:
        document = load_sample_annotations(storage)
        annotations = (document or {}).get("annotations") or {}

    total = len(entries)
    reviewed = 0
    unreviewed = 0
    acceptable = 0
    questionable = 0
    rejected = 0
    missing_artifact_samples = 0
    stale_samples = 0
    needs_followup_samples = 0
    suspicious_visual_samples = 0
    entry_summaries: list[dict[str, Any]] = []

    context = sample_set.get("context") or {}
    sample_set_stale = bool(context.get("stale_visual_review"))

    for entry in entries:
        sample_key = build_sample_key(timestamp=entry.get("timestamp"), layer=entry.get("layer"))
        annotation = annotations.get(sample_key) or {}
        status = str(annotation.get("status") or STATUS_UNREVIEWED).lower()
        tags = set(annotation.get("issue_tags") or []) | set(infer_auto_issue_tags(entry))

        if entry.get("missing_artifacts"):
            missing_artifact_samples += 1
        if entry.get("stale_visual_review") or sample_set_stale:
            stale_samples += 1
        if ISSUE_NEEDS_FOLLOWUP in tags:
            needs_followup_samples += 1
        if ISSUE_SUSPICIOUS_VISUAL in tags:
            suspicious_visual_samples += 1

        if status == STATUS_UNREVIEWED:
            unreviewed += 1
        else:
            reviewed += 1
        if status == STATUS_ACCEPTABLE:
            acceptable += 1
        elif status == STATUS_QUESTIONABLE:
            questionable += 1
        elif status == STATUS_REJECTED:
            rejected += 1

        entry_summaries.append(
            {
                "sample_key": sample_key,
                "timestamp": entry.get("timestamp"),
                "layer": entry.get("layer"),
                "tile_mode": entry.get("tile_mode"),
                "primary_artifact_path": entry.get("primary_artifact_path"),
                "status": status,
                "operator_notes": annotation.get("operator_notes"),
                "reviewed_at": annotation.get("reviewed_at"),
                "reviewer_label": annotation.get("reviewer_label"),
                "issue_tags": sorted(tags),
                "missing_artifacts": entry.get("missing_artifacts") or [],
                "stale_visual_review": bool(entry.get("stale_visual_review") or sample_set_stale),
            }
        )

    if total == 0:
        level = READINESS_NOT_READY
        reason = "empty_sample_set"
    elif rejected > 0:
        level = READINESS_NOT_READY
        reason = "rejected_samples_present"
    elif missing_artifact_samples > 0:
        level = READINESS_NOT_READY
        reason = "missing_artifacts_present"
    elif stale_samples > 0 or sample_set_stale:
        level = READINESS_NOT_READY
        reason = "stale_visual_review_present"
    elif questionable > 0:
        level = READINESS_NEEDS_REVIEW
        reason = "questionable_samples_present"
    elif unreviewed > 0:
        level = READINESS_NEEDS_REVIEW
        reason = "unreviewed_samples_remain"
    elif needs_followup_samples > 0 or suspicious_visual_samples > 0:
        level = READINESS_NEEDS_REVIEW
        reason = "followup_or_suspicious_tags_present"
    elif reviewed == total and acceptable == total:
        level = READINESS_CANDIDATE_READY
        reason = "all_samples_acceptable"
    else:
        level = READINESS_NEEDS_REVIEW
        reason = "insufficient_acceptable_coverage"

    return {
        "computed_at": _utc_now(),
        "readiness_level": level,
        "readiness_reason": reason,
        "total_selected_samples": total,
        "reviewed_samples": reviewed,
        "unreviewed_samples": unreviewed,
        "acceptable_count": acceptable,
        "questionable_count": questionable,
        "rejected_count": rejected,
        "missing_artifact_samples": missing_artifact_samples,
        "stale_samples": stale_samples,
        "needs_followup_samples": needs_followup_samples,
        "suspicious_visual_samples": suspicious_visual_samples,
        "sample_set_created_at": sample_set.get("created_at"),
        "entry_summaries": entry_summaries,
        "markdown_path": _readiness_md_path(storage),
        "annotations_path": _annotations_json_path(storage),
        "suggested_command": SUGGESTED_READINESS_COMMAND,
        **_safety_fields(),
    }


def build_readiness_markdown(readiness: dict[str, Any]) -> str:
    lines = [
        "# MRMS Visual Review Sample Readiness (Local Advisory Only)",
        "",
        f"Computed at: {readiness.get('computed_at') or _utc_now()}",
        "",
        "> **WARNING:** This readiness summary is local operator guidance only.",
        "> `candidate_ready` is **NOT** verified MRMS and is **NOT** production authorization.",
        "> It does **NOT** clear validation alerts, enable production rendering, download/decode MRMS,",
        "> or create production tiles.",
        "",
        "## Readiness summary",
        "",
        f"- Advisory readiness level: **{readiness.get('readiness_level')}**",
        f"- Reason: {readiness.get('readiness_reason')}",
        f"- Total selected samples: {readiness.get('total_selected_samples', 0)}",
        f"- Reviewed samples: {readiness.get('reviewed_samples', 0)}",
        f"- Unreviewed samples: {readiness.get('unreviewed_samples', 0)}",
        f"- Acceptable: {readiness.get('acceptable_count', 0)}",
        f"- Questionable: {readiness.get('questionable_count', 0)}",
        f"- Rejected: {readiness.get('rejected_count', 0)}",
        f"- Missing artifact samples: {readiness.get('missing_artifact_samples', 0)}",
        f"- Stale samples: {readiness.get('stale_samples', 0)}",
        f"- Needs follow-up samples: {readiness.get('needs_followup_samples', 0)}",
        f"- Suspicious visual samples: {readiness.get('suspicious_visual_samples', 0)}",
        "",
        "## Sample annotations",
        "",
    ]
    summaries = readiness.get("entry_summaries") or []
    if not summaries:
        lines.append("No sample set entries — run `make mrms-visual-review-sample-set` first.")
    else:
        lines.append("| Sample key | Status | Tile mode | Notes | Issue tags |")
        lines.append("|---|---|---|---|---|")
        for item in summaries:
            tags = ", ".join(item.get("issue_tags") or []) or "—"
            notes = (item.get("operator_notes") or "—").replace("|", "\\|")
            lines.append(
                f"| `{item.get('sample_key')}` | {item.get('status')} | {item.get('tile_mode')} | "
                f"{notes} | {tags} |"
            )

    lines.extend(
        [
            "",
            "## Suggested local command",
            "",
            f"```bash\n{readiness.get('suggested_command') or SUGGESTED_READINESS_COMMAND}\n```",
        ]
    )
    return "\n".join(lines) + "\n"


def save_readiness_markdown(storage: LocalStorage, readiness: dict[str, Any]) -> str:
    md_path = _readiness_md_path(storage)
    storage.ensure_directories(md_path.rsplit("/", 1)[0])
    storage.absolute_path(md_path).write_text(
        build_readiness_markdown(readiness),
        encoding="utf-8",
    )
    return md_path


def refresh_visual_review_sample_readiness(storage: LocalStorage) -> dict[str, Any]:
    sample_set = load_visual_review_sample_set(storage)
    document = load_sample_annotations(storage) or _default_annotations_document(sample_set)
    annotations = document.get("annotations") or {}
    readiness = compute_readiness_summary(
        storage,
        sample_set=sample_set,
        annotations=annotations,
    )
    document["updated_at"] = _utc_now()
    document["sample_set_created_at"] = (sample_set or {}).get("created_at")
    document["sample_set_entry_count"] = int((sample_set or {}).get("entry_count", 0))
    document["latest_readiness"] = readiness
    save_sample_annotations(storage, document)
    save_readiness_markdown(storage, readiness)
    return readiness


def compact_visual_review_sample_readiness(storage: LocalStorage) -> dict[str, Any]:
    document = load_sample_annotations(storage)
    sample_set = load_visual_review_sample_set(storage)
    if document and document.get("latest_readiness"):
        readiness = document["latest_readiness"]
    else:
        readiness = compute_readiness_summary(storage, sample_set=sample_set)
    return {
        "available": bool(sample_set and sample_set.get("entry_count", 0) > 0)
        or bool(document),
        "readiness_level": readiness.get("readiness_level"),
        "readiness_reason": readiness.get("readiness_reason"),
        "total_selected_samples": readiness.get("total_selected_samples", 0),
        "reviewed_samples": readiness.get("reviewed_samples", 0),
        "unreviewed_samples": readiness.get("unreviewed_samples", 0),
        "acceptable_count": readiness.get("acceptable_count", 0),
        "questionable_count": readiness.get("questionable_count", 0),
        "rejected_count": readiness.get("rejected_count", 0),
        "missing_artifact_samples": readiness.get("missing_artifact_samples", 0),
        "stale_samples": readiness.get("stale_samples", 0),
        "needs_followup_samples": readiness.get("needs_followup_samples", 0),
        "suspicious_visual_samples": readiness.get("suspicious_visual_samples", 0),
        "computed_at": readiness.get("computed_at"),
        "annotations_path": readiness.get("annotations_path") or _annotations_json_path(storage),
        "markdown_path": readiness.get("markdown_path") or _readiness_md_path(storage),
        "suggested_command": readiness.get("suggested_command") or SUGGESTED_READINESS_COMMAND,
        "entry_summaries": readiness.get("entry_summaries") or [],
        **_safety_fields(),
    }


def build_visual_review_sample_readiness_payload(storage: LocalStorage) -> dict[str, Any]:
    sample_set = load_visual_review_sample_set(storage)
    document = load_sample_annotations(storage)
    annotations = (document or {}).get("annotations") or {}
    if document and document.get("latest_readiness"):
        readiness = document["latest_readiness"]
        if readiness.get("sample_set_created_at") != (sample_set or {}).get("created_at"):
            readiness = compute_readiness_summary(
                storage,
                sample_set=sample_set,
                annotations=annotations,
            )
    else:
        readiness = compute_readiness_summary(
            storage,
            sample_set=sample_set,
            annotations=annotations,
        )
    return {
        **_safety_fields(),
        "readiness": readiness,
        "annotations": annotations,
        "compact": compact_visual_review_sample_readiness(storage),
    }
