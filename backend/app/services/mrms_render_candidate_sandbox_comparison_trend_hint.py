"""MRMS render candidate sandbox comparison trend hints — local advisory only."""

from __future__ import annotations

import json
from typing import Any, Callable, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox_comparison_history import (
    COMPARISON_BLOCKED,
    COMPARISON_CHANGED,
    COMPARISON_UNCHANGED,
    HISTORY_MISSING,
    SCHEMA_VERSION,
    evaluate_comparison_history_status,
    load_comparison_history,
)
from backend.app.services.mrms_render_candidate_sandbox_import_export import (
    SUGGESTED_IMPORT_EXPORT_COMMAND,
    load_import_export_status,
)
from backend.app.services.storage import LocalStorage

HINT_JSON = "dev/mrms_render_candidate_sandbox_comparison_trend_hint.json"
HINT_MD = "dev/mrms_render_candidate_sandbox_comparison_trend_hint.md"

SUGGESTED_COMMAND = "make mrms-render-candidate-sandbox-comparison-trend-hint"
SUGGESTED_HISTORY_COMMAND = "make mrms-render-candidate-sandbox-comparison-history --refresh"

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
    "Phase 81 — Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status "
    "trend review acknowledgment status trend review acknowledgment (local acknowledgment of reviewed trend hints "
    "without production authorization)"
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


def _entry_status(entry: dict[str, Any]) -> str:
    return str(entry.get("comparison_status") or "")


def _comparison(entry: dict[str, Any]) -> dict[str, Any]:
    data = entry.get("comparison")
    return data if isinstance(data, dict) else {}


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
    changed_count: int,
    unchanged_count: int,
    blocked_count: int,
    changed_streak: int,
) -> str:
    if not recent:
        return TREND_NO_DATA
    if blocked_count > 0 and changed_count == 0:
        return TREND_BLOCKED
    if changed_streak >= 2:
        return TREND_CHANGING
    if changed_count >= 2 and unchanged_count >= 1:
        return TREND_MIXED
    if changed_count >= 1:
        return TREND_CHANGING
    if unchanged_count >= max(1, len(recent)):
        return TREND_STABLE
    return TREND_MIXED


def _suggested_action_for_trend(trend: str, *, review_recommended: bool) -> str:
    if trend == TREND_NO_DATA:
        return (
            "Run make mrms-render-candidate-sandbox-import-export to seed comparison history "
            "before trend hints are available."
        )
    if trend == TREND_BLOCKED:
        return "Resolve blocked comparison history safety gates before relying on trend hints."
    if review_recommended or trend == TREND_CHANGING:
        return (
            "Review recurring sandbox comparison changes — inspect latest import/export manifests "
            "(local advisory only; does not verify MRMS or clear alerts)."
        )
    if trend == TREND_MIXED:
        return (
            "Monitor mixed sandbox comparison trend — some entries changed and some remained stable."
        )
    return "Sandbox comparison trend stable — local monitoring only; does not verify MRMS."


