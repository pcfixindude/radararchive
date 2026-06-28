"""Bounded proof bundle diff alert timeline — local evidence monitoring only."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_MIXED,
    DIFF_WORSENED,
    proof_bundle_diff_requires_attention,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import (
    CAUSE_PROOF_BUNDLE_DIFF_WORSENED,
    SUGGESTED_ACTIONS,
)

ALERT_HISTORY_PATH = "dev/proof_bundle_diff_alert_history.json"
MAX_ALERT_HISTORY = 25
GUIDANCE_CAUSE_MIXED = "proof_bundle_diff_mixed"
GUIDANCE_CAUSE_WORSENED = "proof_bundle_diff_worsened"


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _history_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(ALERT_HISTORY_PATH)


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
        json.dumps(entries[:MAX_ALERT_HISTORY], indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _guidance_cause_for_status(diff_status: Optional[str]) -> Optional[str]:
    status = str(diff_status or "")
    if status == DIFF_WORSENED:
        return GUIDANCE_CAUSE_WORSENED
    if status == DIFF_MIXED:
        return GUIDANCE_CAUSE_MIXED
    return None


def _suggested_action_for_entry(diff_status: str, guidance_cause: Optional[str]) -> str:
    if guidance_cause == GUIDANCE_CAUSE_MIXED:
        return (
            "Review mixed proof bundle diff — some evidence improved and some worsened; "
            "compare bundle evidence and re-run make scheduled-proof-bundle — does not verify MRMS."
        )
    if guidance_cause == GUIDANCE_CAUSE_WORSENED:
        return SUGGESTED_ACTIONS.get(
            CAUSE_PROOF_BUNDLE_DIFF_WORSENED,
            "Review make mrms-proof-bundle-diff and compare bundle evidence.",
        )
    return (
        f"Proof bundle diff status {diff_status} recorded — local monitoring only; "
        "does not verify MRMS or enable production rendering."
    )


def build_alert_history_entry(diff_report: dict[str, Any]) -> dict[str, Any]:
    """Build a compact timeline entry from a proof bundle diff report."""
    diff_status = str(diff_report.get("overall_diff_status") or "unknown")
    current = diff_report.get("current_bundle") or {}
    baseline = diff_report.get("baseline_bundle") or {}
    guidance_cause = _guidance_cause_for_status(diff_status)
    return {
        "created_at": diff_report.get("checked_at") or _utc_now(),
        "diff_status": diff_status,
        "operator_attention_needed": proof_bundle_diff_requires_attention(diff_status),
        "evidence_changes_count": int(diff_report.get("evidence_changes_count", 0)),
        "bundle_id": current.get("bundle_id"),
        "baseline_bundle_id": baseline.get("bundle_id"),
        "suggested_next_action": _suggested_action_for_entry(diff_status, guidance_cause),
        "guidance_cause": guidance_cause,
        "verified_mrms": False,
        "local_history_only": True,
        "prototype": True,
    }


def _entry_fingerprint(entry: dict[str, Any]) -> tuple[Any, ...]:
    return (
        entry.get("diff_status"),
        entry.get("bundle_id"),
        entry.get("baseline_bundle_id"),
        int(entry.get("evidence_changes_count", 0)),
        bool(entry.get("operator_attention_needed")),
    )


def _is_duplicate_of_latest(entries: list[dict[str, Any]], entry: dict[str, Any]) -> bool:
    if not entries:
        return False
    return _entry_fingerprint(entries[0]) == _entry_fingerprint(entry)


def record_proof_bundle_diff_alert_history(
    storage: LocalStorage,
    diff_report: dict[str, Any],
    *,
    skip_duplicate: bool = True,
) -> Optional[dict[str, Any]]:
    """Append a timeline entry when diff is evaluated; skip exact duplicate of latest."""
    entry = build_alert_history_entry(diff_report)
    entries = _load_entries(storage)
    if skip_duplicate and _is_duplicate_of_latest(entries, entry):
        return None
    entries.insert(0, entry)
    _save_entries(storage, entries)
    return entry


def load_proof_bundle_diff_alert_history(storage: LocalStorage) -> list[dict[str, Any]]:
    return _load_entries(storage)


def load_recent_proof_bundle_diff_alert_history(
    storage: LocalStorage,
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    return _load_entries(storage)[:limit]


def load_latest_proof_bundle_diff_alert_history(
    storage: LocalStorage,
) -> Optional[dict[str, Any]]:
    entries = _load_entries(storage)
    return entries[0] if entries else None


def count_proof_bundle_diff_alert_history(storage: LocalStorage) -> int:
    return len(_load_entries(storage))


def compact_alert_history_entry(entry: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if entry is None:
        return None
    return {
        "created_at": entry.get("created_at"),
        "diff_status": entry.get("diff_status"),
        "operator_attention_needed": bool(entry.get("operator_attention_needed")),
        "evidence_changes_count": int(entry.get("evidence_changes_count", 0)),
        "bundle_id": entry.get("bundle_id"),
        "baseline_bundle_id": entry.get("baseline_bundle_id"),
        "suggested_next_action": entry.get("suggested_next_action"),
        "guidance_cause": entry.get("guidance_cause"),
        "verified_mrms": False,
        "local_history_only": True,
        "prototype": True,
    }


def compact_latest_proof_bundle_diff_alert(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_proof_bundle_diff_alert_history(storage)
    if latest is None:
        return {
            "available": False,
            "count": 0,
            "verified_mrms": False,
            "local_history_only": True,
            "prototype": True,
        }
    compact = compact_alert_history_entry(latest) or {}
    return {
        "available": True,
        "count": count_proof_bundle_diff_alert_history(storage),
        **compact,
        "verified_mrms": False,
        "local_history_only": True,
        "prototype": True,
    }


def build_proof_bundle_diff_alert_history_payload(
    storage: LocalStorage,
    *,
    limit: int = MAX_ALERT_HISTORY,
) -> dict[str, Any]:
    entries = _load_entries(storage)
    latest = compact_alert_history_entry(entries[0] if entries else None)
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_history_only": True,
        "count": len(entries),
        "max_entries": MAX_ALERT_HISTORY,
        "latest": latest,
        "entries": [compact_alert_history_entry(item) for item in entries[:limit] if item],
    }
