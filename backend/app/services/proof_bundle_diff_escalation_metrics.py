"""Escalation history trend metrics — local review only, not verified MRMS."""

from __future__ import annotations

from typing import Any, Callable, Optional

from backend.app.services.proof_bundle_diff_escalation import (
    ESCALATION_ATTENTION,
    ESCALATION_NONE,
    ESCALATION_URGENT,
    ESCALATION_WATCH,
    build_proof_bundle_diff_escalation,
)
from backend.app.services.proof_bundle_diff_escalation_history import (
    load_proof_bundle_diff_escalation_history,
)
from backend.app.services.storage import LocalStorage


def _is_urgent(level: Optional[str]) -> bool:
    return str(level or "") == ESCALATION_URGENT


def _is_attention_or_urgent(level: Optional[str]) -> bool:
    return str(level or "") in (ESCALATION_ATTENTION, ESCALATION_URGENT)


def _longest_streak(entries: list[dict[str, Any]], predicate: Callable[[Optional[str]], bool]) -> int:
    """Entries in chronological order (oldest first)."""
    best = 0
    current = 0
    for entry in entries:
        if predicate(entry.get("escalation_level")):
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _current_streak_from_newest(
    entries: list[dict[str, Any]],
    predicate: Callable[[Optional[str]], bool],
) -> int:
    count = 0
    for entry in entries:
        if predicate(entry.get("escalation_level")):
            count += 1
        else:
            break
    return count


def build_proof_bundle_diff_escalation_metrics(
    storage: LocalStorage,
) -> dict[str, Any]:
    """Compute rollup metrics from bounded escalation history snapshots."""
    entries = load_proof_bundle_diff_escalation_history(storage)
    chronological = list(reversed(entries))
    latest = entries[0] if entries else None
    current_escalation = build_proof_bundle_diff_escalation(storage)

    urgent_times = [
        str(entry.get("created_at"))
        for entry in entries
        if _is_urgent(entry.get("escalation_level")) and entry.get("created_at")
    ]

    counts = {
        ESCALATION_NONE: 0,
        ESCALATION_WATCH: 0,
        ESCALATION_ATTENTION: 0,
        ESCALATION_URGENT: 0,
    }
    stale_acknowledgment_count = 0
    for entry in entries:
        level = str(entry.get("escalation_level") or ESCALATION_NONE)
        counts[level] = counts.get(level, 0) + 1
        if entry.get("stale_acknowledgment"):
            stale_acknowledgment_count += 1

    acknowledgment_status = current_escalation.get("acknowledgment_status")
    if latest and latest.get("acknowledgment_status"):
        acknowledgment_status = latest.get("acknowledgment_status")

    return {
        "total_snapshots": len(entries),
        "urgent_count": counts.get(ESCALATION_URGENT, 0),
        "attention_count": counts.get(ESCALATION_ATTENTION, 0),
        "watch_count": counts.get(ESCALATION_WATCH, 0),
        "none_count": counts.get(ESCALATION_NONE, 0),
        "latest_level": (latest or {}).get("escalation_level") or ESCALATION_NONE,
        "latest_at": (latest or {}).get("created_at"),
        "first_urgent_at": min(urgent_times) if urgent_times else None,
        "last_urgent_at": max(urgent_times) if urgent_times else None,
        "longest_urgent_streak": _longest_streak(chronological, _is_urgent),
        "longest_attention_or_urgent_streak": _longest_streak(
            chronological, _is_attention_or_urgent
        ),
        "current_urgent_streak": _current_streak_from_newest(entries, _is_urgent),
        "current_attention_or_urgent_streak": _current_streak_from_newest(
            entries, _is_attention_or_urgent
        ),
        "acknowledgment_status": acknowledgment_status,
        "stale_acknowledgment_count": stale_acknowledgment_count,
        "verified_mrms": False,
        "local_metrics_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def compact_proof_bundle_diff_escalation_metrics(storage: LocalStorage) -> dict[str, Any]:
    metrics = build_proof_bundle_diff_escalation_metrics(storage)
    return {
        "available": metrics.get("total_snapshots", 0) > 0,
        **metrics,
    }


def build_proof_bundle_diff_escalation_metrics_payload(storage: LocalStorage) -> dict[str, Any]:
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_metrics_only": True,
        "does_not_clear_alerts": True,
        "metrics": compact_proof_bundle_diff_escalation_metrics(storage),
    }
