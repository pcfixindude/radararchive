"""Resolve preflight blockers — orchestrates refreshes; does NOT verify MRMS or force preflight."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.services.mrms_render_candidate_preflight import PREFLIGHT_CANDIDATE_READY
from backend.app.services.mrms_render_candidate_preflight_attempt import (
    ATTEMPT_BLOCKED_BY_READINESS,
    ATTEMPT_RAN_CANDIDATE_READY,
    attempt_gated_preflight,
    compact_preflight_attempt,
)
from backend.app.services.mrms_render_candidate_review_readiness import (
    OVERALL_BLOCKED,
    OVERALL_NEEDS_REVIEW,
    OVERALL_PREFLIGHT_CANDIDATE_READY,
    OVERALL_READY_FOR_PREFLIGHT,
    compact_candidate_review_readiness,
    generate_candidate_review_readiness,
)
from backend.app.services.mrms_render_candidate_trend_hint_ack_status import (
    SUGGESTED_COMMAND as SUGGESTED_ACK_STATUS_COMMAND,
    compact_trend_hint_ack_status,
    refresh_trend_hint_ack_status,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_acknowledgment import (
    SUGGESTED_COMMAND as SUGGESTED_REVIEW_ACK_COMMAND,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest import (
    SUGGESTED_COMMAND as SUGGESTED_DIGEST_COMMAND,
    compact_trend_hint_review_digest,
    refresh_trend_hint_review_digest,
)
from backend.app.services.mrms_visual_review_sample_readiness import (
    READINESS_CANDIDATE_READY,
    SUGGESTED_READINESS_COMMAND,
    compact_visual_review_sample_readiness,
    refresh_visual_review_sample_readiness,
)
from backend.app.services.storage import LocalStorage

BLOCKERS_JSON = "dev/mrms_render_candidate_preflight_blockers_latest.json"
BLOCKERS_MD = "dev/mrms_render_candidate_preflight_blockers_latest.md"

SUGGESTED_COMMAND = "make mrms-resolve-preflight-blockers"

RESOLUTION_BLOCKED = "still_blocked"
RESOLUTION_PREFLIGHT_ATTEMPTED = "preflight_attempted"
RESOLUTION_PREFLIGHT_CANDIDATE_READY = "preflight_candidate_ready"

BLOCKER_CATEGORY_TREND_HINT = "candidate_trend_hint_chain"
BLOCKER_CATEGORY_REVIEW_ACK = "trend_hint_review_acknowledgment"
BLOCKER_CATEGORY_VISUAL = "visual_sample_readiness"
BLOCKER_CATEGORY_REVIEW_CHAIN = "review_chain"
BLOCKER_CATEGORY_PREFLIGHT = "preflight_evidence"

NEXT_PHASE_TREND_HINT = (
    "Phase 91 — bootstrap visual review sample set "
    "(trend-hint chain bootstrap complete; visual sample set still required)"
)
NEXT_PHASE_VISUAL = (
    "Phase 92 — complete MRMS preflight evidence "
    "(review gated preflight attempt and remaining evidence blockers)"
)
NEXT_PHASE_DRY_RUN = (
    "Phase 92 — gated render candidate dry-run plan review "
    "(evaluate dry-run plan when preflight is candidate_preflight_ready)"
)
NEXT_PHASE_PREFLIGHT_EVIDENCE = (
    "Phase 91 — complete MRMS visual review evidence "
    "(manifest, proof report, and sample readiness for preflight)"
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_blocker_report_only": True,
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


def _blockers_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(BLOCKERS_JSON)


def _blockers_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(BLOCKERS_MD)


def _commands_for_visual_blocker(reason: str) -> list[str]:
    if reason == "no_sample_set":
        return [
            "make mrms-visual-review",
            "make mrms-visual-review-sample-set",
            f"{SUGGESTED_READINESS_COMMAND} --refresh",
        ]
    if reason == "empty_sample_set":
        return ["make mrms-visual-review-sample-set", f"{SUGGESTED_READINESS_COMMAND} --refresh"]
    return [
        "make mrms-visual-review",
        "make mrms-visual-review-sample-set",
        f"{SUGGESTED_READINESS_COMMAND} --refresh",
    ]


def _commands_for_blocker_text(text: str) -> list[str]:
    lowered = text.lower()
    if "rollup" in lowered and "missing" in lowered:
        return [
            "make mrms-render-candidate-sandbox-comparison-trend-hint --refresh",
            f"{SUGGESTED_ACK_STATUS_COMMAND} --refresh",
        ]
    if "digest" in lowered and "missing" in lowered:
        return [
            f"{SUGGESTED_DIGEST_COMMAND} --refresh",
            "make mrms-render-candidate-review-readiness --refresh",
        ]
    if "acknowledgment" in lowered and "missing" in lowered:
        return [SUGGESTED_REVIEW_ACK_COMMAND, f"{SUGGESTED_ACK_STATUS_COMMAND} --refresh"]
    if "visual" in lowered or "sample" in lowered:
        return _commands_for_visual_blocker("no_sample_set")
    if "production rendering" in lowered:
        return ["# keep ENABLE_PRODUCTION_RADAR_TILES=false"]
    return [SUGGESTED_COMMAND]


def _visual_blockers_from_compact(visual: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    level = visual.get("readiness_level")
    if not visual.get("available"):
        blockers.append("visual sample readiness: no_sample_set")
    elif level and level != READINESS_CANDIDATE_READY:
        reason = visual.get("readiness_reason") or level
        blockers.append(f"visual sample readiness: {reason}")
    return blockers


def _blocker_category(
    *,
    ack: dict[str, Any],
    visual: dict[str, Any],
    readiness: dict[str, Any],
) -> str:
    if ack.get("rollup_status") == "missing":
        return BLOCKER_CATEGORY_TREND_HINT
    if ack.get("rollup_status") in {"needs_acknowledgment", "stale"}:
        return BLOCKER_CATEGORY_REVIEW_ACK
    if _visual_blockers_from_compact(visual):
        return BLOCKER_CATEGORY_VISUAL
    if readiness.get("overall_readiness_level") in {OVERALL_BLOCKED, OVERALL_NEEDS_REVIEW}:
        return BLOCKER_CATEGORY_REVIEW_CHAIN
    return BLOCKER_CATEGORY_PREFLIGHT


def _merge_next_commands(
    *,
    readiness: dict[str, Any],
    visual: dict[str, Any],
    attempt: dict[str, Any],
    remaining_blockers: list[str],
) -> list[str]:
    commands: list[str] = []
    for blocker in remaining_blockers:
        for cmd in _commands_for_blocker_text(blocker):
            if cmd not in commands:
                commands.append(cmd)
    for blocker in _visual_blockers_from_compact(visual):
        reason = blocker.split(": ", 1)[-1] if ": " in blocker else "no_sample_set"
        for cmd in _commands_for_visual_blocker(reason):
            if cmd not in commands:
                commands.append(cmd)
    for cmd in readiness.get("suggested_commands") or []:
        if cmd not in commands:
            commands.append(cmd)
    if attempt.get("attempt_status") == ATTEMPT_BLOCKED_BY_READINESS:
        for cmd in (
            "make mrms-render-candidate-review-readiness --refresh",
            "make mrms-render-candidate-preflight-attempt --refresh",
        ):
            if cmd not in commands:
                commands.append(cmd)
    if attempt.get("preflight_level") == PREFLIGHT_CANDIDATE_READY:
        commands.append("make mrms-render-candidate-dry-run-plan --refresh")
    if not commands:
        commands.append(SUGGESTED_COMMAND)
    return commands


def _next_phase_for_resolution(
    *,
    resolution_status: str,
    blocker_category: str,
) -> str:
    if resolution_status == RESOLUTION_PREFLIGHT_CANDIDATE_READY:
        return NEXT_PHASE_DRY_RUN
    if blocker_category == BLOCKER_CATEGORY_TREND_HINT:
        return NEXT_PHASE_TREND_HINT
    if blocker_category == BLOCKER_CATEGORY_VISUAL:
        return NEXT_PHASE_VISUAL
    if blocker_category == BLOCKER_CATEGORY_PREFLIGHT:
        return NEXT_PHASE_PREFLIGHT_EVIDENCE
    return NEXT_PHASE_TREND_HINT


def _resolution_status(attempt: dict[str, Any], readiness: dict[str, Any]) -> str:
    if attempt.get("attempt_status") == ATTEMPT_RAN_CANDIDATE_READY:
        return RESOLUTION_PREFLIGHT_CANDIDATE_READY
    if attempt.get("attempt_status") == ATTEMPT_BLOCKED_BY_READINESS:
        return RESOLUTION_BLOCKED
    if readiness.get("overall_readiness_level") in {
        OVERALL_READY_FOR_PREFLIGHT,
        OVERALL_PREFLIGHT_CANDIDATE_READY,
    }:
        return RESOLUTION_PREFLIGHT_ATTEMPTED
    return RESOLUTION_BLOCKED


def _step_record(step_id: str, command: str, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "command": command,
        "completed_at": _utc_now(),
        "summary": summary,
    }


def resolve_preflight_blockers(
    storage: LocalStorage,
    *,
    skip_preflight_attempt: bool = False,
) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []

    refresh_trend_hint_ack_status(storage)
    ack_compact = compact_trend_hint_ack_status(storage)
    steps.append(
        _step_record(
            "ack_status",
            f"{SUGGESTED_ACK_STATUS_COMMAND} --refresh",
            {
                "rollup_status": ack_compact.get("rollup_status"),
                "acknowledgment_status": ack_compact.get("acknowledgment_status"),
            },
        )
    )

    refresh_trend_hint_review_digest(storage)
    digest_compact = compact_trend_hint_review_digest(storage)
    steps.append(
        _step_record(
            "review_digest",
            f"{SUGGESTED_DIGEST_COMMAND} --refresh",
            {
                "digest_status": digest_compact.get("digest_status"),
                "rollup_status": digest_compact.get("rollup_status"),
            },
        )
    )

    generate_candidate_review_readiness(storage)
    readiness_compact = compact_candidate_review_readiness(storage)
    steps.append(
        _step_record(
            "review_readiness",
            "make mrms-render-candidate-review-readiness --refresh",
            {
                "chain_readiness_level": readiness_compact.get("chain_readiness_level"),
                "overall_readiness_level": readiness_compact.get("overall_readiness_level"),
            },
        )
    )

    refresh_visual_review_sample_readiness(storage)
    visual_compact = compact_visual_review_sample_readiness(storage)
    steps.append(
        _step_record(
            "visual_readiness",
            f"{SUGGESTED_READINESS_COMMAND} --refresh",
            {
                "readiness_level": visual_compact.get("readiness_level"),
                "readiness_reason": visual_compact.get("readiness_reason"),
            },
        )
    )

    visual_blockers = _visual_blockers_from_compact(visual_compact)
    if skip_preflight_attempt or visual_blockers:
        attempt = {
            "attempt_status": ATTEMPT_BLOCKED_BY_READINESS,
            "preflight_not_run": True,
            "gate_reason": visual_blockers[0] if visual_blockers else "preflight attempt skipped",
            "blocking_items": list(visual_blockers),
        }
        attempt_compact = {
            **compact_preflight_attempt(storage),
            "attempt_status": ATTEMPT_BLOCKED_BY_READINESS,
            "preflight_not_run": True,
            "gate_reason": attempt.get("gate_reason"),
        }
        preflight_step_command = "(preflight attempt skipped — visual readiness gate)"
    else:
        attempt = attempt_gated_preflight(storage)
        attempt_compact = compact_preflight_attempt(storage)
        preflight_step_command = "make mrms-render-candidate-preflight-attempt --refresh"
    steps.append(
        _step_record(
            "preflight_retry",
            preflight_step_command,
            {
                "attempt_status": attempt_compact.get("attempt_status"),
                "preflight_not_run": attempt_compact.get("preflight_not_run"),
                "preflight_level": attempt_compact.get("preflight_level"),
            },
        )
    )

    remaining_blockers = list(readiness_compact.get("blocking_items") or [])
    visual_blockers = _visual_blockers_from_compact(visual_compact)
    for item in visual_blockers:
        if item not in remaining_blockers:
            remaining_blockers.append(item)
    if attempt.get("attempt_status") == ATTEMPT_BLOCKED_BY_READINESS:
        gate_reason = attempt.get("gate_reason")
        if gate_reason and gate_reason not in remaining_blockers:
            remaining_blockers.append(gate_reason)
    elif attempt.get("blocking_items"):
        for item in attempt["blocking_items"]:
            if item not in remaining_blockers:
                remaining_blockers.append(item)

    blocker_category = _blocker_category(
        ack=ack_compact,
        visual=visual_compact,
        readiness=readiness_compact,
    )
    resolution_status = _resolution_status(attempt_compact, readiness_compact)
    next_commands = _merge_next_commands(
        readiness=readiness_compact,
        visual=visual_compact,
        attempt=attempt_compact,
        remaining_blockers=remaining_blockers,
    )

    report = {
        "resolved_at": _utc_now(),
        "resolution_status": resolution_status,
        "blocker_category": blocker_category,
        "primary_blocker": remaining_blockers[0] if remaining_blockers else None,
        "remaining_blockers": remaining_blockers,
        "visual_blockers": visual_blockers,
        "warnings": list(readiness_compact.get("warnings") or []),
        "steps": steps,
        "readiness_level": readiness_compact.get("overall_readiness_level"),
        "review_chain_ready": readiness_compact.get("review_chain_ready"),
        "visual_readiness_level": visual_compact.get("readiness_level"),
        "visual_readiness_reason": visual_compact.get("readiness_reason"),
        "preflight_attempt_status": attempt_compact.get("attempt_status"),
        "preflight_level": attempt_compact.get("preflight_level"),
        "preflight_not_run": bool(attempt_compact.get("preflight_not_run")),
        "next_commands": next_commands,
        "next_operator_step": attempt_compact.get("next_operator_step")
        or readiness_compact.get("next_operator_step"),
        "next_phase_recommendation": _next_phase_for_resolution(
            resolution_status=resolution_status,
            blocker_category=blocker_category,
        ),
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }
    return save_preflight_blockers_report(storage, report)


def build_blockers_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Candidate preflight blockers resolution",
        "",
        "> **WARNING:** Local blocker resolution only. Does **NOT** verify MRMS or authorize production use.",
        "",
        f"- Resolved at: {report.get('resolved_at')}",
        f"- Resolution status: {report.get('resolution_status')}",
        f"- Blocker category: {report.get('blocker_category')}",
        f"- Primary blocker: {report.get('primary_blocker') or '—'}",
        f"- Preflight not run: {report.get('preflight_not_run')}",
        "",
        "## Remaining blockers",
        "",
    ]
    for item in report.get("remaining_blockers") or []:
        lines.append(f"- {item}")
    if not report.get("remaining_blockers"):
        lines.append("- none")
    lines.extend(["", "## Visual blockers", ""])
    for item in report.get("visual_blockers") or []:
        lines.append(f"- {item}")
    if not report.get("visual_blockers"):
        lines.append("- none")
    lines.extend(["", "## Next commands", ""])
    for cmd in report.get("next_commands") or []:
        lines.append(f"- `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def save_preflight_blockers_report(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
    json_path = _blockers_json_path(storage)
    md_path = _blockers_md_path(storage)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    record = {
        **report,
        "json_path": json_path,
        "markdown_path": md_path,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(record, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(
        build_blockers_markdown(record),
        encoding="utf-8",
    )
    return record


def load_preflight_blockers_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_blockers_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def compact_preflight_blockers(storage: LocalStorage) -> dict[str, Any]:
    latest = load_preflight_blockers_report(storage)
    readiness = compact_candidate_review_readiness(storage)
    attempt = compact_preflight_attempt(storage)
    visual = compact_visual_review_sample_readiness(storage)
    if latest is None:
        remaining = list(readiness.get("blocking_items") or [])
        visual_blockers = _visual_blockers_from_compact(visual)
        for item in visual_blockers:
            if item not in remaining:
                remaining.append(item)
        category = _blocker_category(ack=compact_trend_hint_ack_status(storage), visual=visual, readiness=readiness)
        return {
            "available": False,
            "resolution_status": RESOLUTION_BLOCKED,
            "blocker_category": category,
            "primary_blocker": remaining[0] if remaining else None,
            "remaining_blockers": remaining,
            "visual_blockers": visual_blockers,
            "readiness_level": readiness.get("overall_readiness_level"),
            "visual_readiness_level": visual.get("readiness_level"),
            "visual_readiness_reason": visual.get("readiness_reason"),
            "preflight_attempt_status": attempt.get("attempt_status"),
            "preflight_level": attempt.get("preflight_level"),
            "preflight_not_run": attempt.get("preflight_not_run", True),
            "next_commands": _merge_next_commands(
                readiness=readiness,
                visual=visual,
                attempt=attempt,
                remaining_blockers=remaining,
            ),
            "next_operator_step": readiness.get("next_operator_step"),
            "suggested_command": SUGGESTED_COMMAND,
            "next_phase_recommendation": _next_phase_for_resolution(
                resolution_status=RESOLUTION_BLOCKED,
                blocker_category=category,
            ),
            **_safety_fields(),
        }
    return {
        "available": True,
        "resolution_status": latest.get("resolution_status"),
        "blocker_category": latest.get("blocker_category"),
        "primary_blocker": latest.get("primary_blocker"),
        "remaining_blockers": latest.get("remaining_blockers") or [],
        "visual_blockers": latest.get("visual_blockers") or [],
        "readiness_level": latest.get("readiness_level"),
        "visual_readiness_level": latest.get("visual_readiness_level"),
        "visual_readiness_reason": latest.get("visual_readiness_reason"),
        "preflight_attempt_status": latest.get("preflight_attempt_status"),
        "preflight_level": latest.get("preflight_level"),
        "preflight_not_run": latest.get("preflight_not_run"),
        "next_commands": latest.get("next_commands") or [],
        "next_operator_step": latest.get("next_operator_step"),
        "resolved_at": latest.get("resolved_at"),
        "json_path": latest.get("json_path"),
        "markdown_path": latest.get("markdown_path"),
        "suggested_command": SUGGESTED_COMMAND,
        "next_phase_recommendation": latest.get("next_phase_recommendation"),
        **_safety_fields(),
    }


def build_preflight_blockers_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_preflight_blockers_report(storage)
    return {
        **_safety_fields(),
        "latest": latest or {},
        "compact": compact_preflight_blockers(storage),
    }
