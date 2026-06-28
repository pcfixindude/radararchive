"""Consolidated operator review status — local dev validation only, not verified MRMS."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from backend.app.services.mrms_proof_bundle_diff import DIFF_MIXED, DIFF_UNKNOWN, DIFF_WORSENED
from backend.app.services.mrms_review_session import compact_latest_review_session_summary
from backend.app.services.mrms_review_session_export import (
    SUGGESTED_EXPORT_COMMAND,
    build_review_export_regeneration_hint,
    compact_review_session_export_summary,
)
from backend.app.services.mrms_review_session_export_diff import (
    compact_review_session_export_diff_history_summary,
    compact_review_session_export_diff_summary,
)
from backend.app.services.mrms_visual_review import (
    SUGGESTED_VISUAL_REVIEW_COMMAND,
    compact_mrms_visual_review,
    compact_scheduled_visual_review,
)
from backend.app.services.mrms_visual_review_compare import compact_visual_review_comparison_summary
from backend.app.services.mrms_visual_review_hint import compact_visual_review_hint
from backend.app.services.mrms_review_session_export_diff_trend_hint import (
    SUGGESTED_SCHEDULED_REVIEW_EXPORT_COMMAND,
    build_review_session_export_diff_trend_hint,
)
from backend.app.services.mrms_review_session_export_diff_trends import (
    TREND_IMPROVING,
    TREND_MIXED,
    TREND_NO_DATA,
    TREND_STABLE,
    TREND_WORSENING,
    compact_review_session_export_diff_trend,
)
from backend.app.services.operator_guidance import RUNBOOK_PATH, compact_operator_guidance
from backend.app.services.proof_bundle_diff_alert_trends import (
    compact_proof_bundle_diff_alert_trend,
)
from backend.app.services.proof_bundle_diff_escalation import (
    ESCALATION_URGENT,
    ESCALATION_WATCH,
    compact_proof_bundle_diff_escalation,
)
from backend.app.services.proof_bundle_diff_escalation_digest_diff import (
    build_digest_regeneration_hint,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_report_store import load_latest_scheduled_validation_report
from backend.app.services.validation_alerts import (
    ALERT_FAILED,
    ALERT_WARNING,
    compact_validation_alert,
    load_validation_alert,
)

STATUS_OK = "ok"
STATUS_WATCH = "watch"
STATUS_ATTENTION = "attention"
STATUS_URGENT = "urgent"
STATUS_UNKNOWN = "unknown"

EVIDENCE_IMPROVING = "improving"
EVIDENCE_WORSENING = "worsening"
EVIDENCE_MIXED = "mixed"
EVIDENCE_STABLE = "stable"
EVIDENCE_NO_DATA = "no_data"
EVIDENCE_UNKNOWN = "unknown"

SUGGESTED_INITIAL_SESSION_COMMAND = (
    'make mrms-review-session ARGS="--operator YOUR_INITIALS '
    '--notes \'initial local review\' --accepted-limitations --export-after-create"'
)
SUGGESTED_ATTENTION_SESSION_COMMAND = (
    'make mrms-review-session ARGS="--operator YOUR_INITIALS '
    '--notes \'local review status needs attention\' --accepted-limitations --export-after-create"'
)

SESSION_TREND_REASONS = frozenset(
    {
        "export_diff_trend_worsening",
        "export_diff_trend_mixed_streak",
    }
)

OPERATOR_STATUS_GUIDANCE: dict[str, dict[str, str]] = {
    "status_level_urgent": {
        "title": "Urgent operator review status",
        "path": RUNBOOK_PATH,
        "anchor": "operator-review-status-urgent",
        "section_label": "Urgent operator review status",
        "suggested_action": (
            "Address urgent local review signals before sign-off or production promotion. "
            "Follow runbook urgent section and suggested commands."
        ),
    },
    "status_level_attention": {
        "title": "Attention operator review status",
        "path": RUNBOOK_PATH,
        "anchor": "operator-review-status-attention",
        "section_label": "Attention operator review status",
        "suggested_action": (
            "Review open local attention items and follow the top suggested command "
            "(local review only)."
        ),
    },
    "status_level_watch": {
        "title": "Watch operator review status",
        "path": RUNBOOK_PATH,
        "anchor": "operator-review-status-watch",
        "section_label": "Watch operator review status",
        "suggested_action": (
            "Monitor local review evidence trends; re-check operator review status after "
            "the next scheduled proof/review run."
        ),
    },
    "digest_regeneration_recommended": {
        "title": "Digest regeneration recommended",
        "path": RUNBOOK_PATH,
        "anchor": "operator-review-status-digest-regeneration",
        "section_label": "Digest regeneration recommended",
        "suggested_action": (
            "Run make scheduled-proof-bundle-review-export or make scheduled-proof-bundle-digest "
            "to refresh local digest/checklist evidence."
        ),
    },
    "visual_review_regeneration_recommended": {
        "title": "Visual review regeneration recommended",
        "path": RUNBOOK_PATH,
        "anchor": "operator-review-status-visual-review-regeneration",
        "section_label": "Visual review regeneration recommended",
        "suggested_action": (
            "Run make mrms-visual-review to regenerate the local visual review manifest from "
            "existing tile/render artifacts (does not download or decode MRMS)."
        ),
    },
    "review_export_recommended": {
        "title": "Review export recommended",
        "path": RUNBOOK_PATH,
        "anchor": "operator-review-status-review-export",
        "section_label": "Review export recommended",
        "suggested_action": (
            "Run make mrms-review-session-export to export the latest review session summary "
            "(local review only)."
        ),
    },
    "review_session_recommended": {
        "title": "Review session recommended",
        "path": RUNBOOK_PATH,
        "anchor": "operator-review-status-review-session",
        "section_label": "Review session recommended",
        "suggested_action": (
            "Run make mrms-review-session with --accepted-limitations and --export-after-create "
            "to record a new local review session."
        ),
    },
    "evidence_trend_worsening": {
        "title": "Evidence trend worsening",
        "path": RUNBOOK_PATH,
        "anchor": "operator-review-status-evidence-worsening",
        "section_label": "Evidence trend worsening",
        "suggested_action": (
            "Review export diff trend and history; consider a new review session with export "
            "(local review only)."
        ),
    },
    "evidence_trend_mixed": {
        "title": "Evidence trend mixed",
        "path": RUNBOOK_PATH,
        "anchor": "operator-review-status-evidence-mixed",
        "section_label": "Evidence trend mixed",
        "suggested_action": (
            "Compare export diff history entries and follow runbook mixed-trend guidance."
        ),
    },
    "evidence_trend_stable": {
        "title": "Evidence trend stable",
        "path": RUNBOOK_PATH,
        "anchor": "operator-review-status-evidence-stable",
        "section_label": "Evidence trend stable",
        "suggested_action": (
            "Continue local monitoring; no mandatory action unless regeneration hints appear."
        ),
    },
    "evidence_trend_improving": {
        "title": "Evidence trend improving",
        "path": RUNBOOK_PATH,
        "anchor": "operator-review-status-evidence-improving",
        "section_label": "Evidence trend improving",
        "suggested_action": (
            "Evidence is improving locally — keep monitoring; does not verify MRMS."
        ),
    },
}


def _status_guidance_item(cause: str) -> dict[str, Any]:
    meta = OPERATOR_STATUS_GUIDANCE.get(cause, OPERATOR_STATUS_GUIDANCE["status_level_attention"])
    return {
        "title": meta["title"],
        "path": meta["path"],
        "anchor": meta.get("anchor", ""),
        "section_label": meta.get("section_label", meta["title"]),
        "cause": cause,
        "suggested_action": meta.get("suggested_action", ""),
        "verified_mrms": False,
        "local_guidance_only": True,
        "prototype": True,
    }


def build_operator_review_status_guidance(status: dict[str, Any]) -> list[dict[str, Any]]:
    """Map consolidated operator review status to runbook guidance items."""
    items: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(cause: str) -> None:
        if cause in seen:
            return
        items.append(_status_guidance_item(cause))
        seen.add(cause)

    status_level = str(status.get("status_level") or STATUS_UNKNOWN)
    evidence_trend = str(status.get("evidence_trend") or EVIDENCE_UNKNOWN)

    if status_level == STATUS_URGENT:
        add("status_level_urgent")
    if status.get("digest_regeneration_recommended"):
        add("digest_regeneration_recommended")
    if status.get("visual_review_regeneration_recommended"):
        add("visual_review_regeneration_recommended")
    if status.get("review_export_recommended"):
        add("review_export_recommended")
    if status.get("review_session_recommended"):
        add("review_session_recommended")
    if status_level == STATUS_ATTENTION:
        add("status_level_attention")
    if evidence_trend == EVIDENCE_WORSENING:
        add("evidence_trend_worsening")
    elif evidence_trend == EVIDENCE_MIXED:
        add("evidence_trend_mixed")
    if status_level == STATUS_WATCH:
        add("status_level_watch")
    if evidence_trend == EVIDENCE_STABLE:
        add("evidence_trend_stable")
    elif evidence_trend == EVIDENCE_IMPROVING:
        add("evidence_trend_improving")

    return items[:8]


def _attach_guidance_fields(status: dict[str, Any]) -> dict[str, Any]:
    guidance_items = build_operator_review_status_guidance(status)
    top = guidance_items[0] if guidance_items else None
    status["guidance_items"] = guidance_items
    status["top_guidance_item"] = top
    status["runbook_path"] = top.get("path") if top else None
    status["runbook_section"] = (top or {}).get("section_label") or (top or {}).get("anchor")
    status["suggested_action"] = (top or {}).get("suggested_action")
    return status


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _map_export_trend_to_evidence(trend: Optional[str]) -> str:
    if not trend or trend == TREND_NO_DATA:
        return EVIDENCE_NO_DATA
    if trend == TREND_IMPROVING:
        return EVIDENCE_IMPROVING
    if trend == TREND_WORSENING:
        return EVIDENCE_WORSENING
    if trend == TREND_MIXED:
        return EVIDENCE_MIXED
    if trend == TREND_STABLE:
        return EVIDENCE_STABLE
    return EVIDENCE_UNKNOWN


def _resolve_evidence_trend(
    export_trend: dict[str, Any],
    proof_alert_trend: Optional[dict[str, Any]],
) -> str:
    export_value = str(export_trend.get("trend") or TREND_NO_DATA)
    mapped = _map_export_trend_to_evidence(export_value)
    if mapped != EVIDENCE_NO_DATA:
        return mapped
    if proof_alert_trend:
        alert_trend = str(proof_alert_trend.get("trend") or "")
        alert_mapped = _map_export_trend_to_evidence(alert_trend)
        if alert_mapped != EVIDENCE_NO_DATA:
            return alert_mapped
    if export_value == TREND_NO_DATA:
        return EVIDENCE_NO_DATA
    return EVIDENCE_UNKNOWN


def _session_trend_recommends_review(trend_hint: dict[str, Any]) -> bool:
    if not trend_hint.get("review_trend_regeneration_recommended"):
        return False
    reason = str(trend_hint.get("reason") or "")
    if reason in SESSION_TREND_REASONS:
        return True
    return reason.startswith("latest_export_diff_")


def _has_sufficient_data(
    *,
    session_summary: dict[str, Any],
    export_summary: dict[str, Any],
    export_diff_history: dict[str, Any],
    digest_hint: dict[str, Any],
    alert_compact: Optional[dict[str, Any]],
    escalation: dict[str, Any],
) -> bool:
    if session_summary.get("available"):
        return True
    if export_summary.get("available"):
        return True
    if int(export_diff_history.get("count", 0)) > 0:
        return True
    if digest_hint.get("latest_digest_at"):
        return True
    if alert_compact is not None:
        return True
    if escalation.get("available"):
        return True
    return False


def _pick_top_suggested_command(
    *,
    digest_regeneration_recommended: bool,
    visual_review_regeneration_recommended: bool,
    review_export_recommended: bool,
    review_session_recommended: bool,
    session_available: bool,
    export_stale: bool,
) -> Optional[str]:
    if digest_regeneration_recommended:
        return SUGGESTED_SCHEDULED_REVIEW_EXPORT_COMMAND
    if not session_available and review_session_recommended:
        return SUGGESTED_INITIAL_SESSION_COMMAND
    if session_available and (review_export_recommended or export_stale):
        return SUGGESTED_EXPORT_COMMAND
    if review_session_recommended and session_available:
        return SUGGESTED_ATTENTION_SESSION_COMMAND
    if visual_review_regeneration_recommended:
        return SUGGESTED_VISUAL_REVIEW_COMMAND
    return None


def _top_recommended_action(
    *,
    status_level: str,
    digest_regeneration_recommended: bool,
    visual_review_regeneration_recommended: bool,
    review_export_recommended: bool,
    review_session_recommended: bool,
    session_available: bool,
) -> str:
    if status_level == STATUS_UNKNOWN:
        return "Collect more local review evidence before relying on consolidated status."
    if digest_regeneration_recommended:
        return (
            "Regenerate proof bundle digest/checklist and scheduled review export "
            "(local review only)."
        )
    if visual_review_regeneration_recommended:
        return (
            "Regenerate MRMS visual review manifest from existing local artifacts "
            "(local visual review only)."
        )
    if review_export_recommended:
        return "Export the latest review session summary (local review only)."
    if review_session_recommended and not session_available:
        return "Create an initial local review session with export-after-create."
    if review_session_recommended:
        return "Create a new local review session with export-after-create."
    if status_level == STATUS_URGENT:
        return "Address urgent local review signals before sign-off or production promotion."
    if status_level == STATUS_ATTENTION:
        return "Review open local attention items and follow suggested commands."
    if status_level == STATUS_WATCH:
        return "Monitor local review evidence trends; no mandatory action yet."
    return "No local review actions recommended."


def _compute_status_level(
    *,
    has_data: bool,
    escalation_level: str,
    alert_status: Optional[str],
    export_trend_value: str,
    current_mixed_or_worsened_streak: int,
    digest_regeneration_recommended: bool,
    visual_review_regeneration_recommended: bool,
    visual_review_stale: bool,
    visual_review_missing_artifact_count: int,
    visual_review_available: bool,
    visual_review_comparison_status: Optional[str],
    review_export_recommended: bool,
    review_session_recommended: bool,
    latest_export_diff_status: Optional[str],
    open_attention_count: int,
    export_diff_history_count: int,
) -> tuple[str, str]:
    if (
        not has_data
        and visual_review_regeneration_recommended
        and visual_review_stale
    ):
        return STATUS_ATTENTION, "visual_review_regeneration_recommended"
    if not has_data:
        return STATUS_UNKNOWN, "insufficient_local_review_evidence"

    if escalation_level == ESCALATION_URGENT:
        return STATUS_URGENT, "proof_bundle_diff_escalation_urgent"
    if alert_status == ALERT_FAILED:
        return STATUS_URGENT, "validation_alert_failed"
    if (
        export_trend_value == TREND_WORSENING
        and current_mixed_or_worsened_streak >= 2
    ):
        return STATUS_URGENT, "export_diff_trend_worsening_streak"

    if digest_regeneration_recommended:
        return STATUS_ATTENTION, "digest_regeneration_recommended"
    if visual_review_regeneration_recommended and (
        visual_review_missing_artifact_count > 0
        or (visual_review_stale and visual_review_available)
    ):
        return STATUS_ATTENTION, "visual_review_regeneration_recommended"
    if review_export_recommended:
        return STATUS_ATTENTION, "review_export_regeneration_recommended"
    if latest_export_diff_status in (DIFF_WORSENED, DIFF_MIXED):
        return STATUS_ATTENTION, f"latest_export_diff_{latest_export_diff_status}"
    if review_session_recommended:
        return STATUS_ATTENTION, "review_session_recommended"
    if open_attention_count > 0:
        return STATUS_ATTENTION, "open_review_attention_items"

    if (
        export_trend_value in (TREND_MIXED, TREND_STABLE)
        and export_diff_history_count > 0
    ):
        return STATUS_WATCH, "export_diff_trend_monitoring"
    if visual_review_available and visual_review_comparison_status in (
        DIFF_MIXED,
        DIFF_UNKNOWN,
    ):
        return STATUS_WATCH, "visual_review_comparison_mixed_or_unknown"
    if escalation_level == ESCALATION_WATCH:
        return STATUS_WATCH, "proof_bundle_diff_escalation_watch"
    if alert_status == ALERT_WARNING:
        return STATUS_WATCH, "validation_alert_warning"

    if export_trend_value in (TREND_STABLE, TREND_IMPROVING):
        return STATUS_OK, "local_review_evidence_stable"
    if not (
        digest_regeneration_recommended
        or visual_review_regeneration_recommended
        or review_export_recommended
        or review_session_recommended
    ):
        return STATUS_OK, "no_local_review_actions_recommended"

    return STATUS_UNKNOWN, "local_review_status_ambiguous"


def build_operator_review_status(storage: LocalStorage) -> dict[str, Any]:
    """Consolidate local review hints into one operator-facing status block."""
    alert = load_validation_alert(storage)
    alert_compact = compact_validation_alert(alert)
    escalation = compact_proof_bundle_diff_escalation(storage)
    proof_alert_trend = compact_proof_bundle_diff_alert_trend(storage)
    digest_hint = build_digest_regeneration_hint(storage)
    session_summary = compact_latest_review_session_summary(storage)
    export_summary = compact_review_session_export_summary(storage)
    export_diff = compact_review_session_export_diff_summary(storage)
    export_diff_trend = compact_review_session_export_diff_trend(storage)
    trend_hint = build_review_session_export_diff_trend_hint(storage)
    export_diff_history = compact_review_session_export_diff_history_summary(storage)
    review_export_hint = build_review_export_regeneration_hint(storage)
    visual_review = compact_mrms_visual_review(storage)
    visual_review_comparison = compact_visual_review_comparison_summary(storage)
    visual_review_hint = compact_visual_review_hint(storage)

    operator_guidance = compact_operator_guidance(alert)
    session_guidance = session_summary.get("open_attention_guidance") or []
    active_guidance_count = len(operator_guidance) + len(session_guidance)

    digest_regeneration_recommended = bool(digest_hint.get("digest_regeneration_recommended"))
    review_export_recommended = bool(
        review_export_hint.get("review_export_regeneration_recommended")
    )
    visual_review_regeneration_recommended = bool(
        visual_review_hint.get("visual_review_regeneration_recommended")
    )
    visual_review_hint_reason = visual_review_hint.get("reason")
    visual_review_stale = bool(visual_review_hint.get("stale_visual_review"))
    visual_review_available = bool(visual_review.get("available"))
    visual_review_artifact_count = (
        int(visual_review.get("artifact_count", 0)) if visual_review_available else None
    )
    visual_review_missing_artifact_count = (
        int(visual_review.get("missing_artifact_count", 0)) if visual_review_available else None
    )
    latest_visual_review_comparison_status = (
        visual_review_comparison.get("overall_visual_review_diff_status")
        if visual_review_comparison.get("available")
        else None
    )
    session_available = bool(session_summary.get("available"))
    review_session_recommended = (not session_available) or _session_trend_recommends_review(
        trend_hint
    )

    export_trend_value = str(export_diff_trend.get("trend") or TREND_NO_DATA)
    current_mixed_or_worsened_streak = int(
        export_diff_trend.get("current_mixed_or_worsened_streak", 0)
    )
    latest_export_diff_status = export_diff.get("overall_export_diff_status")
    latest_export_diff_trend = export_trend_value if export_diff_trend.get("available") else None
    open_attention_count = int(session_summary.get("open_attention_count", 0))
    export_diff_history_count = int(export_diff_history.get("count", 0))

    has_data = _has_sufficient_data(
        session_summary=session_summary,
        export_summary=export_summary,
        export_diff_history=export_diff_history,
        digest_hint=digest_hint,
        alert_compact=alert_compact,
        escalation=escalation,
    ) or visual_review_available

    escalation_level = str(escalation.get("escalation_level") or "none")
    alert_status = (alert_compact or {}).get("status")

    status_level, status_reason = _compute_status_level(
        has_data=has_data,
        escalation_level=escalation_level,
        alert_status=alert_status,
        export_trend_value=export_trend_value,
        current_mixed_or_worsened_streak=current_mixed_or_worsened_streak,
        digest_regeneration_recommended=digest_regeneration_recommended,
        visual_review_regeneration_recommended=visual_review_regeneration_recommended,
        visual_review_stale=visual_review_stale,
        visual_review_missing_artifact_count=int(
            visual_review.get("missing_artifact_count", 0)
        ),
        visual_review_available=visual_review_available,
        visual_review_comparison_status=latest_visual_review_comparison_status,
        review_export_recommended=review_export_recommended,
        review_session_recommended=review_session_recommended,
        latest_export_diff_status=latest_export_diff_status,
        open_attention_count=open_attention_count,
        export_diff_history_count=export_diff_history_count,
    )

    export_stale = bool(trend_hint.get("export_is_stale"))
    top_suggested_command = _pick_top_suggested_command(
        digest_regeneration_recommended=digest_regeneration_recommended,
        visual_review_regeneration_recommended=visual_review_regeneration_recommended,
        review_export_recommended=review_export_recommended,
        review_session_recommended=review_session_recommended,
        session_available=session_available,
        export_stale=export_stale,
    )
    top_recommended_action = _top_recommended_action(
        status_level=status_level,
        digest_regeneration_recommended=digest_regeneration_recommended,
        visual_review_regeneration_recommended=visual_review_regeneration_recommended,
        review_export_recommended=review_export_recommended,
        review_session_recommended=review_session_recommended,
        session_available=session_available,
    )

    evidence_trend = (
        EVIDENCE_UNKNOWN
        if not has_data
        else _resolve_evidence_trend(export_diff_trend, proof_alert_trend)
    )

    return _attach_guidance_fields(
        {
            "created_at": _utc_now_iso(),
            "status_level": status_level,
            "status_reason": status_reason,
            "top_recommended_action": top_recommended_action,
            "top_suggested_command": top_suggested_command,
            "review_session_recommended": review_session_recommended,
            "review_export_recommended": review_export_recommended,
            "digest_regeneration_recommended": digest_regeneration_recommended,
            "visual_review_regeneration_recommended": visual_review_regeneration_recommended,
            "visual_review_hint_reason": visual_review_hint_reason,
            "evidence_trend": evidence_trend,
            "latest_review_session_at": session_summary.get("created_at"),
            "latest_review_export_at": export_summary.get("created_at"),
            "latest_digest_at": digest_hint.get("latest_digest_at"),
            "latest_visual_review_at": visual_review.get("created_at")
            if visual_review_available
            else None,
            "latest_visual_review_path": visual_review.get("json_path")
            if visual_review_available
            else None,
            "latest_visual_review_json_path": visual_review.get("json_path")
            if visual_review_available
            else None,
            "latest_visual_review_markdown_path": visual_review.get("markdown_path")
            if visual_review_available
            else None,
            "latest_visual_review_comparison_status": latest_visual_review_comparison_status,
            "visual_review_artifact_count": visual_review_artifact_count,
            "visual_review_missing_artifact_count": visual_review_missing_artifact_count,
            "latest_export_diff_status": latest_export_diff_status,
            "latest_export_diff_trend": latest_export_diff_trend,
            "open_attention_count": open_attention_count if session_available else None,
            "active_guidance_count": active_guidance_count,
            "verified_mrms": False,
            "local_status_only": True,
            "does_not_clear_alerts": True,
            "does_not_enable_production": True,
            "no_external_notifications": True,
            "prototype": True,
        }
    )


def compact_scheduled_operator_status(
    scheduled: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    """Compact operator status step from the latest scheduled validation report."""
    if scheduled is None:
        return None
    return {
        "operator_status_requested": bool(scheduled.get("operator_status_requested")),
        "operator_status_generated": bool(scheduled.get("operator_status_generated")),
        "operator_status_level": scheduled.get("operator_status_level"),
        "operator_status_reason": scheduled.get("operator_status_reason"),
        "operator_status_top_recommended_action": scheduled.get(
            "operator_status_top_recommended_action"
        ),
        "operator_status_top_suggested_command": scheduled.get(
            "operator_status_top_suggested_command"
        ),
        "operator_status_evidence_trend": scheduled.get("operator_status_evidence_trend"),
        "operator_status_elapsed_seconds": scheduled.get("operator_status_elapsed_seconds"),
        "operator_status_error": scheduled.get("operator_status_error"),
        "verified_mrms": False,
        "local_status_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def compact_operator_review_status(storage: LocalStorage) -> dict[str, Any]:
    status = build_operator_review_status(storage)
    scheduled = load_latest_scheduled_validation_report(storage)
    return {
        "available": True,
        **status,
        "scheduled_visual_review": compact_scheduled_visual_review(scheduled),
    }


def build_operator_review_status_payload(storage: LocalStorage) -> dict[str, Any]:
    status = compact_operator_review_status(storage)
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_status_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "status": status,
    }
