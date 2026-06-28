"""Review session export diff trend analysis — local review only, not verified MRMS."""

from __future__ import annotations

from typing import Any, Callable, Optional

from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_IMPROVED,
    DIFF_MIXED,
    DIFF_NO_BASELINE,
    DIFF_UNCHANGED,
    DIFF_WORSENED,
)
from backend.app.services.mrms_review_session_export_diff import (
    MAX_EXPORT_DIFF_HISTORY,
    load_export_diff_history,
)
from backend.app.services.storage import LocalStorage

TREND_NO_DATA = "no_data"
TREND_STABLE = "stable"
TREND_IMPROVING = "improving"
TREND_WORSENING = "worsening"
TREND_MIXED = "mixed"

DEFAULT_TREND_WINDOW = 10

MIXED_OR_WORSE = frozenset({DIFF_WORSENED, DIFF_MIXED})


def _diff_status(entry: dict[str, Any]) -> str:
    return str(entry.get("overall_export_diff_status") or "")


def _last_at_for_status(entries: list[dict[str, Any]], status: str) -> Optional[str]:
    for entry in entries:
        if _diff_status(entry) == status:
            return entry.get("compared_at")
    return None


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


def _longest_streak(
    entries: list[dict[str, Any]],
    *,
    predicate: Callable[[dict[str, Any]], bool],
) -> int:
    best = 0
    current = 0
    for entry in entries:
        if predicate(entry):
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _count_status(entries: list[dict[str, Any]], status: str) -> int:
    return sum(1 for entry in entries if _diff_status(entry) == status)


def _suggested_action_for_trend(trend: str, latest_status: Optional[str]) -> str:
    if trend == TREND_NO_DATA:
        return (
            "Run make mrms-review-session-export at least twice (or use --export-after-create) "
            "to seed export diff history."
        )
    if trend == TREND_WORSENING:
        return (
            "Review worsening export diff trend — inspect regressions in latest export diff "
            "and re-export after triage (local review only; does not clear alerts)."
        )
    if trend == TREND_MIXED:
        return (
            "Review mixed export diff trend — triage improvements and regressions across recent "
            "exports; does not verify MRMS or clear alerts."
        )
    if trend == TREND_IMPROVING:
        return (
            "Export diff trend improving — continue monitoring; improvement does not auto-clear "
            "unrelated validation alerts."
        )
    if latest_status == DIFF_UNCHANGED:
        return "Export diff trend stable (unchanged) — local monitoring only."
    return "Monitor review session export diff trend — local evidence only; does not verify MRMS."


def _classify_trend(
    recent: list[dict[str, Any]],
    *,
    worsened_count: int,
    mixed_count: int,
    improved_count: int,
    unchanged_count: int,
    mixed_or_worsened_streak: int,
) -> str:
    if not recent:
        return TREND_NO_DATA
    latest_status = _diff_status(recent[0])
    if latest_status == DIFF_MIXED or mixed_count >= 2:
        return TREND_MIXED
    if worsened_count > improved_count and (worsened_count > 0 or mixed_or_worsened_streak >= 1):
        return TREND_WORSENING
    if improved_count > worsened_count and improved_count > 0:
        return TREND_IMPROVING
    if unchanged_count >= max(1, len(recent) - 1) or latest_status == DIFF_UNCHANGED:
        return TREND_STABLE
    if latest_status == DIFF_WORSENED or mixed_or_worsened_streak >= 1:
        return TREND_WORSENING
    return TREND_STABLE


