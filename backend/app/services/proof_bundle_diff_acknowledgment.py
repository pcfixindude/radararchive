"""Local proof bundle diff alert acknowledgments — does NOT clear alerts or verify MRMS."""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.proof_bundle_diff_alert_history import (
    load_latest_proof_bundle_diff_alert_history,
)
from backend.app.services.storage import LocalStorage

ACKNOWLEDGMENTS_PATH = "dev/proof_bundle_diff_acknowledgments.json"
MAX_ACKNOWLEDGMENTS = 50


class DiffAcknowledgmentValidationError(ValueError):
    """Raised when acknowledgment input fails validation."""


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ack_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(ACKNOWLEDGMENTS_PATH)


def load_diff_acknowledgments(storage: LocalStorage) -> list[dict[str, Any]]:
    abs_path = storage.absolute_path(_ack_repo_path(storage))
    if not abs_path.is_file():
        return []
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save_acknowledgments(storage: LocalStorage, entries: list[dict[str, Any]]) -> str:
    repo_path = _ack_repo_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    bounded = entries[:MAX_ACKNOWLEDGMENTS]
    storage.absolute_path(repo_path).write_text(
        json.dumps(bounded, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return repo_path


def validate_diff_acknowledgment_input(
    *,
    operator_name: Optional[str] = None,
    operator_initials: Optional[str] = None,
    note: Optional[str] = None,
) -> None:
    identity = (operator_name or "").strip() or (operator_initials or "").strip()
    if not identity:
        raise DiffAcknowledgmentValidationError("operator_name or operator_initials is required")
    if not (note or "").strip():
        raise DiffAcknowledgmentValidationError("note is required")


def create_diff_acknowledgment(
    storage: LocalStorage,
    *,
    operator_name: Optional[str] = None,
    operator_initials: Optional[str] = None,
    note: str,
    related_diff_status: Optional[str] = None,
    related_bundle_id: Optional[str] = None,
    related_baseline_bundle_id: Optional[str] = None,
    acknowledged_attention: Optional[bool] = None,
) -> dict[str, Any]:
    """Persist local acknowledgment; does NOT mutate alerts, proof, or production gates."""
    validate_diff_acknowledgment_input(
        operator_name=operator_name,
        operator_initials=operator_initials,
        note=note,
    )

    latest_alert = load_latest_proof_bundle_diff_alert_history(storage)
    diff_status = related_diff_status or (latest_alert or {}).get("diff_status")
    bundle_id = related_bundle_id or (latest_alert or {}).get("bundle_id")
    baseline_id = related_baseline_bundle_id or (latest_alert or {}).get("baseline_bundle_id")
    if acknowledged_attention is None:
        acknowledged_attention = bool((latest_alert or {}).get("operator_attention_needed"))

    record: dict[str, Any] = {
        "acknowledgment_id": str(uuid.uuid4()),
        "created_at": _utc_now(),
        "operator_name": (operator_name or "").strip() or None,
        "operator_initials": (operator_initials or "").strip() or None,
        "operator": (operator_name or "").strip() or (operator_initials or "").strip(),
        "note": note.strip(),
        "related_diff_status": diff_status,
        "related_bundle_id": bundle_id,
        "related_baseline_bundle_id": baseline_id,
        "acknowledged_attention": bool(acknowledged_attention),
        "verified_mrms": False,
        "local_acknowledgment_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "production_rendering_enabled": settings.enable_production_radar_tiles,
        "prototype": True,
    }

    entries = load_diff_acknowledgments(storage)
    entries.insert(0, record)
    _save_acknowledgments(storage, entries)
    return record


def load_latest_diff_acknowledgment(storage: LocalStorage) -> Optional[dict[str, Any]]:
    entries = load_diff_acknowledgments(storage)
    return entries[0] if entries else None


def count_diff_acknowledgments(storage: LocalStorage) -> int:
    return len(load_diff_acknowledgments(storage))


def compact_diff_acknowledgment(entry: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if entry is None:
        return None
    return {
        "acknowledgment_id": entry.get("acknowledgment_id"),
        "created_at": entry.get("created_at"),
        "operator": entry.get("operator"),
        "operator_name": entry.get("operator_name"),
        "operator_initials": entry.get("operator_initials"),
        "note": entry.get("note"),
        "related_diff_status": entry.get("related_diff_status"),
        "related_bundle_id": entry.get("related_bundle_id"),
        "related_baseline_bundle_id": entry.get("related_baseline_bundle_id"),
        "acknowledged_attention": bool(entry.get("acknowledged_attention")),
        "verified_mrms": False,
        "local_acknowledgment_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def compact_diff_acknowledgment_summary(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_diff_acknowledgment(storage)
    count = count_diff_acknowledgments(storage)
    if latest is None:
        return {
            "available": False,
            "count": 0,
            "verified_mrms": False,
            "local_acknowledgment_only": True,
            "does_not_clear_alerts": True,
            "prototype": True,
        }
    compact = compact_diff_acknowledgment(latest) or {}
    return {
        "available": True,
        "count": count,
        **compact,
        "verified_mrms": False,
        "local_acknowledgment_only": True,
        "does_not_clear_alerts": True,
        "prototype": True,
    }


def build_diff_acknowledgments_payload(
    storage: LocalStorage,
    *,
    limit: int = 25,
) -> dict[str, Any]:
    entries = load_diff_acknowledgments(storage)
    bounded = max(1, min(limit, MAX_ACKNOWLEDGMENTS))
    latest = compact_diff_acknowledgment(entries[0] if entries else None)
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_acknowledgment_only": True,
        "does_not_clear_alerts": True,
        "count": len(entries),
        "max_entries": MAX_ACKNOWLEDGMENTS,
        "latest": latest,
        "entries": [compact_diff_acknowledgment(item) for item in entries[:bounded] if item],
    }
