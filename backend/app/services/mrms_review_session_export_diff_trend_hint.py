"""Review export diff trend regeneration hints — local review only, not verified MRMS."""

from __future__ import annotations

from typing import Any, Optional

from backend.app.services.mrms_proof_bundle_diff import DIFF_MIXED, DIFF_WORSENED
from backend.app.services.mrms_review_session import (
    compact_latest_review_session_summary,
    load_review_sessions,
)
from backend.app.services.mrms_review_session_compare import load_latest_review_session_comparison
from backend.app.services.mrms_review_session_export import (
    SUGGESTED_EXPORT_COMMAND,
    _is_older,
    load_latest_review_session_export_metadata,
)
from backend.app.services.mrms_review_session_export_diff import load_latest_export_diff_metadata
from backend.app.services.mrms_review_session_export_diff_trends import (
    TREND_MIXED,
    TREND_NO_DATA,
    TREND_WORSENING,
    build_review_session_export_diff_trend,
)
from backend.app.services.proof_bundle_diff_escalation_digest_diff import (
    build_digest_regeneration_hint,
)
from backend.app.services.storage import LocalStorage

SUGGESTED_SESSION_EXPORT_COMMAND = (
    'make mrms-review-session ARGS="--operator YOUR_INITIALS '
    '--notes \'review export trend needs review\' --accepted-limitations --export-after-create"'
)
SUGGESTED_SCHEDULED_REVIEW_EXPORT_COMMAND = "make scheduled-proof-bundle-review-export"

MIXED_OR_WORSE = frozenset({DIFF_WORSENED, DIFF_MIXED})


def _export_is_stale(
    export: Optional[dict[str, Any]],
    latest_session: Optional[dict[str, Any]],
    comparison: Optional[dict[str, Any]],
) -> bool:
    if latest_session is None:
        return False
    if export is None:
        return True
    if export.get("session_id") != latest_session.get("session_id"):
        return True
    if _is_older(export.get("created_at"), latest_session.get("created_at")):
        return True
    if comparison and _is_older(export.get("created_at"), comparison.get("compared_at")):
        return True
    if comparison and export.get("comparison_compared_at") != comparison.get("compared_at"):
        return True
    return False


def _suggested_command_for_reason(reason: Optional[str]) -> Optional[str]:
    if not reason:
        return None
    if reason.startswith("digest_regeneration_recommended"):
        return SUGGESTED_SCHEDULED_REVIEW_EXPORT_COMMAND
    if reason == "latest_review_session_newer_than_export":
        return SUGGESTED_EXPORT_COMMAND
    if (
        reason in ("export_diff_trend_worsening", "export_diff_trend_mixed_streak")
        or reason.startswith("latest_export_diff_")
    ):
        return SUGGESTED_SESSION_EXPORT_COMMAND
    return None


def build_review_session_export_diff_trend_hint(storage: LocalStorage) -> dict[str, Any]:
    """Suggest when operators should create a new review session/export from trend signals."""
    trend = build_review_session_export_diff_trend(storage)
    export_diff = load_latest_export_diff_metadata(storage)
    export_meta = load_latest_review_session_export_metadata(storage)
    sessions = load_review_sessions(storage)
    latest_session = sessions[0] if sessions else None
    comparison = load_latest_review_session_comparison(storage)
    session_summary = compact_latest_review_session_summary(storage)
    digest_hint = build_digest_regeneration_hint(storage)

    latest_export_diff_status = (export_diff or {}).get("overall_export_diff_status")
    trend_value = str(trend.get("trend") or TREND_NO_DATA)
    current_mixed_or_worsened_streak = int(trend.get("current_mixed_or_worsened_streak", 0))
    current_worsened_streak = int(trend.get("current_worsened_streak", 0))
    digest_recommended = bool(digest_hint.get("digest_regeneration_recommended"))
    session_newer = _export_is_stale(export_meta, latest_session, comparison)
    diff_worsened_or_mixed = latest_export_diff_status in MIXED_OR_WORSE
    trend_worsening = trend_value == TREND_WORSENING
    trend_mixed_streak = trend_value == TREND_MIXED and current_mixed_or_worsened_streak >= 2
    trend_or_diff_needs_review = (
        trend_worsening or trend_mixed_streak or diff_worsened_or_mixed
    )

    recommended = False
    reason: Optional[str] = None

    if trend_worsening:
        recommended = True
        reason = "export_diff_trend_worsening"
    elif trend_mixed_streak:
        recommended = True
        reason = "export_diff_trend_mixed_streak"
    elif diff_worsened_or_mixed:
        recommended = True
        reason = f"latest_export_diff_{latest_export_diff_status}"
    elif session_newer:
        recommended = True
        reason = "latest_review_session_newer_than_export"
    elif digest_recommended:
        recommended = True
        reason = f"digest_regeneration_recommended_{digest_hint.get('reason') or 'unknown'}"
    elif trend_value == TREND_NO_DATA:
        reason = "no_export_diff_trend_data"

    suggested_command = _suggested_command_for_reason(reason) if recommended else None

    return {
        "review_trend_regeneration_recommended": recommended,
        "reason": reason,
        "suggested_command": suggested_command,
        "trend": trend_value,
        "latest_export_diff_status": latest_export_diff_status,
        "current_mixed_or_worsened_streak": current_mixed_or_worsened_streak,
        "current_worsened_streak": current_worsened_streak,
        "latest_review_session_id": (latest_session or {}).get("session_id"),
        "latest_export_session_id": (export_meta or {}).get("session_id"),
        "export_is_stale": session_newer,
        "latest_session_at": (latest_session or {}).get("created_at"),
        "latest_export_at": (export_meta or {}).get("created_at"),
        "digest_regeneration_recommended": digest_recommended,
        "session_summary_available": bool(session_summary.get("available")),
        "verified_mrms": False,
        "local_hint_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def compact_review_session_export_diff_trend_hint(storage: LocalStorage) -> dict[str, Any]:
    hint = build_review_session_export_diff_trend_hint(storage)
    return {
        "available": True,
        **hint,
    }


def build_review_session_export_diff_trend_hint_payload(storage: LocalStorage) -> dict[str, Any]:
    hint = compact_review_session_export_diff_trend_hint(storage)
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_hint_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "hint": hint,
    }
