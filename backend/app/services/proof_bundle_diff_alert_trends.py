"""Proof bundle diff alert trend analysis — local monitoring only, not verified MRMS."""

from __future__ import annotations

from typing import Any, Optional

from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_IMPROVED,
    DIFF_MIXED,
    DIFF_UNCHANGED,
    DIFF_WORSENED,
    proof_bundle_diff_requires_attention,
)
from backend.app.services.proof_bundle_diff_alert_history import (
    load_proof_bundle_diff_alert_history,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import (
    CAUSE_PROOF_BUNDLE_DIFF_WORSENED,
    SUGGESTED_ACTIONS,
)

TREND_NO_DATA = "no_data"
TREND_STABLE = "stable"
TREND_IMPROVING = "improving"
TREND_WORSENING = "worsening"
TREND_MIXED = "mixed"

DEFAULT_TREND_WINDOW = 10


def _last_at_for_status(
    entries: list[dict[str, Any]],
    status: str,
) -> Optional[str]:
    for entry in entries:
        if str(entry.get("diff_status") or "") == status:
            return entry.get("created_at")
    return None


def _streak_from_latest(
    entries: list[dict[str, Any]],
    *,
    predicate,
) -> int:
    count = 0
    for entry in entries:
        if predicate(entry):
            count += 1
        else:
            break
    return count


def _count_status(entries: list[dict[str, Any]], status: str) -> int:
    return sum(1 for entry in entries if str(entry.get("diff_status") or "") == status)


def _suggested_action_for_trend(trend: str, latest_status: Optional[str]) -> str:
    if trend == TREND_NO_DATA:
        return (
            "Run make mrms-proof-bundle-diff or make scheduled-proof-bundle to seed diff alert history."
        )
    if trend == TREND_WORSENING:
        return SUGGESTED_ACTIONS.get(
            CAUSE_PROOF_BUNDLE_DIFF_WORSENED,
            "Review worsening diff alert trend and compare bundle evidence.",
        )
    if trend == TREND_MIXED:
        return (
            "Review mixed diff alert trend — triage each evidence change; "
            "does not verify MRMS or clear alerts."
        )
    if trend == TREND_IMPROVING:
        return (
            "Diff alert trend improving — continue monitoring; "
            "improvement does not auto-clear unrelated validation alerts."
        )
    if latest_status == DIFF_UNCHANGED:
        return "Diff alert trend stable (unchanged) — local monitoring only."
    return "Monitor proof bundle diff alert trend — local evidence only; does not verify MRMS."


def _classify_trend(
    recent: list[dict[str, Any]],
    *,
    worsened_count: int,
    mixed_count: int,
    improved_count: int,
    unchanged_count: int,
    attention_streak: int,
) -> str:
    if not recent:
        return TREND_NO_DATA
    latest_status = str(recent[0].get("diff_status") or "")
    if latest_status == DIFF_MIXED or mixed_count >= 2:
        return TREND_MIXED
    if worsened_count > improved_count and (worsened_count > 0 or attention_streak >= 1):
        return TREND_WORSENING
    if improved_count > worsened_count and improved_count > 0:
        return TREND_IMPROVING
    if unchanged_count >= max(1, len(recent) - 1) or latest_status == DIFF_UNCHANGED:
        return TREND_STABLE
    if latest_status in (DIFF_WORSENED,) or attention_streak >= 1:
        return TREND_WORSENING
    return TREND_STABLE


def build_proof_bundle_diff_alert_trend(
    storage: LocalStorage,
    *,
    window: int = DEFAULT_TREND_WINDOW,
) -> dict[str, Any]:
    """Analyze recent diff alert history into a compact trend summary."""
    entries = load_proof_bundle_diff_alert_history(storage)
    bounded_window = max(1, min(window, 25))
    recent = entries[:bounded_window]

    if not recent:
        return {
            "latest_status": None,
            "latest_at": None,
            "last_worsened_at": None,
            "last_mixed_at": None,
            "last_improved_at": None,
            "last_unchanged_at": None,
            "current_attention_streak": 0,
            "current_non_attention_streak": 0,
            "recent_worsened_count": 0,
            "recent_mixed_count": 0,
            "recent_improved_count": 0,
            "recent_unchanged_count": 0,
            "trend": TREND_NO_DATA,
            "window_size": bounded_window,
            "history_count": 0,
            "suggested_next_action": _suggested_action_for_trend(TREND_NO_DATA, None),
            "verified_mrms": False,
            "local_trend_only": True,
            "prototype": True,
        }

    latest = recent[0]
    latest_status = latest.get("diff_status")
    worsened_count = _count_status(recent, DIFF_WORSENED)
    mixed_count = _count_status(recent, DIFF_MIXED)
    improved_count = _count_status(recent, DIFF_IMPROVED)
    unchanged_count = _count_status(recent, DIFF_UNCHANGED)
    attention_streak = _streak_from_latest(
        entries,
        predicate=lambda item: bool(item.get("operator_attention_needed")),
    )
    non_attention_streak = _streak_from_latest(
        entries,
        predicate=lambda item: not bool(item.get("operator_attention_needed")),
    )
    trend = _classify_trend(
        recent,
        worsened_count=worsened_count,
        mixed_count=mixed_count,
        improved_count=improved_count,
        unchanged_count=unchanged_count,
        attention_streak=attention_streak,
    )

    return {
        "latest_status": latest_status,
        "latest_at": latest.get("created_at"),
        "last_worsened_at": _last_at_for_status(entries, DIFF_WORSENED),
        "last_mixed_at": _last_at_for_status(entries, DIFF_MIXED),
        "last_improved_at": _last_at_for_status(entries, DIFF_IMPROVED),
        "last_unchanged_at": _last_at_for_status(entries, DIFF_UNCHANGED),
        "current_attention_streak": attention_streak,
        "current_non_attention_streak": non_attention_streak,
        "recent_worsened_count": worsened_count,
        "recent_mixed_count": mixed_count,
        "recent_improved_count": improved_count,
        "recent_unchanged_count": unchanged_count,
        "trend": trend,
        "window_size": bounded_window,
        "history_count": len(entries),
        "suggested_next_action": _suggested_action_for_trend(trend, str(latest_status or "")),
        "verified_mrms": False,
        "local_trend_only": True,
        "prototype": True,
    }


def compact_proof_bundle_diff_alert_trend(storage: LocalStorage) -> dict[str, Any]:
    trend = build_proof_bundle_diff_alert_trend(storage)
    return {
        "available": trend.get("trend") != TREND_NO_DATA,
        **trend,
    }


def build_proof_bundle_diff_alert_trend_payload(
    storage: LocalStorage,
    *,
    window: int = DEFAULT_TREND_WINDOW,
) -> dict[str, Any]:
    trend = build_proof_bundle_diff_alert_trend(storage, window=window)
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_trend_only": True,
        "trend": trend,
    }
