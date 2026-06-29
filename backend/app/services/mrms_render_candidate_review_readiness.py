"""Local candidate trend-hint review chain readiness — does NOT clear alerts or verify MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_proof_bundle_diff import DIFF_MIXED, DIFF_WORSENED
from backend.app.services.mrms_render_candidate_preflight import (
    PREFLIGHT_BLOCKED,
    PREFLIGHT_CANDIDATE_READY,
    SUGGESTED_PREFLIGHT_COMMAND,
    compact_render_candidate_preflight,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint import (
    compact_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint as compact_candidate_trend_hints,
)
from backend.app.services.mrms_render_candidate_trend_hint_ack_status import (
    ROLLUP_BLOCKED,
    ROLLUP_MISSING,
    ROLLUP_NEEDS_ACKNOWLEDGMENT,
    ROLLUP_STALE,
    SUGGESTED_COMMAND as SUGGESTED_ACK_STATUS_COMMAND,
    compact_trend_hint_ack_status,
)
from backend.app.services.mrms_render_candidate_trend_hint_ack_status_history import (
    compact_trend_hint_ack_status_history,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_acknowledgment import (
    SUGGESTED_COMMAND as SUGGESTED_REVIEW_ACK_COMMAND,
    compact_trend_hint_review_acknowledgment_summary,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest import (
    DIGEST_BLOCKED,
    DIGEST_MISSING,
    DIGEST_NEEDS_ATTENTION,
    SUGGESTED_COMMAND as SUGGESTED_DIGEST_COMMAND,
    compact_trend_hint_review_digest,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest_diff import (
    compact_trend_hint_review_digest_diff,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest_history import (
    compact_trend_hint_review_digest_history,
)
from backend.app.services.storage import LocalStorage

READINESS_JSON = "dev/mrms_render_candidate_review_readiness.json"
READINESS_MD = "dev/mrms_render_candidate_review_readiness.md"

SUGGESTED_COMMAND = "make mrms-render-candidate-review-readiness"

CHAIN_BLOCKED = "blocked"
CHAIN_NEEDS_REVIEW = "needs_review"
CHAIN_READY = "chain_ready"

OVERALL_BLOCKED = "blocked"
OVERALL_NEEDS_REVIEW = "needs_review"
OVERALL_READY_FOR_PREFLIGHT = "ready_for_preflight"
OVERALL_PREFLIGHT_CANDIDATE_READY = "preflight_candidate_ready"

NEXT_PHASE_RECOMMENDATION = (
    "Phase 88 — gated real MRMS render candidate preflight attempt "
    "(only when review chain and visual evidence are ready; does not verify MRMS or enable production)"
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_readiness_summary_only": True,
        "advisory_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "does_not_download_or_decode": True,
        "does_not_create_production_tiles": True,
        "does_not_serve_production_tiles": True,
        "does_not_delete_by_default": True,
        "binary_artifacts_included": False,
        "no_external_notifications": True,
        "does_not_authorize_production_use": True,
        "gated_preflight_ready_is_not_production_authorization": True,
        "prototype": True,
    }


def _current_safety_state() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "enable_production_radar_tiles": settings.enable_production_radar_tiles,
        "enable_decoded_tiles": settings.enable_decoded_tiles,
        "placeholder_default": not settings.enable_production_radar_tiles
        and not settings.enable_decoded_tiles,
        "production_tile_serving_enabled": settings.enable_production_radar_tiles,
    }


def _readiness_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(READINESS_JSON)


def _readiness_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(READINESS_MD)


def build_review_regeneration_hint(storage: LocalStorage) -> dict[str, Any]:
    digest = compact_trend_hint_review_digest(storage)
    diff = compact_trend_hint_review_digest_diff(storage)
    digest_status = digest.get("digest_status")
    diff_status = diff.get("diff_status")

    recommended = False
    reason: Optional[str] = None
    suggested_command: Optional[str] = None

    if diff_status in {DIFF_WORSENED, DIFF_MIXED}:
        recommended = True
        reason = f"digest_diff_{diff_status}"
        suggested_command = f"{SUGGESTED_DIGEST_COMMAND} --refresh"
    elif not digest.get("available"):
        recommended = True
        reason = "digest_not_persisted"
        suggested_command = f"{SUGGESTED_DIGEST_COMMAND} --refresh"
    elif digest_status == DIGEST_BLOCKED:
        recommended = True
        reason = "digest_blocked"
        suggested_command = f"{SUGGESTED_DIGEST_COMMAND} --refresh"
    elif digest_status == DIGEST_MISSING:
        recommended = True
        reason = "digest_missing"
        suggested_command = f"{SUGGESTED_DIGEST_COMMAND} --refresh"
    elif digest_status == DIGEST_NEEDS_ATTENTION:
        recommended = True
        reason = "digest_needs_attention"
        suggested_command = f"{SUGGESTED_DIGEST_COMMAND} --refresh"
    elif digest.get("stale_acknowledgment"):
        recommended = True
        reason = "stale_acknowledgment"
        suggested_command = f"{SUGGESTED_ACK_STATUS_COMMAND} --refresh"

    return {
        "regeneration_recommended": recommended,
        "reason": reason,
        "suggested_command": suggested_command,
        "digest_status": digest_status,
        "digest_diff_status": diff_status,
        "digest_available": bool(digest.get("available")),
        **_safety_fields(),
    }


def gather_review_chain_evidence(storage: LocalStorage) -> dict[str, Any]:
    return {
        "safety_state": _current_safety_state(),
        "trend_hints": compact_candidate_trend_hints(storage),
        "review_acknowledgments": compact_trend_hint_review_acknowledgment_summary(storage),
        "ack_status_rollup": compact_trend_hint_ack_status(storage),
        "ack_status_history": compact_trend_hint_ack_status_history(storage),
        "review_digest": compact_trend_hint_review_digest(storage),
        "review_digest_history": compact_trend_hint_review_digest_history(storage),
        "review_digest_diff": compact_trend_hint_review_digest_diff(storage),
        "regeneration_hint": build_review_regeneration_hint(storage),
        "preflight": compact_render_candidate_preflight(storage),
    }


def _suggested_commands_for_evidence(
    evidence: dict[str, Any],
    *,
    blockers: list[str],
    warnings: list[str],
) -> list[str]:
    commands: list[str] = []
    regen = evidence.get("regeneration_hint") or {}
    if regen.get("suggested_command"):
        commands.append(str(regen["suggested_command"]))

    ack_rollup = evidence.get("ack_status_rollup") or {}
    if ack_rollup.get("rollup_status") == ROLLUP_MISSING:
        commands.append(f"{SUGGESTED_ACK_STATUS_COMMAND} --refresh")

    review_ack = evidence.get("review_acknowledgments") or {}
    if review_ack.get("trend_review_still_recommended") and not review_ack.get("available"):
        commands.append(f"{SUGGESTED_REVIEW_ACK_COMMAND}")

    trend_hints = evidence.get("trend_hints") or {}
    if trend_hints.get("suggested_command") and (blockers or warnings):
        cmd = str(trend_hints["suggested_command"])
        if cmd not in commands:
            commands.append(cmd)

    digest = evidence.get("review_digest") or {}
    if digest.get("digest_status") in {DIGEST_MISSING, DIGEST_BLOCKED, DIGEST_NEEDS_ATTENTION}:
        cmd = f"{SUGGESTED_DIGEST_COMMAND} --refresh"
        if cmd not in commands:
            commands.append(cmd)

    if not commands and not blockers:
        commands.append(f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh")
    return commands


def evaluate_candidate_review_readiness(evidence: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    safety = evidence.get("safety_state") or {}
    if safety.get("verified_mrms"):
        blockers.append("verified_mrms must remain false for local review")
    if safety.get("enable_production_radar_tiles"):
        blockers.append("production rendering must remain disabled for local review")
    if not safety.get("placeholder_default"):
        blockers.append("placeholder tile serving must remain the default")

    trend_hints = evidence.get("trend_hints") or {}
    for item in trend_hints.get("blockers") or []:
        blockers.append(f"trend hint blocker: {item}")
    for item in trend_hints.get("warnings") or []:
        warnings.append(f"trend hint warning: {item}")
    if trend_hints.get("trend_review_recommended"):
        warnings.append("candidate trend hints still recommend review")

    ack_rollup = evidence.get("ack_status_rollup") or {}
    rollup_status = ack_rollup.get("rollup_status")
    if rollup_status == ROLLUP_BLOCKED:
        blockers.append("acknowledgment status rollup is blocked")
    elif rollup_status == ROLLUP_MISSING:
        blockers.append("acknowledgment status rollup is missing")
    elif rollup_status in {ROLLUP_NEEDS_ACKNOWLEDGMENT, ROLLUP_STALE}:
        warnings.append(f"acknowledgment rollup status is {rollup_status}")

    review_ack = evidence.get("review_acknowledgments") or {}
    if review_ack.get("trend_review_still_recommended") and not review_ack.get("available"):
        warnings.append("trend review recommended but no review acknowledgment recorded")

    digest = evidence.get("review_digest") or {}
    digest_status = digest.get("digest_status")
    if digest_status == DIGEST_BLOCKED:
        blockers.append("review digest is blocked")
    elif digest_status == DIGEST_MISSING:
        blockers.append("review digest is missing")
    elif digest_status == DIGEST_NEEDS_ATTENTION:
        warnings.append("review digest needs attention")

    regen = evidence.get("regeneration_hint") or {}
    if regen.get("regeneration_recommended"):
        warnings.append(f"digest refresh recommended ({regen.get('reason')})")

    diff = evidence.get("review_digest_diff") or {}
    diff_status = diff.get("diff_status")
    if diff_status in {DIFF_WORSENED, DIFF_MIXED}:
        warnings.append(f"review digest diff is {diff_status}")

    if blockers:
        chain_level = CHAIN_BLOCKED
    elif warnings:
        chain_level = CHAIN_NEEDS_REVIEW
    else:
        chain_level = CHAIN_READY

    preflight = evidence.get("preflight") or {}
    preflight_level = preflight.get("preflight_level")
    preflight_blocked = preflight_level == PREFLIGHT_BLOCKED
    preflight_candidate_ready = preflight_level == PREFLIGHT_CANDIDATE_READY

    suggested_commands = _suggested_commands_for_evidence(
        evidence,
        blockers=blockers,
        warnings=warnings,
    )

    if chain_level == CHAIN_BLOCKED:
        overall_level = OVERALL_BLOCKED
        next_operator_step = blockers[0]
    elif chain_level == CHAIN_NEEDS_REVIEW:
        overall_level = OVERALL_NEEDS_REVIEW
        next_operator_step = warnings[0] if warnings else "complete review chain follow-up"
    elif preflight_candidate_ready:
        overall_level = OVERALL_PREFLIGHT_CANDIDATE_READY
        next_operator_step = (
            "Preflight candidate_ready — consider dry-run plan (still not production authorization)"
        )
        suggested_commands = ["make mrms-render-candidate-dry-run-plan --refresh"]
    elif preflight_blocked or not preflight.get("available"):
        overall_level = OVERALL_READY_FOR_PREFLIGHT
        next_operator_step = "Review chain ready — run gated real MRMS candidate preflight checklist"
        suggested_commands = [f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh"]
    else:
        overall_level = OVERALL_READY_FOR_PREFLIGHT
        next_operator_step = "Review chain ready — run gated real MRMS candidate preflight checklist"
        suggested_commands = [f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh"]

    return {
        "computed_at": _utc_now(),
        "chain_readiness_level": chain_level,
        "overall_readiness_level": overall_level,
        "review_chain_ready": chain_level == CHAIN_READY,
        "preflight_blocked": preflight_blocked,
        "preflight_candidate_ready": preflight_candidate_ready,
        "gated_preflight_still_blocked": chain_level != CHAIN_READY or preflight_blocked,
        "blocking_items": blockers,
        "warnings": warnings,
        "next_operator_step": next_operator_step,
        "suggested_commands": suggested_commands,
        "regeneration_hint": regen,
        "evidence": evidence,
        "json_path": None,
        "markdown_path": None,
        "suggested_command": SUGGESTED_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_readiness_markdown(report: dict[str, Any]) -> str:
    evidence = report.get("evidence") or {}
    lines = [
        "# Candidate trend-hint review readiness",
        "",
        "> **WARNING:** Local review readiness summary only. Advisory metadata — does **NOT** "
        "verify MRMS, enable production rendering, clear alerts, or authorize production use.",
        "",
        f"- Computed at: {report.get('computed_at')}",
        f"- Chain readiness: {report.get('chain_readiness_level')}",
        f"- Overall readiness: {report.get('overall_readiness_level')}",
        f"- Review chain ready: {report.get('review_chain_ready')}",
        f"- Gated preflight still blocked: {report.get('gated_preflight_still_blocked')}",
        f"- Next operator step: {report.get('next_operator_step')}",
        "",
        "## Regeneration hint",
        "",
        f"- Recommended: {(report.get('regeneration_hint') or {}).get('regeneration_recommended')}",
        f"- Reason: {(report.get('regeneration_hint') or {}).get('reason') or '—'}",
        "",
        "## Chain evidence",
        "",
        f"- Trend hints: {(evidence.get('trend_hints') or {}).get('hint_status') or '—'}",
        f"- Review acknowledgments: {(evidence.get('review_acknowledgments') or {}).get('count', 0)}",
        f"- Ack rollup: {(evidence.get('ack_status_rollup') or {}).get('rollup_status') or '—'}",
        f"- Review digest: {(evidence.get('review_digest') or {}).get('digest_status') or '—'}",
        f"- Digest diff: {(evidence.get('review_digest_diff') or {}).get('diff_status') or '—'}",
        f"- Preflight: {(evidence.get('preflight') or {}).get('preflight_level') or '—'}",
        "",
        "## Blocking items",
        "",
    ]
    for item in report.get("blocking_items") or []:
        lines.append(f"- {item}")
    if not report.get("blocking_items"):
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    for item in report.get("warnings") or []:
        lines.append(f"- {item}")
    if not report.get("warnings"):
        lines.append("- none")
    lines.extend(["", "## Suggested commands", ""])
    for cmd in report.get("suggested_commands") or []:
        lines.append(f"- `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def save_candidate_review_readiness(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
    json_path = _readiness_json_path(storage)
    md_path = _readiness_md_path(storage)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    report = {
        **report,
        "json_path": json_path,
        "markdown_path": md_path,
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(
        build_readiness_markdown(report),
        encoding="utf-8",
    )
    return report


def load_candidate_review_readiness(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_readiness_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def generate_candidate_review_readiness(storage: LocalStorage) -> dict[str, Any]:
    evidence = gather_review_chain_evidence(storage)
    report = evaluate_candidate_review_readiness(evidence)
    return save_candidate_review_readiness(storage, report)


def compact_candidate_review_readiness(storage: LocalStorage) -> dict[str, Any]:
    latest = load_candidate_review_readiness(storage)
    if latest is None:
        evidence = gather_review_chain_evidence(storage)
        evaluated = evaluate_candidate_review_readiness(evidence)
        regen = evaluated.get("regeneration_hint") or {}
        return {
            "available": False,
            "chain_readiness_level": evaluated.get("chain_readiness_level"),
            "overall_readiness_level": evaluated.get("overall_readiness_level"),
            "review_chain_ready": evaluated.get("review_chain_ready"),
            "preflight_blocked": evaluated.get("preflight_blocked"),
            "preflight_candidate_ready": evaluated.get("preflight_candidate_ready"),
            "gated_preflight_still_blocked": evaluated.get("gated_preflight_still_blocked"),
            "blocking_items": evaluated.get("blocking_items") or [],
            "warnings": evaluated.get("warnings") or [],
            "next_operator_step": evaluated.get("next_operator_step"),
            "suggested_commands": evaluated.get("suggested_commands") or [],
            "regeneration_recommended": bool(regen.get("regeneration_recommended")),
            "regeneration_reason": regen.get("reason"),
            "regeneration_suggested_command": regen.get("suggested_command"),
            "computed_at": evaluated.get("computed_at"),
            "json_path": _readiness_json_path(storage),
            "markdown_path": _readiness_md_path(storage),
            "suggested_command": SUGGESTED_COMMAND,
            "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
            **_safety_fields(),
        }
    regen = latest.get("regeneration_hint") or {}
    return {
        "available": True,
        "chain_readiness_level": latest.get("chain_readiness_level"),
        "overall_readiness_level": latest.get("overall_readiness_level"),
        "review_chain_ready": latest.get("review_chain_ready"),
        "preflight_blocked": latest.get("preflight_blocked"),
        "preflight_candidate_ready": latest.get("preflight_candidate_ready"),
        "gated_preflight_still_blocked": latest.get("gated_preflight_still_blocked"),
        "blocking_items": latest.get("blocking_items") or [],
        "warnings": latest.get("warnings") or [],
        "next_operator_step": latest.get("next_operator_step"),
        "suggested_commands": latest.get("suggested_commands") or [],
        "regeneration_recommended": bool(regen.get("regeneration_recommended")),
        "regeneration_reason": regen.get("reason"),
        "regeneration_suggested_command": regen.get("suggested_command"),
        "computed_at": latest.get("computed_at"),
        "json_path": latest.get("json_path") or _readiness_json_path(storage),
        "markdown_path": latest.get("markdown_path") or _readiness_md_path(storage),
        "suggested_command": SUGGESTED_COMMAND,
        "next_phase_recommendation": latest.get("next_phase_recommendation") or NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_candidate_review_readiness_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_candidate_review_readiness(storage)
    if latest is None:
        evidence = gather_review_chain_evidence(storage)
        latest = evaluate_candidate_review_readiness(evidence)
    return {
        **_safety_fields(),
        "latest": latest,
        "compact": compact_candidate_review_readiness(storage),
    }
