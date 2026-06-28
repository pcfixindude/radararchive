"""Stale visual review regeneration hints — local hint only."""

from __future__ import annotations

from typing import Any, Optional

from backend.app.services.mrms_proof_bundle import load_latest_proof_bundle_manifest
from backend.app.services.mrms_proof_report import load_mrms_proof_report
from backend.app.services.mrms_visual_review import (
    SUGGESTED_VISUAL_REVIEW_COMMAND,
    load_latest_visual_review,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.time_utils import parse_utc_iso
from backend.app.services.validation_report_store import (
    load_latest_scheduled_validation_report,
    load_latest_validation_report,
)


def _safe_parse(timestamp: Optional[str]) -> Optional[Any]:
    if not timestamp:
        return None
    try:
        return parse_utc_iso(timestamp)
    except ValueError:
        return None


def _latest_timestamp(*candidates: Optional[str]) -> Optional[str]:
    parsed = [(value, _safe_parse(value)) for value in candidates if value]
    valid = [(value, dt) for value, dt in parsed if dt is not None]
    if not valid:
        return None
    return max(valid, key=lambda item: item[1])[0]


def _collect_relevant_evidence_timestamps(storage: LocalStorage) -> dict[str, Optional[str]]:
    proof = load_mrms_proof_report(storage) or {}
    bundle = load_latest_proof_bundle_manifest(storage) or {}
    validation = load_latest_validation_report(storage) or {}
    scheduled = load_latest_scheduled_validation_report(storage) or {}

    return {
        "proof_report": proof.get("generated_at"),
        "proof_bundle": bundle.get("created_at"),
        "validation_report": validation.get("ran_at"),
        "scheduled_validation": scheduled.get("ran_at"),
    }


def build_visual_review_hint(storage: LocalStorage) -> dict[str, Any]:
    """Suggest when operators should regenerate the visual review manifest."""
    visual = load_latest_visual_review(storage)
    visual_at = (visual or {}).get("created_at")
    evidence = _collect_relevant_evidence_timestamps(storage)
    latest_relevant_evidence_at = _latest_timestamp(*evidence.values())

    recommended = False
    reason: Optional[str] = None
    stale_visual_review = False

    if visual is None:
        recommended = True
        stale_visual_review = True
        reason = "no_visual_review"
    elif latest_relevant_evidence_at and visual_at:
        visual_dt = _safe_parse(visual_at)
        evidence_dt = _safe_parse(latest_relevant_evidence_at)
        if visual_dt is not None and evidence_dt is not None and evidence_dt > visual_dt:
            recommended = True
            stale_visual_review = True
            reason = "evidence_newer_than_visual_review"
            missing_count = int(visual.get("missing_artifact_count", 0))
            if missing_count > 0:
                reason = "missing_artifacts_and_newer_proof_render_activity"
    elif latest_relevant_evidence_at and not visual_at:
        recommended = True
        stale_visual_review = True
        reason = "evidence_without_visual_review_timestamp"

    return {
        "visual_review_regeneration_recommended": recommended,
        "reason": reason,
        "suggested_command": SUGGESTED_VISUAL_REVIEW_COMMAND if recommended else None,
        "latest_visual_review_at": visual_at,
        "latest_relevant_evidence_at": latest_relevant_evidence_at,
        "stale_visual_review": stale_visual_review,
        "evidence_timestamps": evidence,
        "verified_mrms": False,
        "local_hint_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def compact_visual_review_hint(storage: LocalStorage) -> dict[str, Any]:
    hint = build_visual_review_hint(storage)
    return {
        "available": True,
        "visual_review_regeneration_recommended": bool(
            hint.get("visual_review_regeneration_recommended")
        ),
        "reason": hint.get("reason"),
        "suggested_command": hint.get("suggested_command") or SUGGESTED_VISUAL_REVIEW_COMMAND,
        "latest_visual_review_at": hint.get("latest_visual_review_at"),
        "latest_relevant_evidence_at": hint.get("latest_relevant_evidence_at"),
        "stale_visual_review": bool(hint.get("stale_visual_review")),
        "verified_mrms": False,
        "local_hint_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def build_visual_review_hint_payload(storage: LocalStorage) -> dict[str, Any]:
    hint = build_visual_review_hint(storage)
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_hint_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "hint": hint,
        "compact": compact_visual_review_hint(storage),
    }
