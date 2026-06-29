"""Gated render candidate scaffold review — local advisory only; does NOT verify MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_dry_run_plan import (
    DRY_RUN_PLAN_READY,
    SUGGESTED_DRY_RUN_PLAN_COMMAND,
    compact_render_candidate_dry_run_plan,
    generate_render_candidate_dry_run_plan,
    load_render_candidate_dry_run_plan,
)
from backend.app.services.mrms_render_candidate_gated_dry_run_review import (
    SUGGESTED_COMMAND as SUGGESTED_DRY_RUN_REVIEW_COMMAND,
)
from backend.app.services.mrms_render_candidate_preflight import (
    PREFLIGHT_CANDIDATE_READY,
    PREFLIGHT_NEEDS_REVIEW,
    SUGGESTED_PREFLIGHT_COMMAND,
    compact_render_candidate_preflight,
    generate_render_candidate_preflight,
)
from backend.app.services.mrms_render_candidate_preflight_blockers import (
    SUGGESTED_COMMAND as SUGGESTED_BLOCKERS_COMMAND,
    compact_preflight_blockers,
    resolve_preflight_blockers,
)
from backend.app.services.mrms_render_candidate_scaffold import (
    SCAFFOLD_READY,
    SUGGESTED_SCAFFOLD_COMMAND,
    compact_render_candidate_scaffold,
    generate_render_candidate_scaffold,
    load_render_candidate_scaffold,
)
from backend.app.services.storage import LocalStorage

REVIEW_JSON = "dev/mrms_render_candidate_gated_scaffold_review_latest.json"
REVIEW_MD = "dev/mrms_render_candidate_gated_scaffold_review_latest.md"

SUGGESTED_COMMAND = "make mrms-review-gated-scaffold"

REVIEW_PREFLIGHT_BLOCKED = "preflight_not_candidate_ready"
REVIEW_DRY_RUN_BLOCKED = "dry_run_plan_not_ready"
REVIEW_SCAFFOLD_BLOCKED = "scaffold_blocked"
REVIEW_SCAFFOLD_DRY_RUN_ONLY = "scaffold_dry_run_only"
REVIEW_SCAFFOLD_READY = "scaffold_ready"

NEXT_PHASE_SANDBOX = (
    "Phase 94 — gated candidate artifact sandbox layout "
    "(local sandbox directory layout isolated from production tile serving)"
)
NEXT_PHASE_PREFLIGHT = (
    "Phase 94 — resolve preflight evidence "
    "(until candidate_preflight_ready before scaffold review)"
)
NEXT_PHASE_DRY_RUN = (
    "Phase 94 — complete gated dry-run plan review "
    "(until dry_run_plan_ready before scaffold review)"
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_gated_scaffold_review_only": True,
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
        "scaffold_ready_is_not_production_authorization": True,
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


def _preflight_blockers_and_warnings(preflight: dict[str, Any]) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    level = preflight.get("preflight_level")
    if level != PREFLIGHT_CANDIDATE_READY:
        blockers.append(f"preflight level is {level or 'missing'} (need candidate_preflight_ready)")
    for item in preflight.get("blocking_items") or []:
        if item not in blockers:
            blockers.append(str(item))
    for item in preflight.get("warnings") or []:
        warnings.append(str(item))
    if level == PREFLIGHT_NEEDS_REVIEW and not warnings:
        warnings.append("preflight needs_review")
    return blockers, warnings


def _dry_run_blockers(plan: dict[str, Any], *, skipped: bool) -> list[str]:
    if skipped:
        return ["dry-run plan not generated — preflight gate closed"]
    blockers: list[str] = []
    status = plan.get("plan_status")
    if status != DRY_RUN_PLAN_READY:
        blockers.append(f"dry-run plan status is {status or 'missing'} (need dry_run_plan_ready)")
    for item in plan.get("blocking_items") or []:
        if item not in blockers:
            blockers.append(str(item))
    return blockers


def _next_commands_preflight_blocked(
    *,
    preflight: dict[str, Any],
    blockers: dict[str, Any],
) -> list[str]:
    commands: list[str] = []
    for cmd in blockers.get("next_commands") or []:
        if cmd not in commands:
            commands.append(str(cmd))
    for cmd in (
        f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
        f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
        f"{SUGGESTED_DRY_RUN_REVIEW_COMMAND} --refresh",
    ):
        if cmd not in commands:
            commands.append(cmd)
    return commands


def _next_commands_dry_run_blocked() -> list[str]:
    return [
        f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
        f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
        f"{SUGGESTED_DRY_RUN_REVIEW_COMMAND} --refresh",
        f"{SUGGESTED_DRY_RUN_PLAN_COMMAND} --refresh",
    ]


def _next_commands_scaffold_status(scaffold_status: str) -> list[str]:
    if scaffold_status == SCAFFOLD_READY:
        return ["make mrms-render-candidate-sandbox --refresh"]
    return [
        f"{SUGGESTED_SCAFFOLD_COMMAND} --refresh",
        f"{SUGGESTED_DRY_RUN_REVIEW_COMMAND} --refresh",
    ]


def _classify_review_status(
    *,
    preflight: dict[str, Any],
    dry_run_skipped: bool,
    plan_compact: dict[str, Any],
    scaffold_skipped: bool,
    scaffold_compact: dict[str, Any],
    preflight_blockers: list[str],
    dry_run_blockers: list[str],
    blockers_compact: dict[str, Any],
) -> tuple[str, str, list[str]]:
    if preflight.get("preflight_level") != PREFLIGHT_CANDIDATE_READY:
        return (
            REVIEW_PREFLIGHT_BLOCKED,
            "Preflight is not candidate_preflight_ready — scaffold not generated.",
            _next_commands_preflight_blocked(preflight=preflight, blockers=blockers_compact),
        )

    if dry_run_skipped or plan_compact.get("plan_status") != DRY_RUN_PLAN_READY:
        return (
            REVIEW_DRY_RUN_BLOCKED,
            "Dry-run plan is not dry_run_plan_ready — scaffold not generated.",
            _next_commands_dry_run_blocked(),
        )

    if scaffold_skipped:
        return (
            REVIEW_SCAFFOLD_BLOCKED,
            "Scaffold review gate closed unexpectedly.",
            _next_commands_dry_run_blocked(),
        )

    scaffold_status = scaffold_compact.get("scaffold_status")
    if scaffold_status == SCAFFOLD_READY:
        return (
            REVIEW_SCAFFOLD_READY,
            "Scaffold ready (dry-run only) — consider gated sandbox layout (not production authorization).",
            _next_commands_scaffold_status(scaffold_status),
        )

    if scaffold_status == "dry_run_only":
        return (
            REVIEW_SCAFFOLD_DRY_RUN_ONLY,
            "Scaffold dry-run only — review warnings before sandbox layout.",
            _next_commands_scaffold_status(scaffold_status),
        )

    return (
        REVIEW_SCAFFOLD_BLOCKED,
        "Scaffold blocked — resolve blocking items before advancing.",
        _next_commands_scaffold_status(str(scaffold_status or "blocked")),
    )


def _next_phase_for_review(review_status: str) -> str:
    if review_status == REVIEW_SCAFFOLD_READY:
        return NEXT_PHASE_SANDBOX
    if review_status == REVIEW_PREFLIGHT_BLOCKED:
        return NEXT_PHASE_PREFLIGHT
    if review_status == REVIEW_DRY_RUN_BLOCKED:
        return NEXT_PHASE_DRY_RUN
    return (
        "Phase 94 — resolve scaffold or upstream gate blockers "
        "(depending on gated scaffold review report)"
    )


def review_gated_scaffold(storage: LocalStorage) -> dict[str, Any]:
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

    resolve_preflight_blockers(storage)
    blockers_compact = compact_preflight_blockers(storage)
    steps.append(
        _step_record(
            "preflight_blockers",
            f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
            {
                "resolution_status": blockers_compact.get("resolution_status"),
                "preflight_level": blockers_compact.get("preflight_level"),
            },
        )
    )

    preflight_compact = compact_render_candidate_preflight(storage)
    preflight_level = preflight_compact.get("preflight_level")
    dry_run_skipped = preflight_level != PREFLIGHT_CANDIDATE_READY

    if dry_run_skipped:
        plan_compact = compact_render_candidate_dry_run_plan(storage)
        steps.append(
            _step_record(
                "gated_dry_run_review",
                f"{SUGGESTED_DRY_RUN_REVIEW_COMMAND} --refresh",
                {
                    "dry_run_plan_skipped": True,
                    "existing_plan_status": (load_render_candidate_dry_run_plan(storage) or {}).get(
                        "plan_status"
                    ),
                },
            )
        )
    else:
        generate_render_candidate_dry_run_plan(storage)
        plan_compact = compact_render_candidate_dry_run_plan(storage)
        steps.append(
            _step_record(
                "gated_dry_run_review",
                f"{SUGGESTED_DRY_RUN_REVIEW_COMMAND} --refresh",
                {
                    "dry_run_plan_skipped": False,
                    "plan_status": plan_compact.get("plan_status"),
                    "plan_reason": plan_compact.get("plan_reason"),
                },
            )
        )

    preflight_blockers, preflight_warnings = _preflight_blockers_and_warnings(preflight_compact)
    dry_run_blockers = _dry_run_blockers(plan_compact, skipped=dry_run_skipped)

    scaffold_skipped = (
        preflight_level != PREFLIGHT_CANDIDATE_READY
        or dry_run_skipped
        or plan_compact.get("plan_status") != DRY_RUN_PLAN_READY
    )

    if scaffold_skipped:
        scaffold_compact = compact_render_candidate_scaffold(storage)
        steps.append(
            _step_record(
                "scaffold",
                "(scaffold skipped — upstream gate closed)",
                {
                    "skipped": True,
                    "existing_scaffold_status": (load_render_candidate_scaffold(storage) or {}).get(
                        "scaffold_status"
                    ),
                },
            )
        )
    else:
        scaffold = generate_render_candidate_scaffold(storage)
        scaffold_compact = compact_render_candidate_scaffold(storage)
        steps.append(
            _step_record(
                "scaffold",
                f"{SUGGESTED_SCAFFOLD_COMMAND} --refresh",
                {
                    "skipped": False,
                    "scaffold_status": scaffold.get("scaffold_status"),
                    "scaffold_reason": scaffold.get("scaffold_reason"),
                    "execute_performed": scaffold.get("execute_performed"),
                },
            )
        )

    review_status, next_operator_step, next_commands = _classify_review_status(
        preflight=preflight_compact,
        dry_run_skipped=dry_run_skipped,
        plan_compact=plan_compact,
        scaffold_skipped=scaffold_skipped,
        scaffold_compact=scaffold_compact,
        preflight_blockers=preflight_blockers,
        dry_run_blockers=dry_run_blockers,
        blockers_compact=blockers_compact,
    )

    report = {
        "reviewed_at": _utc_now(),
        "review_status": review_status,
        "preflight_level": preflight_level,
        "preflight_reason": preflight_compact.get("preflight_reason"),
        "preflight_blockers": preflight_blockers,
        "preflight_warnings": preflight_warnings,
        "dry_run_plan_skipped": dry_run_skipped,
        "dry_run_plan_status": None if dry_run_skipped else plan_compact.get("plan_status"),
        "dry_run_plan_reason": None if dry_run_skipped else plan_compact.get("plan_reason"),
        "dry_run_plan_blockers": dry_run_blockers,
        "scaffold_skipped": scaffold_skipped,
        "scaffold_status": None if scaffold_skipped else scaffold_compact.get("scaffold_status"),
        "scaffold_reason": None if scaffold_skipped else scaffold_compact.get("scaffold_reason"),
        "scaffold_blocking_items": [] if scaffold_skipped else (scaffold_compact.get("blocking_items") or []),
        "execute_performed": False if scaffold_skipped else bool(scaffold_compact.get("execute_performed")),
        "resolution_status": blockers_compact.get("resolution_status"),
        "remaining_blockers": blockers_compact.get("remaining_blockers") or [],
        "next_operator_step": next_operator_step,
        "next_commands": next_commands,
        "next_phase_recommendation": _next_phase_for_review(review_status),
        "steps": steps,
        "safety_state": _current_safety_state(),
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }
    return save_gated_scaffold_review_report(storage, report)


def build_review_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Gated render candidate scaffold review",
        "",
        "> **WARNING:** Local gated scaffold review only. Advisory metadata — does **NOT** verify MRMS, "
        "execute candidate steps, enable production rendering, clear alerts, or authorize production use.",
        "",
        f"- Reviewed at: {report.get('reviewed_at')}",
        f"- Review status: **{report.get('review_status')}**",
        f"- Preflight level: {report.get('preflight_level')}",
        f"- Dry-run plan skipped: {report.get('dry_run_plan_skipped')}",
        f"- Dry-run plan status: {report.get('dry_run_plan_status') or '—'}",
        f"- Scaffold skipped: {report.get('scaffold_skipped')}",
        f"- Scaffold status: {report.get('scaffold_status') or '—'}",
        f"- Execute performed: {report.get('execute_performed')}",
        f"- Next operator step: {report.get('next_operator_step')}",
        "",
        "## Preflight blockers",
        "",
    ]
    for item in report.get("preflight_blockers") or []:
        lines.append(f"- {item}")
    if not report.get("preflight_blockers"):
        lines.append("- none")
    lines.extend(["", "## Preflight warnings", ""])
    for item in report.get("preflight_warnings") or []:
        lines.append(f"- {item}")
    if not report.get("preflight_warnings"):
        lines.append("- none")
    lines.extend(["", "## Dry-run plan blockers", ""])
    for item in report.get("dry_run_plan_blockers") or []:
        lines.append(f"- {item}")
    if not report.get("dry_run_plan_blockers"):
        lines.append("- none")
    if not report.get("scaffold_skipped"):
        lines.extend(["", "## Scaffold blocking items", ""])
        for item in report.get("scaffold_blocking_items") or []:
            lines.append(f"- {item}")
        if not report.get("scaffold_blocking_items"):
            lines.append("- none")
    lines.extend(["", "## Next commands", ""])
    for cmd in report.get("next_commands") or []:
        lines.append(f"- `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def save_gated_scaffold_review_report(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
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


def load_gated_scaffold_review_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
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


def compact_gated_scaffold_review(storage: LocalStorage) -> dict[str, Any]:
    latest = load_gated_scaffold_review_report(storage)
    if latest is None:
        preflight = compact_render_candidate_preflight(storage)
        plan = compact_render_candidate_dry_run_plan(storage)
        skipped_preflight = preflight.get("preflight_level") != PREFLIGHT_CANDIDATE_READY
        skipped_plan = skipped_preflight or plan.get("plan_status") != DRY_RUN_PLAN_READY
        if skipped_preflight:
            review_status = REVIEW_PREFLIGHT_BLOCKED
        elif skipped_plan:
            review_status = REVIEW_DRY_RUN_BLOCKED
        else:
            review_status = REVIEW_SCAFFOLD_BLOCKED
        return {
            "available": False,
            "review_status": review_status,
            "preflight_level": preflight.get("preflight_level"),
            "dry_run_plan_skipped": skipped_preflight,
            "dry_run_plan_status": None if skipped_preflight else plan.get("plan_status"),
            "scaffold_skipped": True,
            "execute_performed": False,
            "next_commands": _next_commands_preflight_blocked(
                preflight=preflight,
                blockers=compact_preflight_blockers(storage),
            ),
            "next_operator_step": "Run gated scaffold review after upstream gates open.",
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
        "preflight_blockers": latest.get("preflight_blockers") or [],
        "preflight_warnings": latest.get("preflight_warnings") or [],
        "dry_run_plan_skipped": bool(latest.get("dry_run_plan_skipped")),
        "dry_run_plan_status": latest.get("dry_run_plan_status"),
        "dry_run_plan_reason": latest.get("dry_run_plan_reason"),
        "dry_run_plan_blockers": latest.get("dry_run_plan_blockers") or [],
        "scaffold_skipped": bool(latest.get("scaffold_skipped")),
        "scaffold_status": latest.get("scaffold_status"),
        "scaffold_reason": latest.get("scaffold_reason"),
        "scaffold_blocking_items": latest.get("scaffold_blocking_items") or [],
        "execute_performed": bool(latest.get("execute_performed")),
        "resolution_status": latest.get("resolution_status"),
        "remaining_blockers": latest.get("remaining_blockers") or [],
        "next_commands": latest.get("next_commands") or [],
        "next_operator_step": latest.get("next_operator_step"),
        "reviewed_at": latest.get("reviewed_at"),
        "json_path": latest.get("json_path"),
        "markdown_path": latest.get("markdown_path"),
        "suggested_command": latest.get("suggested_command") or SUGGESTED_COMMAND,
        "next_phase_recommendation": latest.get("next_phase_recommendation"),
        **_safety_fields(),
    }


def build_gated_scaffold_review_payload(storage: LocalStorage) -> dict[str, Any]:
    return {
        **_safety_fields(),
        "latest": load_gated_scaffold_review_report(storage),
        "compact": compact_gated_scaffold_review(storage),
    }
