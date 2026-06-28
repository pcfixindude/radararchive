"""Review session export diff metadata — local review only."""

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
from backend.app.services.mrms_review_session_export import (
    EXPORT_HISTORY_PATH,
    _load_export_history,
)
from backend.app.services.proof_bundle_diff_escalation import (
    ESCALATION_ATTENTION,
    ESCALATION_NONE,
    ESCALATION_URGENT,
    ESCALATION_WATCH,
)
from backend.app.services.storage import LocalStorage

EXPORT_DIFF_LATEST_PATH = "dev/mrms_review_session_export_diff_latest.json"
EXPORT_DIFF_HISTORY_PATH = "dev/mrms_review_session_export_diff_history.json"
MAX_EXPORT_DIFF_HISTORY = 25

ESCALATION_LEVEL_RANK = {
    ESCALATION_NONE: 0,
    ESCALATION_WATCH: 1,
    ESCALATION_ATTENTION: 2,
    ESCALATION_URGENT: 3,
}

DIFF_STATUS_WORSE = frozenset({DIFF_WORSENED, DIFF_MIXED})


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _diff_latest_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(EXPORT_DIFF_LATEST_PATH)


def _diff_history_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(EXPORT_DIFF_HISTORY_PATH)


def _load_diff_history(storage: LocalStorage) -> list[dict[str, Any]]:
    abs_path = storage.absolute_path(_diff_history_repo_path(storage))
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
    repo_path = _diff_history_repo_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(entries[:MAX_EXPORT_DIFF_HISTORY], indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _snapshot_from_export(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "created_at": entry.get("created_at"),
        "session_id": entry.get("session_id"),
        "comparison_status": entry.get("comparison_status"),
        "open_attention_count": int(entry.get("open_attention_count", 0)),
        "escalation_level": entry.get("escalation_level"),
        "digest_regeneration_recommended": bool(entry.get("digest_regeneration_recommended")),
        "proof_bundle_diff_status": entry.get("proof_bundle_diff_status"),
        "acknowledgment_id": entry.get("acknowledgment_id"),
        "export_path": entry.get("export_path"),
    }


def _diff_status_signal(baseline: Optional[str], current: Optional[str]) -> int:
    if baseline is None or current is None:
        return 0
    if baseline == current:
        return 0
    base_worse = baseline in DIFF_STATUS_WORSE
    cur_worse = current in DIFF_STATUS_WORSE
    if cur_worse and not base_worse:
        return -1
    if base_worse and not cur_worse:
        return 1
    if current == DIFF_IMPROVED and baseline != DIFF_IMPROVED:
        return 1
    if baseline == DIFF_IMPROVED and current != DIFF_IMPROVED:
        return -1
    return 0


def _count_lower_is_better_signal(baseline: int, current: int) -> int:
    if current < baseline:
        return 1
    if current > baseline:
        return -1
    return 0


def _escalation_level_signal(baseline: Optional[str], current: Optional[str]) -> int:
    base_rank = ESCALATION_LEVEL_RANK.get(str(baseline or ESCALATION_NONE), 0)
    cur_rank = ESCALATION_LEVEL_RANK.get(str(current or ESCALATION_NONE), 0)
    if cur_rank > base_rank:
        return -1
    if cur_rank < base_rank:
        return 1
    return 0


def _digest_regeneration_signal(baseline: bool, current: bool) -> int:
    if baseline == current:
        return 0
    if baseline and not current:
        return 1
    if not baseline and current:
        return -1
    return 0


def _acknowledgment_signal(baseline: Optional[str], current: Optional[str]) -> int:
    if baseline == current:
        return 0
    if baseline is None and current is not None:
        return 1
    if baseline is not None and current is None:
        return -1
    if baseline != current:
        return 1
    return 0


def _classify_overall_export_diff(signals: list[int]) -> str:
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


def _append_signal_result(
    label: str,
    signal: int,
    improvements: list[str],
    regressions: list[str],
    unchanged_items: list[str],
) -> None:
    if signal > 0:
        improvements.append(label)
    elif signal < 0:
        regressions.append(label)
    else:
        unchanged_items.append(label)


def compare_export_metadata(
    baseline: Optional[dict[str, Any]],
    current: dict[str, Any],
) -> dict[str, Any]:
    """Compare previous and latest review session export snapshots."""
    safety = {
        "verified_mrms": False,
        "local_export_diff_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }
    cur_snap = _snapshot_from_export(current)
    if baseline is None:
        return {
            "compared_at": _utc_now(),
            "latest_export_created_at": cur_snap.get("created_at"),
            "baseline_export_created_at": None,
            "latest_session_id": cur_snap.get("session_id"),
            "baseline_session_id": None,
            "session_changed": False,
            "comparison_status_change": None,
            "open_attention_count_change": None,
            "escalation_level_change": None,
            "digest_regeneration_recommended_change": None,
            "proof_bundle_diff_status_change": None,
            "acknowledgment_status_change": None,
            "export_path_changed": False,
            "overall_export_diff_status": DIFF_NO_BASELINE,
            "improvements": [],
            "regressions": [],
            "unchanged_items": [],
            **safety,
        }

    base_snap = _snapshot_from_export(baseline)
    session_changed = base_snap.get("session_id") != cur_snap.get("session_id")
    comparison_status_change = {
        "baseline": base_snap.get("comparison_status"),
        "latest": cur_snap.get("comparison_status"),
    }
    open_attention_count_change = {
        "baseline": base_snap.get("open_attention_count"),
        "latest": cur_snap.get("open_attention_count"),
    }
    escalation_level_change = {
        "baseline": base_snap.get("escalation_level"),
        "latest": cur_snap.get("escalation_level"),
    }
    digest_regeneration_recommended_change = {
        "baseline": base_snap.get("digest_regeneration_recommended"),
        "latest": cur_snap.get("digest_regeneration_recommended"),
    }
    proof_bundle_diff_status_change = {
        "baseline": base_snap.get("proof_bundle_diff_status"),
        "latest": cur_snap.get("proof_bundle_diff_status"),
    }
    acknowledgment_status_change = {
        "baseline_acknowledgment_id": base_snap.get("acknowledgment_id"),
        "latest_acknowledgment_id": cur_snap.get("acknowledgment_id"),
    }
    export_path_changed = base_snap.get("export_path") != cur_snap.get("export_path")

    improvements: list[str] = []
    regressions: list[str] = []
    unchanged_items: list[str] = []

    if session_changed:
        unchanged_items.append("session_changed")
    else:
        unchanged_items.append("session_id")

    _append_signal_result(
        "open_attention_count",
        _count_lower_is_better_signal(
            int(base_snap.get("open_attention_count", 0)),
            int(cur_snap.get("open_attention_count", 0)),
        ),
        improvements,
        regressions,
        unchanged_items,
    )
    _append_signal_result(
        "comparison_status",
        _diff_status_signal(
            base_snap.get("comparison_status"),
            cur_snap.get("comparison_status"),
        ),
        improvements,
        regressions,
        unchanged_items,
    )
    _append_signal_result(
        "escalation_level",
        _escalation_level_signal(
            base_snap.get("escalation_level"),
            cur_snap.get("escalation_level"),
        ),
        improvements,
        regressions,
        unchanged_items,
    )
    _append_signal_result(
        "digest_regeneration_recommended",
        _digest_regeneration_signal(
            bool(base_snap.get("digest_regeneration_recommended")),
            bool(cur_snap.get("digest_regeneration_recommended")),
        ),
        improvements,
        regressions,
        unchanged_items,
    )
    _append_signal_result(
        "proof_bundle_diff_status",
        _diff_status_signal(
            base_snap.get("proof_bundle_diff_status"),
            cur_snap.get("proof_bundle_diff_status"),
        ),
        improvements,
        regressions,
        unchanged_items,
    )
    _append_signal_result(
        "acknowledgment_status",
        _acknowledgment_signal(
            base_snap.get("acknowledgment_id"),
            cur_snap.get("acknowledgment_id"),
        ),
        improvements,
        regressions,
        unchanged_items,
    )

    if export_path_changed:
        unchanged_items.append("export_path_changed")
    else:
        unchanged_items.append("export_path")

    signals = [
        _count_lower_is_better_signal(
            int(base_snap.get("open_attention_count", 0)),
            int(cur_snap.get("open_attention_count", 0)),
        ),
        _diff_status_signal(
            base_snap.get("comparison_status"),
            cur_snap.get("comparison_status"),
        ),
        _escalation_level_signal(
            base_snap.get("escalation_level"),
            cur_snap.get("escalation_level"),
        ),
        _digest_regeneration_signal(
            bool(base_snap.get("digest_regeneration_recommended")),
            bool(cur_snap.get("digest_regeneration_recommended")),
        ),
        _diff_status_signal(
            base_snap.get("proof_bundle_diff_status"),
            cur_snap.get("proof_bundle_diff_status"),
        ),
        _acknowledgment_signal(
            base_snap.get("acknowledgment_id"),
            cur_snap.get("acknowledgment_id"),
        ),
    ]

    return {
        "compared_at": _utc_now(),
        "latest_export_created_at": cur_snap.get("created_at"),
        "baseline_export_created_at": base_snap.get("created_at"),
        "latest_session_id": cur_snap.get("session_id"),
        "baseline_session_id": base_snap.get("session_id"),
        "session_changed": session_changed,
        "comparison_status_change": comparison_status_change,
        "open_attention_count_change": open_attention_count_change,
        "escalation_level_change": escalation_level_change,
        "digest_regeneration_recommended_change": digest_regeneration_recommended_change,
        "proof_bundle_diff_status_change": proof_bundle_diff_status_change,
        "acknowledgment_status_change": acknowledgment_status_change,
        "export_path_changed": export_path_changed,
        "overall_export_diff_status": _classify_overall_export_diff(signals),
        "improvements": improvements,
        "regressions": regressions,
        "unchanged_items": unchanged_items,
        **safety,
    }


def record_export_diff_metadata(
    storage: LocalStorage,
    current_metadata: dict[str, Any],
    *,
    baseline_history_entry: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Persist latest export diff and append to bounded diff history."""
    baseline = baseline_history_entry
    if baseline is None:
        history = _load_export_history(storage)
        baseline = history[1] if len(history) > 1 else None
    diff_record = compare_export_metadata(baseline, current_metadata)
    latest_repo = _diff_latest_repo_path(storage)
    storage.ensure_directories(latest_repo.rsplit("/", 1)[0])
    storage.absolute_path(latest_repo).write_text(
        json.dumps(diff_record, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    history = _load_diff_history(storage)
    history.insert(0, diff_record)
    _save_diff_history(storage, history)
    return diff_record


def load_latest_export_diff_metadata(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_diff_latest_repo_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def compact_review_session_export_diff_summary(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_export_diff_metadata(storage)
    history = _load_diff_history(storage)
    empty = {
        "available": False,
        "overall_export_diff_status": None,
        "compared_at": None,
        "latest_export_created_at": None,
        "baseline_export_created_at": None,
        "session_changed": False,
        "open_attention_count_change": None,
        "improvements": [],
        "regressions": [],
        "history_count": len(history),
        "verified_mrms": False,
        "local_export_diff_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }
    if latest is None:
        return empty
    return {
        "available": True,
        "overall_export_diff_status": latest.get("overall_export_diff_status"),
        "compared_at": latest.get("compared_at"),
        "latest_export_created_at": latest.get("latest_export_created_at"),
        "baseline_export_created_at": latest.get("baseline_export_created_at"),
        "session_changed": bool(latest.get("session_changed")),
        "open_attention_count_change": latest.get("open_attention_count_change"),
        "improvements": latest.get("improvements") or [],
        "regressions": latest.get("regressions") or [],
        "history_count": len(history),
        "verified_mrms": False,
        "local_export_diff_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def build_review_session_export_diff_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_export_diff_metadata(storage)
    history = _load_diff_history(storage)[:MAX_EXPORT_DIFF_HISTORY]
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_export_diff_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "latest": latest,
        "count": len(history),
        "max_entries": MAX_EXPORT_DIFF_HISTORY,
        "entries": history,
        "compact": compact_review_session_export_diff_summary(storage),
    }
