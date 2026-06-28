"""Bounded proof bundle diff escalation history — local monitoring only."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.services.proof_bundle_diff_escalation import (
    ESCALATION_NONE,
    build_proof_bundle_diff_escalation,
)
from backend.app.services.storage import LocalStorage

ESCALATION_HISTORY_PATH = "dev/proof_bundle_diff_escalation_history.json"
MAX_ESCALATION_HISTORY = 25


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _history_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(ESCALATION_HISTORY_PATH)


def _load_entries(storage: LocalStorage) -> list[dict[str, Any]]:
    abs_path = storage.absolute_path(_history_repo_path(storage))
    if not abs_path.is_file():
        return []
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save_entries(storage: LocalStorage, entries: list[dict[str, Any]]) -> None:
    repo_path = _history_repo_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(entries[:MAX_ESCALATION_HISTORY], indent=2, sort_keys=True),
        encoding="utf-8",
    )


def build_escalation_snapshot(
    escalation: dict[str, Any],
    *,
    source: str,
    run_id: Optional[str] = None,
) -> dict[str, Any]:
    guidance_items = escalation.get("guidance_items") or []
    return {
        "created_at": _utc_now(),
        "escalation_level": escalation.get("escalation_level", ESCALATION_NONE),
        "reason": escalation.get("reason", ""),
        "latest_diff_status": escalation.get("latest_diff_status"),
        "current_attention_streak": int(escalation.get("current_attention_streak", 0)),
        "acknowledgment_status": escalation.get("acknowledgment_status", "none"),
        "stale_acknowledgment": bool(escalation.get("stale_acknowledgment")),
        "suggested_next_action": escalation.get("suggested_next_action", ""),
        "guidance_item_count": len(guidance_items),
        "source": source,
        "run_id": run_id,
        "verified_mrms": False,
        "local_history_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def _snapshot_fingerprint(entry: dict[str, Any]) -> tuple[Any, ...]:
    return (
        entry.get("escalation_level"),
        entry.get("latest_diff_status"),
        int(entry.get("current_attention_streak", 0)),
        entry.get("acknowledgment_status"),
        bool(entry.get("stale_acknowledgment")),
        entry.get("reason"),
    )


def _is_duplicate_of_latest(
    entries: list[dict[str, Any]],
    entry: dict[str, Any],
    *,
    run_id: Optional[str] = None,
) -> bool:
    if not entries:
        return False
    latest = entries[0]
    if _snapshot_fingerprint(latest) != _snapshot_fingerprint(entry):
        return False
    if run_id is not None and latest.get("run_id") == run_id:
        return True
    if run_id is None and entry.get("run_id") and latest.get("run_id") == entry.get("run_id"):
        return True
    return _snapshot_fingerprint(latest) == _snapshot_fingerprint(entry)


def record_proof_bundle_diff_escalation_history(
    storage: LocalStorage,
    escalation: dict[str, Any],
    *,
    source: str,
    run_id: Optional[str] = None,
    skip_duplicate: bool = True,
) -> Optional[dict[str, Any]]:
    """Append escalation snapshot; skip exact duplicate of latest (same run or same state)."""
    entry = build_escalation_snapshot(escalation, source=source, run_id=run_id)
    entries = _load_entries(storage)
    if skip_duplicate and _is_duplicate_of_latest(entries, entry, run_id=run_id):
        return None
    entries.insert(0, entry)
    _save_entries(storage, entries)
    return entry


def record_escalation_from_storage(
    storage: LocalStorage,
    *,
    source: str,
    run_id: Optional[str] = None,
    skip_duplicate: bool = True,
) -> Optional[dict[str, Any]]:
    escalation = build_proof_bundle_diff_escalation(storage)
    return record_proof_bundle_diff_escalation_history(
        storage,
        escalation,
        source=source,
        run_id=run_id,
        skip_duplicate=skip_duplicate,
    )


def load_proof_bundle_diff_escalation_history(storage: LocalStorage) -> list[dict[str, Any]]:
    return _load_entries(storage)


def load_recent_proof_bundle_diff_escalation_history(
    storage: LocalStorage,
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    return _load_entries(storage)[:limit]


def load_latest_proof_bundle_diff_escalation_history(
    storage: LocalStorage,
) -> Optional[dict[str, Any]]:
    entries = _load_entries(storage)
    return entries[0] if entries else None


def count_proof_bundle_diff_escalation_history(storage: LocalStorage) -> int:
    return len(_load_entries(storage))


def compact_escalation_history_entry(entry: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if entry is None:
        return None
    return {
        "created_at": entry.get("created_at"),
        "escalation_level": entry.get("escalation_level"),
        "reason": entry.get("reason"),
        "latest_diff_status": entry.get("latest_diff_status"),
        "current_attention_streak": int(entry.get("current_attention_streak", 0)),
        "acknowledgment_status": entry.get("acknowledgment_status"),
        "stale_acknowledgment": bool(entry.get("stale_acknowledgment")),
        "suggested_next_action": entry.get("suggested_next_action"),
        "guidance_item_count": int(entry.get("guidance_item_count", 0)),
        "source": entry.get("source"),
        "verified_mrms": False,
        "local_history_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def compact_proof_bundle_diff_escalation_history_summary(
    storage: LocalStorage,
    *,
    recent_limit: int = 5,
) -> dict[str, Any]:
    from backend.app.services.proof_bundle_diff_escalation_stdout import (
        compact_latest_stdout_notice,
    )

    entries = _load_entries(storage)
    latest = entries[0] if entries else None
    stdout = compact_latest_stdout_notice(storage)
    return {
        "available": bool(entries),
        "count": len(entries),
        "max_entries": MAX_ESCALATION_HISTORY,
        "latest_snapshot_at": (latest or {}).get("created_at"),
        "latest_escalation_level": (latest or {}).get("escalation_level"),
        "recent": [
            compact_escalation_history_entry(item)
            for item in entries[:recent_limit]
            if item
        ],
        "urgent_stdout_notice_triggered": bool(stdout.get("triggered")),
        "urgent_stdout_notice_at": stdout.get("triggered_at"),
        "urgent_stdout_local_only": True,
        "verified_mrms": False,
        "local_history_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def build_proof_bundle_diff_escalation_history_payload(
    storage: LocalStorage,
    *,
    limit: int = MAX_ESCALATION_HISTORY,
) -> dict[str, Any]:
    entries = _load_entries(storage)
    latest = compact_escalation_history_entry(entries[0] if entries else None)
    bounded = max(1, min(limit, MAX_ESCALATION_HISTORY))
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_history_only": True,
        "does_not_clear_alerts": True,
        "count": len(entries),
        "max_entries": MAX_ESCALATION_HISTORY,
        "latest": latest,
        "entries": [
            compact_escalation_history_entry(item) for item in entries[:bounded] if item
        ],
    }
