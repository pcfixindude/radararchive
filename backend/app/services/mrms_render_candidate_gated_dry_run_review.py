"""Gated render candidate dry-run plan review — local advisory only; does NOT verify MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_dry_run_plan import (
    DRY_RUN_BLOCKED,
    DRY_RUN_NEEDS_REVIEW,
    DRY_RUN_PLAN_READY,
    SUGGESTED_DRY_RUN_PLAN_COMMAND,
    compact_render_candidate_dry_run_plan,
    generate_render_candidate_dry_run_plan,
    load_render_candidate_dry_run_plan,
)
from backend.app.services.mrms_render_candidate_preflight import (
    PREFLIGHT_CANDIDATE_READY,
    SUGGESTED_PREFLIGHT_COMMAND,
    compact_render_candidate_preflight,
    generate_render_candidate_preflight,
)
from backend.app.services.mrms_render_candidate_preflight_blockers import (
    RESOLUTION_PREFLIGHT_CANDIDATE_READY,
    SUGGESTED_COMMAND as SUGGESTED_BLOCKERS_COMMAND,
    compact_preflight_blockers,
    resolve_preflight_blockers,
)
from backend.app.services.storage import LocalStorage

REVIEW_JSON = "dev/mrms_render_candidate_gated_dry_run_review_latest.json"
REVIEW_MD = "dev/mrms_render_candidate_gated_dry_run_review_latest.md"

SUGGESTED_COMMAND = "make mrms-review-gated-dry-run-plan"

REVIEW_PREFLIGHT_BLOCKED = "preflight_not_candidate_ready"
REVIEW_PLAN_BLOCKED = "dry_run_plan_blocked"
REVIEW_PLAN_NEEDS_REVIEW = "dry_run_plan_needs_review"
REVIEW_PLAN_READY = "dry_run_plan_ready"

NEXT_PHASE_SCAFFOLD = (
    "Phase 94 — gated candidate artifact sandbox layout "
    "(local sandbox directory layout isolated from production tile serving)"
)
NEXT_PHASE_PREFLIGHT_EVIDENCE = (
    "Phase 93 — complete MRMS preflight evidence "
    "(resolve remaining preflight blockers before dry-run plan)"
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_gated_dry_run_review_only": True,
        "advisory_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "does_not_download_or_decode": True,
        "does_not_create_production_tiles": True,
        "does_not_execute_candidate_steps": True,
        "does_not_serve_production_tiles": True,
        "does_not_delete_by_default": True,
        "binary_artifacts_included": False,
        "no_external_notifications": True,
        "does_not_authorize_production_use": True,
        "dry_run_plan_ready_is_not_production_authorization": True,
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


def _review_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(REVIEW_JSON)


def _review_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(REVIEW_MD)


def _step_record(step_id: str, command: str, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "command": command,
        "completed_at": _utc_now(),
        "summary": summary,
    }


def _preflight_blockers(preflight: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    level = preflight.get("preflight_level")
    if level != PREFLIGHT_CANDIDATE_READY:
        blockers.append(f"preflight level is {level or 'missing'} (need candidate_preflight_ready)")
    for item in preflight.get("blocking_items") or []:
        if item not in blockers:
            blockers.append(str(item))
    return blockers


def _next_commands_for_preflight_blockers(
    *,
    preflight: dict[str, Any],
    blockers: dict[str, Any],
) -> list[str]:
    commands: list[str] = []
    for cmd in blockers.get("next_commands") or []:
        if cmd not in commands:
            commands.append(str(cmd))
    preflight_cmd = f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh"
    if preflight_cmd not in commands:
        commands.append(preflight_cmd)
    blockers_cmd = f"{SUGGESTED_BLOCKERS_COMMAND} --refresh"
    if blockers_cmd not in commands:
        commands.append(blockers_cmd)
    return commands


def _next_commands_for_plan_status(plan_status: str) -> list[str]:
    if plan_status == DRY_RUN_PLAN_READY:
        return ["make mrms-render-candidate-scaffold --refresh"]
    if plan_status == DRY_RUN_NEEDS_REVIEW:
        return [
            f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
            f"{SUGGESTED_DRY_RUN_PLAN_COMMAND} --refresh",
        ]
    return [
        f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
        f"{SUGGESTED_DRY_RUN_PLAN_COMMAND} --refresh",
        f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
    ]


def _classify_review_status(
    *,
    preflight: dict[str, Any],
    plan_compact: dict[str, Any],
    dry_run_plan_skipped: bool,
    blockers: dict[str, Any],
) -> tuple[str, str, list[str]]:
    if dry_run_plan_skipped:
        preflight_blockers = _preflight_blockers(preflight)
        remaining = list(blockers.get("remaining_blockers") or [])
        for item in preflight_blockers:
            if item not in remaining:
                remaining.append(item)
        return (
            REVIEW_PREFLIGHT_BLOCKED,
            "Preflight is not candidate_preflight_ready — dry-run plan not generated.",
            _next_commands_for_preflight_blockers(preflight=preflight, blockers=blockers),
        )

    plan_status = plan_compact.get("plan_status")
    if plan_status == DRY_RUN_PLAN_READY:
        return (
            REVIEW_PLAN_READY,
            "Dry-run plan ready — consider gated render candidate scaffold (not production authorization).",
            _next_commands_for_plan_status(plan_status),
        )
    if plan_status == DRY_RUN_NEEDS_REVIEW:
        return (
            REVIEW_PLAN_NEEDS_REVIEW,
            "Dry-run plan needs review — resolve warnings before scaffold evaluation.",
            _next_commands_for_plan_status(plan_status),
        )
    return (
        REVIEW_PLAN_BLOCKED,
        "Dry-run plan blocked — resolve blocking items before advancing.",
        _next_commands_for_plan_status(str(plan_status or DRY_RUN_BLOCKED)),
    )


def _next_phase_for_review(review_status: str) -> str:
    if review_status == REVIEW_PLAN_READY:
        return NEXT_PHASE_SCAFFOLD
    if review_status == REVIEW_PREFLIGHT_BLOCKED:
        return NEXT_PHASE_PREFLIGHT_EVIDENCE
    return (
        "Phase 93 — resolve dry-run plan blockers or complete preflight evidence "
        "(depending on gated dry-run review report)"
    )


def review_gated_dry_run_plan(storage: LocalStorage) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []

    generate_render_candidate_preflight(storage)
    preflight_compact = compact_render_candidate_preflight(storage)
    steps.append(
        _step_record(
            "preflight",
            f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
            {
                "preflight_level": preflight_compact.get("preflight_level"),
                "preflight_reason": preflight_compact.get("preflight_reason"),
            },
        )
    )

    blockers_report = resolve_preflight_blockers(storage)
    blockers_compact = compact_preflight_blockers(storage)
    steps.append(
        _step_record(
            "preflight_blockers",
            f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
            {
                "resolution_status": blockers_compact.get("resolution_status"),
                "preflight_level": blockers_compact.get("preflight_level"),
                "preflight_not_run": blockers_compact.get("preflight_not_run"),
            },
        )
    )

    preflight_compact = compact_render_candidate_preflight(storage)
    preflight_level = preflight_compact.get("preflight_level")
    dry_run_plan_skipped = preflight_level != PREFLIGHT_CANDIDATE_READY

    plan_compact: dict[str, Any]
    if dry_run_plan_skipped:
        existing = load_render_candidate_dry_run_plan(storage)
        plan_compact = compact_render_candidate_dry_run_plan(storage)
        steps.append(
            _step_record(
                "dry_run_plan",
                "(dry-run plan skipped — preflight gate closed)",
                {
                    "skipped": True,
                    "existing_plan_status": existing.get("plan_status") if existing else None,
                },
            )
        )
    else:
        plan = generate_render_candidate_dry_run_plan(storage)
        plan_compact = compact_render_candidate_dry_run_plan(storage)
        steps.append(
            _step_record(
                "dry_run_plan",
                f"{SUGGESTED_DRY_RUN_PLAN_COMMAND} --refresh",
                {
                    "skipped": False,
                    "plan_status": plan.get("plan_status"),
                    "plan_reason": plan.get("plan_reason"),
                },
            )
        )

    review_status, next_operator_step, next_commands = _classify_review_status(
        preflight=preflight_compact,
        plan_compact=plan_compact,
        dry_run_plan_skipped=dry_run_plan_skipped,
        blockers=blockers_compact,
    )

    report = {
        "reviewed_at": _utc_now(),
        "review_status": review_status,
        "preflight_level": preflight_level,
        "preflight_reason": preflight_compact.get("preflight_reason"),
        "preflight_blocking_items": preflight_compact.get("blocking_items") or [],
        "dry_run_plan_skipped": dry_run_plan_skipped,
        "dry_run_plan_status": None if dry_run_plan_skipped else plan_compact.get("plan_status"),
        "dry_run_plan_reason": None if dry_run_plan_skipped else plan_compact.get("plan_reason"),
        "dry_run_plan_blocking_items": [] if dry_run_plan_skipped else (plan_compact.get("blocking_items") or []),
        "resolution_status": blockers_compact.get("resolution_status"),
        "remaining_blockers": blockers_compact.get("remaining_blockers") or [],
        "preflight_not_run": bool(blockers_compact.get("preflight_not_run", True)),
        "next_operator_step": next_operator_step,
        "next_commands": next_commands,
        "next_phase_recommendation": _next_phase_for_review(review_status),
        "steps": steps,
        "safety_state": _current_safety_state(),
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }
    if blockers_compact.get("resolution_status") == RESOLUTION_PREFLIGHT_CANDIDATE_READY:
        report["preflight_candidate_ready"] = True
    return save_gated_dry_run_review_report(storage, report)


def build_review_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Gated render candidate dry-run plan review",
        "",
        "> **WARNING:** Local gated review only. Advisory metadata — does **NOT** verify MRMS, "
        "execute candidate steps, enable production rendering, clear alerts, or authorize production use.",
        "",
        f"- Reviewed at: {report.get('reviewed_at')}",
        f"- Review status: **{report.get('review_status')}**",
        f"- Preflight level: {report.get('preflight_level')}",
        f"- Dry-run plan skipped: {report.get('dry_run_plan_skipped')}",
        f"- Dry-run plan status: {report.get('dry_run_plan_status') or '—'}",
        f"- Next operator step: {report.get('next_operator_step')}",
        "",
        "## Preflight blocking items",
        "",
    ]
    for item in report.get("preflight_blocking_items") or []:
        lines.append(f"- {item}")
    if not report.get("preflight_blocking_items"):
        lines.append("- none")
    lines.extend(["", "## Remaining blockers", ""])
    for item in report.get("remaining_blockers") or []:
        lines.append(f"- {item}")
    if not report.get("remaining_blockers"):
        lines.append("- none")
    if not report.get("dry_run_plan_skipped"):
        lines.extend(["", "## Dry-run plan blocking items", ""])
        for item in report.get("dry_run_plan_blocking_items") or []:
            lines.append(f"- {item}")
        if not report.get("dry_run_plan_blocking_items"):
            lines.append("- none")
    lines.extend(["", "## Next commands", ""])
    for cmd in report.get("next_commands") or []:
        lines.append(f"- `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def save_gated_dry_run_review_report(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
    json_path = _review_json_path(storage)
    md_path = _review_md_path(storage)
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
        build_review_markdown(report),
        encoding="utf-8",
    )
    return report


def load_gated_dry_run_review_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_review_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def compact_gated_dry_run_review(storage: LocalStorage) -> dict[str, Any]:
    latest = load_gated_dry_run_review_report(storage)
    if latest is None:
        preflight = compact_render_candidate_preflight(storage)
        plan = compact_render_candidate_dry_run_plan(storage)
        skipped = preflight.get("preflight_level") != PREFLIGHT_CANDIDATE_READY
        review_status = REVIEW_PREFLIGHT_BLOCKED if skipped else REVIEW_PLAN_BLOCKED
        return {
            "available": False,
            "review_status": review_status,
            "preflight_level": preflight.get("preflight_level"),
            "dry_run_plan_skipped": skipped,
            "dry_run_plan_status": None if skipped else plan.get("plan_status"),
            "preflight_not_run": True,
            "next_commands": _next_commands_for_preflight_blockers(
                preflight=preflight,
                blockers=compact_preflight_blockers(storage),
            ),
            "next_operator_step": "Run gated dry-run plan review after preflight is candidate_preflight_ready.",
            "json_path": _review_json_path(storage),
            "markdown_path": _review_md_path(storage),
            "suggested_command": SUGGESTED_COMMAND,
            "next_phase_recommendation": _next_phase_for_review(review_status),
            **_safety_fields(),
        }
    return {
        "available": True,
        "review_status": latest.get("review_status"),
        "preflight_level": latest.get("preflight_level"),
        "preflight_reason": latest.get("preflight_reason"),
        "preflight_blocking_items": latest.get("preflight_blocking_items") or [],
        "dry_run_plan_skipped": bool(latest.get("dry_run_plan_skipped")),
        "dry_run_plan_status": latest.get("dry_run_plan_status"),
        "dry_run_plan_reason": latest.get("dry_run_plan_reason"),
        "dry_run_plan_blocking_items": latest.get("dry_run_plan_blocking_items") or [],
        "resolution_status": latest.get("resolution_status"),
        "remaining_blockers": latest.get("remaining_blockers") or [],
        "preflight_not_run": bool(latest.get("preflight_not_run", True)),
        "preflight_candidate_ready": bool(latest.get("preflight_candidate_ready")),
        "next_commands": latest.get("next_commands") or [],
        "next_operator_step": latest.get("next_operator_step"),
        "reviewed_at": latest.get("reviewed_at"),
        "json_path": latest.get("json_path"),
        "markdown_path": latest.get("markdown_path"),
        "suggested_command": latest.get("suggested_command") or SUGGESTED_COMMAND,
        "next_phase_recommendation": latest.get("next_phase_recommendation"),
        **_safety_fields(),
    }


def build_gated_dry_run_review_payload(storage: LocalStorage) -> dict[str, Any]:
    return {
        **_safety_fields(),
        "latest": load_gated_dry_run_review_report(storage),
        "compact": compact_gated_dry_run_review(storage),
    }
