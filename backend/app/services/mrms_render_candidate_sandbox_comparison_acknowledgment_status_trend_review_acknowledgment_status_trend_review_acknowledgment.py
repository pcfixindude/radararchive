"""Local trend review acknowledgment status trend hint review acknowledgments — does NOT clear alerts or verify MRMS."""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_hint import (
    build_ack_status_trend_review_acknowledgment_status_trend_hint,
    load_ack_status_trend_review_acknowledgment_status_trend_hint,
)
from backend.app.services.storage import LocalStorage

ACKNOWLEDGMENTS_PATH = (
    "dev/mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgments.json"
)
MAX_ACKNOWLEDGMENTS = 50

SUGGESTED_COMMAND = (
    "make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment"
)

NEXT_PHASE_RECOMMENDATION = (
    "Phase 78 — Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status "
    "trend review acknowledgment status (local rollup linking trend review acknowledgment status trend hints "
    "to trend review acknowledgments without production authorization)"
)


class AckStatusTrendReviewAckStatusTrendReviewAcknowledgmentValidationError(ValueError):
    """Raised when acknowledgment input fails validation."""


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_acknowledgment_only": True,
        "advisory_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "does_not_download_or_decode": True,
        "does_not_create_production_tiles": True,
        "does_not_serve_production_tiles": True,
        "does_not_authorize_production_use": True,
        "prototype": True,
    }


def _ack_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(ACKNOWLEDGMENTS_PATH)


def load_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgments(
    storage: LocalStorage,
) -> list[dict[str, Any]]:
    abs_path = storage.absolute_path(_ack_repo_path(storage))
    if not abs_path.is_file():
        return []
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save_acknowledgments(storage: LocalStorage, entries: list[dict[str, Any]]) -> str:
    repo_path = _ack_repo_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    bounded = entries[:MAX_ACKNOWLEDGMENTS]
    storage.absolute_path(repo_path).write_text(
        json.dumps(bounded, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return repo_path


def _latest_status_trend_hint(storage: LocalStorage) -> dict[str, Any]:
    return (
        load_ack_status_trend_review_acknowledgment_status_trend_hint(storage)
        or build_ack_status_trend_review_acknowledgment_status_trend_hint(storage)
    )


def validate_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_input(
    *,
    operator_name: Optional[str] = None,
    operator_initials: Optional[str] = None,
    note: Optional[str] = None,
) -> None:
    identity = (operator_name or "").strip() or (operator_initials or "").strip()
    if not identity:
        raise AckStatusTrendReviewAckStatusTrendReviewAcknowledgmentValidationError(
            "operator_name or operator_initials is required"
        )
    if not (note or "").strip():
        raise AckStatusTrendReviewAckStatusTrendReviewAcknowledgmentValidationError("note is required")


def create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
    storage: LocalStorage,
    *,
    operator_name: Optional[str] = None,
    operator_initials: Optional[str] = None,
    note: str,
    related_trend: Optional[str] = None,
    related_hint_status: Optional[str] = None,
    related_hint_reason: Optional[str] = None,
    related_trend_review_recommended: Optional[bool] = None,
    acknowledged_trend_review: Optional[bool] = None,
) -> dict[str, Any]:
    """Persist local acknowledgment; does NOT mutate alerts, trend hints, or production gates."""
    validate_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_input(
        operator_name=operator_name,
        operator_initials=operator_initials,
        note=note,
    )

    hint = _latest_status_trend_hint(storage)
    trend = related_trend or hint.get("trend")
    hint_status = related_hint_status or hint.get("hint_status")
    hint_reason = related_hint_reason or hint.get("hint_reason")
    if related_trend_review_recommended is None:
        related_trend_review_recommended = bool(hint.get("trend_review_recommended"))
    if acknowledged_trend_review is None:
        acknowledged_trend_review = bool(related_trend_review_recommended)

    record: dict[str, Any] = {
        "acknowledgment_id": str(uuid.uuid4()),
        "created_at": _utc_now(),
        "operator_name": (operator_name or "").strip() or None,
        "operator_initials": (operator_initials or "").strip() or None,
        "operator": (operator_name or "").strip() or (operator_initials or "").strip(),
        "note": note.strip(),
        "related_trend": trend,
        "related_hint_status": hint_status,
        "related_hint_reason": hint_reason,
        "related_trend_review_recommended": bool(related_trend_review_recommended),
        "related_hint_generated_at": hint.get("generated_at"),
        "related_worsened_count": hint.get("worsened_count"),
        "related_history_count": hint.get("history_count"),
        "latest_rollup_status": hint.get("latest_rollup_status"),
        "acknowledged_trend_review": bool(acknowledged_trend_review),
        "production_rendering_enabled": settings.enable_production_radar_tiles,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }

    entries = load_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgments(storage)
    entries.insert(0, record)
    _save_acknowledgments(storage, entries)
    return record


def load_latest_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
    storage: LocalStorage,
) -> Optional[dict[str, Any]]:
    entries = load_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgments(storage)
    return entries[0] if entries else None


def count_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgments(
    storage: LocalStorage,
) -> int:
    return len(load_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgments(storage))


def compact_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
    entry: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    if entry is None:
        return None
    return {
        "acknowledgment_id": entry.get("acknowledgment_id"),
        "created_at": entry.get("created_at"),
        "operator": entry.get("operator"),
        "operator_name": entry.get("operator_name"),
        "operator_initials": entry.get("operator_initials"),
        "note": entry.get("note"),
        "related_trend": entry.get("related_trend"),
        "related_hint_status": entry.get("related_hint_status"),
        "related_hint_reason": entry.get("related_hint_reason"),
        "related_trend_review_recommended": bool(entry.get("related_trend_review_recommended")),
        "acknowledged_trend_review": bool(entry.get("acknowledged_trend_review")),
        "latest_rollup_status": entry.get("latest_rollup_status"),
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }


def compact_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_summary(
    storage: LocalStorage,
) -> dict[str, Any]:
    latest = load_latest_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment(storage)
    count = count_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgments(storage)
    hint = _latest_status_trend_hint(storage)
    trend_review_still_recommended = bool(hint.get("trend_review_recommended"))
    if latest is None:
        return {
            "available": False,
            "count": 0,
            "trend_review_still_recommended": trend_review_still_recommended,
            "suggested_command": SUGGESTED_COMMAND,
            "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
            **_safety_fields(),
        }
    compact = compact_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment(latest) or {}
    return {
        "available": True,
        "count": count,
        "trend_review_still_recommended": trend_review_still_recommended,
        "suggested_command": SUGGESTED_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **compact,
        **_safety_fields(),
    }


def build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgments_payload(
    storage: LocalStorage,
    *,
    limit: int = 25,
) -> dict[str, Any]:
    entries = load_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgments(storage)
    bounded = max(1, min(limit, MAX_ACKNOWLEDGMENTS))
    hint = _latest_status_trend_hint(storage)
    latest = compact_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
        entries[0] if entries else None
    )
    return {
        "count": len(entries),
        "max_entries": MAX_ACKNOWLEDGMENTS,
        "trend_review_still_recommended": bool(hint.get("trend_review_recommended")),
        "latest": latest,
        "entries": [
            compact_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment(item)
            for item in entries[:bounded]
            if item
        ],
        "suggested_command": SUGGESTED_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }
