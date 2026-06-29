"""MRMS render candidate command scaffold — disabled-by-default, dry-run/no-op only."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_dry_run_plan import (
    DRY_RUN_BLOCKED,
    DRY_RUN_NEEDS_REVIEW,
    DRY_RUN_PLAN_READY,
    evaluate_dry_run_plan_status,
    gather_dry_run_context,
    load_render_candidate_dry_run_plan,
)
from backend.app.services.mrms_render_candidate_preflight import (
    PREFLIGHT_BLOCKED,
    PREFLIGHT_CANDIDATE_READY,
    PREFLIGHT_NEEDS_REVIEW,
    REQUIRED_DOC_PATHS,
    evaluate_render_candidate_preflight,
    gather_preflight_evidence,
    load_render_candidate_preflight,
)
from backend.app.services.storage import LocalStorage

SCAFFOLD_JSON = "dev/mrms_render_candidate_scaffold.json"
SCAFFOLD_MD = "dev/mrms_render_candidate_scaffold.md"

SUGGESTED_SCAFFOLD_COMMAND = "make mrms-render-candidate-scaffold"

SCAFFOLD_BLOCKED = "blocked"
SCAFFOLD_DRY_RUN_ONLY = "dry_run_only"
SCAFFOLD_READY = "scaffold_ready"

EXECUTE_ENV_VAR = "ENABLE_MRMS_RENDER_CANDIDATE_EXECUTE"
EXECUTE_DEFAULT = "false"

NEXT_PHASE_RECOMMENDATION = (
    "Phase 65 — Gated candidate artifact sandbox layout "
    "(local sandbox directory layout isolated from production tile serving; disabled by default)"
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _scaffold_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(SCAFFOLD_JSON)


def _scaffold_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(SCAFFOLD_MD)


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_scaffold_only": True,
        "disabled_by_default": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "does_not_download_or_decode": True,
        "does_not_create_production_tiles": True,
        "does_not_serve_production_tiles": True,
        "does_not_execute_by_default": True,
        "no_external_notifications": True,
        "does_not_authorize_production_use": True,
        "prototype": True,
    }


def _required_docs_status() -> list[dict[str, Any]]:
    root = _project_root()
    return [
        {"path": relative_path, "available": (root / relative_path).is_file()}
        for relative_path in REQUIRED_DOC_PATHS
    ]


def _current_safety_state() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "enable_production_radar_tiles": settings.enable_production_radar_tiles,
        "enable_decoded_tiles": settings.enable_decoded_tiles,
        "placeholder_default": not settings.enable_production_radar_tiles
        and not settings.enable_decoded_tiles,
        "production_tile_serving_enabled": settings.enable_production_radar_tiles,
    }


def _execute_opt_in_status() -> dict[str, Any]:
    raw = os.environ.get(EXECUTE_ENV_VAR, EXECUTE_DEFAULT)
    enabled = str(raw).strip().lower() in {"1", "true", "yes", "on"}
    return {
        "env_var": EXECUTE_ENV_VAR,
        "env_value": raw,
        "execute_opt_in_enabled": enabled,
        "default": EXECUTE_DEFAULT,
        "note": "Phase 64 scaffold never executes download/decode/render even when opt-in is set",
    }


def _future_candidate_commands() -> list[dict[str, str]]:
    return [
        {
            "command": "make discover-mrms",
            "phase": "future",
            "executed_by_scaffold": "false",
            "requires_opt_in": "true",
        },
        {
            "command": "make download-mrms",
            "phase": "future",
            "executed_by_scaffold": "false",
            "requires_opt_in": "true",
        },
        {
            "command": "make decode-grib2",
            "phase": "future",
            "executed_by_scaffold": "false",
            "requires_opt_in": "true",
        },
        {
            "command": "make build-production-tiles",
            "phase": "future",
            "executed_by_scaffold": "false",
            "requires_opt_in": "true",
        },
    ]


def _gate(*, gate_id: str, passed: bool, message: str, evidence: Optional[dict] = None) -> dict[str, Any]:
    return {
        "id": gate_id,
        "passed": passed,
        "message": message,
        "evidence": evidence or {},
    }


def gather_scaffold_context(storage: LocalStorage) -> dict[str, Any]:
    preflight_latest = load_render_candidate_preflight(storage)
    if preflight_latest is None:
        evidence = gather_preflight_evidence(storage)
        preflight_evaluated = evaluate_render_candidate_preflight(evidence)
        preflight_available = False
    else:
        preflight_evaluated = preflight_latest
        preflight_available = True

    dry_run_latest = load_render_candidate_dry_run_plan(storage)
    dry_run_context = gather_dry_run_context(storage)
    dry_run_evaluated = evaluate_dry_run_plan_status(dry_run_context)

    return {
        "safety_state": _current_safety_state(),
        "execute_opt_in": _execute_opt_in_status(),
        "required_docs": _required_docs_status(),
        "preflight": {
            "available": preflight_available,
            "preflight_level": preflight_evaluated.get("preflight_level"),
            "preflight_reason": preflight_evaluated.get("preflight_reason"),
            "blocking_items": preflight_evaluated.get("blocking_items") or [],
            "warnings": preflight_evaluated.get("warnings") or [],
            "json_path": preflight_evaluated.get("json_path"),
        },
        "dry_run_plan": {
            "available": dry_run_latest is not None,
            "plan_status": dry_run_evaluated.get("plan_status"),
            "plan_reason": dry_run_evaluated.get("plan_reason"),
            "blocking_items": dry_run_evaluated.get("blocking_items") or [],
            "warnings": dry_run_evaluated.get("warnings") or [],
            "json_path": (dry_run_latest or {}).get("json_path"),
        },
    }


def evaluate_scaffold_status(
    context: dict[str, Any],
    *,
    execute_requested: bool = False,
) -> dict[str, Any]:
    blocking_items: list[str] = []
    warnings: list[str] = []
    safety_gates: list[dict[str, Any]] = []

    safety = context.get("safety_state") or {}
    preflight = context.get("preflight") or {}
    dry_run = context.get("dry_run_plan") or {}
    execute_opt_in = context.get("execute_opt_in") or {}
    required_docs = context.get("required_docs") or []

    safety_gates.append(
        _gate(
            gate_id="verified_mrms_false",
            passed=not bool(safety.get("verified_mrms")),
            message="verified_mrms must remain false",
        )
    )
    safety_gates.append(
        _gate(
            gate_id="production_rendering_disabled",
            passed=not bool(safety.get("enable_production_radar_tiles")),
            message="production rendering gate must remain disabled",
        )
    )
    safety_gates.append(
        _gate(
            gate_id="placeholder_default_preserved",
            passed=bool(safety.get("placeholder_default")),
            message="placeholder-first default must be preserved",
        )
    )
    safety_gates.append(
        _gate(
            gate_id="production_tile_serving_disabled",
            passed=not bool(safety.get("production_tile_serving_enabled")),
            message="production tile serving path must remain disabled",
        )
    )
    safety_gates.append(
        _gate(
            gate_id="dry_run_mode_default",
            passed=not execute_requested,
            message="scaffold defaults to dry-run/no-op mode",
            evidence={"execute_requested": execute_requested},
        )
    )
    safety_gates.append(
        _gate(
            gate_id="execute_opt_in_disabled_by_default",
            passed=not bool(execute_opt_in.get("execute_opt_in_enabled")),
            message=f"{EXECUTE_ENV_VAR} must remain false/disabled by default",
            evidence=execute_opt_in,
        )
    )

    missing_docs = [item["path"] for item in required_docs if not item.get("available")]
    safety_gates.append(
        _gate(
            gate_id="required_docs_present",
            passed=not missing_docs,
            message="required docs/runbooks must be present",
            evidence={"missing_docs": missing_docs},
        )
    )

    if not preflight.get("available"):
        blocking_items.append(
            "Phase 62 preflight report missing — run make mrms-render-candidate-preflight --refresh"
        )
    preflight_level = preflight.get("preflight_level")
    safety_gates.append(
        _gate(
            gate_id="preflight_present",
            passed=bool(preflight_level),
            message="Phase 62 preflight status must exist",
            evidence={"preflight_level": preflight_level},
        )
    )
    if preflight_level == PREFLIGHT_BLOCKED:
        blocking_items.extend(
            preflight.get("blocking_items") or ["Phase 62 preflight status is blocked"]
        )
    elif preflight_level == PREFLIGHT_NEEDS_REVIEW:
        for item in preflight.get("warnings") or []:
            warnings.append(f"preflight warning: {item}")

    if not dry_run.get("available"):
        blocking_items.append(
            "Phase 63 dry-run plan missing — run make mrms-render-candidate-dry-run-plan --refresh"
        )
    plan_status = dry_run.get("plan_status")
    safety_gates.append(
        _gate(
            gate_id="dry_run_plan_present",
            passed=bool(plan_status),
            message="Phase 63 dry-run plan status must exist",
            evidence={"plan_status": plan_status},
        )
    )
    if plan_status == DRY_RUN_BLOCKED:
        blocking_items.extend(
            dry_run.get("blocking_items") or ["Phase 63 dry-run plan status is blocked"]
        )
    elif plan_status == DRY_RUN_NEEDS_REVIEW:
        for item in dry_run.get("warnings") or []:
            warnings.append(f"dry-run plan warning: {item}")

    for gate in safety_gates:
        if not gate["passed"]:
            blocking_items.append(gate["message"])

    if execute_requested:
        blocking_items.append(
            "execute requested but Phase 64 scaffold performs no download/decode/render side effects"
        )

    if blocking_items:
        level = SCAFFOLD_BLOCKED
        reason = "blocking_items_present"
    elif warnings or preflight_level == PREFLIGHT_NEEDS_REVIEW or plan_status == DRY_RUN_NEEDS_REVIEW:
        level = SCAFFOLD_DRY_RUN_ONLY
        reason = "warnings_or_advisory_prerequisites"
    elif (
        preflight_level == PREFLIGHT_CANDIDATE_READY
        and plan_status == DRY_RUN_PLAN_READY
        and not execute_requested
    ):
        level = SCAFFOLD_READY
        reason = "scaffold_ready_dry_run_only"
    else:
        level = SCAFFOLD_DRY_RUN_ONLY
        reason = "prerequisites_not_fully_ready"

    return {
        "scaffold_status": level,
        "scaffold_reason": reason,
        "blocking_items": blocking_items,
        "warnings": warnings,
        "safety_gates": safety_gates,
        "dry_run_mode": True,
        "execute_requested": execute_requested,
        "execute_performed": False,
        "execute_blocked_reason": "disabled_by_default_phase_64",
    }


def build_scaffold_body(
    storage: LocalStorage,
    context: dict[str, Any],
    *,
    execute_requested: bool = False,
) -> dict[str, Any]:
    status = evaluate_scaffold_status(context, execute_requested=execute_requested)
    return {
        "created_at": _utc_now(),
        "scaffold_status": status["scaffold_status"],
        "scaffold_reason": status["scaffold_reason"],
        "blocking_items": status["blocking_items"],
        "warnings": status["warnings"],
        "safety_gates": status["safety_gates"],
        "safety_state": context.get("safety_state") or {},
        "execute_opt_in": context.get("execute_opt_in") or {},
        "dry_run_mode": status["dry_run_mode"],
        "execute_requested": status["execute_requested"],
        "execute_performed": status["execute_performed"],
        "execute_blocked_reason": status["execute_blocked_reason"],
        "preflight_status": context.get("preflight") or {},
        "dry_run_plan_status": context.get("dry_run_plan") or {},
        "required_docs": context.get("required_docs") or [],
        "future_candidate_commands": _future_candidate_commands(),
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        "suggested_command": SUGGESTED_SCAFFOLD_COMMAND,
        **_safety_fields(),
    }


def build_scaffold_markdown(scaffold: dict[str, Any]) -> str:
    lines = [
        "# MRMS Render Candidate Command Scaffold (Disabled-by-Default)",
        "",
        f"Generated at: {scaffold.get('created_at') or _utc_now()}",
        "",
        "> **WARNING:** This is a disabled-by-default local scaffold.",
        "> It does **NOT** verify MRMS, enable production rendering, download/decode/render by default,",
        "> create or serve production tiles, clear validation alerts, mutate catalog/render gates,",
        "> or authorize production use.",
        "> Future candidate commands listed below are **NOT executed** by this phase.",
        "",
        "## Scaffold status",
        "",
        f"- Advisory status: **{scaffold.get('scaffold_status')}**",
        f"- Reason: {scaffold.get('scaffold_reason')}",
        f"- Dry-run/no-op mode: {scaffold.get('dry_run_mode')}",
        f"- Execute performed: {scaffold.get('execute_performed')} "
        f"({scaffold.get('execute_blocked_reason')})",
        "",
        "## Safety state",
        "",
    ]
    safety = scaffold.get("safety_state") or {}
    lines.extend(
        [
            f"- verified_mrms: {safety.get('verified_mrms')}",
            f"- ENABLE_PRODUCTION_RADAR_TILES: {safety.get('enable_production_radar_tiles')}",
            f"- ENABLE_DECODED_TILES: {safety.get('enable_decoded_tiles')}",
            f"- placeholder_default: {safety.get('placeholder_default')}",
            "",
            "## Safety gates",
            "",
            "| Gate | Passed | Message |",
            "|---|---|---|",
        ]
    )
    for gate in scaffold.get("safety_gates") or []:
        lines.append(f"| {gate.get('id')} | {gate.get('passed')} | {gate.get('message')} |")

    lines.extend(["", "## Blocking items", ""])
    blocking = scaffold.get("blocking_items") or []
    if blocking:
        lines.extend(f"- {item}" for item in blocking)
    else:
        lines.append("- None")

    lines.extend(["", "## Warnings", ""])
    warnings = scaffold.get("warnings") or []
    if warnings:
        lines.extend(f"- {item}" for item in warnings)
    else:
        lines.append("- None")

    lines.extend(["", "## Future candidate commands (NOT executed by default)", ""])
    for entry in scaffold.get("future_candidate_commands") or []:
        lines.append(
            f"- `{entry.get('command')}` — executed_by_scaffold={entry.get('executed_by_scaffold')} "
            f"requires_opt_in={entry.get('requires_opt_in')}"
        )

    execute_opt_in = scaffold.get("execute_opt_in") or {}
    lines.extend(
        [
            "",
            "## Execute opt-in (future; disabled now)",
            "",
            f"- Env var: `{execute_opt_in.get('env_var')}`",
            f"- Current value: {execute_opt_in.get('env_value')}",
            f"- Default: {execute_opt_in.get('default')}",
            f"- Note: {execute_opt_in.get('note')}",
            "",
            "## Suggested local command",
            "",
            f"```bash\n{scaffold.get('suggested_command') or SUGGESTED_SCAFFOLD_COMMAND} --refresh\n```",
        ]
    )
    return "\n".join(lines) + "\n"


def save_render_candidate_scaffold(
    storage: LocalStorage,
    scaffold: dict[str, Any],
) -> dict[str, Any]:
    json_path = _scaffold_json_path(storage)
    md_path = _scaffold_md_path(storage)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    scaffold = {
        **scaffold,
        "json_path": json_path,
        "markdown_path": md_path,
        "suggested_command": SUGGESTED_SCAFFOLD_COMMAND,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(scaffold, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(
        build_scaffold_markdown(scaffold),
        encoding="utf-8",
    )
    return scaffold


def load_render_candidate_scaffold(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_scaffold_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def generate_render_candidate_scaffold(
    storage: LocalStorage,
    *,
    execute_requested: bool = False,
) -> dict[str, Any]:
    context = gather_scaffold_context(storage)
    scaffold = build_scaffold_body(storage, context, execute_requested=execute_requested)
    return save_render_candidate_scaffold(storage, scaffold)


def compact_render_candidate_scaffold(storage: LocalStorage) -> dict[str, Any]:
    latest = load_render_candidate_scaffold(storage)
    if latest is None:
        context = gather_scaffold_context(storage)
        status = evaluate_scaffold_status(context)
        return {
            "available": False,
            "scaffold_status": status.get("scaffold_status"),
            "scaffold_reason": status.get("scaffold_reason"),
            "blocking_items": status.get("blocking_items") or [],
            "warnings": status.get("warnings") or [],
            "dry_run_mode": True,
            "execute_performed": False,
            "created_at": None,
            "json_path": _scaffold_json_path(storage),
            "markdown_path": _scaffold_md_path(storage),
            "suggested_command": SUGGESTED_SCAFFOLD_COMMAND,
            "safety_gates": status.get("safety_gates") or [],
            "future_candidate_commands": _future_candidate_commands(),
            "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
            **_safety_fields(),
        }
    return {
        "available": True,
        "scaffold_status": latest.get("scaffold_status"),
        "scaffold_reason": latest.get("scaffold_reason"),
        "blocking_items": latest.get("blocking_items") or [],
        "warnings": latest.get("warnings") or [],
        "dry_run_mode": bool(latest.get("dry_run_mode", True)),
        "execute_performed": bool(latest.get("execute_performed", False)),
        "created_at": latest.get("created_at"),
        "json_path": latest.get("json_path") or _scaffold_json_path(storage),
        "markdown_path": latest.get("markdown_path") or _scaffold_md_path(storage),
        "suggested_command": latest.get("suggested_command") or SUGGESTED_SCAFFOLD_COMMAND,
        "safety_gates": latest.get("safety_gates") or [],
        "future_candidate_commands": latest.get("future_candidate_commands") or _future_candidate_commands(),
        "next_phase_recommendation": latest.get("next_phase_recommendation") or NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_render_candidate_scaffold_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_render_candidate_scaffold(storage)
    if latest is None:
        context = gather_scaffold_context(storage)
        scaffold = build_scaffold_body(storage, context)
    else:
        scaffold = latest
    return {
        **_safety_fields(),
        "latest": scaffold,
        "compact": compact_render_candidate_scaffold(storage),
    }
