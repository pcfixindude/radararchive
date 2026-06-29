"""MRMS render candidate sandbox acknowledgment status trend review acknowledgment status trend hints — local advisory only."""

from __future__ import annotations

import json
from typing import Any, Callable, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status import (
    ROLLUP_BLOCKED,
    ROLLUP_NEEDS_ACKNOWLEDGMENT,
    ROLLUP_STALE,
    SUGGESTED_COMMAND as SUGGESTED_STATUS_COMMAND,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_history import (
    COVERAGE_IMPROVED,
    COVERAGE_UNCHANGED,
    COVERAGE_WORSENED,
    load_ack_status_trend_review_acknowledgment_status_history,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_trend_hint import SCHEMA_VERSION
from backend.app.services.storage import LocalStorage

HINT_JSON = (
    "dev/mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_hint.json"
)
HINT_MD = (
    "dev/mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_hint.md"
)

SUGGESTED_COMMAND = (
    "make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-hint"
)
SUGGESTED_HISTORY_COMMAND = (
    "make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-history --refresh"
)

DEFAULT_TREND_WINDOW = 10

TREND_NO_DATA = "no_data"
TREND_STABLE = "stable"
TREND_CHANGING = "changing"
TREND_MIXED = "mixed"
TREND_BLOCKED = "blocked"

HINT_MISSING = "missing"
HINT_READY = "ready"
HINT_NEEDS_REVIEW = "needs_review"
HINT_BLOCKED = "blocked"

NEXT_PHASE_RECOMMENDATION = (
    "Phase 82 — Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status "
    "trend review acknowledgment status trend review acknowledgment status (local rollup linking trend hints "
    "to acknowledgments without production authorization)"
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_trend_hint_only": True,
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


def _hint_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(HINT_JSON)


def _hint_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(HINT_MD)


def _rollup_status(entry: dict[str, Any]) -> str:
    return str(entry.get("rollup_status") or "")


def _coverage_change(entry: dict[str, Any]) -> str:
    return str(entry.get("coverage_change") or "")


def _streak_from_latest(
    entries: list[dict[str, Any]],
    *,
    predicate: Callable[[dict[str, Any]], bool],
) -> int:
    count = 0
    for entry in entries:
        if predicate(entry):
            count += 1
        else:
            break
    return count


def _count_entries(entries: list[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]) -> int:
    return sum(1 for entry in entries if predicate(entry))


def _classify_trend(
    recent: list[dict[str, Any]],
    *,
    worsened_count: int,
    improved_count: int,
    unchanged_count: int,
    needs_ack_streak: int,
    stale_streak: int,
) -> str:
    if not recent:
        return TREND_NO_DATA
    if needs_ack_streak >= 2 or stale_streak >= 2 or worsened_count >= 2:
        return TREND_CHANGING
    if worsened_count >= 1 and improved_count >= 1:
        return TREND_MIXED
    if worsened_count >= 1 or stale_streak >= 1:
        return TREND_CHANGING
    if unchanged_count >= max(1, len(recent)) or improved_count >= max(1, len(recent)):
        return TREND_STABLE
    return TREND_MIXED


def _suggested_action_for_trend(trend: str, *, review_recommended: bool) -> str:
    if trend == TREND_NO_DATA:
        return (
            "Refresh trend review acknowledgment status to seed history before status trend hints are available."
        )
    if trend == TREND_BLOCKED:
        return (
            "Resolve blocked trend review acknowledgment status safety gates before relying on trend hints."
        )
    if review_recommended or trend == TREND_CHANGING:
        return (
            "Review recurring trend review acknowledgment status coverage changes — refresh status rollup and "
            "record trend review acknowledgment (local advisory only; does not verify MRMS or clear alerts)."
        )
    if trend == TREND_MIXED:
        return (
            "Monitor mixed trend review acknowledgment status trend — some entries improved and some worsened."
        )
    return "Trend review acknowledgment status trend stable — local monitoring only; does not verify MRMS."


def build_ack_status_trend_review_acknowledgment_status_trend_hint(
    storage: LocalStorage,
    *,
    window: int = DEFAULT_TREND_WINDOW,
) -> dict[str, Any]:
    history = load_ack_status_trend_review_acknowledgment_status_history(storage, limit=window)
    recent = history[:window]

    worsened_count = _count_entries(recent, lambda e: _coverage_change(e) == COVERAGE_WORSENED)
    improved_count = _count_entries(recent, lambda e: _coverage_change(e) == COVERAGE_IMPROVED)
    unchanged_count = _count_entries(recent, lambda e: _coverage_change(e) == COVERAGE_UNCHANGED)
    needs_ack_count = _count_entries(recent, lambda e: _rollup_status(e) == ROLLUP_NEEDS_ACKNOWLEDGMENT)
    stale_count = _count_entries(recent, lambda e: _rollup_status(e) == ROLLUP_STALE)
    stale_ack_count = _count_entries(recent, lambda e: bool(e.get("stale_acknowledgment")))
    needs_ack_streak = _streak_from_latest(
        recent,
        predicate=lambda e: _rollup_status(e) == ROLLUP_NEEDS_ACKNOWLEDGMENT,
    )
    stale_streak = _streak_from_latest(
        recent,
        predicate=lambda e: _rollup_status(e) == ROLLUP_STALE,
    )

    trend = _classify_trend(
        recent,
        worsened_count=worsened_count,
        improved_count=improved_count,
        unchanged_count=unchanged_count,
        needs_ack_streak=needs_ack_streak,
        stale_streak=stale_streak,
    )

    blockers: list[str] = []
    warnings: list[str] = []
    safety = _current_safety_state()
    if bool(safety.get("verified_mrms")):
        blockers.append("verified_mrms must remain false")
    if bool(safety.get("enable_production_radar_tiles")):
        blockers.append("production rendering must remain disabled")
    if not history:
        warnings.append("run trend review acknowledgment status refresh to seed history")

    review_recommended = False
    reason: Optional[str] = None
    if blockers:
        trend = TREND_BLOCKED
        reason = "safety_gate_failure"
    elif trend == TREND_NO_DATA:
        reason = "no_trend_review_ack_status_history"
    elif needs_ack_streak >= 2:
        review_recommended = True
        reason = "needs_acknowledgment_streak"
    elif stale_streak >= 2:
        review_recommended = True
        reason = "stale_acknowledgment_streak"
    elif worsened_count >= 2:
        review_recommended = True
        reason = "recurring_coverage_worsened"
    elif trend == TREND_CHANGING:
        review_recommended = True
        reason = "recent_coverage_changes"
    elif trend == TREND_MIXED:
        reason = "mixed_coverage_trend"
    elif trend == TREND_STABLE:
        reason = "stable_coverage_trend"

    if not history and trend == TREND_NO_DATA:
        hint_status = HINT_MISSING
    elif blockers or trend == TREND_BLOCKED:
        hint_status = HINT_BLOCKED
    elif review_recommended:
        hint_status = HINT_NEEDS_REVIEW
    else:
        hint_status = HINT_READY

    suggested_command = None
    if review_recommended or trend == TREND_NO_DATA:
        suggested_command = SUGGESTED_STATUS_COMMAND

    recurring_signals: list[str] = []
    if needs_ack_count >= 2:
        recurring_signals.append("needs_acknowledgment_entries")
    if stale_count >= 2 or stale_ack_count >= 2:
        recurring_signals.append("stale_acknowledgment_entries")
    if worsened_count >= 2:
        recurring_signals.append("coverage_worsened_entries")

    latest_rollup = (recent[0] or {}).get("rollup_status") if recent else None

    return {
        "generated_at": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "hint_status": hint_status,
        "hint_reason": reason,
        "trend": trend,
        "trend_review_recommended": review_recommended,
        "trend_window": window,
        "history_count": len(history),
        "worsened_count": worsened_count,
        "improved_count": improved_count,
        "unchanged_count": unchanged_count,
        "needs_acknowledgment_count": needs_ack_count,
        "stale_rollup_count": stale_count,
        "stale_acknowledgment_count": stale_ack_count,
        "current_needs_ack_streak": needs_ack_streak,
        "current_stale_streak": stale_streak,
        "latest_rollup_status": latest_rollup,
        "recurring_signals": recurring_signals,
        "blockers": blockers,
        "warnings": warnings,
        "safety_state": safety,
        "suggested_action": _suggested_action_for_trend(trend, review_recommended=review_recommended),
        "suggested_command": suggested_command,
        "suggested_history_command": SUGGESTED_HISTORY_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_ack_status_trend_review_acknowledgment_status_trend_hint_markdown(
    hint: dict[str, Any],
) -> str:
    lines = [
        "# MRMS Render Candidate Sandbox Acknowledgment Status Trend Review Acknowledgment Status Trend Hint",
        "",
        f"Generated at: {hint.get('generated_at')}",
        "",
        "> **WARNING:** Local trend review acknowledgment status trend hints only. Advisory metadata — does **NOT** "
        "verify MRMS, enable production rendering, download/decode/render, create or serve production "
        "tiles, clear alerts, or authorize production use.",
        "",
        f"- Hint status: **{hint.get('hint_status')}**",
        f"- Trend: **{hint.get('trend')}**",
        f"- Review recommended: {hint.get('trend_review_recommended')}",
        f"- Reason: {hint.get('hint_reason')}",
        "",
        "## Trend summary",
        "",
        f"- Window: {hint.get('trend_window')} entries",
        f"- Worsened: {hint.get('worsened_count')}",
        f"- Improved: {hint.get('improved_count')}",
        f"- Unchanged: {hint.get('unchanged_count')}",
        f"- Needs acknowledgment streak: {hint.get('current_needs_ack_streak')}",
        f"- Stale streak: {hint.get('current_stale_streak')}",
        "",
        "## Suggested action",
        "",
        hint.get("suggested_action") or "—",
        "",
    ]
    signals = hint.get("recurring_signals") or []
    lines.extend(["## Recurring signals", ""])
    if signals:
        lines.extend(f"- {item}" for item in signals)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def save_ack_status_trend_review_acknowledgment_status_trend_hint(
    storage: LocalStorage,
    hint: dict[str, Any],
) -> dict[str, Any]:
    json_path = _hint_json_path(storage)
    md_path = _hint_md_path(storage)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    hint = {
        **hint,
        "json_path": json_path,
        "markdown_path": md_path,
        "suggested_command": hint.get("suggested_command") or SUGGESTED_COMMAND,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(hint, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(
        build_ack_status_trend_review_acknowledgment_status_trend_hint_markdown(hint),
        encoding="utf-8",
    )
    return hint


def load_ack_status_trend_review_acknowledgment_status_trend_hint(
    storage: LocalStorage,
) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_hint_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def refresh_ack_status_trend_review_acknowledgment_status_trend_hint(
    storage: LocalStorage,
) -> dict[str, Any]:
    hint = build_ack_status_trend_review_acknowledgment_status_trend_hint(storage)
    return save_ack_status_trend_review_acknowledgment_status_trend_hint(storage, hint)


def compact_ack_status_trend_review_acknowledgment_status_trend_hint(
    storage: LocalStorage,
) -> dict[str, Any]:
    latest = load_ack_status_trend_review_acknowledgment_status_trend_hint(storage)
    if latest is None:
        latest = build_ack_status_trend_review_acknowledgment_status_trend_hint(storage)
    return {
        "available": load_ack_status_trend_review_acknowledgment_status_trend_hint(storage) is not None,
        "hint_status": latest.get("hint_status"),
        "hint_reason": latest.get("hint_reason"),
        "trend": latest.get("trend"),
        "trend_review_recommended": bool(latest.get("trend_review_recommended")),
        "history_count": latest.get("history_count"),
        "worsened_count": latest.get("worsened_count"),
        "improved_count": latest.get("improved_count"),
        "unchanged_count": latest.get("unchanged_count"),
        "current_needs_ack_streak": latest.get("current_needs_ack_streak"),
        "current_stale_streak": latest.get("current_stale_streak"),
        "latest_rollup_status": latest.get("latest_rollup_status"),
        "recurring_signals": latest.get("recurring_signals") or [],
        "blockers": latest.get("blockers") or [],
        "warnings": latest.get("warnings") or [],
        "suggested_action": latest.get("suggested_action"),
        "suggested_command": latest.get("suggested_command") or SUGGESTED_COMMAND,
        "schema_version": latest.get("schema_version") or SCHEMA_VERSION,
        "json_path": _hint_json_path(storage),
        "markdown_path": _hint_md_path(storage),
        "next_phase_recommendation": latest.get("next_phase_recommendation") or NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_ack_status_trend_review_acknowledgment_status_trend_hint_payload(
    storage: LocalStorage,
) -> dict[str, Any]:
    latest = load_ack_status_trend_review_acknowledgment_status_trend_hint(storage)
    if latest is None:
        latest = build_ack_status_trend_review_acknowledgment_status_trend_hint(storage)
    return {
        **_safety_fields(),
        "latest": latest,
        "compact": compact_ack_status_trend_review_acknowledgment_status_trend_hint(storage),
    }
