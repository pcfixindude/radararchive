"""Bounded proof bundle diff escalation digest export history — local review only."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.services.storage import LocalStorage

DIGEST_HISTORY_PATH = "dev/proof_bundle_diff_escalation_digest_history.json"
MAX_DIGEST_HISTORY = 25


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _history_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(DIGEST_HISTORY_PATH)


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
        json.dumps(entries[:MAX_DIGEST_HISTORY], indent=2, sort_keys=True),
        encoding="utf-8",
    )


def build_digest_history_entry(metadata: dict[str, Any]) -> dict[str, Any]:
    """Build a bounded history record from digest export metadata."""
    metrics = metadata.get("metrics") or {}
    return {
        "created_at": metadata.get("generated_at") or _utc_now(),
        "digest_path": metadata.get("markdown_path"),
        "metadata_path": metadata.get("json_path"),
        "latest_escalation_level": metadata.get("latest_escalation_level"),
        "latest_diff_status": metadata.get("latest_diff_status"),
        "current_attention_or_urgent_streak": int(
            metadata.get("current_attention_or_urgent_streak", metrics.get("current_attention_or_urgent_streak", 0))
        ),
        "urgent_count": int(metadata.get("urgent_count", metrics.get("urgent_count", 0))),
        "attention_count": int(metadata.get("attention_count", metrics.get("attention_count", 0))),
        "stale_acknowledgment_count": int(
            metadata.get("stale_acknowledgment_count", metrics.get("stale_acknowledgment_count", 0))
        ),
        "verified_mrms": False,
        "local_digest_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def record_digest_export_history(
    storage: LocalStorage,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Append digest export metadata to bounded history (newest first)."""
    entry = build_digest_history_entry(metadata)
    entries = _load_entries(storage)
    entries.insert(0, entry)
    _save_entries(storage, entries)
    return entry


def load_digest_export_history(storage: LocalStorage) -> list[dict[str, Any]]:
    return _load_entries(storage)


def load_recent_digest_export_history(
    storage: LocalStorage,
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    return _load_entries(storage)[:limit]


def load_previous_digest_history_entry(storage: LocalStorage) -> Optional[dict[str, Any]]:
    entries = _load_entries(storage)
    return entries[1] if len(entries) >= 2 else None


def count_digest_export_history(storage: LocalStorage) -> int:
    return len(_load_entries(storage))


def compact_digest_history_entry(entry: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if entry is None:
        return None
    return {
        "created_at": entry.get("created_at"),
        "digest_path": entry.get("digest_path"),
        "metadata_path": entry.get("metadata_path"),
        "latest_escalation_level": entry.get("latest_escalation_level"),
        "latest_diff_status": entry.get("latest_diff_status"),
        "current_attention_or_urgent_streak": int(entry.get("current_attention_or_urgent_streak", 0)),
        "urgent_count": int(entry.get("urgent_count", 0)),
        "attention_count": int(entry.get("attention_count", 0)),
        "stale_acknowledgment_count": int(entry.get("stale_acknowledgment_count", 0)),
        "verified_mrms": False,
        "local_digest_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def compact_digest_history_summary(
    storage: LocalStorage,
    *,
    recent_limit: int = 5,
) -> dict[str, Any]:
    entries = _load_entries(storage)
    latest = entries[0] if entries else None
    return {
        "available": bool(entries),
        "count": len(entries),
        "max_entries": MAX_DIGEST_HISTORY,
        "latest": compact_digest_history_entry(latest),
        "recent": [
            item
            for item in (
                compact_digest_history_entry(entry) for entry in entries[:recent_limit]
            )
            if item
        ],
        "verified_mrms": False,
        "local_digest_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def build_digest_export_history_payload(
    storage: LocalStorage,
    *,
    limit: int = MAX_DIGEST_HISTORY,
) -> dict[str, Any]:
    bounded = max(1, min(limit, MAX_DIGEST_HISTORY))
    entries = _load_entries(storage)[:bounded]
    latest = entries[0] if entries else None
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_digest_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "count": len(entries),
        "max_entries": MAX_DIGEST_HISTORY,
        "latest": compact_digest_history_entry(latest),
        "entries": [item for item in (compact_digest_history_entry(e) for e in entries) if item],
        "compact": compact_digest_history_summary(storage, recent_limit=min(5, bounded)),
    }
