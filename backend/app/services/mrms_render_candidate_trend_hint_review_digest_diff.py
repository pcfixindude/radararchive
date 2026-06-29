"""Local candidate trend-hint review digest diff — does NOT clear alerts or verify MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_IMPROVED,
    DIFF_MIXED,
    DIFF_NO_BASELINE,
    DIFF_UNCHANGED,
    DIFF_UNKNOWN,
    DIFF_WORSENED,
)
from backend.app.services.mrms_render_candidate_trend_hint_ack_status import (
    ROLLUP_BLOCKED,
    ROLLUP_CURRENT,
    ROLLUP_MISSING,
    ROLLUP_NEEDS_ACKNOWLEDGMENT,
    ROLLUP_NOT_NEEDED,
    ROLLUP_STALE,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest import (
    DIGEST_BLOCKED,
    DIGEST_CURRENT,
    DIGEST_MISSING,
    DIGEST_NEEDS_ATTENTION,
    DIGEST_STABLE,
    SUGGESTED_COMMAND as SUGGESTED_DIGEST_COMMAND,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest_history import (
    COVERAGE_IMPROVED,
    COVERAGE_MIXED,
    COVERAGE_WORSENED,
    load_trend_hint_review_digest_history,
)
from backend.app.services.storage import LocalStorage

DIFF_LATEST_JSON = "dev/mrms_render_candidate_trend_hint_review_digest_diff_latest.json"
DIFF_HISTORY_JSON = "dev/mrms_render_candidate_trend_hint_review_digest_diff_history.json"

MAX_DIFF_HISTORY = 25
SUGGESTED_COMMAND = "make mrms-render-candidate-trend-hint-review-digest-diff"

NEXT_PHASE_RECOMMENDATION = (
    "Phase 88 — gated real MRMS render candidate preflight attempt "
    "(only when review chain and visual evidence are ready; does not verify MRMS or enable production)"
)

DIGEST_STATUS_RANK = {
    DIGEST_BLOCKED: 0,
    DIGEST_MISSING: 1,
    DIGEST_NEEDS_ATTENTION: 2,
    DIGEST_STABLE: 3,
    DIGEST_CURRENT: 4,
}

ROLLUP_STATUS_RANK = {
    ROLLUP_BLOCKED: 0,
    ROLLUP_MISSING: 1,
    ROLLUP_NEEDS_ACKNOWLEDGMENT: 2,
    ROLLUP_STALE: 3,
    ROLLUP_NOT_NEEDED: 4,
    ROLLUP_CURRENT: 5,
}

COVERAGE_CHANGE_WORSE = frozenset({COVERAGE_WORSENED, COVERAGE_MIXED})


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_digest_diff_only": True,
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


def _diff_latest_path(storage: LocalStorage) -> str:
    return storage.normalize_path(DIFF_LATEST_JSON)


def _diff_history_path(storage: LocalStorage) -> str:
    return storage.normalize_path(DIFF_HISTORY_JSON)


def _load_diff_history(storage: LocalStorage) -> list[dict[str, Any]]:
    abs_path = storage.absolute_path(_diff_history_path(storage))
    if not abs_path.is_file():
        return []
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save_diff_history(storage: LocalStorage, entries: list[dict[str, Any]]) -> None:
    repo_path = _diff_history_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(entries[:MAX_DIFF_HISTORY], indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _snapshot_from_history_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "recorded_at": entry.get("recorded_at"),
        "digest_status": entry.get("digest_status"),
        "rollup_status": entry.get("rollup_status"),
        "acknowledgment_status": entry.get("acknowledgment_status"),
        "history_count": entry.get("history_count"),
        "coverage_change": entry.get("coverage_change"),
    }


def _rank_signal(
    baseline: Optional[str],
    current: Optional[str],
    *,
    ranks: dict[str, int],
) -> int:
    base_rank = ranks.get(str(baseline or ""), 0)
    cur_rank = ranks.get(str(current or ""), 0)
    if cur_rank > base_rank:
        return 1
    if cur_rank < base_rank:
        return -1
    return 0


def _coverage_change_signal(baseline: Optional[str], current: Optional[str]) -> int:
    if baseline is None or current is None:
        return 0
    if baseline == current:
        return 0
    base_worse = baseline in COVERAGE_CHANGE_WORSE
    cur_worse = current in COVERAGE_CHANGE_WORSE
    if cur_worse and not base_worse:
        return -1
    if base_worse and not cur_worse:
        return 1
    if current == COVERAGE_IMPROVED and baseline != COVERAGE_IMPROVED:
        return 1
    if baseline == COVERAGE_IMPROVED and current != COVERAGE_IMPROVED:
        return -1
    return 0


def _classify_overall_diff(signals: list[int]) -> str:
    if not signals:
        return DIFF_UNKNOWN
    positives = sum(1 for value in signals if value > 0)
    negatives = sum(1 for value in signals if value < 0)
    if positives == 0 and negatives == 0:
        return DIFF_UNCHANGED
    if positives > 0 and negatives == 0:
        return DIFF_IMPROVED
    if negatives > 0 and positives == 0:
        return DIFF_WORSENED
    return DIFF_MIXED


def compare_trend_hint_review_digest_entries(
    baseline: Optional[dict[str, Any]],
    current: dict[str, Any],
) -> dict[str, Any]:
    if baseline is None:
        return {
            "checked_at": _utc_now(),
            "diff_status": DIFF_NO_BASELINE,
            "baseline_snapshot": None,
            "current_snapshot": _snapshot_from_history_entry(current),
            "changes": {},
            "suggested_command": SUGGESTED_DIGEST_COMMAND,
            "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
            **_safety_fields(),
        }

    base_snap = _snapshot_from_history_entry(baseline)
    cur_snap = _snapshot_from_history_entry(current)
    changes = {
        "digest_status": {
            "baseline": base_snap.get("digest_status"),
            "current": cur_snap.get("digest_status"),
        },
        "rollup_status": {
            "baseline": base_snap.get("rollup_status"),
            "current": cur_snap.get("rollup_status"),
        },
        "acknowledgment_status": {
            "baseline": base_snap.get("acknowledgment_status"),
            "current": cur_snap.get("acknowledgment_status"),
        },
        "history_count": {
            "baseline": base_snap.get("history_count"),
            "current": cur_snap.get("history_count"),
        },
        "coverage_change": {
            "baseline": base_snap.get("coverage_change"),
            "current": cur_snap.get("coverage_change"),
        },
    }
    signals = [
        _rank_signal(
            base_snap.get("digest_status"),
            cur_snap.get("digest_status"),
            ranks=DIGEST_STATUS_RANK,
        ),
        _rank_signal(
            base_snap.get("rollup_status"),
            cur_snap.get("rollup_status"),
            ranks=ROLLUP_STATUS_RANK,
        ),
        _coverage_change_signal(base_snap.get("coverage_change"), cur_snap.get("coverage_change")),
    ]
    return {
        "checked_at": _utc_now(),
        "diff_status": _classify_overall_diff(signals),
        "baseline_snapshot": base_snap,
        "current_snapshot": cur_snap,
        "changes": changes,
        "suggested_command": SUGGESTED_DIGEST_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def record_trend_hint_review_digest_diff(
    storage: LocalStorage,
    *,
    current_entry: dict[str, Any],
    baseline_entry: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    diff_record = compare_trend_hint_review_digest_entries(baseline_entry, current_entry)
    latest_path = _diff_latest_path(storage)
    storage.ensure_directories(latest_path.rsplit("/", 1)[0])
    storage.absolute_path(latest_path).write_text(
        json.dumps(diff_record, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    history = _load_diff_history(storage)
    history.insert(0, diff_record)
    _save_diff_history(storage, history)
    return diff_record


def refresh_trend_hint_review_digest_diff(storage: LocalStorage) -> Optional[dict[str, Any]]:
    history = load_trend_hint_review_digest_history(storage, limit=2)
    if not history:
        return None
    current = history[0]
    baseline = history[1] if len(history) > 1 else None
    return record_trend_hint_review_digest_diff(
        storage,
        current_entry=current,
        baseline_entry=baseline,
    )


def load_latest_trend_hint_review_digest_diff(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_diff_latest_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def compact_trend_hint_review_digest_diff(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_trend_hint_review_digest_diff(storage)
    history = _load_diff_history(storage)
    if latest is None:
        return {
            "available": False,
            "diff_status": None,
            "checked_at": None,
            "history_count": len(history),
            "suggested_command": SUGGESTED_COMMAND,
            "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
            **_safety_fields(),
        }
    return {
        "available": True,
        "diff_status": latest.get("diff_status"),
        "checked_at": latest.get("checked_at"),
        "history_count": len(history),
        "changes": latest.get("changes"),
        "suggested_command": SUGGESTED_COMMAND,
        "next_phase_recommendation": latest.get("next_phase_recommendation") or NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_trend_hint_review_digest_diff_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_trend_hint_review_digest_diff(storage)
    history = _load_diff_history(storage)[:MAX_DIFF_HISTORY]
    return {
        **_safety_fields(),
        "latest": latest,
        "count": len(history),
        "max_entries": MAX_DIFF_HISTORY,
        "entries": history,
        "compact": compact_trend_hint_review_digest_diff(storage),
    }
