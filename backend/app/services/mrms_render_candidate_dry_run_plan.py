"""MRMS render candidate dry-run plan — local advisory only, does not execute candidate steps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight import (
    PREFLIGHT_BLOCKED,
    PREFLIGHT_CANDIDATE_READY,
    PREFLIGHT_NEEDS_REVIEW,
    REQUIRED_DOC_PATHS,
    evaluate_render_candidate_preflight,
    gather_preflight_evidence,
    load_render_candidate_preflight,
)
from backend.app.services.mrms_visual_review_sample_readiness import READINESS_CANDIDATE_READY
from backend.app.services.operator_guidance import RUNBOOK_PATH, VERIFIED_CRITERIA_PATH
from backend.app.services.storage import LocalStorage

DRY_RUN_PLAN_JSON = "dev/mrms_render_candidate_dry_run_plan.json"
DRY_RUN_PLAN_MD = "dev/mrms_render_candidate_dry_run_plan.md"

SUGGESTED_DRY_RUN_PLAN_COMMAND = "make mrms-render-candidate-dry-run-plan"

DRY_RUN_BLOCKED = "blocked"
DRY_RUN_NEEDS_REVIEW = "needs_review"
DRY_RUN_PLAN_READY = "dry_run_plan_ready"

NEXT_PHASE_RECOMMENDATION = (
    "Phase 64 — Gated real MRMS rendering candidate command scaffold "
    "(explicitly disabled-by-default; no production tile serving)"
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _dry_run_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(DRY_RUN_PLAN_JSON)


def _dry_run_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(DRY_RUN_PLAN_MD)


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_advisory_dry_run_plan_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "does_not_download_or_decode": True,
        "does_not_create_production_tiles": True,
        "does_not_execute_candidate_steps": True,
        "no_external_notifications": True,
        "does_not_authorize_production_use": True,
        "prototype": True,
    }


def _required_docs_status() -> list[dict[str, Any]]:
    root = _project_root()
    items: list[dict[str, Any]] = []
    for relative_path in REQUIRED_DOC_PATHS:
        abs_path = root / relative_path
        items.append({"path": relative_path, "available": abs_path.is_file()})
    return items


def _current_safety_state() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "enable_production_radar_tiles": settings.enable_production_radar_tiles,
        "enable_decoded_tiles": settings.enable_decoded_tiles,
        "placeholder_default": not settings.enable_production_radar_tiles
        and not settings.enable_decoded_tiles,
    }


def _operator_commands_later() -> list[dict[str, str]]:
    return [
        {
            "command": "make mrms-visual-review",
            "purpose": "Refresh local visual review manifest before any candidate attempt",
            "run_by_this_phase": "false",
        },
        {
            "command": "make mrms-visual-review-sample-set",
            "purpose": "Rebuild drilldown sample set from latest visual review",
            "run_by_this_phase": "false",
        },
        {
            "command": "make mrms-visual-review-readiness --refresh",
            "purpose": "Refresh sample-set annotations/readiness summary",
            "run_by_this_phase": "false",
        },
        {
            "command": "make mrms-render-candidate-preflight --refresh",
            "purpose": "Refresh render candidate preflight checklist",
            "run_by_this_phase": "false",
        },
        {
            "command": "make discover-mrms",
            "purpose": "Future candidate step — discover MRMS inventory (NOT run now)",
            "run_by_this_phase": "false",
        },
        {
            "command": "make download-mrms",
            "purpose": "Future candidate step — download MRMS raw files (NOT run now)",
            "run_by_this_phase": "false",
        },
        {
            "command": "make decode-grib2",
            "purpose": "Future candidate step — decode GRIB2 prototype (NOT run now)",
            "run_by_this_phase": "false",
        },
        {
            "command": "make build-production-tiles",
            "purpose": "Future candidate step — production tile build (NOT run now; gated off)",
            "run_by_this_phase": "false",
        },
    ]


def _expected_artifacts() -> list[dict[str, str]]:
    return [
        {"path": "data/dev/mrms_visual_review_latest.json", "description": "Visual review manifest"},
        {"path": "data/dev/mrms_visual_review_sample_set.json", "description": "Sample set JSON"},
        {"path": "data/dev/mrms_visual_review_sample_annotations.json", "description": "Sample annotations"},
        {"path": "data/dev/mrms_visual_review_sample_readiness.md", "description": "Sample readiness summary"},
        {"path": "data/dev/mrms_render_candidate_preflight.json", "description": "Render candidate preflight"},
        {"path": "data/dev/mrms_render_candidate_dry_run_plan.json", "description": "This dry-run plan"},
    ]


def _rollback_steps() -> list[str]:
    return [
        "Confirm ENABLE_PRODUCTION_RADAR_TILES remains false.",
        "Confirm ENABLE_DECODED_TILES remains false unless explicitly scoped in a later gated phase.",
        "Re-run make mrms-render-candidate-preflight --refresh and verify preflight is not blocked.",
        "Do not clear validation alerts as part of rollback.",
        "Do not mutate catalog or render gates.",
        "Preserve placeholder-first tile serving until a later explicitly gated phase authorizes otherwise.",
    ]


def _stop_conditions() -> list[str]:
    return [
        "verified_mrms becomes true unexpectedly.",
        "Production rendering gate becomes enabled unexpectedly.",
        "Placeholder-first default is no longer preserved.",
        "Phase 62 preflight status becomes blocked.",
        "Sample-set readiness is not candidate_ready.",
        "Any sample is rejected, questionable, stale, missing artifacts, or tagged for follow-up.",
        "Required runbooks/docs are missing.",
        "Operator attempts download/decode/render before dry_run_plan_ready and preflight candidate_preflight_ready.",
    ]


def _evidence_checklist() -> list[dict[str, str]]:
    return [
        {"item": "Visual review manifest generated", "artifact": "data/dev/mrms_visual_review_latest.json"},
        {"item": "Sample set selected", "artifact": "data/dev/mrms_visual_review_sample_set.json"},
        {"item": "Sample annotations recorded", "artifact": "data/dev/mrms_visual_review_sample_annotations.json"},
        {"item": "Sample readiness candidate_ready", "artifact": "data/dev/mrms_visual_review_sample_readiness.md"},
        {"item": "Render candidate preflight candidate_preflight_ready", "artifact": "data/dev/mrms_render_candidate_preflight.json"},
        {"item": "Dry-run plan dry_run_plan_ready", "artifact": "data/dev/mrms_render_candidate_dry_run_plan.json"},
        {"item": "Runbook reviewed", "artifact": RUNBOOK_PATH},
        {"item": "Verified MRMS criteria reviewed (not met)", "artifact": VERIFIED_CRITERIA_PATH},
    ]


def _prerequisites() -> list[str]:
    return [
        "verified_mrms remains false.",
        "ENABLE_PRODUCTION_RADAR_TILES remains false by default.",
        "Placeholder-first tile serving remains the default behavior.",
        "Local visual review, sample set, and sample readiness evidence exist.",
        "Phase 62 preflight report exists and is not blocked.",
        "Required docs/runbooks are present in the repository.",
        "Operator has read docs/RUNBOOK_REAL_MRMS_VALIDATION.md and docs/VERIFIED_MRMS_CRITERIA.md.",
    ]


def gather_dry_run_context(storage: LocalStorage) -> dict[str, Any]:
    preflight_latest = load_render_candidate_preflight(storage)
    if preflight_latest is None:
        evidence = gather_preflight_evidence(storage)
        preflight_evaluated = evaluate_render_candidate_preflight(evidence)
        preflight_available = False
    else:
        preflight_evaluated = preflight_latest
        preflight_available = True
        evidence = preflight_latest.get("evidence") or gather_preflight_evidence(storage)

    sample_readiness = evidence.get("sample_readiness") or {}
    return {
        "safety_state": _current_safety_state(),
        "required_docs": _required_docs_status(),
        "preflight": {
            "available": preflight_available,
            "preflight_level": preflight_evaluated.get("preflight_level"),
            "preflight_reason": preflight_evaluated.get("preflight_reason"),
            "blocking_items": preflight_evaluated.get("blocking_items") or [],
            "warnings": preflight_evaluated.get("warnings") or [],
            "json_path": preflight_evaluated.get("json_path"),
            "markdown_path": preflight_evaluated.get("markdown_path"),
        },
        "visual_review": evidence.get("visual_review") or {},
        "sample_set": evidence.get("sample_set") or {},
        "sample_readiness": sample_readiness,
    }


def evaluate_dry_run_plan_status(context: dict[str, Any]) -> dict[str, Any]:
    blocking_items: list[str] = []
    warnings: list[str] = []

    safety = context.get("safety_state") or {}
    preflight = context.get("preflight") or {}
    sample_readiness = context.get("sample_readiness") or {}
    visual_review = context.get("visual_review") or {}
    sample_set = context.get("sample_set") or {}
    required_docs = context.get("required_docs") or []

    if safety.get("verified_mrms"):
        blocking_items.append("verified_mrms must remain false")
    if safety.get("enable_production_radar_tiles"):
        blocking_items.append("production rendering gate must remain disabled")
    if not safety.get("placeholder_default"):
        blocking_items.append("placeholder-first default must be preserved")

    missing_docs = [item["path"] for item in required_docs if not item.get("available")]
    if missing_docs:
        blocking_items.append(f"required docs/runbooks missing: {', '.join(missing_docs)}")

    if not preflight.get("available") and not preflight.get("preflight_level"):
        blocking_items.append("Phase 62 preflight status is missing — run make mrms-render-candidate-preflight --refresh")
    elif not preflight.get("available"):
        blocking_items.append("Phase 62 preflight report not persisted — run make mrms-render-candidate-preflight --refresh")

    preflight_level = preflight.get("preflight_level")
    if preflight_level == PREFLIGHT_BLOCKED:
        blocking_items.extend(
            [f"preflight blocked: {item}" for item in (preflight.get("blocking_items") or [])]
            or ["Phase 62 preflight status is blocked"]
        )
    elif preflight_level == PREFLIGHT_NEEDS_REVIEW:
        for item in preflight.get("warnings") or []:
            warnings.append(f"preflight warning: {item}")

    if not visual_review.get("available"):
        blocking_items.append("visual review evidence is missing")
    if not sample_set.get("available") or int(sample_set.get("entry_count") or 0) <= 0:
        blocking_items.append("visual review sample set evidence is missing")
    if not sample_readiness.get("readiness_level"):
        blocking_items.append("sample-set readiness evidence is missing")
    elif sample_readiness.get("readiness_level") != READINESS_CANDIDATE_READY:
        blocking_items.append(
            f"sample-set readiness must be candidate_ready (found {sample_readiness.get('readiness_level')})"
        )

    if blocking_items:
        level = DRY_RUN_BLOCKED
        reason = "blocking_items_present"
    elif warnings or preflight_level == PREFLIGHT_NEEDS_REVIEW:
        level = DRY_RUN_NEEDS_REVIEW
        reason = "warnings_or_preflight_needs_review"
    elif preflight_level == PREFLIGHT_CANDIDATE_READY and not missing_docs:
        level = DRY_RUN_PLAN_READY
        reason = "dry_run_plan_complete"
    else:
        level = DRY_RUN_NEEDS_REVIEW
        reason = "preflight_not_candidate_ready"

    return {
        "plan_status": level,
        "plan_reason": reason,
        "blocking_items": blocking_items,
        "warnings": warnings,
    }


def build_dry_run_plan_body(storage: LocalStorage, context: dict[str, Any]) -> dict[str, Any]:
    status = evaluate_dry_run_plan_status(context)
    return {
        "created_at": _utc_now(),
        "plan_status": status["plan_status"],
        "plan_reason": status["plan_reason"],
        "blocking_items": status["blocking_items"],
        "warnings": status["warnings"],
        "safety_state": context.get("safety_state") or {},
        "preflight_status": context.get("preflight") or {},
        "visual_review_dependency": {
            "available": bool((context.get("visual_review") or {}).get("available")),
            "json_path": (context.get("visual_review") or {}).get("json_path"),
        },
        "sample_readiness_dependency": {
            "readiness_level": (context.get("sample_readiness") or {}).get("readiness_level"),
            "readiness_reason": (context.get("sample_readiness") or {}).get("readiness_reason"),
        },
        "required_docs": context.get("required_docs") or [],
        "prerequisites": _prerequisites(),
        "operator_commands_later_not_run_now": _operator_commands_later(),
        "expected_artifacts": _expected_artifacts(),
        "rollback_steps": _rollback_steps(),
        "stop_conditions": _stop_conditions(),
        "evidence_checklist": _evidence_checklist(),
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        "suggested_command": SUGGESTED_DRY_RUN_PLAN_COMMAND,
        **_safety_fields(),
    }


def build_dry_run_plan_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# MRMS Render Candidate Dry-Run Plan (Local Advisory Only)",
        "",
        f"Generated at: {plan.get('created_at') or _utc_now()}",
        "",
        "> **WARNING:** This dry-run plan is local operator guidance only.",
        "> It does **NOT** verify MRMS, enable production rendering, download/decode/render by default,",
        "> create production tiles, clear validation alerts, mutate catalog/render gates,",
        "> or authorize production use.",
        "> Commands listed below are for a **future** gated candidate attempt — **NOT run by this phase**.",
        "",
        "## Plan status",
        "",
        f"- Advisory status: **{plan.get('plan_status')}**",
        f"- Reason: {plan.get('plan_reason')}",
        "",
        "## Current safety state",
        "",
    ]
    safety = plan.get("safety_state") or {}
    lines.extend(
        [
            f"- verified_mrms: {safety.get('verified_mrms')}",
            f"- ENABLE_PRODUCTION_RADAR_TILES: {safety.get('enable_production_radar_tiles')}",
            f"- ENABLE_DECODED_TILES: {safety.get('enable_decoded_tiles')}",
            f"- placeholder_default: {safety.get('placeholder_default')}",
            "",
            "## Phase 62 preflight status",
            "",
        ]
    )
    preflight = plan.get("preflight_status") or {}
    lines.extend(
        [
            f"- Preflight level: {preflight.get('preflight_level') or '—'}",
            f"- Preflight reason: {preflight.get('preflight_reason') or '—'}",
            "",
            "## Blocking items",
            "",
        ]
    )
    blocking = plan.get("blocking_items") or []
    if blocking:
        lines.extend(f"- {item}" for item in blocking)
    else:
        lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    warnings = plan.get("warnings") or []
    if warnings:
        lines.extend(f"- {item}" for item in warnings)
    else:
        lines.append("- None")

    lines.extend(["", "## Prerequisites", ""])
    lines.extend(f"- {item}" for item in plan.get("prerequisites") or [])

    lines.extend(["", "## Required docs/runbooks", ""])
    for doc in plan.get("required_docs") or []:
        lines.append(f"- `{doc.get('path')}` — available: {doc.get('available')}")

    lines.extend(["", "## Operator commands (NOT run by this phase)", ""])
    for entry in plan.get("operator_commands_later_not_run_now") or []:
        lines.append(
            f"- `{entry.get('command')}` — {entry.get('purpose')} "
            f"(run_by_this_phase={entry.get('run_by_this_phase')})"
        )

    lines.extend(["", "## Expected data/dev/ artifacts", ""])
    for artifact in plan.get("expected_artifacts") or []:
        lines.append(f"- `{artifact.get('path')}` — {artifact.get('description')}")

    lines.extend(["", "## Rollback / safety checks", ""])
    lines.extend(f"- {item}" for item in plan.get("rollback_steps") or [])

    lines.extend(["", "## Stop conditions", ""])
    lines.extend(f"- {item}" for item in plan.get("stop_conditions") or [])

    lines.extend(["", "## Evidence checklist", ""])
    for item in plan.get("evidence_checklist") or []:
        lines.append(f"- {item.get('item')} — `{item.get('artifact')}`")

    lines.extend(
        [
            "",
            "## Next phase readiness recommendation",
            "",
            plan.get("next_phase_recommendation") or NEXT_PHASE_RECOMMENDATION,
            "",
            "## Suggested local command",
            "",
            f"```bash\n{plan.get('suggested_command') or SUGGESTED_DRY_RUN_PLAN_COMMAND} --refresh\n```",
        ]
    )
    return "\n".join(lines) + "\n"


def save_render_candidate_dry_run_plan(
    storage: LocalStorage,
    plan: dict[str, Any],
) -> dict[str, Any]:
    json_path = _dry_run_json_path(storage)
    md_path = _dry_run_md_path(storage)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    plan = {
        **plan,
        "json_path": json_path,
        "markdown_path": md_path,
        "suggested_command": SUGGESTED_DRY_RUN_PLAN_COMMAND,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(plan, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(
        build_dry_run_plan_markdown(plan),
        encoding="utf-8",
    )
    return plan


def load_render_candidate_dry_run_plan(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_dry_run_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def generate_render_candidate_dry_run_plan(storage: LocalStorage) -> dict[str, Any]:
    context = gather_dry_run_context(storage)
    plan = build_dry_run_plan_body(storage, context)
    return save_render_candidate_dry_run_plan(storage, plan)


def compact_render_candidate_dry_run_plan(storage: LocalStorage) -> dict[str, Any]:
    latest = load_render_candidate_dry_run_plan(storage)
    if latest is None:
        context = gather_dry_run_context(storage)
        evaluated = evaluate_dry_run_plan_status(context)
        return {
            "available": False,
            "plan_status": evaluated.get("plan_status"),
            "plan_reason": evaluated.get("plan_reason"),
            "blocking_items": evaluated.get("blocking_items") or [],
            "warnings": evaluated.get("warnings") or [],
            "created_at": None,
            "json_path": _dry_run_json_path(storage),
            "markdown_path": _dry_run_md_path(storage),
            "suggested_command": SUGGESTED_DRY_RUN_PLAN_COMMAND,
            "prerequisites": _prerequisites(),
            "stop_conditions": _stop_conditions(),
            "expected_artifacts": _expected_artifacts(),
            "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
            **_safety_fields(),
        }
    return {
        "available": True,
        "plan_status": latest.get("plan_status"),
        "plan_reason": latest.get("plan_reason"),
        "blocking_items": latest.get("blocking_items") or [],
        "warnings": latest.get("warnings") or [],
        "created_at": latest.get("created_at"),
        "json_path": latest.get("json_path") or _dry_run_json_path(storage),
        "markdown_path": latest.get("markdown_path") or _dry_run_md_path(storage),
        "suggested_command": latest.get("suggested_command") or SUGGESTED_DRY_RUN_PLAN_COMMAND,
        "prerequisites": latest.get("prerequisites") or _prerequisites(),
        "stop_conditions": latest.get("stop_conditions") or _stop_conditions(),
        "expected_artifacts": latest.get("expected_artifacts") or _expected_artifacts(),
        "next_phase_recommendation": latest.get("next_phase_recommendation") or NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_render_candidate_dry_run_plan_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_render_candidate_dry_run_plan(storage)
    if latest is None:
        context = gather_dry_run_context(storage)
        plan = build_dry_run_plan_body(storage, context)
    else:
        plan = latest
    return {
        **_safety_fields(),
        "latest": plan,
        "compact": compact_render_candidate_dry_run_plan(storage),
    }
