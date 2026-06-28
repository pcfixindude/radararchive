"""Operator workflow presets — local dev guidance only, not verified MRMS."""

from __future__ import annotations

from typing import Any, Optional

from backend.app.services.operator_review_status import (
    EVIDENCE_MIXED,
    EVIDENCE_WORSENING,
    STATUS_OK,
    STATUS_WATCH,
    SUGGESTED_ATTENTION_SESSION_COMMAND,
    SUGGESTED_INITIAL_SESSION_COMMAND,
    build_operator_review_status,
)
from backend.app.services.storage import LocalStorage

PRESET_QUICK_STATUS_CHECK = "quick-status-check"
PRESET_FULL_LOCAL_PROOF_REVIEW = "full-local-proof-review"
PRESET_CREATE_REVIEW_SESSION_AND_EXPORT = "create-review-session-and-export"
PRESET_REGENERATE_DIGEST_CHECKLIST_EXPORT = "regenerate-digest-checklist-export"
PRESET_INSPECT_WORSENING_EXPORT_TREND = "inspect-worsening-export-trend"
PRESET_REVIEW_PROOF_BUNDLE_DIFF = "review-proof-bundle-diff"
PRESET_RUN_SCHEDULED_PROOF_BUNDLE_OPERATOR_STATUS = "run-scheduled-proof-bundle-operator-status"

EXPECTED_PRESET_IDS = (
    PRESET_QUICK_STATUS_CHECK,
    PRESET_FULL_LOCAL_PROOF_REVIEW,
    PRESET_CREATE_REVIEW_SESSION_AND_EXPORT,
    PRESET_REGENERATE_DIGEST_CHECKLIST_EXPORT,
    PRESET_INSPECT_WORSENING_EXPORT_TREND,
    PRESET_REVIEW_PROOF_BUNDLE_DIFF,
    PRESET_RUN_SCHEDULED_PROOF_BUNDLE_OPERATOR_STATUS,
)

COMMON_SAFETY_NOTES = [
    "Local workflow guidance only — does not verify MRMS.",
    "Does not clear validation alerts.",
    "Does not enable production rendering.",
    "Does not send external notifications.",
]

_PRESET_DEFINITIONS: list[dict[str, Any]] = [
    {
        "preset_id": PRESET_QUICK_STATUS_CHECK,
        "title": "Quick status check",
        "description": "Print consolidated operator review status from existing local evidence.",
        "when_to_use": "Start of a review shift or after any scheduled run when you need a single summary.",
        "command": "make operator-review-status",
        "expected_outputs": [
            "status_level and status_reason",
            "top recommended action and suggested command",
            "review session/export/digest recommendation flags",
            "evidence trend and latest timestamps",
        ],
    },
    {
        "preset_id": PRESET_FULL_LOCAL_PROOF_REVIEW,
        "title": "Full local proof review",
        "description": "Run scheduled proof report, bundle export, and bundle diff in one local pass.",
        "when_to_use": "After validation changes or before recording a review session — refreshes proof evidence.",
        "command": "make scheduled-proof-bundle",
        "expected_outputs": [
            "proof report and regression step results",
            "proof bundle folder and ZIP under data/dev/proof_bundles/",
            "proof bundle diff status vs baseline",
        ],
    },
    {
        "preset_id": PRESET_CREATE_REVIEW_SESSION_AND_EXPORT,
        "title": "Create review session and export",
        "description": "Record a local MRMS proof review session and export Markdown in one step.",
        "when_to_use": "When no review session exists, export trend is worsening/mixed, or operator status recommends a session.",
        "command": SUGGESTED_INITIAL_SESSION_COMMAND,
        "expected_outputs": [
            "timestamped review session JSON under data/dev/",
            "Markdown export when --export-after-create is used",
            "open attention and escalation snapshot at review time",
        ],
    },
    {
        "preset_id": PRESET_REGENERATE_DIGEST_CHECKLIST_EXPORT,
        "title": "Regenerate digest, checklist, and export",
        "description": "Run scheduled proof bundle with escalation digest, handoff checklist, and review export.",
        "when_to_use": "When digest/checklist is stale or operator status recommends digest regeneration.",
        "command": "make scheduled-proof-bundle-review-export",
        "expected_outputs": [
            "escalation digest Markdown and metadata",
            "operator handoff checklist when escalation review is included",
            "latest review session Markdown export when a session exists",
        ],
    },
    {
        "preset_id": PRESET_INSPECT_WORSENING_EXPORT_TREND,
        "title": "Inspect worsening export trend",
        "description": "Summarize review export diff trend and regeneration hint from local history.",
        "when_to_use": "When export diff trend is mixed or worsening and you need streak/context before acting.",
        "command": "make mrms-review-session-export-diff-trend-hint",
        "expected_outputs": [
            "export diff trend label (improving/worsening/mixed/stable/no_data)",
            "worsened and mixed/worsened streak counts",
            "regeneration recommended yes/no with suggested command",
        ],
    },
    {
        "preset_id": PRESET_REVIEW_PROOF_BUNDLE_DIFF,
        "title": "Review proof bundle diff",
        "description": "Compare latest proof bundle evidence against the saved baseline diff report.",
        "when_to_use": "After exporting at least two proof bundles or when escalation/diff alerts need review.",
        "command": "make mrms-proof-bundle-diff",
        "expected_outputs": [
            "overall_diff_status (unchanged/improved/worsened/mixed)",
            "evidence change count and checked_at timestamp",
            "diff JSON under data/dev/ for Dev Validation summary",
        ],
    },
    {
        "preset_id": PRESET_RUN_SCHEDULED_PROOF_BUNDLE_OPERATOR_STATUS,
        "title": "Run scheduled proof bundle with operator status",
        "description": "Full scheduled proof bundle review export plus consolidated operator review status step.",
        "when_to_use": "End-to-end local review run when you want digest, export, and operator status in one report.",
        "command": "make scheduled-proof-bundle-operator-status",
        "expected_outputs": [
            "scheduled validation report with proof/digest/export steps",
            "operator_review_status step with status_level and top_suggested_command",
            "scheduled_operator_status compact in validation summary",
        ],
    },
]


