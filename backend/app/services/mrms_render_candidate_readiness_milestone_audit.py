"""MRMS candidate readiness milestone audit — consolidates gated chain; does NOT verify MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_gated_ack_history import (
    REVIEW_ACK_HISTORY_READY,
    REVIEW_PREFLIGHT_BLOCKED as ACK_HISTORY_PREFLIGHT_BLOCKED,
    SUGGESTED_COMMAND as SUGGESTED_GATED_ACK_HISTORY_COMMAND,
    compact_gated_ack_history,
    review_gated_ack_history,
)
from backend.app.services.mrms_render_candidate_gated_comparison_ack import (
    REVIEW_ACK_NEEDS_ACK,
    REVIEW_ACK_READY,
    REVIEW_ACK_STALE,
    REVIEW_PREFLIGHT_BLOCKED as ACK_PREFLIGHT_BLOCKED,
    SUGGESTED_COMMAND as SUGGESTED_GATED_ACK_COMMAND,
    compact_gated_comparison_ack,
    review_gated_comparison_ack,
)
from backend.app.services.mrms_render_candidate_gated_comparison_history import (
    REVIEW_COMPARISON_READY,
    REVIEW_PREFLIGHT_BLOCKED as COMPARISON_PREFLIGHT_BLOCKED,
    SUGGESTED_COMMAND as SUGGESTED_GATED_COMPARISON_COMMAND,
    compact_gated_comparison_history,
    review_gated_comparison_history,
)
from backend.app.services.mrms_render_candidate_gated_dry_run_review import (
    REVIEW_PLAN_READY,
    REVIEW_PREFLIGHT_BLOCKED as DRY_RUN_PREFLIGHT_BLOCKED,
    SUGGESTED_COMMAND as SUGGESTED_GATED_DRY_RUN_COMMAND,
    compact_gated_dry_run_review,
    review_gated_dry_run_plan,
)
from backend.app.services.mrms_render_candidate_gated_manifest_io import (
    REVIEW_MANIFEST_IO_READY,
    REVIEW_PREFLIGHT_BLOCKED as MANIFEST_PREFLIGHT_BLOCKED,
    SUGGESTED_COMMAND as SUGGESTED_GATED_MANIFEST_IO_COMMAND,
    compact_gated_manifest_io,
    review_gated_manifest_io,
)
from backend.app.services.mrms_render_candidate_gated_sandbox_layout import (
    REVIEW_LAYOUT_READY,
    REVIEW_PREFLIGHT_BLOCKED as LAYOUT_PREFLIGHT_BLOCKED,
    SUGGESTED_COMMAND as SUGGESTED_GATED_LAYOUT_COMMAND,
    compact_gated_sandbox_layout,
    review_gated_sandbox_layout,
)
from backend.app.services.mrms_render_candidate_gated_scaffold_review import (
    REVIEW_SCAFFOLD_READY,
    REVIEW_PREFLIGHT_BLOCKED as SCAFFOLD_PREFLIGHT_BLOCKED,
    SUGGESTED_COMMAND as SUGGESTED_GATED_SCAFFOLD_COMMAND,
    compact_gated_scaffold_review,
    review_gated_scaffold,
)
from backend.app.services.mrms_render_candidate_gated_trend_review import (
    REVIEW_TREND_NEEDS_REVIEW,
    REVIEW_TREND_READY,
    REVIEW_PREFLIGHT_BLOCKED as TREND_PREFLIGHT_BLOCKED,
    SUGGESTED_COMMAND as SUGGESTED_GATED_TREND_COMMAND,
    compact_gated_trend_review,
    review_gated_trend_review,
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

AUDIT_JSON = "dev/mrms_render_candidate_readiness_milestone_audit_latest.json"
AUDIT_MD = "dev/mrms_render_candidate_readiness_milestone_audit_latest.md"

SUGGESTED_COMMAND = "make mrms-readiness-milestone-audit"

AUDIT_BLOCKED = "readiness_blocked"
AUDIT_NEEDS_REVIEW = "readiness_needs_review"
AUDIT_READY = "readiness_ready"

ROOT_GATE_PREFLIGHT = "preflight"
ROOT_GATE_BLOCKERS = "preflight_blockers"
ROOT_GATE_DRY_RUN = "dry_run_plan"
ROOT_GATE_SCAFFOLD = "scaffold"
ROOT_GATE_LAYOUT = "sandbox_layout"
ROOT_GATE_MANIFEST_IO = "manifest_io"
ROOT_GATE_COMPARISON = "comparison_history"
ROOT_GATE_TREND = "trend_hint"
ROOT_GATE_ACK = "comparison_ack"
ROOT_GATE_ACK_HISTORY = "ack_history"
ROOT_GATE_NONE = "none"

CATEGORY_DATA = "data"
CATEGORY_VISUAL_EVIDENCE = "visual_evidence"
CATEGORY_OPERATOR_ACTION = "operator_action"
CATEGORY_MANIFEST_SCAFFOLD = "manifest_scaffold_layout"
CATEGORY_PREFLIGHT_EVIDENCE = "preflight_evidence"
CATEGORY_CODE_LOGIC = "code_logic"
CATEGORY_NONE = "none"

_PREFLIGHT_BLOCKED_STATUSES = frozenset(
    {
        DRY_RUN_PREFLIGHT_BLOCKED,
        SCAFFOLD_PREFLIGHT_BLOCKED,
        LAYOUT_PREFLIGHT_BLOCKED,
        MANIFEST_PREFLIGHT_BLOCKED,
        COMPARISON_PREFLIGHT_BLOCKED,
        TREND_PREFLIGHT_BLOCKED,
        ACK_PREFLIGHT_BLOCKED,
        ACK_HISTORY_PREFLIGHT_BLOCKED,
    }
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_milestone_audit_only": True,
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
        "milestone_audit_is_not_production_authorization": True,
        "stop_gated_wrapper_loop": True,
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


def _audit_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(AUDIT_JSON)


def _audit_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(AUDIT_MD)


def refresh_readiness_chain(storage: LocalStorage) -> list[dict[str, Any]]:
    """Refresh existing gated chain reports without adding a new gated wrapper."""
    steps: list[tuple[str, str, Any]] = [
        ("preflight", f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh", generate_render_candidate_preflight),
        ("preflight_blockers", f"{SUGGESTED_BLOCKERS_COMMAND} --refresh", resolve_preflight_blockers),
        ("dry_run_plan", f"{SUGGESTED_GATED_DRY_RUN_COMMAND} --refresh", review_gated_dry_run_plan),
        ("scaffold", f"{SUGGESTED_GATED_SCAFFOLD_COMMAND} --refresh", review_gated_scaffold),
        ("sandbox_layout", f"{SUGGESTED_GATED_LAYOUT_COMMAND} --refresh", review_gated_sandbox_layout),
        ("manifest_io", f"{SUGGESTED_GATED_MANIFEST_IO_COMMAND} --refresh", review_gated_manifest_io),
        ("comparison_history", f"{SUGGESTED_GATED_COMPARISON_COMMAND} --refresh", review_gated_comparison_history),
        ("trend_hint", f"{SUGGESTED_GATED_TREND_COMMAND} --refresh", review_gated_trend_review),
        ("comparison_ack", f"{SUGGESTED_GATED_ACK_COMMAND} --refresh", review_gated_comparison_ack),
        ("ack_history", f"{SUGGESTED_GATED_ACK_HISTORY_COMMAND} --refresh", review_gated_ack_history),
    ]
    completed: list[dict[str, Any]] = []
    for step_id, command, runner in steps:
        summary = runner(storage)
        completed.append(
            {
                "step_id": step_id,
                "command": command,
                "completed_at": _utc_now(),
                "summary": {
                    "review_status": summary.get("review_status"),
                    "preflight_level": summary.get("preflight_level"),
                    "resolution_status": summary.get("resolution_status"),
                },
            }
        )
    return completed


def _gate_snapshot(
    *,
    gate_id: str,
    label: str,
    command: str,
    review_status: Optional[str],
    ready: bool,
    skipped: bool,
    detail: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "label": label,
        "command": command,
        "review_status": review_status,
        "ready": ready,
        "skipped": skipped,
        "detail": detail,
        "blocked_only_because_preflight": False,
    }


def gather_gate_snapshots(storage: LocalStorage) -> list[dict[str, Any]]:
    preflight = compact_render_candidate_preflight(storage)
    blockers = compact_preflight_blockers(storage)
    dry_run = compact_gated_dry_run_review(storage)
    scaffold = compact_gated_scaffold_review(storage)
    layout = compact_gated_sandbox_layout(storage)
    manifest = compact_gated_manifest_io(storage)
    comparison = compact_gated_comparison_history(storage)
    trend = compact_gated_trend_review(storage)
    ack = compact_gated_comparison_ack(storage)
    ack_history = compact_gated_ack_history(storage)

    preflight_ready = preflight.get("preflight_level") == PREFLIGHT_CANDIDATE_READY
    blockers_ready = blockers.get("resolution_status") == RESOLUTION_PREFLIGHT_CANDIDATE_READY

    return [
        _gate_snapshot(
            gate_id=ROOT_GATE_PREFLIGHT,
            label="Preflight",
            command=f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
            review_status=preflight.get("preflight_level"),
            ready=preflight_ready,
            skipped=False,
            detail=preflight.get("preflight_reason"),
        ),
        _gate_snapshot(
            gate_id=ROOT_GATE_BLOCKERS,
            label="Preflight blockers",
            command=f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
            review_status=blockers.get("resolution_status"),
            ready=blockers_ready,
            skipped=False,
            detail=blockers.get("next_operator_step"),
        ),
        _gate_snapshot(
            gate_id=ROOT_GATE_DRY_RUN,
            label="Gated dry-run plan",
            command=f"{SUGGESTED_GATED_DRY_RUN_COMMAND} --refresh",
            review_status=dry_run.get("review_status"),
            ready=dry_run.get("review_status") == REVIEW_PLAN_READY,
            skipped=bool(dry_run.get("dry_run_plan_skipped")),
            detail=dry_run.get("dry_run_plan_status"),
        ),
        _gate_snapshot(
            gate_id=ROOT_GATE_SCAFFOLD,
            label="Gated scaffold",
            command=f"{SUGGESTED_GATED_SCAFFOLD_COMMAND} --refresh",
            review_status=scaffold.get("review_status"),
            ready=scaffold.get("review_status") == REVIEW_SCAFFOLD_READY,
            skipped=bool(scaffold.get("scaffold_skipped")),
            detail=scaffold.get("scaffold_status"),
        ),
        _gate_snapshot(
            gate_id=ROOT_GATE_LAYOUT,
            label="Gated sandbox layout",
            command=f"{SUGGESTED_GATED_LAYOUT_COMMAND} --refresh",
            review_status=layout.get("review_status"),
            ready=layout.get("review_status") == REVIEW_LAYOUT_READY,
            skipped=bool(layout.get("sandbox_skipped")),
            detail=layout.get("sandbox_status"),
        ),
        _gate_snapshot(
            gate_id=ROOT_GATE_MANIFEST_IO,
            label="Gated manifest IO",
            command=f"{SUGGESTED_GATED_MANIFEST_IO_COMMAND} --refresh",
            review_status=manifest.get("review_status"),
            ready=manifest.get("review_status") == REVIEW_MANIFEST_IO_READY,
            skipped=bool(manifest.get("manifest_io_skipped")),
            detail=manifest.get("import_export_status"),
        ),
        _gate_snapshot(
            gate_id=ROOT_GATE_COMPARISON,
            label="Gated comparison history",
            command=f"{SUGGESTED_GATED_COMPARISON_COMMAND} --refresh",
            review_status=comparison.get("review_status"),
            ready=comparison.get("review_status") == REVIEW_COMPARISON_READY,
            skipped=bool(comparison.get("comparison_skipped")),
            detail=comparison.get("history_status"),
        ),
        _gate_snapshot(
            gate_id=ROOT_GATE_TREND,
            label="Gated trend hint",
            command=f"{SUGGESTED_GATED_TREND_COMMAND} --refresh",
            review_status=trend.get("review_status"),
            ready=trend.get("review_status") in {REVIEW_TREND_READY, REVIEW_TREND_NEEDS_REVIEW},
            skipped=bool(trend.get("trend_skipped")),
            detail=trend.get("hint_status"),
        ),
        _gate_snapshot(
            gate_id=ROOT_GATE_ACK,
            label="Gated comparison ack",
            command=f"{SUGGESTED_GATED_ACK_COMMAND} --refresh",
            review_status=ack.get("review_status"),
            ready=ack.get("review_status")
            in {REVIEW_ACK_READY, REVIEW_ACK_NEEDS_ACK, REVIEW_ACK_STALE},
            skipped=bool(ack.get("ack_skipped")),
            detail=ack.get("rollup_status"),
        ),
        _gate_snapshot(
            gate_id=ROOT_GATE_ACK_HISTORY,
            label="Gated ack history",
            command=f"{SUGGESTED_GATED_ACK_HISTORY_COMMAND} --refresh",
            review_status=ack_history.get("review_status"),
            ready=ack_history.get("review_status") == REVIEW_ACK_HISTORY_READY,
            skipped=bool(ack_history.get("history_skipped")),
            detail=str(ack_history.get("ack_history_count")),
        ),
    ]


def _classify_blocker_category(
    *,
    preflight: dict[str, Any],
    blockers: dict[str, Any],
) -> str:
    upstream = blockers.get("blocker_category")
    if upstream == "visual_sample_readiness":
        return CATEGORY_VISUAL_EVIDENCE
    if upstream in {"review_chain", "candidate_trend_hint_chain", "trend_hint_review_acknowledgment"}:
        return CATEGORY_OPERATOR_ACTION

    texts: list[str] = []
    for item in preflight.get("blocking_items") or []:
        texts.append(str(item))
    for item in preflight.get("warnings") or []:
        texts.append(str(item))
    for item in blockers.get("remaining_blockers") or []:
        texts.append(str(item))
    for item in blockers.get("visual_blockers") or []:
        texts.append(str(item))
    joined = " ".join(texts).lower()
    if "operator review" in joined or "attention items" in joined:
        return CATEGORY_OPERATOR_ACTION
    if "wgrib2" in joined or "gdal" in joined or "tooling" in joined:
        return CATEGORY_DATA
    if "visual" in joined or "sample" in joined or "manifest" in joined or "proof" in joined:
        return CATEGORY_VISUAL_EVIDENCE
    if "scaffold" in joined or "sandbox layout" in joined or "import/export" in joined:
        return CATEGORY_MANIFEST_SCAFFOLD
    if texts:
        return CATEGORY_PREFLIGHT_EVIDENCE
    return CATEGORY_NONE


def _commands_for_category(category: str) -> list[str]:
    if category == CATEGORY_DATA:
        return [
            "# install wgrib2/GDAL locally or document tooling waiver in preflight notes",
            f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
            f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
        ]
    if category == CATEGORY_OPERATOR_ACTION:
        return [
            "make operator-review-status ARGS=\"--refresh\"",
            f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
            f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
        ]
    if category == CATEGORY_VISUAL_EVIDENCE:
        return [
            "make mrms-bootstrap-visual-sample-set ARGS=\"--refresh\"",
            "make mrms-visual-review-sample-set",
            f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
            f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
        ]
    if category == CATEGORY_MANIFEST_SCAFFOLD:
        return [
            f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
            f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
        ]
    if category == CATEGORY_PREFLIGHT_EVIDENCE:
        return [
            f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh",
            f"{SUGGESTED_BLOCKERS_COMMAND} --refresh",
        ]
    return [SUGGESTED_COMMAND]


def _next_phase_for_audit(
    *,
    preflight_ready: bool,
    root_gate: str,
    blocker_category: str,
    gates: list[dict[str, Any]],
) -> tuple[str, str, bool]:
    if not preflight_ready:
        if blocker_category == CATEGORY_DATA:
            return (
                "Phase 101 — resolve local decode tooling evidence for preflight",
                "Preflight remains needs_review because local wgrib2/GDAL tooling evidence is missing.",
                False,
            )
        if blocker_category == CATEGORY_OPERATOR_ACTION:
            return (
                "Phase 101 — resolve operator review attention items",
                "Preflight remains needs_review because operator review status has open attention items.",
                False,
            )
        if blocker_category == CATEGORY_VISUAL_EVIDENCE:
            return (
                "Phase 101 — resolve visual sample evidence for preflight",
                "Preflight remains needs_review because visual/sample/manifest evidence is incomplete.",
                False,
            )
        return (
            "Phase 101 — resolve preflight evidence blockers",
            "Preflight is not candidate_preflight_ready; fix preflight evidence before adding gated wrappers.",
            False,
        )

    for gate in gates:
        if gate["gate_id"] in {ROOT_GATE_PREFLIGHT, ROOT_GATE_BLOCKERS}:
            continue
        if gate["ready"]:
            continue
        return (
            f"Phase 101 — continue {gate['label'].lower()}",
            f"Preflight is candidate_preflight_ready; continue existing gated step: {gate['command']}",
            False,
        )

    return (
        "Phase 101 — continue gated dry-run plan review",
        "Preflight is candidate_preflight_ready; continue the next gated evaluation step.",
        False,
    )


def build_readiness_milestone_audit(storage: LocalStorage) -> dict[str, Any]:
    preflight = compact_render_candidate_preflight(storage)
    blockers = compact_preflight_blockers(storage)
    gates = gather_gate_snapshots(storage)

    preflight_level = preflight.get("preflight_level")
    preflight_ready = preflight_level == PREFLIGHT_CANDIDATE_READY
    preflight_blockers = [
        *(preflight.get("blocking_items") or []),
        *(
            [f"preflight level is {preflight_level} (need candidate_preflight_ready)"]
            if not preflight_ready
            else []
        ),
    ]
    preflight_warnings = list(preflight.get("warnings") or [])

    root_gate = ROOT_GATE_NONE
    for gate in gates:
        if not gate["ready"]:
            root_gate = gate["gate_id"]
            break

    if preflight_ready:
        downstream_blocked_by_preflight: list[str] = []
    else:
        downstream_blocked_by_preflight = [
            gate["gate_id"]
            for gate in gates
            if gate["gate_id"] not in {ROOT_GATE_PREFLIGHT, ROOT_GATE_BLOCKERS}
            and not gate["ready"]
        ]
        for gate in gates:
            if gate["gate_id"] in downstream_blocked_by_preflight:
                gate["blocked_only_because_preflight"] = True

    blocker_category = _classify_blocker_category(preflight=preflight, blockers=blockers)
    if preflight_ready:
        blocker_category = CATEGORY_NONE

    if not preflight_ready:
        audit_status = AUDIT_BLOCKED
        next_operator_step = (
            f"Resolve preflight blockers ({blocker_category}) before re-running gated reviews."
        )
        retry_commands = _commands_for_category(blocker_category)
        add_gated_wrapper = False
    elif all(gate["ready"] for gate in gates):
        audit_status = AUDIT_READY
        next_operator_step = "All milestone gates ready (local advisory) — continue operator review."
        retry_commands = [SUGGESTED_COMMAND]
        add_gated_wrapper = False
    else:
        audit_status = AUDIT_NEEDS_REVIEW
        next_gate = next(g for g in gates if not g["ready"])
        next_operator_step = f"Continue {next_gate['label']} — preflight is candidate_preflight_ready."
        retry_commands = [next_gate["command"], SUGGESTED_COMMAND]
        add_gated_wrapper = False

    next_phase, next_phase_rationale, _ = _next_phase_for_audit(
        preflight_ready=preflight_ready,
        root_gate=root_gate,
        blocker_category=blocker_category,
        gates=gates,
    )

    return {
        "audited_at": _utc_now(),
        "audit_status": audit_status,
        "preflight_level": preflight_level,
        "preflight_reason": preflight.get("preflight_reason"),
        "preflight_ready": preflight_ready,
        "preflight_blockers": preflight_blockers,
        "preflight_warnings": preflight_warnings,
        "root_gate": root_gate,
        "blocker_category": blocker_category,
        "downstream_blocked_only_because_preflight": downstream_blocked_by_preflight,
        "gates": gates,
        "resolution_status": blockers.get("resolution_status"),
        "remaining_blockers": blockers.get("remaining_blockers") or [],
        "next_operator_step": next_operator_step,
        "retry_commands": retry_commands,
        "next_phase_recommendation": next_phase,
        "next_phase_rationale": next_phase_rationale,
        "add_gated_wrapper_recommended": add_gated_wrapper,
        "stop_gated_wrapper_loop": True,
        "safety_state": _current_safety_state(),
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }


def build_audit_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MRMS candidate readiness milestone audit (Phase 100)",
        "",
        "> **WARNING:** Local milestone audit only. Advisory metadata — does **NOT** verify MRMS, "
        "enable production rendering, clear alerts, or authorize production use. "
        "Do **not** add another gated wrapper while preflight remains blocked.",
        "",
        f"- Audited at: {report.get('audited_at')}",
        f"- Audit status: **{report.get('audit_status')}**",
        f"- Preflight level: {report.get('preflight_level')}",
        f"- Root gate: {report.get('root_gate')}",
        f"- Blocker category: {report.get('blocker_category')}",
        f"- Next operator step: {report.get('next_operator_step')}",
        f"- Next phase: {report.get('next_phase_recommendation')}",
        f"- Add gated wrapper recommended: {report.get('add_gated_wrapper_recommended')}",
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
    lines.extend(["", "## Gate chain", ""])
    for gate in report.get("gates") or []:
        suffix = " (blocked only because preflight)" if gate.get("blocked_only_because_preflight") else ""
        lines.append(
            f"- {gate.get('label')}: {gate.get('review_status') or '—'} — "
            f"ready={gate.get('ready')} skipped={gate.get('skipped')}{suffix}"
        )
    lines.extend(["", "## Retry commands", ""])
    for cmd in report.get("retry_commands") or []:
        lines.append(f"- `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def save_readiness_milestone_audit(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
    json_path = _audit_json_path(storage)
    md_path = _audit_md_path(storage)
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
    storage.absolute_path(md_path).write_text(build_audit_markdown(report), encoding="utf-8")
    return report


def load_readiness_milestone_audit(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_audit_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def run_readiness_milestone_audit(
    storage: LocalStorage,
    *,
    refresh_chain: bool = False,
) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    if refresh_chain:
        steps = refresh_readiness_chain(storage)
    report = build_readiness_milestone_audit(storage)
    if steps:
        report["refresh_steps"] = steps
    return save_readiness_milestone_audit(storage, report)


def compact_readiness_milestone_audit(storage: LocalStorage) -> dict[str, Any]:
    latest = load_readiness_milestone_audit(storage)
    if latest is None:
        report = build_readiness_milestone_audit(storage)
        return {
            "available": False,
            "audit_status": report.get("audit_status"),
            "preflight_level": report.get("preflight_level"),
            "preflight_ready": bool(report.get("preflight_ready")),
            "root_gate": report.get("root_gate"),
            "blocker_category": report.get("blocker_category"),
            "preflight_blockers": report.get("preflight_blockers") or [],
            "preflight_warnings": report.get("preflight_warnings") or [],
            "downstream_blocked_only_because_preflight": report.get(
                "downstream_blocked_only_because_preflight"
            )
            or [],
            "gates": report.get("gates") or [],
            "retry_commands": report.get("retry_commands") or [],
            "next_operator_step": report.get("next_operator_step"),
            "next_phase_recommendation": report.get("next_phase_recommendation"),
            "next_phase_rationale": report.get("next_phase_rationale"),
            "add_gated_wrapper_recommended": bool(report.get("add_gated_wrapper_recommended")),
            "stop_gated_wrapper_loop": True,
            "json_path": _audit_json_path(storage),
            "markdown_path": _audit_md_path(storage),
            "suggested_command": SUGGESTED_COMMAND,
            **_safety_fields(),
        }
    return {
        "available": True,
        "audit_status": latest.get("audit_status"),
        "preflight_level": latest.get("preflight_level"),
        "preflight_reason": latest.get("preflight_reason"),
        "preflight_ready": bool(latest.get("preflight_ready")),
        "root_gate": latest.get("root_gate"),
        "blocker_category": latest.get("blocker_category"),
        "preflight_blockers": latest.get("preflight_blockers") or [],
        "preflight_warnings": latest.get("preflight_warnings") or [],
        "downstream_blocked_only_because_preflight": latest.get(
            "downstream_blocked_only_because_preflight"
        )
        or [],
        "gates": latest.get("gates") or [],
        "retry_commands": latest.get("retry_commands") or [],
        "next_operator_step": latest.get("next_operator_step"),
        "next_phase_recommendation": latest.get("next_phase_recommendation"),
        "next_phase_rationale": latest.get("next_phase_rationale"),
        "add_gated_wrapper_recommended": bool(latest.get("add_gated_wrapper_recommended")),
        "stop_gated_wrapper_loop": bool(latest.get("stop_gated_wrapper_loop")),
        "audited_at": latest.get("audited_at"),
        "json_path": latest.get("json_path"),
        "markdown_path": latest.get("markdown_path"),
        "suggested_command": latest.get("suggested_command") or SUGGESTED_COMMAND,
        **_safety_fields(),
    }


def build_readiness_milestone_audit_payload(storage: LocalStorage) -> dict[str, Any]:
    return {
        **_safety_fields(),
        "latest": load_readiness_milestone_audit(storage),
        "compact": compact_readiness_milestone_audit(storage),
    }