def build_sandbox_comparison_trend_hint(
    storage: LocalStorage,
    *,
    window: int = DEFAULT_TREND_WINDOW,
) -> dict[str, Any]:
    history_eval = evaluate_comparison_history_status(storage)
    history = load_comparison_history(storage, limit=window)
    recent = history[:window]
    import_export = load_import_export_status(storage) or {}

    changed_count = _count_entries(recent, lambda e: _entry_status(e) == COMPARISON_CHANGED)
    unchanged_count = _count_entries(recent, lambda e: _entry_status(e) == COMPARISON_UNCHANGED)
    blocked_count = _count_entries(recent, lambda e: _entry_status(e) == COMPARISON_BLOCKED)
    changed_streak = _streak_from_latest(
        recent,
        predicate=lambda e: _entry_status(e) == COMPARISON_CHANGED,
    )
    sandbox_status_changes = _count_entries(
        recent,
        predicate=lambda e: bool(_comparison(e).get("changed_sandbox_status")),
    )
    safety_gate_changes = _count_entries(
        recent,
        predicate=lambda e: bool(_comparison(e).get("changed_safety_gate_summary")),
    )
    file_count_changes = _count_entries(
        recent,
        predicate=lambda e: bool(_comparison(e).get("changed_file_counts")),
    )

    trend = _classify_trend(
        recent,
        changed_count=changed_count,
        unchanged_count=unchanged_count,
        blocked_count=blocked_count,
        changed_streak=changed_streak,
    )

    blockers: list[str] = list(history_eval.get("blockers") or [])
    warnings: list[str] = list(history_eval.get("warnings") or [])
    safety = _current_safety_state()
    if bool(safety.get("verified_mrms")):
        blockers.append("verified_mrms must remain false")
    if bool(safety.get("enable_production_radar_tiles")):
        blockers.append("production rendering must remain disabled")

    review_recommended = False
    reason: Optional[str] = None
    if blockers:
        trend = TREND_BLOCKED
        reason = "safety_gate_failure"
    elif trend == TREND_NO_DATA:
        reason = "no_comparison_history"
    elif changed_streak >= 2:
        review_recommended = True
        reason = "comparison_changed_streak"
    elif sandbox_status_changes >= 2:
        review_recommended = True
        reason = "recurring_sandbox_status_changes"
    elif safety_gate_changes >= 2:
        review_recommended = True
        reason = "recurring_safety_gate_changes"
    elif trend == TREND_CHANGING:
        review_recommended = True
        reason = "recent_comparison_changes"
    elif trend == TREND_MIXED:
        reason = "mixed_comparison_trend"
    elif trend == TREND_STABLE:
        reason = "stable_comparison_trend"

    if history_eval.get("history_status") == HISTORY_MISSING and trend == TREND_NO_DATA:
        hint_status = HINT_MISSING
    elif blockers or trend == TREND_BLOCKED:
        hint_status = HINT_BLOCKED
    elif review_recommended:
        hint_status = HINT_NEEDS_REVIEW
    else:
        hint_status = HINT_READY

    suggested_command = None
    if review_recommended:
        suggested_command = SUGGESTED_IMPORT_EXPORT_COMMAND
    elif trend == TREND_NO_DATA:
        suggested_command = SUGGESTED_IMPORT_EXPORT_COMMAND

    recurring_signals: list[str] = []
    if sandbox_status_changes >= 2:
        recurring_signals.append("sandbox_status_changes")
    if safety_gate_changes >= 2:
        recurring_signals.append("safety_gate_changes")
    if file_count_changes >= 2:
        recurring_signals.append("file_count_changes")

    return {
        "generated_at": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "hint_status": hint_status,
        "hint_reason": reason,
        "trend": trend,
        "trend_review_recommended": review_recommended,
        "trend_window": window,
        "history_count": len(history),
        "changed_count": changed_count,
        "unchanged_count": unchanged_count,
        "blocked_count": blocked_count,
        "current_changed_streak": changed_streak,
        "sandbox_status_change_count": sandbox_status_changes,
        "safety_gate_change_count": safety_gate_changes,
        "file_count_change_count": file_count_changes,
        "recurring_signals": recurring_signals,
        "blockers": blockers,
        "warnings": warnings,
        "safety_state": safety,
        "history_status": history_eval.get("history_status"),
        "latest_import_export_status": import_export.get("import_export_status"),
        "suggested_action": _suggested_action_for_trend(trend, review_recommended=review_recommended),
        "suggested_command": suggested_command,
        "suggested_history_command": SUGGESTED_HISTORY_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_trend_hint_markdown(hint: dict[str, Any]) -> str:
    lines = [
        "# MRMS Render Candidate Sandbox Comparison Trend Hint",
        "",
        f"Generated at: {hint.get('generated_at')}",
        "",
        "> **WARNING:** Local trend hints only. Advisory metadata — does **NOT** verify MRMS, "
        "enable production rendering, download/decode/render, create or serve production tiles, "
        "clear alerts, or authorize production use.",
        "",
        f"- Hint status: **{hint.get('hint_status')}**",
        f"- Trend: **{hint.get('trend')}**",
        f"- Review recommended: {hint.get('trend_review_recommended')}",
        f"- Reason: {hint.get('hint_reason')}",
        "",
        "## Trend summary",
        "",
        f"- Window: {hint.get('trend_window')} entries",
        f"- Changed: {hint.get('changed_count')}",
        f"- Unchanged: {hint.get('unchanged_count')}",
        f"- Current changed streak: {hint.get('current_changed_streak')}",
        f"- Sandbox status changes: {hint.get('sandbox_status_change_count')}",
        f"- Safety gate changes: {hint.get('safety_gate_change_count')}",
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


def save_sandbox_comparison_trend_hint(storage: LocalStorage, hint: dict[str, Any]) -> dict[str, Any]:
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
    storage.absolute_path(md_path).write_text(build_trend_hint_markdown(hint), encoding="utf-8")
    return hint


def load_sandbox_comparison_trend_hint(storage: LocalStorage) -> Optional[dict[str, Any]]:
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


def refresh_sandbox_comparison_trend_hint(storage: LocalStorage) -> dict[str, Any]:
    hint = build_sandbox_comparison_trend_hint(storage)
    return save_sandbox_comparison_trend_hint(storage, hint)


def compact_sandbox_comparison_trend_hint(storage: LocalStorage) -> dict[str, Any]:
    latest = load_sandbox_comparison_trend_hint(storage)
    if latest is None:
        latest = build_sandbox_comparison_trend_hint(storage)
    return {
        "available": load_sandbox_comparison_trend_hint(storage) is not None,
        "hint_status": latest.get("hint_status"),
        "hint_reason": latest.get("hint_reason"),
        "trend": latest.get("trend"),
        "trend_review_recommended": bool(latest.get("trend_review_recommended")),
        "history_count": latest.get("history_count"),
        "changed_count": latest.get("changed_count"),
        "unchanged_count": latest.get("unchanged_count"),
        "current_changed_streak": latest.get("current_changed_streak"),
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


def build_sandbox_comparison_trend_hint_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_sandbox_comparison_trend_hint(storage)
    if latest is None:
        latest = build_sandbox_comparison_trend_hint(storage)
    return {
        **_safety_fields(),
        "latest": latest,
        "compact": compact_sandbox_comparison_trend_hint(storage),
    }