def build_review_session_export_diff_trend(
    storage: LocalStorage,
    *,
    window: int = DEFAULT_TREND_WINDOW,
) -> dict[str, Any]:
    """Analyze bounded export diff history into a compact trend summary."""
    entries = load_export_diff_history(storage)
    bounded_window = max(1, min(window, MAX_EXPORT_DIFF_HISTORY))
    recent_all = entries[:bounded_window]
    recent = [entry for entry in recent_all if _diff_status(entry) != DIFF_NO_BASELINE]

    empty = {
        "total_diffs": 0,
        "latest_status": None,
        "latest_at": None,
        "last_worsened_at": None,
        "last_improved_at": None,
        "last_mixed_at": None,
        "last_unchanged_at": None,
        "worsened_count": 0,
        "improved_count": 0,
        "mixed_count": 0,
        "unchanged_count": 0,
        "no_baseline_count": 0,
        "current_worsened_streak": 0,
        "current_improved_streak": 0,
        "current_mixed_or_worsened_streak": 0,
        "longest_worsened_streak": 0,
        "longest_mixed_or_worsened_streak": 0,
        "trend": TREND_NO_DATA,
        "window_size": bounded_window,
        "history_count": 0,
        "suggested_next_action": _suggested_action_for_trend(TREND_NO_DATA, None),
        "verified_mrms": False,
        "local_trend_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }
    if not entries:
        return empty

    latest = entries[0]
    latest_status = _diff_status(latest) or None
    worsened_count = _count_status(recent, DIFF_WORSENED)
    mixed_count = _count_status(recent, DIFF_MIXED)
    improved_count = _count_status(recent, DIFF_IMPROVED)
    unchanged_count = _count_status(recent, DIFF_UNCHANGED)
    no_baseline_count = _count_status(entries, DIFF_NO_BASELINE)

    is_worsened = lambda item: _diff_status(item) == DIFF_WORSENED
    is_improved = lambda item: _diff_status(item) == DIFF_IMPROVED
    is_mixed_or_worse = lambda item: _diff_status(item) in MIXED_OR_WORSE

    current_worsened_streak = _streak_from_latest(entries, predicate=is_worsened)
    current_improved_streak = _streak_from_latest(entries, predicate=is_improved)
    current_mixed_or_worsened_streak = _streak_from_latest(entries, predicate=is_mixed_or_worse)
    longest_worsened_streak = _longest_streak(entries, predicate=is_worsened)
    longest_mixed_or_worsened_streak = _longest_streak(entries, predicate=is_mixed_or_worse)

    trend = _classify_trend(
        recent if recent else recent_all,
        worsened_count=worsened_count,
        mixed_count=mixed_count,
        improved_count=improved_count,
        unchanged_count=unchanged_count,
        mixed_or_worsened_streak=current_mixed_or_worsened_streak,
    )

    return {
        "total_diffs": len(entries),
        "latest_status": latest_status,
        "latest_at": latest.get("compared_at"),
        "last_worsened_at": _last_at_for_status(entries, DIFF_WORSENED),
        "last_improved_at": _last_at_for_status(entries, DIFF_IMPROVED),
        "last_mixed_at": _last_at_for_status(entries, DIFF_MIXED),
        "last_unchanged_at": _last_at_for_status(entries, DIFF_UNCHANGED),
        "worsened_count": worsened_count,
        "improved_count": improved_count,
        "mixed_count": mixed_count,
        "unchanged_count": unchanged_count,
        "no_baseline_count": no_baseline_count,
        "current_worsened_streak": current_worsened_streak,
        "current_improved_streak": current_improved_streak,
        "current_mixed_or_worsened_streak": current_mixed_or_worsened_streak,
        "longest_worsened_streak": longest_worsened_streak,
        "longest_mixed_or_worsened_streak": longest_mixed_or_worsened_streak,
        "trend": trend,
        "window_size": bounded_window,
        "history_count": len(entries),
        "suggested_next_action": _suggested_action_for_trend(trend, latest_status),
        "verified_mrms": False,
        "local_trend_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def compact_review_session_export_diff_trend(storage: LocalStorage) -> dict[str, Any]:
    trend = build_review_session_export_diff_trend(storage)
    return {
        "available": trend.get("trend") != TREND_NO_DATA,
        **trend,
    }


def build_review_session_export_diff_trend_payload(
    storage: LocalStorage,
    *,
    window: int = DEFAULT_TREND_WINDOW,
) -> dict[str, Any]:
    trend = build_review_session_export_diff_trend(storage, window=window)
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_trend_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "trend": {
            "available": trend.get("trend") != TREND_NO_DATA,
            **trend,
        },
    }
