"""Local MRMS proof review session records — does NOT verify MRMS."""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_operator_handoff import (
    REVIEW_CHECKLIST_ITEMS,
    load_latest_operator_handoff,
)
from backend.app.services.mrms_proof_bundle import load_latest_proof_bundle_manifest
from backend.app.services.mrms_proof_bundle_diff import (
    load_latest_proof_bundle_diff,
    proof_bundle_diff_requires_attention,
)
from backend.app.services.mrms_proof_report import load_mrms_proof_report
from backend.app.services.proof_bundle_diff_acknowledgment import load_latest_diff_acknowledgment
from backend.app.services.proof_bundle_diff_escalation import (
    ESCALATION_ATTENTION,
    ESCALATION_URGENT,
    build_proof_bundle_diff_escalation,
)
from backend.app.services.proof_bundle_diff_escalation_digest import (
    load_latest_escalation_digest_metadata,
)
from backend.app.services.proof_bundle_diff_escalation_digest_diff import (
    build_digest_regeneration_hint,
)
from backend.app.services.proof_bundle_diff_escalation_history import (
    load_latest_proof_bundle_diff_escalation_history,
)
from backend.app.services.operator_guidance import build_open_attention_guidance
from backend.app.services.mrms_proof_regression import load_proof_regression_report
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import load_validation_alert

REVIEW_SESSIONS_PATH = "dev/mrms_review_sessions.json"
MAX_REVIEW_SESSIONS = 50


class ReviewSessionValidationError(ValueError):
    """Raised when review session input fails validation."""


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sessions_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(REVIEW_SESSIONS_PATH)


