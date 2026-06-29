"""MRMS render candidate sandbox acknowledgment status trend review acknowledgment status — local rollup only."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint import (
    HINT_BLOCKED,
    HINT_MISSING,
    SCHEMA_VERSION,
    TREND_BLOCKED,
    TREND_NO_DATA,
    build_ack_status_trend_hint,
    load_ack_status_trend_hint,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment import (
    count_ack_status_trend_review_acknowledgments,
    load_latest_ack_status_trend_review_acknowledgment,
)
from backend.app.services.storage import LocalStorage

STATUS_JSON = (
    "dev/mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status.json"
)
STATUS_MD = (
    "dev/mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status.md"
)

SUGGESTED_COMMAND = (
    "make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status"
)
SUGGESTED_ACK_COMMAND = (
    "make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment"
)

ACK_STATUS_MISSING = "missing"
ACK_STATUS_NOT_NEEDED = "not_needed"
ACK_STATUS_NONE = "none"
ACK_STATUS_CURRENT = "current"
ACK_STATUS_STALE = "stale"
ACK_STATUS_BLOCKED = "blocked"

ROLLUP_MISSING = "missing"
ROLLUP_NOT_NEEDED = "not_needed"
ROLLUP_NEEDS_ACKNOWLEDGMENT = "needs_acknowledgment"
ROLLUP_CURRENT = "current"
ROLLUP_STALE = "stale"
ROLLUP_BLOCKED = "blocked"

NEXT_PHASE_RECOMMENDATION = (
    "Phase 80 — Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status "
    "trend review acknowledgment status trend hints (local advisory trend hints derived from status history "
    "without production authorization)"
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_status_rollup_only": True,
        "advisory_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "does_not_download_or_decode": True,
        "does_not_create_production_tiles": True,
        "does_not_serve_production_tiles": True,
        "does_not_delete_by_default": True,
        "binary_artifacts_included": False,
        "no_external_notifications": True,
        "does_not_authorize_production_use": True,
        "prototype": True,
    }


def _current_safety_state() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "enable_production_radar_tiles": settings.enable_production_radar_tiles,
        "enable_decoded_tiles": settings.enable_decoded_tiles,
        "placeholder_default": not settings.enable_production_radar_tiles
        and not settings.enable_decoded_tiles,
        "production_tile_serving_enabled": settings.enable_production_radar_tiles,
    }


def _status_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(STATUS_JSON)


def _status_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(STATUS_MD)


def _iso_before(left: Optional[str], right: Optional[str]) -> bool:
    if not left or not right:
        return False
    return str(left) < str(right)


def _hint_snapshot_matches_acknowledgment(
    hint: dict[str, Any],
    acknowledgment: dict[str, Any],
) -> bool:
    if acknowledgment.get("related_trend") != hint.get("trend"):
        return False
    if acknowledgment.get("related_hint_status") != hint.get("hint_status"):
        return False
    hint_generated = hint.get("generated_at")
    ack_generated = acknowledgment.get("related_hint_generated_at")
    if hint_generated and ack_generated and hint_generated != ack_generated:
        return False
    if hint.get("worsened_count") != acknowledgment.get("related_worsened_count"):
        return False
    if hint.get("history_count") != acknowledgment.get("related_history_count"):
        return False
    if hint.get("latest_rollup_status") != acknowledgment.get("latest_rollup_status"):
        return False
    return True


def _classify_acknowledgment_status(
    *,
    hint: dict[str, Any],
    latest_ack: Optional[dict[str, Any]],
    blockers: list[str],
) -> tuple[str, bool, str]:
    if blockers or hint.get("trend") == TREND_BLOCKED or hint.get("hint_status") == HINT_BLOCKED:
        return ACK_STATUS_BLOCKED, False, "safety_gate_failure"
    if hint.get("trend") == TREND_NO_DATA or hint.get("hint_status") == HINT_MISSING:
        return ACK_STATUS_MISSING, False, "no_status_trend_hint"
    if not bool(hint.get("trend_review_recommended")):
        return ACK_STATUS_NOT_NEEDED, False, "trend_review_not_recommended"
    if latest_ack is None:
        return ACK_STATUS_NONE, False, "acknowledgment_missing"
    if not _hint_snapshot_matches_acknowledgment(hint, latest_ack):
        return ACK_STATUS_STALE, True, "acknowledgment_stale"
    ack_at = latest_ack.get("created_at")
    hint_at = hint.get("generated_at")
    if _iso_before(ack_at, hint_at):
        return ACK_STATUS_STALE, True, "acknowledgment_before_hint"
    return ACK_STATUS_CURRENT, False, "acknowledgment_current"


def _rollup_status_for_acknowledgment_status(acknowledgment_status: str) -> str:
    if acknowledgment_status == ACK_STATUS_BLOCKED:
        return ROLLUP_BLOCKED
    if acknowledgment_status == ACK_STATUS_MISSING:
        return ROLLUP_MISSING
    if acknowledgment_status == ACK_STATUS_NOT_NEEDED:
        return ROLLUP_NOT_NEEDED
    if acknowledgment_status == ACK_STATUS_NONE:
        return ROLLUP_NEEDS_ACKNOWLEDGMENT
    if acknowledgment_status == ACK_STATUS_STALE:
        return ROLLUP_STALE
    return ROLLUP_CURRENT


def _suggested_action_for_status(
    *,
    rollup_status: str,
    acknowledgment_status: str,
    stale_acknowledgment: bool,
) -> str:
    if rollup_status == ROLLUP_BLOCKED:
        return (
            "Resolve blocked acknowledgment status trend hint safety gates before relying on "
            "trend review acknowledgment status."
        )
    if rollup_status == ROLLUP_MISSING:
        return (
            "Seed acknowledgment status history and refresh status trend hints before trend review "
            "acknowledgment status is available."
        )
    if rollup_status == ROLLUP_NOT_NEEDED:
        return (
            "Acknowledgment status trend stable — trend review acknowledgment not required "
            "(local monitoring only)."
        )
    if rollup_status == ROLLUP_NEEDS_ACKNOWLEDGMENT:
        return (
            "Record local status trend review acknowledgment after reviewing trend hints "
            "(does not verify MRMS or clear alerts)."
        )
    if rollup_status == ROLLUP_STALE or stale_acknowledgment:
        return (
            "Re-review updated acknowledgment status trend hints and record a fresh trend review "
            "acknowledgment (local advisory only)."
        )
    return (
        "Status trend review acknowledgment status current for latest acknowledgment status trend hint snapshot."
    )


def build_ack_status_trend_review_acknowledgment_status(storage: LocalStorage) -> dict[str, Any]:
    hint = load_ack_status_trend_hint(storage) or build_ack_status_trend_hint(storage)
    latest_ack = load_latest_ack_status_trend_review_acknowledgment(storage)
    acknowledgment_count = count_ack_status_trend_review_acknowledgments(storage)

    blockers: list[str] = list(hint.get("blockers") or [])
    safety = _current_safety_state()
    if bool(safety.get("verified_mrms")):
        blockers.append("verified_mrms must remain false")
    if bool(safety.get("enable_production_radar_tiles")):
        blockers.append("production rendering must remain disabled")

    acknowledgment_status, stale_acknowledgment, status_reason = _classify_acknowledgment_status(
        hint=hint,
        latest_ack=latest_ack,
        blockers=blockers,
    )
    rollup_status = _rollup_status_for_acknowledgment_status(acknowledgment_status)

    suggested_command = None
    if rollup_status in {ROLLUP_NEEDS_ACKNOWLEDGMENT, ROLLUP_STALE}:
        suggested_command = SUGGESTED_ACK_COMMAND

    return {
        "generated_at": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "rollup_status": rollup_status,
        "acknowledgment_status": acknowledgment_status,
        "status_reason": status_reason,
        "stale_acknowledgment": stale_acknowledgment,
        "trend": hint.get("trend"),
        "hint_status": hint.get("hint_status"),
        "hint_reason": hint.get("hint_reason"),
        "trend_review_recommended": bool(hint.get("trend_review_recommended")),
        "hint_generated_at": hint.get("generated_at"),
        "acknowledgment_count": acknowledgment_count,
        "latest_acknowledgment_id": (latest_ack or {}).get("acknowledgment_id"),
        "latest_acknowledgment_created_at": (latest_ack or {}).get("created_at"),
        "latest_acknowledgment_operator": (latest_ack or {}).get("operator"),
        "blockers": blockers,
        "warnings": list(hint.get("warnings") or []),
        "safety_state": safety,
        "suggested_action": _suggested_action_for_status(
            rollup_status=rollup_status,
            acknowledgment_status=acknowledgment_status,
            stale_acknowledgment=stale_acknowledgment,
        ),
        "suggested_command": suggested_command,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_ack_status_trend_review_acknowledgment_status_markdown(status: dict[str, Any]) -> str:
    lines = [
        "# MRMS Render Candidate Sandbox Comparison Acknowledgment Status Trend Review Acknowledgment Status",
        "",
        f"Generated at: {status.get('generated_at')}",
        "",
        "> **WARNING:** Local trend review acknowledgment status rollup only. Advisory metadata — does **NOT** "
        "verify MRMS, enable production rendering, download/decode/render, create or serve production "
        "tiles, clear alerts, or authorize production use.",
        "",
        f"- Rollup status: **{status.get('rollup_status')}**",
        f"- Acknowledgment status: **{status.get('acknowledgment_status')}**",
        f"- Reason: {status.get('status_reason')}",
        f"- Stale acknowledgment: {status.get('stale_acknowledgment')}",
        "",
        "## Status trend hint snapshot",
        "",
        f"- Trend: {status.get('trend')}",
        f"- Hint status: {status.get('hint_status')}",
        f"- Review recommended: {status.get('trend_review_recommended')}",
        f"- Hint generated at: {status.get('hint_generated_at')}",
        "",
        "## Latest trend review acknowledgment",
        "",
        f"- Count: {status.get('acknowledgment_count')}",
        f"- Latest ID: {status.get('latest_acknowledgment_id') or '—'}",
        f"- Latest operator: {status.get('latest_acknowledgment_operator') or '—'}",
        f"- Latest created at: {status.get('latest_acknowledgment_created_at') or '—'}",
        "",
        "## Suggested action",
        "",
        status.get("suggested_action") or "—",
        "",
    ]
    return "\n".join(lines) + "\n"


def save_ack_status_trend_review_acknowledgment_status(
    storage: LocalStorage,
    status: dict[str, Any],
) -> dict[str, Any]:
    from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_history import (
        append_ack_status_trend_review_acknowledgment_status_history_entry,
        refresh_ack_status_trend_review_acknowledgment_status_history_report,
    )

    json_path = _status_json_path(storage)
    md_path = _status_md_path(storage)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    status = {
        **status,
        "json_path": json_path,
        "markdown_path": md_path,
        "suggested_command": status.get("suggested_command") or SUGGESTED_COMMAND,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(status, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(
        build_ack_status_trend_review_acknowledgment_status_markdown(status),
        encoding="utf-8",
    )
    append_ack_status_trend_review_acknowledgment_status_history_entry(storage, status)
    refresh_ack_status_trend_review_acknowledgment_status_history_report(storage)
    return status


def load_ack_status_trend_review_acknowledgment_status(
    storage: LocalStorage,
) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_status_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def refresh_ack_status_trend_review_acknowledgment_status(storage: LocalStorage) -> dict[str, Any]:
    status = build_ack_status_trend_review_acknowledgment_status(storage)
    return save_ack_status_trend_review_acknowledgment_status(storage, status)


def compact_ack_status_trend_review_acknowledgment_status(storage: LocalStorage) -> dict[str, Any]:
    latest = load_ack_status_trend_review_acknowledgment_status(storage)
    if latest is None:
        latest = build_ack_status_trend_review_acknowledgment_status(storage)
    return {
        "available": load_ack_status_trend_review_acknowledgment_status(storage) is not None,
        "rollup_status": latest.get("rollup_status"),
        "acknowledgment_status": latest.get("acknowledgment_status"),
        "status_reason": latest.get("status_reason"),
        "stale_acknowledgment": bool(latest.get("stale_acknowledgment")),
        "trend": latest.get("trend"),
        "hint_status": latest.get("hint_status"),
        "trend_review_recommended": bool(latest.get("trend_review_recommended")),
        "acknowledgment_count": latest.get("acknowledgment_count"),
        "latest_acknowledgment_id": latest.get("latest_acknowledgment_id"),
        "latest_acknowledgment_created_at": latest.get("latest_acknowledgment_created_at"),
        "latest_acknowledgment_operator": latest.get("latest_acknowledgment_operator"),
        "blockers": latest.get("blockers") or [],
        "warnings": latest.get("warnings") or [],
        "suggested_action": latest.get("suggested_action"),
        "suggested_command": latest.get("suggested_command") or SUGGESTED_COMMAND,
        "schema_version": latest.get("schema_version") or SCHEMA_VERSION,
        "json_path": _status_json_path(storage),
        "markdown_path": _status_md_path(storage),
        "next_phase_recommendation": latest.get("next_phase_recommendation") or NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_ack_status_trend_review_acknowledgment_status_payload(
    storage: LocalStorage,
) -> dict[str, Any]:
    latest = load_ack_status_trend_review_acknowledgment_status(storage)
    if latest is None:
        latest = build_ack_status_trend_review_acknowledgment_status(storage)
    return {
        **_safety_fields(),
        "latest": latest,
        "compact": compact_ack_status_trend_review_acknowledgment_status(storage),
    }