def _preset_safety_fields() -> dict[str, Any]:
    return {
        "safety_notes": list(COMMON_SAFETY_NOTES),
        "verified_mrms": False,
        "local_workflow_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def _recommendation_for_preset(
    preset_id: str,
    status: dict[str, Any],
) -> tuple[bool, Optional[str]]:
    status_level = str(status.get("status_level") or "")
    digest_regeneration_recommended = bool(status.get("digest_regeneration_recommended"))
    review_session_recommended = bool(status.get("review_session_recommended"))
    has_session = bool(status.get("latest_review_session_at"))
    evidence_trend = str(status.get("evidence_trend") or "")

    if preset_id == PRESET_QUICK_STATUS_CHECK:
        if status_level in (STATUS_OK, STATUS_WATCH):
            return True, "operator_review_status_ok_or_watch"
        return False, None

    if preset_id == PRESET_REGENERATE_DIGEST_CHECKLIST_EXPORT:
        if digest_regeneration_recommended:
            return True, "digest_or_checklist_stale"
        return False, None

    if preset_id == PRESET_CREATE_REVIEW_SESSION_AND_EXPORT:
        if not has_session:
            return True, "no_review_session"
        if evidence_trend in (EVIDENCE_WORSENING, EVIDENCE_MIXED):
            return True, "export_diff_trend_worsening_or_mixed"
        if review_session_recommended:
            return True, "review_session_recommended"
        return False, None

    return False, None


def _build_preset(
    definition: dict[str, Any],
    status: dict[str, Any],
) -> dict[str, Any]:
    preset_id = str(definition["preset_id"])
    recommended, recommendation_reason = _recommendation_for_preset(preset_id, status)
    command = str(definition["command"])
    if preset_id == PRESET_CREATE_REVIEW_SESSION_AND_EXPORT and status.get("latest_review_session_at"):
        if recommended and str(status.get("status_level") or "") not in (STATUS_OK, STATUS_WATCH):
            command = SUGGESTED_ATTENTION_SESSION_COMMAND
    return {
        **definition,
        "command": command,
        "recommended": recommended,
        "recommendation_reason": recommendation_reason,
        **_preset_safety_fields(),
    }


def build_operator_workflow_presets(
    storage: LocalStorage,
    *,
    status: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """Build read-only workflow presets from operator review status."""
    review_status = status if status is not None else build_operator_review_status(storage)
    presets = [_build_preset(defn, review_status) for defn in _PRESET_DEFINITIONS]
    presets.sort(key=lambda item: (not item["recommended"], EXPECTED_PRESET_IDS.index(item["preset_id"])))
    return presets


def compact_operator_workflow_presets(storage: LocalStorage) -> dict[str, Any]:
    """Compact presets for validation summary embedding."""
    presets = build_operator_workflow_presets(storage)
    recommended_count = sum(1 for preset in presets if preset.get("recommended"))
    return {
        "available": True,
        "recommended_count": recommended_count,
        "presets": presets,
        **_preset_safety_fields(),
    }


def build_operator_workflow_presets_payload(storage: LocalStorage) -> dict[str, Any]:
    """API/CLI payload for operator workflow presets."""
    presets = build_operator_workflow_presets(storage)
    recommended_presets = [preset for preset in presets if preset.get("recommended")]
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_workflow_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "recommended_count": len(recommended_presets),
        "presets": presets,
        "recommended_presets": recommended_presets,
    }