def load_review_sessions(storage: LocalStorage) -> list[dict[str, Any]]:
    abs_path = storage.absolute_path(_sessions_repo_path(storage))
    if not abs_path.is_file():
        return []
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save_review_sessions(storage: LocalStorage, entries: list[dict[str, Any]]) -> str:
    repo_path = _sessions_repo_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(entries[:MAX_REVIEW_SESSIONS], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return repo_path


def validate_review_session_input(
    *,
    operator_name: Optional[str] = None,
    operator_initials: Optional[str] = None,
    session_notes: Optional[str] = None,
    checklist_items_reviewed: Optional[list[str]] = None,
    accepted_limitations: bool = False,
    accepted_limitations_text: Optional[str] = None,
) -> None:
    identity = (operator_name or "").strip() or (operator_initials or "").strip()
    if not identity:
        raise ReviewSessionValidationError("operator_name or operator_initials is required")

    notes = (session_notes or "").strip()
    reviewed = [item.strip() for item in (checklist_items_reviewed or []) if str(item).strip()]
    if not notes and not reviewed:
        raise ReviewSessionValidationError(
            "session_notes or at least one checklist_items_reviewed entry is required"
        )

    if not accepted_limitations and not (accepted_limitations_text or "").strip():
        raise ReviewSessionValidationError(
            "accepted_limitations must be explicitly acknowledged "
            "(does not verify MRMS; local review only)"
        )


def _build_open_attention_items(storage: LocalStorage) -> list[str]:
    items: list[str] = []
    alert = load_validation_alert(storage) or {}
    if alert.get("operator_attention_needed"):
        items.append("Validation alert: operator attention needed")
    if alert.get("proof_bundle_diff_attention"):
        items.append(
            f"Proof bundle diff attention: {alert.get('proof_bundle_diff_status') or 'unknown'}"
        )
    if alert.get("proof_regression_still_active"):
        items.append("Proof regression still active")

    escalation = build_proof_bundle_diff_escalation(storage)
    level = escalation.get("escalation_level")
    if level in (ESCALATION_ATTENTION, ESCALATION_URGENT):
        items.append(f"Escalation level: {level} — {escalation.get('reason', '')}")

    diff = load_latest_proof_bundle_diff(storage) or {}
    diff_status = diff.get("overall_diff_status")
    if proof_bundle_diff_requires_attention(str(diff_status or "")):
        items.append(f"Proof bundle diff status: {diff_status}")

    regression = load_proof_regression_report(storage)
    if regression and regression.get("regression_detected"):
        items.append("Proof regression detected in latest check")

    proof = load_mrms_proof_report(storage) or {}
    if proof.get("overall_status") == "failed":
        items.append("Latest proof report overall_status: failed")

    hint = build_digest_regeneration_hint(storage)
    if hint.get("digest_regeneration_recommended"):
        items.append(
            f"Digest regeneration recommended: {hint.get('reason') or 'see runbook'}"
        )

    if escalation.get("stale_acknowledgment"):
        items.append("Diff alert acknowledgment is stale relative to latest alerts")

    return items


def _gather_evidence_links(storage: LocalStorage) -> dict[str, Any]:
    escalation = build_proof_bundle_diff_escalation(storage)
    escalation_snapshot = load_latest_proof_bundle_diff_escalation_history(storage)
    digest = load_latest_escalation_digest_metadata(storage)
    handoff = load_latest_operator_handoff(storage)
    ack = load_latest_diff_acknowledgment(storage)
    bundle = load_latest_proof_bundle_manifest(storage)
    diff = load_latest_proof_bundle_diff(storage)
    proof = load_mrms_proof_report(storage)

    return {
        "latest_escalation_level": escalation.get("escalation_level"),
        "latest_escalation_snapshot_at": (escalation_snapshot or {}).get("created_at"),
        "latest_digest_path": (digest or {}).get("markdown_path"),
        "latest_digest_metadata_path": (digest or {}).get("json_path"),
        "latest_operator_handoff_path": (handoff or {}).get("markdown_path"),
        "latest_acknowledgment_id": (ack or {}).get("acknowledgment_id"),
        "latest_acknowledgment_at": (ack or {}).get("created_at"),
        "latest_proof_bundle_id": (bundle or {}).get("bundle_id"),
        "latest_proof_bundle_path": (bundle or {}).get("bundle_folder"),
        "latest_proof_bundle_diff_status": (diff or {}).get("overall_diff_status"),
        "latest_proof_report_status": (proof or {}).get("overall_status"),
    }


def create_review_session_record(
    storage: LocalStorage,
    *,
    operator_name: Optional[str] = None,
    operator_initials: Optional[str] = None,
    session_notes: Optional[str] = None,
    checklist_items_reviewed: Optional[list[str]] = None,
    accepted_limitations: bool = False,
    accepted_limitations_text: Optional[str] = None,
) -> dict[str, Any]:
    """Create and persist a local MRMS proof review session (does not verify MRMS)."""
    validate_review_session_input(
        operator_name=operator_name,
        operator_initials=operator_initials,
        session_notes=session_notes,
        checklist_items_reviewed=checklist_items_reviewed,
        accepted_limitations=accepted_limitations,
        accepted_limitations_text=accepted_limitations_text,
    )

    reviewed = [item.strip() for item in (checklist_items_reviewed or []) if str(item).strip()]
    valid_reviewed = [item for item in reviewed if item in REVIEW_CHECKLIST_ITEMS]
    not_reviewed = [item for item in REVIEW_CHECKLIST_ITEMS if item not in valid_reviewed]

    limitations_text = (accepted_limitations_text or "").strip()
    if not limitations_text and accepted_limitations:
        limitations_text = (
            "Accepted known prototype limitations — local review session only; "
            "does not verify MRMS or enable production rendering."
        )

    open_attention = _build_open_attention_items(storage)
    open_attention_guidance = build_open_attention_guidance(open_attention)
    evidence = _gather_evidence_links(storage)

    record: dict[str, Any] = {
        "session_id": str(uuid.uuid4()),
        "created_at": _utc_now(),
        "operator_name": (operator_name or "").strip() or None,
        "operator_initials": (operator_initials or "").strip() or None,
        "session_notes": (session_notes or "").strip() or None,
        "accepted_limitations": limitations_text or None,
        "accepted_limitations_acknowledged": bool(accepted_limitations or limitations_text),
        **evidence,
        "open_attention_items": open_attention,
        "open_attention_guidance": open_attention_guidance,
        "open_attention_count": len(open_attention),
        "checklist_items_reviewed": valid_reviewed,
        "checklist_items_not_reviewed": not_reviewed,
        "verified_mrms": False,
        "local_review_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "production_rendering_enabled": settings.enable_production_radar_tiles,
        "no_external_notifications": True,
        "prototype": True,
    }

    entries = load_review_sessions(storage)
    entries.insert(0, record)
    _save_review_sessions(storage, entries)
    from backend.app.services.mrms_review_session_compare import record_review_session_comparison

    record_review_session_comparison(storage, latest_session=record)
    return record


def compact_review_session_item(entry: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if entry is None:
        return None
    return {
        "session_id": entry.get("session_id"),
        "created_at": entry.get("created_at"),
        "operator": entry.get("operator_name") or entry.get("operator_initials"),
        "session_notes": entry.get("session_notes"),
        "latest_escalation_level": entry.get("latest_escalation_level"),
        "latest_escalation_snapshot_at": entry.get("latest_escalation_snapshot_at"),
        "latest_digest_path": entry.get("latest_digest_path"),
        "latest_operator_handoff_path": entry.get("latest_operator_handoff_path"),
        "latest_proof_bundle_diff_status": entry.get("latest_proof_bundle_diff_status"),
        "latest_proof_report_status": entry.get("latest_proof_report_status"),
        "open_attention_count": int(entry.get("open_attention_count", 0)),
        "checklist_items_reviewed": entry.get("checklist_items_reviewed") or [],
        "checklist_items_not_reviewed": entry.get("checklist_items_not_reviewed") or [],
        "verified_mrms": False,
        "local_review_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def compact_latest_review_session_summary(storage: LocalStorage) -> dict[str, Any]:
    from backend.app.services.mrms_review_session_compare import (
        compact_review_session_comparison_summary,
    )

    entries = load_review_sessions(storage)
    latest = entries[0] if entries else None
    open_attention_guidance: list[dict[str, Any]] = []
    if latest:
        open_attention_guidance = latest.get("open_attention_guidance") or []
        if not open_attention_guidance:
            open_attention_guidance = build_open_attention_guidance(
                latest.get("open_attention_items") or []
            )
    return {
        "available": latest is not None,
        "session_count": len(entries),
        "latest_created_at": (latest or {}).get("created_at"),
        "latest_operator": (
            (latest or {}).get("operator_name") or (latest or {}).get("operator_initials")
            if latest
            else None
        ),
        "latest_escalation_level": (latest or {}).get("latest_escalation_level"),
        "open_attention_count": int((latest or {}).get("open_attention_count", 0)),
        "open_attention_guidance": open_attention_guidance,
        "comparison": compact_review_session_comparison_summary(storage),
        "verified_mrms": False,
        "local_review_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def build_review_sessions_payload(
    storage: LocalStorage,
    *,
    limit: int = MAX_REVIEW_SESSIONS,
) -> dict[str, Any]:
    bounded = max(1, min(limit, MAX_REVIEW_SESSIONS))
    entries = load_review_sessions(storage)[:bounded]
    latest = entries[0] if entries else None
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_review_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "count": len(entries),
        "max_entries": MAX_REVIEW_SESSIONS,
        "latest": compact_review_session_item(latest),
        "entries": [item for item in (compact_review_session_item(e) for e in entries) if item],
        "compact": compact_latest_review_session_summary(storage),
    }
