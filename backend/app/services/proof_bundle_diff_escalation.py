"""Proof bundle diff alert escalation hints — local guidance only, not verified MRMS."""

from __future__ import annotations

from typing import Any, Optional

from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_MIXED,
    DIFF_UNCHANGED,
    DIFF_WORSENED,
    proof_bundle_diff_requires_attention,
)
from backend.app.services.operator_guidance import RUNBOOK_PATH, _guidance_item
from backend.app.services.proof_bundle_diff_acknowledgment import load_latest_diff_acknowledgment
from backend.app.services.proof_bundle_diff_alert_history import (
    load_latest_proof_bundle_diff_alert_history,
    load_proof_bundle_diff_alert_history,
)
from backend.app.services.proof_bundle_diff_alert_trends import (
    TREND_NO_DATA,
    TREND_STABLE,
    build_proof_bundle_diff_alert_trend,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import (
    CAUSE_PROOF_BUNDLE_DIFF_WORSENED,
    SUGGESTED_ACTIONS,
)

ESCALATION_NONE = "none"
ESCALATION_WATCH = "watch"
ESCALATION_ATTENTION = "attention"
ESCALATION_URGENT = "urgent"

ACK_NONE = "none"
ACK_CURRENT = "current"
ACK_STALE = "stale"
ACK_NOT_NEEDED = "not_needed"


def _latest_attention_entry(entries: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    for entry in entries:
        if entry.get("operator_attention_needed"):
            return entry
    return None


def _attention_streak(entries: list[dict[str, Any]]) -> int:
    count = 0
    for entry in entries:
        if entry.get("operator_attention_needed"):
            count += 1
        else:
            break
    return count


def _iso_before(left: Optional[str], right: Optional[str]) -> bool:
    if not left or not right:
        return False
    return str(left) < str(right)


def _classify_acknowledgment_status(
    *,
    latest_ack: Optional[dict[str, Any]],
    latest_attention: Optional[dict[str, Any]],
    latest_entry: Optional[dict[str, Any]],
    attention_streak: int,
) -> tuple[str, bool]:
    if attention_streak == 0:
        return ACK_NOT_NEEDED, False
    if latest_ack is None:
        return ACK_NONE, False

    ack_at = latest_ack.get("created_at")
    attention_at = (latest_attention or {}).get("created_at")
    latest_at = (latest_entry or {}).get("created_at")

    stale = False
    if attention_at and ack_at and _iso_before(ack_at, attention_at):
        stale = True
    if (
        latest_entry
        and latest_entry.get("operator_attention_needed")
        and ack_at
        and latest_at
        and _iso_before(ack_at, latest_at)
    ):
        stale = True

    if not stale and attention_at and ack_at and not _iso_before(ack_at, attention_at):
        return ACK_CURRENT, False
    if stale:
        return ACK_STALE, True
    return ACK_STALE, True


def _classify_escalation_level(
    *,
    trend: str,
    latest_status: Optional[str],
    attention_streak: int,
    acknowledgment_status: str,
) -> str:
    if trend == TREND_NO_DATA or not latest_status:
        return ESCALATION_NONE

    needs_attention = proof_bundle_diff_requires_attention(str(latest_status))
    if not needs_attention and attention_streak == 0:
        if trend in (TREND_STABLE,) or latest_status == DIFF_UNCHANGED:
            return ESCALATION_NONE

    has_current_ack = acknowledgment_status == ACK_CURRENT

    if attention_streak >= 3 and not has_current_ack:
        return ESCALATION_URGENT
    if attention_streak >= 2:
        return ESCALATION_ATTENTION
    if needs_attention or latest_status in (DIFF_WORSENED, DIFF_MIXED) or attention_streak >= 1:
        return ESCALATION_WATCH
    return ESCALATION_NONE


def _reason_for_escalation(
    *,
    escalation_level: str,
    latest_status: Optional[str],
    attention_streak: int,
    acknowledgment_status: str,
    stale_acknowledgment: bool,
) -> str:
    if escalation_level == ESCALATION_NONE:
        return "No diff alert escalation — stable or no attention-needed history."
    if escalation_level == ESCALATION_URGENT:
        return (
            f"Urgent: {attention_streak} consecutive attention-needed diff alerts "
            f"(latest {latest_status}) without current acknowledgment."
        )
    if escalation_level == ESCALATION_ATTENTION:
        return (
            f"Attention: {attention_streak} consecutive worsened/mixed diff alerts "
            f"(latest {latest_status})."
        )
    if stale_acknowledgment:
        return (
            f"Watch: latest acknowledgment is stale relative to diff alert "
            f"(status {latest_status}, streak {attention_streak})."
        )
    if acknowledgment_status == ACK_NONE:
        return f"Watch: {latest_status} diff alert with no acknowledgment recorded yet."
    return f"Watch: diff alert trend warrants operator review (latest {latest_status})."


def _suggested_action_for_escalation(
    *,
    escalation_level: str,
    latest_status: Optional[str],
    stale_acknowledgment: bool,
) -> str:
    if escalation_level == ESCALATION_NONE:
        return "Continue monitoring proof bundle diff alert history — local guidance only."
    if escalation_level == ESCALATION_URGENT:
        return (
            "Urgent local review: compare bundle evidence, refresh acknowledgment with notes, "
            "run make proof-bundle-diff-escalation — does NOT verify MRMS or clear alerts."
        )
    if escalation_level == ESCALATION_ATTENTION:
        return (
            "Review worsened/mixed streak in diff alert timeline; "
            "re-run make scheduled-proof-bundle after fixes — does not clear alerts."
        )
    if stale_acknowledgment:
        return (
            "Submit a new local acknowledgment after reviewing latest worsened/mixed diff — "
            "acknowledgment does not clear alerts."
        )
    if latest_status == DIFF_MIXED:
        return (
            "Review mixed diff evidence changes; see runbook mixed section — "
            "local monitoring only."
        )
    return SUGGESTED_ACTIONS.get(
        CAUSE_PROOF_BUNDLE_DIFF_WORSENED,
        "Review make mrms-proof-bundle-diff and compare bundle evidence.",
    )


def _guidance_for_escalation(
    *,
    escalation_level: str,
    latest_status: Optional[str],
    stale_acknowledgment: bool,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    status = str(latest_status or "")
    if status == DIFF_MIXED:
        items.append(_guidance_item("proof_bundle_diff_mixed", diff_status=DIFF_MIXED))
    elif status == DIFF_WORSENED or escalation_level != ESCALATION_NONE:
        items.append(_guidance_item("proof_bundle_diff_worsened", diff_status=DIFF_WORSENED))

    if escalation_level in (ESCALATION_WATCH, ESCALATION_ATTENTION, ESCALATION_URGENT):
        items.append(
            {
                "title": f"Diff alert escalation ({escalation_level})",
                "path": RUNBOOK_PATH,
                "anchor": f"proof-bundle-diff-escalation-{escalation_level}",
                "section_label": f"Escalation level: {escalation_level}",
                "cause": f"proof_bundle_diff_escalation_{escalation_level}",
                "suggested_action": _suggested_action_for_escalation(
                    escalation_level=escalation_level,
                    latest_status=latest_status,
                    stale_acknowledgment=stale_acknowledgment,
                ),
                "verified_mrms": False,
                "local_guidance_only": True,
                "prototype": True,
            }
        )

    if stale_acknowledgment:
        items.append(
            {
                "title": "Stale diff alert acknowledgment",
                "path": RUNBOOK_PATH,
                "anchor": "proof-bundle-diff-stale-acknowledgment",
                "section_label": "Stale acknowledgment",
                "cause": "proof_bundle_diff_stale_acknowledgment",
                "suggested_action": (
                    "Re-acknowledge after reviewing latest worsened/mixed diff — "
                    "does not clear alerts."
                ),
                "verified_mrms": False,
                "local_guidance_only": True,
                "prototype": True,
            }
        )

    if escalation_level != ESCALATION_NONE:
        items.append(_guidance_item("verified_mrms_criteria"))
        items.append(_guidance_item("before_signoff"))

    return items[:8]


def build_proof_bundle_diff_escalation(storage: LocalStorage) -> dict[str, Any]:
    """Build escalation hint from trend, history, and acknowledgment state."""
    entries = load_proof_bundle_diff_alert_history(storage)
    trend_summary = build_proof_bundle_diff_alert_trend(storage)
    latest_ack = load_latest_diff_acknowledgment(storage)
    latest_history = load_latest_proof_bundle_diff_alert_history(storage)

    latest_status = trend_summary.get("latest_status") or (latest_history or {}).get("diff_status")
    attention_streak = _attention_streak(entries)
    latest_attention = _latest_attention_entry(entries)
    latest_entry = entries[0] if entries else None

    acknowledgment_status, stale_acknowledgment = _classify_acknowledgment_status(
        latest_ack=latest_ack,
        latest_attention=latest_attention,
        latest_entry=latest_entry,
        attention_streak=attention_streak,
    )

    escalation_level = _classify_escalation_level(
        trend=str(trend_summary.get("trend") or TREND_NO_DATA),
        latest_status=str(latest_status) if latest_status else None,
        attention_streak=attention_streak,
        acknowledgment_status=acknowledgment_status,
    )

    reason = _reason_for_escalation(
        escalation_level=escalation_level,
        latest_status=str(latest_status) if latest_status else None,
        attention_streak=attention_streak,
        acknowledgment_status=acknowledgment_status,
        stale_acknowledgment=stale_acknowledgment,
    )
    suggested = _suggested_action_for_escalation(
        escalation_level=escalation_level,
        latest_status=str(latest_status) if latest_status else None,
        stale_acknowledgment=stale_acknowledgment,
    )
    guidance_items = _guidance_for_escalation(
        escalation_level=escalation_level,
        latest_status=str(latest_status) if latest_status else None,
        stale_acknowledgment=stale_acknowledgment,
    )

    return {
        "escalation_level": escalation_level,
        "reason": reason,
        "latest_diff_status": latest_status,
        "current_attention_streak": attention_streak,
        "acknowledgment_status": acknowledgment_status,
        "latest_acknowledgment_at": (latest_ack or {}).get("created_at"),
        "latest_acknowledgment_operator": (latest_ack or {}).get("operator"),
        "stale_acknowledgment": stale_acknowledgment,
        "suggested_next_action": suggested,
        "guidance_items": guidance_items,
        "trend": trend_summary.get("trend"),
        "verified_mrms": False,
        "local_escalation_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def compact_proof_bundle_diff_escalation(storage: LocalStorage) -> dict[str, Any]:
    escalation = build_proof_bundle_diff_escalation(storage)
    return {
        "available": escalation.get("escalation_level") != ESCALATION_NONE,
        **escalation,
    }


def build_proof_bundle_diff_escalation_payload(storage: LocalStorage) -> dict[str, Any]:
    escalation = compact_proof_bundle_diff_escalation(storage)
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_escalation_only": True,
        "does_not_clear_alerts": True,
        "escalation": escalation,
    }
