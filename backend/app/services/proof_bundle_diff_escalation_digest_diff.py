"""Digest export diff metadata and regeneration hints — local review only."""

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
from backend.app.services.proof_bundle_diff_escalation import (
    ESCALATION_ATTENTION,
    ESCALATION_NONE,
    ESCALATION_URGENT,
    ESCALATION_WATCH,
    build_proof_bundle_diff_escalation,
)
from backend.app.services.proof_bundle_diff_escalation_digest import (
    load_latest_escalation_digest_metadata,
)
from backend.app.services.proof_bundle_diff_escalation_digest_history import (
    load_digest_export_history,
    load_previous_digest_history_entry,
)
from backend.app.services.proof_bundle_diff_escalation_history import (
    load_latest_proof_bundle_diff_escalation_history,
)
from backend.app.services.proof_bundle_diff_escalation_metrics import (
    build_proof_bundle_diff_escalation_metrics,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.time_utils import parse_utc_iso

DIGEST_DIFF_LATEST_PATH = "dev/proof_bundle_diff_escalation_digest_diff_latest.json"
DIGEST_DIFF_HISTORY_PATH = "dev/proof_bundle_diff_escalation_digest_diff_history.json"
MAX_DIGEST_DIFF_HISTORY = 25

SUGGESTED_DIGEST_COMMAND = "make scheduled-proof-bundle-digest"

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
    return storage.normalize_path(DIGEST_DIFF_LATEST_PATH)


def _diff_history_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(DIGEST_DIFF_HISTORY_PATH)


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
        json.dumps(entries[:MAX_DIGEST_DIFF_HISTORY], indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _snapshot_from_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    metrics = metadata.get("metrics") or {}
    return {
        "created_at": metadata.get("generated_at"),
        "latest_escalation_level": metadata.get("latest_escalation_level"),
        "latest_diff_status": metadata.get("latest_diff_status"),
        "urgent_count": int(metadata.get("urgent_count", metrics.get("urgent_count", 0))),
        "attention_count": int(metadata.get("attention_count", metrics.get("attention_count", 0))),
        "stale_acknowledgment_count": int(
            metadata.get("stale_acknowledgment_count", metrics.get("stale_acknowledgment_count", 0))
        ),
        "current_attention_or_urgent_streak": int(
            metadata.get(
                "current_attention_or_urgent_streak",
                metrics.get("current_attention_or_urgent_streak", 0),
            )
        ),
    }


def _snapshot_from_history_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "created_at": entry.get("created_at"),
        "latest_escalation_level": entry.get("latest_escalation_level"),
        "latest_diff_status": entry.get("latest_diff_status"),
        "urgent_count": int(entry.get("urgent_count", 0)),
        "attention_count": int(entry.get("attention_count", 0)),
        "stale_acknowledgment_count": int(entry.get("stale_acknowledgment_count", 0)),
        "current_attention_or_urgent_streak": int(entry.get("current_attention_or_urgent_streak", 0)),
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


def _count_signal(baseline: int, current: int) -> int:
    if current > baseline:
        return -1
    if current < baseline:
        return 1
    return 0


def _escalation_level_signal(baseline: Optional[str], current: Optional[str]) -> int:
    base_rank = ESCALATION_LEVEL_RANK.get(str(baseline or ESCALATION_NONE), 0)
    cur_rank = ESCALATION_LEVEL_RANK.get(str(current or ESCALATION_NONE), 0)
    if cur_rank > base_rank:
        return -1
    if cur_rank < base_rank:
        return 1
    return 0


def _classify_overall_digest_diff(signals: list[int]) -> str:
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


def compare_digest_metadata(
    baseline: Optional[dict[str, Any]],
    current: dict[str, Any],
) -> dict[str, Any]:
    """Compare previous and current digest snapshots; return diff metadata."""
    if baseline is None:
        return {
            "checked_at": _utc_now(),
            "overall_digest_diff_status": DIFF_NO_BASELINE,
            "baseline_snapshot": None,
            "current_snapshot": _snapshot_from_metadata(current),
            "changes": {},
            "verified_mrms": False,
            "local_digest_only": True,
            "does_not_clear_alerts": True,
            "does_not_enable_production": True,
            "prototype": True,
        }

    base_snap = _snapshot_from_history_entry(baseline)
    cur_snap = _snapshot_from_metadata(current)
    changes = {
        "latest_escalation_level": {
            "baseline": base_snap.get("latest_escalation_level"),
            "current": cur_snap.get("latest_escalation_level"),
        },
        "latest_diff_status": {
            "baseline": base_snap.get("latest_diff_status"),
            "current": cur_snap.get("latest_diff_status"),
        },
        "urgent_count": {
            "baseline": base_snap.get("urgent_count"),
            "current": cur_snap.get("urgent_count"),
        },
        "attention_count": {
            "baseline": base_snap.get("attention_count"),
            "current": cur_snap.get("attention_count"),
        },
        "stale_acknowledgment_count": {
            "baseline": base_snap.get("stale_acknowledgment_count"),
            "current": cur_snap.get("stale_acknowledgment_count"),
        },
    }
    signals = [
        _escalation_level_signal(
            base_snap.get("latest_escalation_level"),
            cur_snap.get("latest_escalation_level"),
        ),
        _diff_status_signal(base_snap.get("latest_diff_status"), cur_snap.get("latest_diff_status")),
        _count_signal(int(base_snap.get("urgent_count", 0)), int(cur_snap.get("urgent_count", 0))),
        _count_signal(int(base_snap.get("attention_count", 0)), int(cur_snap.get("attention_count", 0))),
        _count_signal(
            int(base_snap.get("stale_acknowledgment_count", 0)),
            int(cur_snap.get("stale_acknowledgment_count", 0)),
        ),
    ]
    return {
        "checked_at": _utc_now(),
        "overall_digest_diff_status": _classify_overall_digest_diff(signals),
        "baseline_snapshot": base_snap,
        "current_snapshot": cur_snap,
        "changes": changes,
        "verified_mrms": False,
        "local_digest_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def record_digest_diff_metadata(
    storage: LocalStorage,
    current_metadata: dict[str, Any],
    *,
    baseline_history_entry: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Persist latest digest diff and append to bounded diff history."""
    baseline = baseline_history_entry
    if baseline is None:
        baseline = load_previous_digest_history_entry(storage)
    diff_record = compare_digest_metadata(baseline, current_metadata)
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


def load_latest_digest_diff_metadata(storage: LocalStorage) -> Optional[dict[str, Any]]:
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


def compact_digest_diff_summary(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_digest_diff_metadata(storage)
    history = _load_diff_history(storage)
    if latest is None:
        return {
            "available": False,
            "overall_digest_diff_status": None,
            "checked_at": None,
            "history_count": len(history),
            "verified_mrms": False,
            "local_digest_only": True,
            "does_not_clear_alerts": True,
            "does_not_enable_production": True,
            "prototype": True,
        }
    return {
        "available": True,
        "overall_digest_diff_status": latest.get("overall_digest_diff_status"),
        "checked_at": latest.get("checked_at"),
        "history_count": len(history),
        "changes": latest.get("changes"),
        "verified_mrms": False,
        "local_digest_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def _digest_older_than_escalation(
    digest_at: Optional[str],
    escalation_at: Optional[str],
) -> bool:
    if not digest_at or not escalation_at:
        return False
    try:
        return parse_utc_iso(digest_at) < parse_utc_iso(escalation_at)
    except ValueError:
        return False


def build_digest_regeneration_hint(storage: LocalStorage) -> dict[str, Any]:
    """Suggest when operator should regenerate digest/checklist (local review only)."""
    escalation = build_proof_bundle_diff_escalation(storage)
    metrics = build_proof_bundle_diff_escalation_metrics(storage)
    digest = load_latest_escalation_digest_metadata(storage)
    latest_escalation_snapshot = load_latest_proof_bundle_diff_escalation_history(storage)
    latest_diff = load_latest_digest_diff_metadata(storage)

    escalation_level = escalation.get("escalation_level", ESCALATION_NONE)
    streak = int(metrics.get("current_attention_or_urgent_streak", 0))
    digest_at = (digest or {}).get("generated_at")
    escalation_at = (latest_escalation_snapshot or {}).get("created_at")
    diff_status = (latest_diff or {}).get("overall_digest_diff_status")

    recommended = False
    reason: Optional[str] = None

    if escalation_level == ESCALATION_URGENT and digest is None:
        recommended = True
        reason = "urgent_escalation_and_digest_missing"
    elif digest is None and streak >= 2:
        recommended = True
        reason = "attention_streak_and_digest_missing"
    elif digest is not None and _digest_older_than_escalation(digest_at, escalation_at):
        recommended = True
        reason = "digest_older_than_latest_escalation_snapshot"
    elif streak >= 2 and _digest_older_than_escalation(digest_at, escalation_at):
        recommended = True
        reason = "attention_streak_and_digest_stale"
    elif diff_status in (DIFF_WORSENED, DIFF_MIXED):
        recommended = True
        reason = f"digest_diff_{diff_status}"

    return {
        "digest_regeneration_recommended": recommended,
        "reason": reason,
        "suggested_command": SUGGESTED_DIGEST_COMMAND if recommended else None,
        "latest_escalation_level": escalation_level,
        "current_attention_or_urgent_streak": streak,
        "latest_digest_at": digest_at,
        "latest_escalation_snapshot_at": escalation_at,
        "latest_digest_diff_status": diff_status,
        "verified_mrms": False,
        "local_digest_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def build_digest_diff_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_digest_diff_metadata(storage)
    history = _load_diff_history(storage)[:MAX_DIGEST_DIFF_HISTORY]
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_digest_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "latest": latest,
        "count": len(history),
        "max_entries": MAX_DIGEST_DIFF_HISTORY,
        "entries": history,
        "compact": compact_digest_diff_summary(storage),
        "regeneration_hint": build_digest_regeneration_hint(storage),
    }
