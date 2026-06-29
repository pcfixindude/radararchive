"""Gated sandbox comparison acknowledgment review — local advisory only; does NOT verify MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_dry_run_plan import (
    DRY_RUN_PLAN_READY,
    compact_render_candidate_dry_run_plan,
    generate_render_candidate_dry_run_plan,
    load_render_candidate_dry_run_plan,
)
from backend.app.services.mrms_render_candidate_gated_comparison_history import (
    SUGGESTED_COMMAND as SUGGESTED_GATED_COMPARISON_COMMAND,
)
from backend.app.services.mrms_render_candidate_gated_dry_run_review import (
    SUGGESTED_COMMAND as SUGGESTED_DRY_RUN_REVIEW_COMMAND,
)
from backend.app.services.mrms_render_candidate_gated_sandbox_layout import (
    REVIEW_LAYOUT_BLOCKED,
    REVIEW_LAYOUT_READY,
    SUGGESTED_COMMAND as SUGGESTED_LAYOUT_REVIEW_COMMAND,
)
from backend.app.services.mrms_render_candidate_gated_scaffold_review import (
    SUGGESTED_COMMAND as SUGGESTED_SCAFFOLD_REVIEW_COMMAND,
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
from backend.app.services.mrms_render_candidate_sandbox import (
    SANDBOX_READY,
    SUGGESTED_SANDBOX_COMMAND,
    compact_render_candidate_sandbox,
    generate_render_candidate_sandbox,
    load_sandbox_manifest,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_history import (
    HISTORY_READY,
    SUGGESTED_COMMAND as SUGGESTED_COMPARISON_HISTORY_COMMAND,
    compact_comparison_history,
    refresh_comparison_history_report,
)
from backend.app.services.mrms_render_candidate_gated_trend_review import (
    SUGGESTED_COMMAND as SUGGESTED_GATED_TREND_COMMAND,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status import (
    ROLLUP_BLOCKED,
    ROLLUP_CURRENT,
    ROLLUP_NEEDS_ACKNOWLEDGMENT,
    ROLLUP_NOT_NEEDED,
    ROLLUP_STALE,
    SUGGESTED_COMMAND as SUGGESTED_ACK_STATUS_COMMAND,
    compact_sandbox_comparison_acknowledgment_status,
    refresh_sandbox_comparison_acknowledgment_status,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_trend_hint import (
    HINT_BLOCKED,
    HINT_MISSING,
    HINT_NEEDS_REVIEW,
    HINT_READY,
    SUGGESTED_COMMAND as SUGGESTED_TREND_HINT_COMMAND,
    compact_sandbox_comparison_trend_hint,
    refresh_sandbox_comparison_trend_hint,
)
from backend.app.services.mrms_render_candidate_sandbox_import_export import (
    STATUS_IMPORTED,
    compact_render_candidate_sandbox_import_export,
    load_import_export_status,
    run_import_export_workflow,
    SUGGESTED_IMPORT_EXPORT_COMMAND,
)
from backend.app.services.mrms_render_candidate_scaffold import (
    SCAFFOLD_READY,
    compact_render_candidate_scaffold,
    generate_render_candidate_scaffold,
    load_render_candidate_scaffold,
)
from backend.app.services.storage import LocalStorage

REVIEW_JSON = "dev/mrms_render_candidate_gated_comparison_ack_latest.json"
REVIEW_MD = "dev/mrms_render_candidate_gated_comparison_ack_latest.md"

SUGGESTED_COMMAND = "make mrms-review-gated-ack"

REVIEW_PREFLIGHT_BLOCKED = "preflight_not_candidate_ready"
REVIEW_DRY_RUN_BLOCKED = "dry_run_plan_not_ready"
REVIEW_SCAFFOLD_BLOCKED = "scaffold_not_ready"
REVIEW_LAYOUT_NOT_READY = "sandbox_layout_not_ready"
REVIEW_MANIFEST_IO_NOT_READY = "manifest_io_not_ready"
REVIEW_COMPARISON_NOT_READY = "comparison_history_not_ready"
REVIEW_TREND_NOT_READY = "trend_hint_not_ready"
REVIEW_TREND_BLOCKED = "trend_hint_blocked"
REVIEW_ACK_BLOCKED = "comparison_ack_blocked"
REVIEW_ACK_NEEDS_ACK = "comparison_ack_needs_acknowledgment"
REVIEW_ACK_STALE = "comparison_ack_stale"
REVIEW_ACK_READY = "comparison_ack_ready"

NEXT_PHASE_ACK_HISTORY = (
    "Phase 99 — gated sandbox acknowledgment history "
    "(local acknowledgment history rollup without production authorization)"
)
NEXT_PHASE_PREFLIGHT = (
    "Phase 98 — resolve preflight evidence "
    "(until candidate_preflight_ready before comparison acknowledgment)"
)
NEXT_PHASE_DRY_RUN = (
    "Phase 98 — complete gated dry-run plan review "
    "(until dry_run_plan_ready before comparison acknowledgment)"
)
NEXT_PHASE_SCAFFOLD = (
    "Phase 98 — complete gated scaffold review "
    "(until scaffold_ready before comparison acknowledgment)"
)
NEXT_PHASE_LAYOUT = (
    "Phase 98 — complete gated sandbox layout review "
    "(until sandbox_layout_ready before comparison acknowledgment)"
)
NEXT_PHASE_MANIFEST_IO = (
    "Phase 98 — complete gated manifest import/export "
    "(until manifest_io ready before comparison acknowledgment)"
)
NEXT_PHASE_COMPARISON = (
    "Phase 98 — complete gated comparison history "
    "(until comparison_history_ready before comparison acknowledgment)"
)
NEXT_PHASE_TREND = (
    "Phase 98 — complete gated trend hint review "
    "(until trend_hint_ready before comparison acknowledgment)"
)

_LAYOUT_READY_STATUSES = frozenset({SANDBOX_READY, "needs_cleanup"})
_MANIFEST_IO_READY_STATUSES = frozenset({STATUS_IMPORTED, "import_ready", "export_ready"})


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_gated_comparison_ack_only": True,
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
        "comparison_ack_ready_is_not_production_authorization": True,
        "trend_hint_ready_is_not_production_authorization": True,
        "comparison_history_ready_is_not_production_authorization": True,
        "manifest_io_ready_is_not_production_authorization": True,
        "sandbox_layout_ready_is_not_production_authorization": True,
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


def _scaffold_blockers(scaffold: dict[str, Any], *, skipped: bool) -> list[str]:
    if skipped:
        return ["scaffold not generated — upstream gate closed"]
    blockers: list[str] = []
    status = scaffold.get("scaffold_status")
    if status != SCAFFOLD_READY:
        blockers.append(f"scaffold status is {status or 'missing'} (need scaffold_ready)")
    for item in scaffold.get("blocking_items") or []:
        if item not in blockers:
            blockers.append(str(item))
    return blockers


def _layout_blockers(sandbox: dict[str, Any], *, skipped: bool) -> list[str]:
    if skipped:
        return ["sandbox layout not generated — upstream gate closed"]
    blockers: list[str] = []
    status = sandbox.get("sandbox_status")
    if status not in _LAYOUT_READY_STATUSES:
        blockers.append(
            f"sandbox layout status is {status or 'missing'} (need sandbox_layout_ready)"
        )
    for item in sandbox.get("blocking_items") or []:
        if item not in blockers:
            blockers.append(str(item))
    return blockers


def _sandbox_layout_ready(sandbox_compact: dict[str, Any]) -> bool:
    return sandbox_compact.get("sandbox_status") in _LAYOUT_READY_STATUSES


def _manifest_io_ready(manifest_compact: dict[str, Any]) -> bool:
    return manifest_compact.get("import_export_status") in _MANIFEST_IO_READY_STATUSES


def _comparison_history_ready(comparison_compact: dict[str, Any]) -> bool:
    return comparison_compact.get("history_status") == HISTORY_READY


def _trend_hint_ready(trend_compact: dict[str, Any]) -> bool:
    return trend_compact.get("hint_status") in {HINT_READY, HINT_NEEDS_REVIEW}


def _next_commands_preflight_blocked(
    *,
    preflight: dict[str, Any],
    blockers: dict[str, Any],
) -> list[str]:
    commands = [
        f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
        f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
    ]
    for cmd in blockers.get("suggested_commands") or []:
        if cmd not in commands:
            commands.append(str(cmd))
    if preflight.get("preflight_level") == PREFLIGHT_NEEDS_REVIEW:
        for cmd in (
            f"{SUGGESTED_DRY_RUN_REVIEW_COMMAND} --refresh",
            f"{SUGGESTED_LAYOUT_REVIEW_COMMAND} --refresh",
            f"{SUGGESTED_GATED_COMPARISON_COMMAND} --refresh",
            f"{SUGGESTED_GATED_TREND_COMMAND} --refresh",
            f"{SUGGESTED_COMMAND} --refresh",
        ):
            if cmd not in commands:
                commands.append(cmd)
    return commands


def _next_commands_dry_run_blocked() -> list[str]:
    return [
        f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
        f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
        f"{SUGGESTED_DRY_RUN_REVIEW_COMMAND} --refresh",
        f"{SUGGESTED_LAYOUT_REVIEW_COMMAND} --refresh",
        f"{SUGGESTED_GATED_COMPARISON_COMMAND} --refresh",
        f"{SUGGESTED_GATED_TREND_COMMAND} --refresh",
        f"{SUGGESTED_COMMAND} --refresh",
    ]


def _next_commands_scaffold_blocked() -> list[str]:
    return [
        f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
        f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
        f"{SUGGESTED_DRY_RUN_REVIEW_COMMAND} --refresh",
        f"{SUGGESTED_SCAFFOLD_REVIEW_COMMAND} --refresh",
        f"{SUGGESTED_LAYOUT_REVIEW_COMMAND} --refresh",
        f"{SUGGESTED_GATED_COMPARISON_COMMAND} --refresh",
        f"{SUGGESTED_GATED_TREND_COMMAND} --refresh",
        f"{SUGGESTED_COMMAND} --refresh",
    ]


def _next_commands_layout_blocked() -> list[str]:
    return [
        f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
        f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
        f"{SUGGESTED_DRY_RUN_REVIEW_COMMAND} --refresh",
        f"{SUGGESTED_SCAFFOLD_REVIEW_COMMAND} --refresh",
        f"{SUGGESTED_LAYOUT_REVIEW_COMMAND} --refresh",
        f"{SUGGESTED_SANDBOX_COMMAND} --refresh",
        f"{SUGGESTED_GATED_COMPARISON_COMMAND} --refresh",
        f"{SUGGESTED_GATED_TREND_COMMAND} --refresh",
        f"{SUGGESTED_COMMAND} --refresh",
    ]


def _next_commands_manifest_io_not_ready() -> list[str]:
    return [
        f"{SUGGESTED_IMPORT_EXPORT_COMMAND} --refresh",
        f"{SUGGESTED_LAYOUT_REVIEW_COMMAND} --refresh",
        f"{SUGGESTED_GATED_COMPARISON_COMMAND} --refresh",
        f"{SUGGESTED_GATED_TREND_COMMAND} --refresh",
        f"{SUGGESTED_COMMAND} --refresh",
    ]


def _next_commands_comparison_not_ready() -> list[str]:
    return [
        f"{SUGGESTED_GATED_COMPARISON_COMMAND} --refresh",
        f"{SUGGESTED_COMPARISON_HISTORY_COMMAND} --refresh",
        f"{SUGGESTED_IMPORT_EXPORT_COMMAND} --refresh",
        f"{SUGGESTED_GATED_TREND_COMMAND} --refresh",
        f"{SUGGESTED_COMMAND} --refresh",
    ]


def _next_commands_trend_not_ready() -> list[str]:
    return [
        f"{SUGGESTED_GATED_TREND_COMMAND} --refresh",
        f"{SUGGESTED_GATED_COMPARISON_COMMAND} --refresh",
        f"{SUGGESTED_COMMAND} --refresh",
    ]


def _next_commands_comparison_ack() -> list[str]:
    return [f"{SUGGESTED_COMMAND} --refresh"]


def _classify_review_status(
    *,
    preflight: dict[str, Any],
    dry_run_skipped: bool,
    plan_compact: dict[str, Any],
    scaffold_skipped: bool,
    scaffold_compact: dict[str, Any],
    sandbox_skipped: bool,
    sandbox_compact: dict[str, Any],
    manifest_io_skipped: bool,
    manifest_compact: dict[str, Any],
    comparison_skipped: bool,
    comparison_compact: dict[str, Any],
    trend_skipped: bool,
    trend_compact: dict[str, Any],
    ack_skipped: bool,
    ack_compact: dict[str, Any],
    blockers_compact: dict[str, Any],
) -> tuple[str, str, list[str]]:
    if preflight.get("preflight_level") != PREFLIGHT_CANDIDATE_READY:
        return (
            REVIEW_PREFLIGHT_BLOCKED,
            "Preflight is not candidate_preflight_ready — comparison acknowledgment not run.",
            _next_commands_preflight_blocked(preflight=preflight, blockers=blockers_compact),
        )

    if dry_run_skipped or plan_compact.get("plan_status") != DRY_RUN_PLAN_READY:
        return (
            REVIEW_DRY_RUN_BLOCKED,
            "Dry-run plan is not dry_run_plan_ready — comparison acknowledgment not run.",
            _next_commands_dry_run_blocked(),
        )

    if scaffold_skipped or scaffold_compact.get("scaffold_status") != SCAFFOLD_READY:
        return (
            REVIEW_SCAFFOLD_BLOCKED,
            "Scaffold is not scaffold_ready — comparison acknowledgment not run.",
            _next_commands_scaffold_blocked(),
        )

    if sandbox_skipped or not _sandbox_layout_ready(sandbox_compact):
        return (
            REVIEW_LAYOUT_NOT_READY,
            "Sandbox layout is not sandbox_layout_ready — comparison acknowledgment not run.",
            _next_commands_layout_blocked(),
        )

    if manifest_io_skipped or not _manifest_io_ready(manifest_compact):
        return (
            REVIEW_MANIFEST_IO_NOT_READY,
            "Manifest import/export is not ready — comparison acknowledgment not run.",
            _next_commands_manifest_io_not_ready(),
        )

    if comparison_skipped or not _comparison_history_ready(comparison_compact):
        return (
            REVIEW_COMPARISON_NOT_READY,
            "Comparison history is not comparison_history_ready — comparison acknowledgment not run.",
            _next_commands_comparison_not_ready(),
        )

    if ack_skipped or not _trend_hint_ready(trend_compact):
        hint_status = trend_compact.get("hint_status")
        if hint_status in {HINT_BLOCKED, HINT_MISSING}:
            return (
                REVIEW_TREND_BLOCKED,
                "Trend hint blocked — comparison acknowledgment not run.",
                _next_commands_trend_not_ready(),
            )
        return (
            REVIEW_TREND_NOT_READY,
            "Trend hint is not trend_hint_ready — comparison acknowledgment not run.",
            _next_commands_trend_not_ready(),
        )

    rollup_status = ack_compact.get("rollup_status")
    if rollup_status == ROLLUP_BLOCKED:
        return (
            REVIEW_ACK_BLOCKED,
            "Comparison acknowledgment blocked — resolve blockers before advancing.",
            _next_commands_comparison_ack(),
        )
    if rollup_status == ROLLUP_NEEDS_ACKNOWLEDGMENT:
        return (
            REVIEW_ACK_NEEDS_ACK,
            "Comparison acknowledgment needs operator acknowledgment (local advisory).",
            _next_commands_comparison_ack(),
        )
    if rollup_status == ROLLUP_STALE:
        return (
            REVIEW_ACK_STALE,
            "Comparison acknowledgment stale — re-record local review acknowledgment.",
            _next_commands_comparison_ack(),
        )
    if rollup_status in {ROLLUP_CURRENT, ROLLUP_NOT_NEEDED}:
        return (
            REVIEW_ACK_READY,
            "Comparison acknowledgment ready (local advisory) — consider acknowledgment history.",
            _next_commands_comparison_ack(),
        )

    return (
        REVIEW_ACK_BLOCKED,
        "Comparison acknowledgment blocked — resolve blocking items before advancing.",
        _next_commands_comparison_ack(),
    )


def _next_phase_for_review(review_status: str) -> str:
    if review_status in {REVIEW_ACK_READY, REVIEW_ACK_NEEDS_ACK, REVIEW_ACK_STALE}:
        return NEXT_PHASE_ACK_HISTORY
    if review_status == REVIEW_PREFLIGHT_BLOCKED:
        return NEXT_PHASE_PREFLIGHT
    if review_status == REVIEW_DRY_RUN_BLOCKED:
        return NEXT_PHASE_DRY_RUN
    if review_status == REVIEW_SCAFFOLD_BLOCKED:
        return NEXT_PHASE_SCAFFOLD
    if review_status == REVIEW_LAYOUT_NOT_READY:
        return NEXT_PHASE_LAYOUT
    if review_status == REVIEW_MANIFEST_IO_NOT_READY:
        return NEXT_PHASE_MANIFEST_IO
    if review_status == REVIEW_COMPARISON_NOT_READY:
        return NEXT_PHASE_COMPARISON
    if review_status in {REVIEW_TREND_NOT_READY, REVIEW_TREND_BLOCKED}:
        return NEXT_PHASE_TREND
    return (
        "Phase 98 — resolve comparison acknowledgment or upstream gate blockers "
        "(depending on gated comparison acknowledgment report)"
    )


def review_gated_comparison_ack(storage: LocalStorage) -> dict[str, Any]:
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

    scaffold_skipped = (
        preflight_level != PREFLIGHT_CANDIDATE_READY
        or dry_run_skipped
        or plan_compact.get("plan_status") != DRY_RUN_PLAN_READY
    )

    if scaffold_skipped:
        scaffold_compact = compact_render_candidate_scaffold(storage)
        steps.append(
            _step_record(
                "gated_scaffold_review",
                f"{SUGGESTED_SCAFFOLD_REVIEW_COMMAND} --refresh",
                {
                    "scaffold_skipped": True,
                    "existing_scaffold_status": (load_render_candidate_scaffold(storage) or {}).get(
                        "scaffold_status"
                    ),
                },
            )
        )
    else:
        generate_render_candidate_scaffold(storage)
        scaffold_compact = compact_render_candidate_scaffold(storage)
        steps.append(
            _step_record(
                "gated_scaffold_review",
                f"{SUGGESTED_SCAFFOLD_REVIEW_COMMAND} --refresh",
                {
                    "scaffold_skipped": False,
                    "scaffold_status": scaffold_compact.get("scaffold_status"),
                    "scaffold_reason": scaffold_compact.get("scaffold_reason"),
                },
            )
        )

    sandbox_skipped = scaffold_skipped or scaffold_compact.get("scaffold_status") != SCAFFOLD_READY

    if sandbox_skipped:
        sandbox_compact = compact_render_candidate_sandbox(storage)
        steps.append(
            _step_record(
                "gated_sandbox_layout",
                f"{SUGGESTED_LAYOUT_REVIEW_COMMAND} --refresh",
                {
                    "sandbox_skipped": True,
                    "existing_sandbox_status": (load_sandbox_manifest(storage) or {}).get(
                        "sandbox_status"
                    ),
                },
            )
        )
    else:
        generate_render_candidate_sandbox(storage)
        sandbox_compact = compact_render_candidate_sandbox(storage)
        steps.append(
            _step_record(
                "gated_sandbox_layout",
                f"{SUGGESTED_LAYOUT_REVIEW_COMMAND} --refresh",
                {
                    "sandbox_skipped": False,
                    "sandbox_status": sandbox_compact.get("sandbox_status"),
                    "sandbox_reason": sandbox_compact.get("sandbox_reason"),
                    "layout_review_status": REVIEW_LAYOUT_READY
                    if _sandbox_layout_ready(sandbox_compact)
                    else REVIEW_LAYOUT_BLOCKED,
                },
            )
        )

    preflight_blockers, preflight_warnings = _preflight_blockers_and_warnings(preflight_compact)
    dry_run_blockers = _dry_run_blockers(plan_compact, skipped=dry_run_skipped)
    scaffold_blockers = _scaffold_blockers(scaffold_compact, skipped=scaffold_skipped)
    layout_blockers = _layout_blockers(sandbox_compact, skipped=sandbox_skipped)

    manifest_io_skipped = sandbox_skipped or not _sandbox_layout_ready(sandbox_compact)

    if manifest_io_skipped:
        manifest_compact = compact_render_candidate_sandbox_import_export(storage)
        steps.append(
            _step_record(
                "manifest_io",
                "(manifest import/export skipped — upstream gate closed)",
                {
                    "skipped": True,
                    "existing_import_export_status": (load_import_export_status(storage) or {}).get(
                        "import_export_status"
                    ),
                },
            )
        )
    else:
        run_import_export_workflow(storage, export=True, import_after_export=True)
        manifest_compact = compact_render_candidate_sandbox_import_export(storage)
        steps.append(
            _step_record(
                "manifest_io",
                f"{SUGGESTED_IMPORT_EXPORT_COMMAND} --refresh",
                {
                    "skipped": False,
                    "import_export_status": manifest_compact.get("import_export_status"),
                    "import_export_reason": manifest_compact.get("import_export_reason"),
                },
            )
        )

    comparison_skipped = manifest_io_skipped or not _manifest_io_ready(manifest_compact)

    if comparison_skipped:
        comparison_compact = compact_comparison_history(storage)
        steps.append(
            _step_record(
                "comparison_history",
                "(comparison history skipped — manifest import/export not ready)",
                {
                    "skipped": True,
                    "existing_history_status": comparison_compact.get("history_status"),
                },
            )
        )
    else:
        refresh_comparison_history_report(storage)
        comparison_compact = compact_comparison_history(storage)
        steps.append(
            _step_record(
                "comparison_history",
                f"{SUGGESTED_GATED_COMPARISON_COMMAND} --refresh",
                {
                    "skipped": False,
                    "history_status": comparison_compact.get("history_status"),
                    "history_reason": comparison_compact.get("history_reason"),
                    "history_count": comparison_compact.get("history_count"),
                },
            )
        )

    trend_skipped = comparison_skipped or not _comparison_history_ready(comparison_compact)

    if trend_skipped:
        trend_compact = compact_sandbox_comparison_trend_hint(storage)
        steps.append(
            _step_record(
                "trend_hint",
                "(trend hint skipped — comparison history not ready)",
                {
                    "skipped": True,
                    "existing_hint_status": trend_compact.get("hint_status"),
                    "existing_trend": trend_compact.get("trend"),
                },
            )
        )
    else:
        refresh_sandbox_comparison_trend_hint(storage)
        trend_compact = compact_sandbox_comparison_trend_hint(storage)
        steps.append(
            _step_record(
                "trend_hint",
                f"{SUGGESTED_GATED_TREND_COMMAND} --refresh",
                {
                    "skipped": False,
                    "hint_status": trend_compact.get("hint_status"),
                    "hint_reason": trend_compact.get("hint_reason"),
                    "trend": trend_compact.get("trend"),
                    "trend_review_recommended": trend_compact.get("trend_review_recommended"),
                },
            )
        )

    ack_skipped = trend_skipped or not _trend_hint_ready(trend_compact)

    if ack_skipped:
        ack_compact = compact_sandbox_comparison_acknowledgment_status(storage)
        steps.append(
            _step_record(
                "comparison_ack",
                "(comparison acknowledgment skipped — trend hint not ready)",
                {
                    "skipped": True,
                    "existing_rollup_status": ack_compact.get("rollup_status"),
                    "existing_acknowledgment_status": ack_compact.get("acknowledgment_status"),
                },
            )
        )
    else:
        refresh_sandbox_comparison_acknowledgment_status(storage)
        ack_compact = compact_sandbox_comparison_acknowledgment_status(storage)
        steps.append(
            _step_record(
                "comparison_ack",
                f"{SUGGESTED_ACK_STATUS_COMMAND} --refresh",
                {
                    "skipped": False,
                    "rollup_status": ack_compact.get("rollup_status"),
                    "acknowledgment_status": ack_compact.get("acknowledgment_status"),
                    "status_reason": ack_compact.get("status_reason"),
                    "stale_acknowledgment": ack_compact.get("stale_acknowledgment"),
                },
            )
        )

    review_status, next_operator_step, next_commands = _classify_review_status(
        preflight=preflight_compact,
        dry_run_skipped=dry_run_skipped,
        plan_compact=plan_compact,
        scaffold_skipped=scaffold_skipped,
        scaffold_compact=scaffold_compact,
        sandbox_skipped=sandbox_skipped,
        sandbox_compact=sandbox_compact,
        manifest_io_skipped=manifest_io_skipped,
        manifest_compact=manifest_compact,
        comparison_skipped=comparison_skipped,
        comparison_compact=comparison_compact,
        trend_skipped=trend_skipped,
        trend_compact=trend_compact,
        ack_skipped=ack_skipped,
        ack_compact=ack_compact,
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
        "scaffold_blockers": scaffold_blockers,
        "sandbox_skipped": sandbox_skipped,
        "sandbox_status": None if sandbox_skipped else sandbox_compact.get("sandbox_status"),
        "sandbox_reason": None if sandbox_skipped else sandbox_compact.get("sandbox_reason"),
        "sandbox_layout_blockers": layout_blockers,
        "sandbox_root": None if sandbox_skipped else sandbox_compact.get("sandbox_root"),
        "manifest_io_skipped": manifest_io_skipped,
        "import_export_status": None if manifest_io_skipped else manifest_compact.get("import_export_status"),
        "import_export_reason": None if manifest_io_skipped else manifest_compact.get("import_export_reason"),
        "manifest_io_blockers": [] if manifest_io_skipped else (manifest_compact.get("blockers") or []),
        "manifest_io_warnings": [] if manifest_io_skipped else (manifest_compact.get("warnings") or []),
        "included_reports": [] if manifest_io_skipped else (manifest_compact.get("included_reports") or []),
        "comparison_skipped": comparison_skipped,
        "history_status": None if comparison_skipped else comparison_compact.get("history_status"),
        "history_reason": None if comparison_skipped else comparison_compact.get("history_reason"),
        "history_count": 0 if comparison_skipped else (comparison_compact.get("history_count") or 0),
        "comparison_history_blockers": [] if comparison_skipped else (comparison_compact.get("blockers") or []),
        "comparison_history_warnings": [] if comparison_skipped else (comparison_compact.get("warnings") or []),
        "trend_skipped": trend_skipped,
        "hint_status": None if trend_skipped else trend_compact.get("hint_status"),
        "hint_reason": None if trend_skipped else trend_compact.get("hint_reason"),
        "trend": None if trend_skipped else trend_compact.get("trend"),
        "trend_review_recommended": False
        if trend_skipped
        else bool(trend_compact.get("trend_review_recommended")),
        "trend_blockers": [] if trend_skipped else (trend_compact.get("blockers") or []),
        "trend_warnings": [] if trend_skipped else (trend_compact.get("warnings") or []),
        "recurring_signals": [] if trend_skipped else (trend_compact.get("recurring_signals") or []),
        "ack_skipped": ack_skipped,
        "rollup_status": None if ack_skipped else ack_compact.get("rollup_status"),
        "acknowledgment_status": None if ack_skipped else ack_compact.get("acknowledgment_status"),
        "status_reason": None if ack_skipped else ack_compact.get("status_reason"),
        "stale_acknowledgment": False if ack_skipped else bool(ack_compact.get("stale_acknowledgment")),
        "acknowledgment_count": 0 if ack_skipped else (ack_compact.get("acknowledgment_count") or 0),
        "ack_blockers": [] if ack_skipped else (ack_compact.get("blockers") or []),
        "ack_warnings": [] if ack_skipped else (ack_compact.get("warnings") or []),
        "suggested_action": None if ack_skipped else ack_compact.get("suggested_action"),
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
    return save_gated_comparison_ack_report(storage, report)


def build_review_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Gated sandbox comparison acknowledgment review",
        "",
        "> **WARNING:** Local gated comparison acknowledgment review only. Advisory metadata — does **NOT** "
        "verify MRMS, enable production rendering, clear alerts, or authorize production use.",
        "",
        f"- Reviewed at: {report.get('reviewed_at')}",
        f"- Review status: **{report.get('review_status')}**",
        f"- Preflight level: {report.get('preflight_level')}",
        f"- Dry-run plan skipped: {report.get('dry_run_plan_skipped')}",
        f"- Scaffold skipped: {report.get('scaffold_skipped')}",
        f"- Sandbox skipped: {report.get('sandbox_skipped')}",
        f"- Manifest IO skipped: {report.get('manifest_io_skipped')}",
        f"- Comparison skipped: {report.get('comparison_skipped')}",
        f"- Trend skipped: {report.get('trend_skipped')}",
        f"- Ack skipped: {report.get('ack_skipped')}",
        f"- Import/export status: {report.get('import_export_status') or '—'}",
        f"- History status: {report.get('history_status') or '—'}",
        f"- Hint status: {report.get('hint_status') or '—'}",
        f"- Trend: {report.get('trend') or '—'}",
        f"- Rollup status: {report.get('rollup_status') or '—'}",
        f"- Acknowledgment status: {report.get('acknowledgment_status') or '—'}",
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
    lines.extend(["", "## Scaffold blockers", ""])
    for item in report.get("scaffold_blockers") or []:
        lines.append(f"- {item}")
    if not report.get("scaffold_blockers"):
        lines.append("- none")
    lines.extend(["", "## Sandbox layout blockers", ""])
    for item in report.get("sandbox_layout_blockers") or []:
        lines.append(f"- {item}")
    if not report.get("sandbox_layout_blockers"):
        lines.append("- none")
    if not report.get("manifest_io_skipped"):
        lines.extend(["", "## Manifest IO blockers", ""])
        for item in report.get("manifest_io_blockers") or []:
            lines.append(f"- {item}")
        if not report.get("manifest_io_blockers"):
            lines.append("- none")
    if not report.get("comparison_skipped"):
        lines.extend(["", "## Comparison history blockers", ""])
        for item in report.get("comparison_history_blockers") or []:
            lines.append(f"- {item}")
        if not report.get("comparison_history_blockers"):
            lines.append("- none")
    if not report.get("trend_skipped"):
        lines.extend(["", "## Trend hint blockers", ""])
        for item in report.get("trend_blockers") or []:
            lines.append(f"- {item}")
        if not report.get("trend_blockers"):
            lines.append("- none")
        lines.extend(["", "## Trend hint warnings", ""])
        for item in report.get("trend_warnings") or []:
            lines.append(f"- {item}")
        if not report.get("trend_warnings"):
            lines.append("- none")
    if not report.get("ack_skipped"):
        lines.extend(["", "## Acknowledgment blockers", ""])
        for item in report.get("ack_blockers") or []:
            lines.append(f"- {item}")
        if not report.get("ack_blockers"):
            lines.append("- none")
        lines.extend(["", "## Acknowledgment warnings", ""])
        for item in report.get("ack_warnings") or []:
            lines.append(f"- {item}")
        if not report.get("ack_warnings"):
            lines.append("- none")
    lines.extend(["", "## Next commands", ""])
    for cmd in report.get("next_commands") or []:
        lines.append(f"- `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def save_gated_comparison_ack_report(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
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


def load_gated_comparison_ack_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
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


def compact_gated_comparison_ack(storage: LocalStorage) -> dict[str, Any]:
    latest = load_gated_comparison_ack_report(storage)
    if latest is None:
        preflight = compact_render_candidate_preflight(storage)
        plan = compact_render_candidate_dry_run_plan(storage)
        scaffold = compact_render_candidate_scaffold(storage)
        sandbox = compact_render_candidate_sandbox(storage)
        skipped_preflight = preflight.get("preflight_level") != PREFLIGHT_CANDIDATE_READY
        skipped_plan = skipped_preflight or plan.get("plan_status") != DRY_RUN_PLAN_READY
        skipped_scaffold = skipped_plan or scaffold.get("scaffold_status") != SCAFFOLD_READY
        skipped_layout = skipped_scaffold or not _sandbox_layout_ready(sandbox)
        if skipped_preflight:
            review_status = REVIEW_PREFLIGHT_BLOCKED
        elif skipped_plan:
            review_status = REVIEW_DRY_RUN_BLOCKED
        elif skipped_scaffold:
            review_status = REVIEW_SCAFFOLD_BLOCKED
        elif skipped_layout:
            review_status = REVIEW_LAYOUT_NOT_READY
        else:
            review_status = REVIEW_MANIFEST_IO_NOT_READY
        return {
            "available": False,
            "review_status": review_status,
            "preflight_level": preflight.get("preflight_level"),
            "dry_run_plan_skipped": skipped_preflight,
            "scaffold_skipped": skipped_plan,
            "sandbox_skipped": skipped_scaffold,
            "manifest_io_skipped": True,
            "comparison_skipped": True,
            "trend_skipped": True,
            "ack_skipped": True,
            "history_count": 0,
            "acknowledgment_count": 0,
            "next_commands": _next_commands_preflight_blocked(
                preflight=preflight,
                blockers=compact_preflight_blockers(storage),
            ),
            "next_operator_step": "Run gated comparison acknowledgment after upstream gates open.",
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
        "scaffold_blockers": latest.get("scaffold_blockers") or [],
        "sandbox_skipped": bool(latest.get("sandbox_skipped")),
        "sandbox_status": latest.get("sandbox_status"),
        "sandbox_reason": latest.get("sandbox_reason"),
        "sandbox_layout_blockers": latest.get("sandbox_layout_blockers") or [],
        "sandbox_root": latest.get("sandbox_root"),
        "manifest_io_skipped": bool(latest.get("manifest_io_skipped")),
        "import_export_status": latest.get("import_export_status"),
        "import_export_reason": latest.get("import_export_reason"),
        "manifest_io_blockers": latest.get("manifest_io_blockers") or [],
        "manifest_io_warnings": latest.get("manifest_io_warnings") or [],
        "included_reports": latest.get("included_reports") or [],
        "comparison_skipped": bool(latest.get("comparison_skipped")),
        "history_status": latest.get("history_status"),
        "history_reason": latest.get("history_reason"),
        "history_count": latest.get("history_count") if latest.get("history_count") is not None else 0,
        "comparison_history_blockers": latest.get("comparison_history_blockers") or [],
        "comparison_history_warnings": latest.get("comparison_history_warnings") or [],
        "trend_skipped": bool(latest.get("trend_skipped")),
        "hint_status": latest.get("hint_status"),
        "hint_reason": latest.get("hint_reason"),
        "trend": latest.get("trend"),
        "trend_review_recommended": bool(latest.get("trend_review_recommended")),
        "trend_blockers": latest.get("trend_blockers") or [],
        "trend_warnings": latest.get("trend_warnings") or [],
        "recurring_signals": latest.get("recurring_signals") or [],
        "ack_skipped": bool(latest.get("ack_skipped")),
        "rollup_status": latest.get("rollup_status"),
        "acknowledgment_status": latest.get("acknowledgment_status"),
        "status_reason": latest.get("status_reason"),
        "stale_acknowledgment": bool(latest.get("stale_acknowledgment")),
        "acknowledgment_count": latest.get("acknowledgment_count")
        if latest.get("acknowledgment_count") is not None
        else 0,
        "ack_blockers": latest.get("ack_blockers") or [],
        "ack_warnings": latest.get("ack_warnings") or [],
        "suggested_action": latest.get("suggested_action"),
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


def build_gated_comparison_ack_payload(storage: LocalStorage) -> dict[str, Any]:
    return {
        **_safety_fields(),
        "latest": load_gated_comparison_ack_report(storage),
        "compact": compact_gated_comparison_ack(storage),
    }
