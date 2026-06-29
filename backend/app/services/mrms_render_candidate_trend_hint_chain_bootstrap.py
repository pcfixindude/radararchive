"""Bootstrap sandbox comparison trend-hint chain — local advisory only; does NOT verify MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight_blockers import (
    RESOLUTION_PREFLIGHT_ATTEMPTED,
    RESOLUTION_PREFLIGHT_CANDIDATE_READY,
    _visual_blockers_from_compact,
    compact_preflight_blockers,
    resolve_preflight_blockers,
)
from backend.app.services.mrms_render_candidate_review_readiness import (
    CHAIN_BLOCKED,
    CHAIN_READY,
    OVERALL_READY_FOR_PREFLIGHT,
    SUGGESTED_COMMAND as SUGGESTED_READINESS_COMMAND,
    compact_candidate_review_readiness,
    generate_candidate_review_readiness,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status import (
    refresh_sandbox_comparison_acknowledgment_status,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_history import (
    refresh_ack_status_history_report,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint import (
    refresh_ack_status_trend_hint,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status import (
    refresh_ack_status_trend_review_acknowledgment_status,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_history import (
    refresh_ack_status_trend_review_acknowledgment_status_history_report,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_hint import (
    refresh_ack_status_trend_review_acknowledgment_status_trend_hint,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status import (
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history import (
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history_report,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint import (
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_history import (
    COMPARISON_TYPE_CURRENT_VS_IMPORTED,
    COMPARISON_UNCHANGED,
    append_comparison_history_entry,
    build_comparison_history_entry,
    load_comparison_history,
    refresh_comparison_history_report,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_trend_hint import (
    SUGGESTED_COMMAND as SUGGESTED_SANDBOX_TREND_HINT_COMMAND,
    refresh_sandbox_comparison_trend_hint,
)
from backend.app.services.mrms_render_candidate_trend_hint_ack_status import (
    ROLLUP_BLOCKED,
    ROLLUP_MISSING,
    SUGGESTED_COMMAND as SUGGESTED_ACK_STATUS_COMMAND,
    compact_trend_hint_ack_status,
    refresh_trend_hint_ack_status,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest import (
    DIGEST_BLOCKED,
    DIGEST_MISSING,
    SUGGESTED_COMMAND as SUGGESTED_DIGEST_COMMAND,
    compact_trend_hint_review_digest,
    refresh_trend_hint_review_digest,
)
from backend.app.services.mrms_visual_review_sample_readiness import (
    SUGGESTED_READINESS_COMMAND,
    compact_visual_review_sample_readiness,
)
from backend.app.services.storage import LocalStorage

BOOTSTRAP_JSON = "dev/mrms_render_candidate_trend_hint_chain_bootstrap_latest.json"
BOOTSTRAP_MD = "dev/mrms_render_candidate_trend_hint_chain_bootstrap_latest.md"

SUGGESTED_COMMAND = "make mrms-bootstrap-trend-hint-chain"

BOOTSTRAP_STILL_BLOCKED = "trend_hint_chain_still_blocked"
BOOTSTRAP_CHAIN_READY_VISUAL_BLOCKED = "chain_ready_visual_blocked"
BOOTSTRAP_READY_FOR_PREFLIGHT = "ready_for_preflight"
BOOTSTRAP_PREFLIGHT_ATTEMPTED = "preflight_attempted"
BOOTSTRAP_PREFLIGHT_CANDIDATE_READY = "preflight_candidate_ready"

NEXT_PHASE_VISUAL = (
    "Phase 91 — bootstrap visual review sample set "
    "(create sample set and annotations for candidate_preflight_ready)"
)
NEXT_PHASE_DRY_RUN = (
    "Phase 92 — gated render candidate dry-run plan review "
    "(evaluate dry-run plan when preflight is candidate_preflight_ready)"
)

VISUAL_NEXT_COMMANDS = [
    "make mrms-visual-review",
    "make mrms-visual-review-sample-set",
    f"{SUGGESTED_READINESS_COMMAND} --refresh",
    "make mrms-resolve-preflight-blockers --refresh",
]


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_chain_bootstrap_only": True,
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


def _bootstrap_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(BOOTSTRAP_JSON)


def _bootstrap_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(BOOTSTRAP_MD)


def seed_sandbox_comparison_history_if_needed(storage: LocalStorage) -> dict[str, Any]:
    history = load_comparison_history(storage)
    if history:
        return {
            "seeded": False,
            "entries_added": 0,
            "history_count": len(history),
            "reason": "comparison_history_already_present",
        }

    entries_added = 0
    for _ in range(2):
        entry = build_comparison_history_entry(
            comparison_type=COMPARISON_TYPE_CURRENT_VS_IMPORTED,
            comparison={
                "changed_sandbox_status": False,
                "changed_safety_gate_summary": False,
                "changed_file_counts": False,
            },
            comparison_status=COMPARISON_UNCHANGED,
            source_paths={"import_json_path": "data/dev/bootstrap_seed.json"},
            notes=["bootstrap seed — local advisory only"],
        )
        append_comparison_history_entry(storage, entry)
        entries_added += 1

    return {
        "seeded": True,
        "entries_added": entries_added,
        "history_count": len(load_comparison_history(storage)),
        "reason": "seeded_stable_comparison_history",
    }


def refresh_upstream_sandbox_chain(storage: LocalStorage) -> dict[str, Any]:
    refresh_comparison_history_report(storage)
    refresh_sandbox_comparison_trend_hint(storage)
    refresh_sandbox_comparison_acknowledgment_status(storage)
    refresh_ack_status_history_report(storage)
    refresh_ack_status_trend_hint(storage)
    refresh_ack_status_trend_review_acknowledgment_status(storage)
    refresh_ack_status_trend_review_acknowledgment_status_history_report(storage)
    refresh_ack_status_trend_review_acknowledgment_status_trend_hint(storage)
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status(storage)
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history_report(
        storage
    )
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(
        storage
    )
    return {"upstream_chain_refreshed": True}


def _step_record(step_id: str, command: str, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "command": command,
        "completed_at": _utc_now(),
        "summary": summary,
    }


def _trend_hint_chain_blockers(
    *,
    ack: dict[str, Any],
    digest: dict[str, Any],
    readiness: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    rollup = ack.get("rollup_status")
    if rollup in {ROLLUP_MISSING, ROLLUP_BLOCKED}:
        blockers.append(f"acknowledgment status rollup is {rollup}")
    digest_status = digest.get("digest_status")
    if digest_status in {DIGEST_MISSING, DIGEST_BLOCKED}:
        blockers.append(f"review digest is {digest_status}")
    if readiness.get("chain_readiness_level") == CHAIN_BLOCKED:
        for item in readiness.get("blocking_items") or []:
            lowered = str(item).lower()
            if "visual" in lowered or "sample" in lowered:
                continue
            if item not in blockers:
                blockers.append(str(item))
    return blockers


def _next_commands_for_trend_hint_blockers(blockers: list[str]) -> list[str]:
    commands: list[str] = []
    for blocker in blockers:
        lowered = blocker.lower()
        if "rollup" in lowered:
            for cmd in (
                f"{SUGGESTED_SANDBOX_TREND_HINT_COMMAND} --refresh",
                f"{SUGGESTED_ACK_STATUS_COMMAND} --refresh",
            ):
                if cmd not in commands:
                    commands.append(cmd)
        elif "digest" in lowered:
            for cmd in (
                f"{SUGGESTED_DIGEST_COMMAND} --refresh",
                f"{SUGGESTED_READINESS_COMMAND} --refresh",
            ):
                if cmd not in commands:
                    commands.append(cmd)
    if not commands:
        commands = [
            f"{SUGGESTED_SANDBOX_TREND_HINT_COMMAND} --refresh",
            f"{SUGGESTED_ACK_STATUS_COMMAND} --refresh",
            f"{SUGGESTED_DIGEST_COMMAND} --refresh",
            f"{SUGGESTED_READINESS_COMMAND} --refresh",
            "make mrms-resolve-preflight-blockers --refresh",
        ]
    return commands


def _classify_bootstrap_status(
    *,
    trend_hint_blockers: list[str],
    visual_blockers: list[str],
    readiness: dict[str, Any],
    blockers_report: dict[str, Any],
) -> tuple[str, str, list[str]]:
    if trend_hint_blockers:
        return (
            BOOTSTRAP_STILL_BLOCKED,
            "Trend-hint chain still blocked — do not force preflight.",
            _next_commands_for_trend_hint_blockers(trend_hint_blockers),
        )

    if visual_blockers:
        return (
            BOOTSTRAP_CHAIN_READY_VISUAL_BLOCKED,
            "Trend-hint chain ready — visual sample readiness still blocked.",
            list(VISUAL_NEXT_COMMANDS),
        )

    resolution = blockers_report.get("resolution_status")
    if resolution == RESOLUTION_PREFLIGHT_CANDIDATE_READY:
        return (
            BOOTSTRAP_PREFLIGHT_CANDIDATE_READY,
            "Preflight candidate_ready — dry-run plan review next (not production authorization).",
            ["make mrms-render-candidate-dry-run-plan --refresh"],
        )
    if resolution == RESOLUTION_PREFLIGHT_ATTEMPTED:
        return (
            BOOTSTRAP_PREFLIGHT_ATTEMPTED,
            "Gated preflight attempted — review advisory preflight result.",
            blockers_report.get("next_commands") or ["make mrms-render-candidate-preflight-attempt --refresh"],
        )
    if readiness.get("overall_readiness_level") == OVERALL_READY_FOR_PREFLIGHT:
        return (
            BOOTSTRAP_READY_FOR_PREFLIGHT,
            "Review readiness ready_for_preflight — gated preflight advisory captured.",
            blockers_report.get("next_commands")
            or ["make mrms-render-candidate-preflight-attempt --refresh"],
        )

    return (
        BOOTSTRAP_STILL_BLOCKED,
        "Bootstrap completed but preflight gate still closed.",
        blockers_report.get("next_commands") or ["make mrms-resolve-preflight-blockers --refresh"],
    )


def _next_phase_for_bootstrap(bootstrap_status: str) -> str:
    if bootstrap_status == BOOTSTRAP_PREFLIGHT_CANDIDATE_READY:
        return NEXT_PHASE_DRY_RUN
    if bootstrap_status == BOOTSTRAP_CHAIN_READY_VISUAL_BLOCKED:
        return NEXT_PHASE_VISUAL
    if bootstrap_status in {BOOTSTRAP_READY_FOR_PREFLIGHT, BOOTSTRAP_PREFLIGHT_ATTEMPTED}:
        return NEXT_PHASE_VISUAL
    return (
        "Phase 91 — continue trend-hint chain bootstrap or bootstrap visual review sample set "
        "(depending on remaining blockers)"
    )


def bootstrap_trend_hint_chain(storage: LocalStorage) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []

    seed_result = seed_sandbox_comparison_history_if_needed(storage)
    steps.append(
        _step_record(
            "seed_comparison_history",
            "(internal seed)",
            seed_result,
        )
    )

    upstream = refresh_upstream_sandbox_chain(storage)
    steps.append(
        _step_record(
            "upstream_sandbox_chain",
            "(internal upstream refresh)",
            upstream,
        )
    )

    sandbox_hint = refresh_sandbox_comparison_trend_hint(storage)
    steps.append(
        _step_record(
            "sandbox_comparison_trend_hint",
            f"{SUGGESTED_SANDBOX_TREND_HINT_COMMAND} --refresh",
            {
                "trend": sandbox_hint.get("trend"),
                "hint_status": sandbox_hint.get("hint_status"),
            },
        )
    )

    ack_status = refresh_trend_hint_ack_status(storage)
    ack_compact = compact_trend_hint_ack_status(storage)
    steps.append(
        _step_record(
            "trend_hint_ack_status",
            f"{SUGGESTED_ACK_STATUS_COMMAND} --refresh",
            {
                "rollup_status": ack_compact.get("rollup_status"),
                "acknowledgment_status": ack_compact.get("acknowledgment_status"),
            },
        )
    )

    digest = refresh_trend_hint_review_digest(storage)
    digest_compact = compact_trend_hint_review_digest(storage)
    steps.append(
        _step_record(
            "trend_hint_review_digest",
            f"{SUGGESTED_DIGEST_COMMAND} --refresh",
            {
                "digest_status": digest_compact.get("digest_status"),
                "rollup_status": digest_compact.get("rollup_status"),
            },
        )
    )

    readiness = generate_candidate_review_readiness(storage)
    readiness_compact = compact_candidate_review_readiness(storage)
    steps.append(
        _step_record(
            "review_readiness",
            f"{SUGGESTED_READINESS_COMMAND} --refresh",
            {
                "chain_readiness_level": readiness_compact.get("chain_readiness_level"),
                "overall_readiness_level": readiness_compact.get("overall_readiness_level"),
            },
        )
    )

    blockers_report = resolve_preflight_blockers(storage)
    blockers_compact = compact_preflight_blockers(storage)
    visual_compact = compact_visual_review_sample_readiness(storage)
    steps.append(
        _step_record(
            "preflight_blockers",
            "make mrms-resolve-preflight-blockers --refresh",
            {
                "resolution_status": blockers_compact.get("resolution_status"),
                "preflight_not_run": blockers_compact.get("preflight_not_run"),
                "preflight_attempt_status": blockers_compact.get("preflight_attempt_status"),
            },
        )
    )

    trend_hint_blockers = _trend_hint_chain_blockers(
        ack=ack_compact,
        digest=digest_compact,
        readiness=readiness_compact,
    )
    visual_blockers = _visual_blockers_from_compact(visual_compact)
    bootstrap_status, next_operator_step, next_commands = _classify_bootstrap_status(
        trend_hint_blockers=trend_hint_blockers,
        visual_blockers=visual_blockers,
        readiness=readiness_compact,
        blockers_report=blockers_report,
    )

    report = {
        "bootstrapped_at": _utc_now(),
        "bootstrap_status": bootstrap_status,
        "seed_result": seed_result,
        "trend_hint_chain_ready": readiness_compact.get("chain_readiness_level") == CHAIN_READY,
        "trend_hint_blockers": trend_hint_blockers,
        "visual_blockers": visual_blockers,
        "rollup_status": ack_compact.get("rollup_status"),
        "digest_status": digest_compact.get("digest_status"),
        "chain_readiness_level": readiness_compact.get("chain_readiness_level"),
        "overall_readiness_level": readiness_compact.get("overall_readiness_level"),
        "preflight_not_run": blockers_compact.get("preflight_not_run"),
        "preflight_attempt_status": blockers_compact.get("preflight_attempt_status"),
        "preflight_level": blockers_compact.get("preflight_level"),
        "resolution_status": blockers_compact.get("resolution_status"),
        "remaining_blockers": blockers_compact.get("remaining_blockers") or [],
        "next_operator_step": next_operator_step,
        "next_commands": next_commands,
        "next_phase_recommendation": _next_phase_for_bootstrap(bootstrap_status),
        "steps": steps,
        "safety_state": _current_safety_state(),
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }
    return save_trend_hint_chain_bootstrap_report(storage, report)


def build_bootstrap_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Candidate trend-hint chain bootstrap",
        "",
        "> **WARNING:** Local bootstrap only. Advisory metadata — does **NOT** verify MRMS, "
        "enable production rendering, force preflight when gated, clear alerts, or authorize production use.",
        "",
        f"- Bootstrapped at: {report.get('bootstrapped_at')}",
        f"- Bootstrap status: **{report.get('bootstrap_status')}**",
        f"- Trend-hint chain ready: {report.get('trend_hint_chain_ready')}",
        f"- Rollup status: {report.get('rollup_status')}",
        f"- Digest status: {report.get('digest_status')}",
        f"- Chain readiness: {report.get('chain_readiness_level')}",
        f"- Overall readiness: {report.get('overall_readiness_level')}",
        f"- Preflight not run: {report.get('preflight_not_run')}",
        f"- Next operator step: {report.get('next_operator_step')}",
        "",
        "## Trend-hint chain blockers",
        "",
    ]
    for item in report.get("trend_hint_blockers") or []:
        lines.append(f"- {item}")
    if not report.get("trend_hint_blockers"):
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


def save_trend_hint_chain_bootstrap_report(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
    json_path = _bootstrap_json_path(storage)
    md_path = _bootstrap_md_path(storage)
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
        build_bootstrap_markdown(report),
        encoding="utf-8",
    )
    return report


def load_trend_hint_chain_bootstrap_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_bootstrap_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def compact_trend_hint_chain_bootstrap(storage: LocalStorage) -> dict[str, Any]:
    latest = load_trend_hint_chain_bootstrap_report(storage)
    if latest is None:
        ack = compact_trend_hint_ack_status(storage)
        digest = compact_trend_hint_review_digest(storage)
        readiness = compact_candidate_review_readiness(storage)
        visual = compact_visual_review_sample_readiness(storage)
        trend_hint_blockers = _trend_hint_chain_blockers(
            ack=ack,
            digest=digest,
            readiness=readiness,
        )
        visual_blockers = _visual_blockers_from_compact(visual)
        if trend_hint_blockers:
            bootstrap_status = BOOTSTRAP_STILL_BLOCKED
            next_commands = _next_commands_for_trend_hint_blockers(trend_hint_blockers)
        elif visual_blockers:
            bootstrap_status = BOOTSTRAP_CHAIN_READY_VISUAL_BLOCKED
            next_commands = list(VISUAL_NEXT_COMMANDS)
        else:
            bootstrap_status = BOOTSTRAP_STILL_BLOCKED
            next_commands = [SUGGESTED_COMMAND]
        return {
            "available": False,
            "bootstrap_status": bootstrap_status,
            "trend_hint_chain_ready": readiness.get("chain_readiness_level") == CHAIN_READY,
            "trend_hint_blockers": trend_hint_blockers,
            "visual_blockers": visual_blockers,
            "rollup_status": ack.get("rollup_status"),
            "digest_status": digest.get("digest_status"),
            "chain_readiness_level": readiness.get("chain_readiness_level"),
            "overall_readiness_level": readiness.get("overall_readiness_level"),
            "preflight_not_run": True,
            "next_commands": next_commands,
            "next_operator_step": "Run trend-hint chain bootstrap to seed comparison history.",
            "json_path": _bootstrap_json_path(storage),
            "markdown_path": _bootstrap_md_path(storage),
            "suggested_command": SUGGESTED_COMMAND,
            "next_phase_recommendation": _next_phase_for_bootstrap(bootstrap_status),
            **_safety_fields(),
        }
    return {
        "available": True,
        "bootstrap_status": latest.get("bootstrap_status"),
        "trend_hint_chain_ready": bool(latest.get("trend_hint_chain_ready")),
        "trend_hint_blockers": latest.get("trend_hint_blockers") or [],
        "visual_blockers": latest.get("visual_blockers") or [],
        "rollup_status": latest.get("rollup_status"),
        "digest_status": latest.get("digest_status"),
        "chain_readiness_level": latest.get("chain_readiness_level"),
        "overall_readiness_level": latest.get("overall_readiness_level"),
        "preflight_not_run": bool(latest.get("preflight_not_run", True)),
        "preflight_attempt_status": latest.get("preflight_attempt_status"),
        "preflight_level": latest.get("preflight_level"),
        "resolution_status": latest.get("resolution_status"),
        "remaining_blockers": latest.get("remaining_blockers") or [],
        "next_commands": latest.get("next_commands") or [],
        "next_operator_step": latest.get("next_operator_step"),
        "bootstrapped_at": latest.get("bootstrapped_at"),
        "json_path": latest.get("json_path"),
        "markdown_path": latest.get("markdown_path"),
        "suggested_command": latest.get("suggested_command") or SUGGESTED_COMMAND,
        "next_phase_recommendation": latest.get("next_phase_recommendation"),
        **_safety_fields(),
    }


def build_trend_hint_chain_bootstrap_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_trend_hint_chain_bootstrap_report(storage)
    if latest is None:
        latest = compact_trend_hint_chain_bootstrap(storage)
    return {
        **_safety_fields(),
        "latest": latest if load_trend_hint_chain_bootstrap_report(storage) else None,
        "compact": compact_trend_hint_chain_bootstrap(storage),
    }
