"""Compare local MRMS proof review sessions — does NOT verify MRMS."""

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
    PROOF_RANK,
)
from backend.app.services.proof_bundle_diff_escalation import (
    ESCALATION_ATTENTION,
    ESCALATION_NONE,
    ESCALATION_URGENT,
    ESCALATION_WATCH,
)
from backend.app.services.storage import LocalStorage

COMPARISON_LATEST_PATH = "dev/mrms_review_session_comparison_latest.json"
COMPARISON_HISTORY_PATH = "dev/mrms_review_session_comparison_history.json"
MAX_COMPARISON_HISTORY = 25

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


def _comparison_latest_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(COMPARISON_LATEST_PATH)


def _comparison_history_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(COMPARISON_HISTORY_PATH)


def _load_comparison_history(storage: LocalStorage) -> list[dict[str, Any]]:
    abs_path = storage.absolute_path(_comparison_history_repo_path(storage))
    if not abs_path.is_file():
        return []
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save_comparison_history(storage: LocalStorage, entries: list[dict[str, Any]]) -> None:
    repo_path = _comparison_history_repo_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(entries[:MAX_COMPARISON_HISTORY], indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _session_operator(session: dict[str, Any]) -> Optional[str]:
    return session.get("operator_name") or session.get("operator_initials")


def _session_snapshot(session: dict[str, Any]) -> dict[str, Any]:
    reviewed = session.get("checklist_items_reviewed") or []
    not_reviewed = session.get("checklist_items_not_reviewed") or []
    return {
        "session_id": session.get("session_id"),
        "created_at": session.get("created_at"),
        "operator": _session_operator(session),
        "escalation_level": session.get("latest_escalation_level"),
        "open_attention_count": int(session.get("open_attention_count", 0)),
        "checklist_reviewed_count": len(reviewed),
        "checklist_not_reviewed_count": len(not_reviewed),
        "proof_bundle_diff_status": session.get("latest_proof_bundle_diff_status"),
        "proof_report_status": session.get("latest_proof_report_status"),
        "acknowledgment_id": session.get("latest_acknowledgment_id"),
        "acknowledgment_at": session.get("latest_acknowledgment_at"),
        "digest_path": session.get("latest_digest_path"),
        "handoff_path": session.get("latest_operator_handoff_path"),
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


def _count_higher_is_better_signal(baseline: int, current: int) -> int:
    if current > baseline:
        return 1
    if current < baseline:
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


def _proof_report_signal(baseline: Optional[str], current: Optional[str]) -> int:
    base_rank = PROOF_RANK.get(str(baseline or "not_started"), 0)
    cur_rank = PROOF_RANK.get(str(current or "not_started"), 0)
    if cur_rank > base_rank:
        return 1
    if cur_rank < base_rank:
        return -1
    return 0


def _acknowledgment_signal(baseline: dict[str, Any], current: dict[str, Any]) -> int:
    base_id = baseline.get("acknowledgment_id")
    cur_id = current.get("acknowledgment_id")
    if base_id == cur_id:
        return 0
    if base_id is None and cur_id is not None:
        return 1
    if base_id is not None and cur_id is None:
        return -1
    if base_id != cur_id:
        return 1
    return 0


def _classify_overall_review_diff(signals: list[int]) -> str:
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


def compare_review_sessions(
    baseline: Optional[dict[str, Any]],
    latest: dict[str, Any],
) -> dict[str, Any]:
    """Compare baseline and latest review session snapshots."""
    base_snap = _session_snapshot(baseline) if baseline else None
    latest_snap = _session_snapshot(latest)
    safety = {
        "verified_mrms": False,
        "local_comparison_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }

    if baseline is None:
        return {
            "compared_at": _utc_now(),
            "latest_session_id": latest_snap.get("session_id"),
            "baseline_session_id": None,
            "latest_created_at": latest_snap.get("created_at"),
            "baseline_created_at": None,
            "latest_operator": latest_snap.get("operator"),
            "baseline_operator": None,
            "escalation_level_change": None,
            "open_attention_count_change": None,
            "checklist_reviewed_count_change": None,
            "checklist_not_reviewed_count_change": None,
            "proof_bundle_diff_status_change": None,
            "proof_report_status_change": None,
            "acknowledgment_status_change": None,
            "digest_path_changed": False,
            "handoff_path_changed": False,
            "overall_review_diff_status": DIFF_NO_BASELINE,
            "improvements": [],
            "regressions": [],
            "unchanged_items": [],
            **safety,
        }

    assert base_snap is not None
    escalation_level_change = {
        "baseline": base_snap.get("escalation_level"),
        "latest": latest_snap.get("escalation_level"),
    }
    open_attention_count_change = {
        "baseline": base_snap.get("open_attention_count"),
        "latest": latest_snap.get("open_attention_count"),
    }
    checklist_reviewed_count_change = {
        "baseline": base_snap.get("checklist_reviewed_count"),
        "latest": latest_snap.get("checklist_reviewed_count"),
    }
    checklist_not_reviewed_count_change = {
        "baseline": base_snap.get("checklist_not_reviewed_count"),
        "latest": latest_snap.get("checklist_not_reviewed_count"),
    }
    proof_bundle_diff_status_change = {
        "baseline": base_snap.get("proof_bundle_diff_status"),
        "latest": latest_snap.get("proof_bundle_diff_status"),
    }
    proof_report_status_change = {
        "baseline": base_snap.get("proof_report_status"),
        "latest": latest_snap.get("proof_report_status"),
    }
    acknowledgment_status_change = {
        "baseline_acknowledgment_id": base_snap.get("acknowledgment_id"),
        "latest_acknowledgment_id": latest_snap.get("acknowledgment_id"),
        "baseline_acknowledgment_at": base_snap.get("acknowledgment_at"),
        "latest_acknowledgment_at": latest_snap.get("acknowledgment_at"),
    }
    digest_path_changed = base_snap.get("digest_path") != latest_snap.get("digest_path")
    handoff_path_changed = base_snap.get("handoff_path") != latest_snap.get("handoff_path")

    improvements: list[str] = []
    regressions: list[str] = []
    unchanged_items: list[str] = []

    _append_signal_result(
        "escalation_level",
        _escalation_level_signal(
            base_snap.get("escalation_level"),
            latest_snap.get("escalation_level"),
        ),
        improvements,
        regressions,
        unchanged_items,
    )
    _append_signal_result(
        "open_attention_count",
        _count_lower_is_better_signal(
            int(base_snap.get("open_attention_count", 0)),
            int(latest_snap.get("open_attention_count", 0)),
        ),
        improvements,
        regressions,
        unchanged_items,
    )
    _append_signal_result(
        "checklist_reviewed_count",
        _count_higher_is_better_signal(
            int(base_snap.get("checklist_reviewed_count", 0)),
            int(latest_snap.get("checklist_reviewed_count", 0)),
        ),
        improvements,
        regressions,
        unchanged_items,
    )
    _append_signal_result(
        "checklist_not_reviewed_count",
        _count_lower_is_better_signal(
            int(base_snap.get("checklist_not_reviewed_count", 0)),
            int(latest_snap.get("checklist_not_reviewed_count", 0)),
        ),
        improvements,
        regressions,
        unchanged_items,
    )
    _append_signal_result(
        "proof_bundle_diff_status",
        _diff_status_signal(
            base_snap.get("proof_bundle_diff_status"),
            latest_snap.get("proof_bundle_diff_status"),
        ),
        improvements,
        regressions,
        unchanged_items,
    )
    _append_signal_result(
        "proof_report_status",
        _proof_report_signal(
            base_snap.get("proof_report_status"),
            latest_snap.get("proof_report_status"),
        ),
        improvements,
        regressions,
        unchanged_items,
    )
    _append_signal_result(
        "acknowledgment_status",
        _acknowledgment_signal(base_snap, latest_snap),
        improvements,
        regressions,
        unchanged_items,
    )

    if digest_path_changed:
        unchanged_items.append("digest_path_changed")
    else:
        unchanged_items.append("digest_path")
    if handoff_path_changed:
        unchanged_items.append("handoff_path_changed")
    else:
        unchanged_items.append("handoff_path")

    signals = [
        _escalation_level_signal(
            base_snap.get("escalation_level"),
            latest_snap.get("escalation_level"),
        ),
        _count_lower_is_better_signal(
            int(base_snap.get("open_attention_count", 0)),
            int(latest_snap.get("open_attention_count", 0)),
        ),
        _count_higher_is_better_signal(
            int(base_snap.get("checklist_reviewed_count", 0)),
            int(latest_snap.get("checklist_reviewed_count", 0)),
        ),
        _count_lower_is_better_signal(
            int(base_snap.get("checklist_not_reviewed_count", 0)),
            int(latest_snap.get("checklist_not_reviewed_count", 0)),
        ),
        _diff_status_signal(
            base_snap.get("proof_bundle_diff_status"),
            latest_snap.get("proof_bundle_diff_status"),
        ),
        _proof_report_signal(
            base_snap.get("proof_report_status"),
            latest_snap.get("proof_report_status"),
        ),
        _acknowledgment_signal(base_snap, latest_snap),
    ]

    return {
        "compared_at": _utc_now(),
        "latest_session_id": latest_snap.get("session_id"),
        "baseline_session_id": base_snap.get("session_id"),
        "latest_created_at": latest_snap.get("created_at"),
        "baseline_created_at": base_snap.get("created_at"),
        "latest_operator": latest_snap.get("operator"),
        "baseline_operator": base_snap.get("operator"),
        "escalation_level_change": escalation_level_change,
        "open_attention_count_change": open_attention_count_change,
        "checklist_reviewed_count_change": checklist_reviewed_count_change,
        "checklist_not_reviewed_count_change": checklist_not_reviewed_count_change,
        "proof_bundle_diff_status_change": proof_bundle_diff_status_change,
        "proof_report_status_change": proof_report_status_change,
        "acknowledgment_status_change": acknowledgment_status_change,
        "digest_path_changed": digest_path_changed,
        "handoff_path_changed": handoff_path_changed,
        "overall_review_diff_status": _classify_overall_review_diff(signals),
        "improvements": improvements,
        "regressions": regressions,
        "unchanged_items": unchanged_items,
        **safety,
    }


def record_review_session_comparison(
    storage: LocalStorage,
    *,
    baseline_session: Optional[dict[str, Any]] = None,
    latest_session: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Compare latest vs previous review session and persist bounded history."""
    from backend.app.services.mrms_review_session import load_review_sessions

    entries = load_review_sessions(storage)
    latest = latest_session if latest_session is not None else (entries[0] if entries else None)
    if latest is None:
        comparison = {
            "compared_at": _utc_now(),
            "latest_session_id": None,
            "baseline_session_id": None,
            "latest_created_at": None,
            "baseline_created_at": None,
            "latest_operator": None,
            "baseline_operator": None,
            "escalation_level_change": None,
            "open_attention_count_change": None,
            "checklist_reviewed_count_change": None,
            "checklist_not_reviewed_count_change": None,
            "proof_bundle_diff_status_change": None,
            "proof_report_status_change": None,
            "acknowledgment_status_change": None,
            "digest_path_changed": False,
            "handoff_path_changed": False,
            "overall_review_diff_status": DIFF_UNKNOWN,
            "improvements": [],
            "regressions": [],
            "unchanged_items": [],
            "verified_mrms": False,
            "local_comparison_only": True,
            "does_not_clear_alerts": True,
            "does_not_enable_production": True,
            "prototype": True,
        }
    else:
        baseline = baseline_session
        if baseline is None and len(entries) > 1:
            baseline = entries[1]
        comparison = compare_review_sessions(baseline, latest)

    latest_repo = _comparison_latest_repo_path(storage)
    storage.ensure_directories(latest_repo.rsplit("/", 1)[0])
    storage.absolute_path(latest_repo).write_text(
        json.dumps(comparison, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    history = _load_comparison_history(storage)
    history.insert(0, comparison)
    _save_comparison_history(storage, history)
    return comparison


def load_latest_review_session_comparison(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_comparison_latest_repo_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def compact_review_session_comparison_summary(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_review_session_comparison(storage)
    history = _load_comparison_history(storage)
    empty = {
        "available": False,
        "overall_review_diff_status": None,
        "compared_at": None,
        "latest_created_at": None,
        "baseline_created_at": None,
        "latest_operator": None,
        "baseline_operator": None,
        "open_attention_count_change": None,
        "checklist_reviewed_count_change": None,
        "checklist_not_reviewed_count_change": None,
        "improvements": [],
        "regressions": [],
        "history_count": len(history),
        "verified_mrms": False,
        "local_comparison_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }
    if latest is None:
        return empty
    return {
        "available": True,
        "overall_review_diff_status": latest.get("overall_review_diff_status"),
        "compared_at": latest.get("compared_at"),
        "latest_created_at": latest.get("latest_created_at"),
        "baseline_created_at": latest.get("baseline_created_at"),
        "latest_operator": latest.get("latest_operator"),
        "baseline_operator": latest.get("baseline_operator"),
        "open_attention_count_change": latest.get("open_attention_count_change"),
        "checklist_reviewed_count_change": latest.get("checklist_reviewed_count_change"),
        "checklist_not_reviewed_count_change": latest.get("checklist_not_reviewed_count_change"),
        "improvements": latest.get("improvements") or [],
        "regressions": latest.get("regressions") or [],
        "history_count": len(history),
        "verified_mrms": False,
        "local_comparison_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def build_review_session_comparison_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_review_session_comparison(storage)
    history = _load_comparison_history(storage)[:MAX_COMPARISON_HISTORY]
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_comparison_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "latest": latest,
        "count": len(history),
        "max_entries": MAX_COMPARISON_HISTORY,
        "entries": history,
        "compact": compact_review_session_comparison_summary(storage),
    }
