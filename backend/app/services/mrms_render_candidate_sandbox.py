"""MRMS render candidate artifact sandbox — local-only, isolated from production tiles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.storage import LocalStorage

SANDBOX_ROOT_REL = "dev/mrms_render_candidate_sandbox"
MANIFEST_JSON = "dev/mrms_render_candidate_sandbox_manifest.json"
REPORT_MD = "dev/mrms_render_candidate_sandbox_report.md"

SUGGESTED_SANDBOX_COMMAND = "make mrms-render-candidate-sandbox"

EXPECTED_SUBDIRS = (
    "incoming",
    "decoded",
    "rendered",
    "reports",
    "logs",
    "manifests",
    "scratch",
    "quarantine",
)

PRODUCTION_TILE_ROOT_PARTS = ("tiles", "production")

SANDBOX_MISSING = "missing"
SANDBOX_NEEDS_SETUP = "needs_setup"
SANDBOX_READY = "ready"
SANDBOX_NEEDS_CLEANUP = "needs_cleanup"
SANDBOX_BLOCKED = "blocked"

DELETE_CONFIRM_FLAG = "--confirm-delete-dev-sandbox"
CLEANUP_REPORT_ONLY = "report_only"

NEXT_PHASE_RECOMMENDATION = (
    "Phase 66 — Gated candidate sandbox manifest import/export "
    "(local import/export for candidate sandbox manifests without production tile serving)"
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_sandbox_only": True,
        "disabled_by_default": True,
        "cleanup_report_only_by_default": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "does_not_download_or_decode": True,
        "does_not_create_production_tiles": True,
        "does_not_serve_production_tiles": True,
        "does_not_delete_by_default": True,
        "no_external_notifications": True,
        "does_not_authorize_production_use": True,
        "prototype": True,
    }


def _sandbox_root_normalized(storage: LocalStorage) -> str:
    return storage.normalize_path(SANDBOX_ROOT_REL)


def _manifest_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(MANIFEST_JSON)


def _report_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(REPORT_MD)


def _sandbox_root_abs(storage: LocalStorage) -> Path:
    return storage.absolute_path(_sandbox_root_normalized(storage)).resolve()


def _production_tile_root_abs(storage: LocalStorage) -> Path:
    return storage.absolute_path(storage.normalize_path(*PRODUCTION_TILE_ROOT_PARTS)).resolve()


def _data_dev_root_abs(storage: LocalStorage) -> Path:
    return storage.absolute_path("dev").resolve()


def _current_safety_state() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "enable_production_radar_tiles": settings.enable_production_radar_tiles,
        "enable_decoded_tiles": settings.enable_decoded_tiles,
        "placeholder_default": not settings.enable_production_radar_tiles
        and not settings.enable_decoded_tiles,
        "production_tile_serving_enabled": settings.enable_production_radar_tiles,
    }


def _gate(*, gate_id: str, passed: bool, message: str, evidence: Optional[dict] = None) -> dict[str, Any]:
    return {
        "id": gate_id,
        "passed": passed,
        "message": message,
        "evidence": evidence or {},
    }


def _path_is_under(parent: Path, child: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _paths_overlap(left: Path, right: Path) -> bool:
    left_resolved = left.resolve()
    right_resolved = right.resolve()
    return (
        left_resolved == right_resolved
        or _path_is_under(left_resolved, right_resolved)
        or _path_is_under(right_resolved, left_resolved)
    )


def _detect_unsafe_symlinks(path: Path) -> list[str]:
    issues: list[str] = []
    candidate = path
    while True:
        if candidate.is_symlink():
            issues.append(f"unsafe symlink detected in sandbox path chain: {candidate}")
            break
        if candidate.parent == candidate:
            break
        candidate = candidate.parent
    if path.is_symlink():
        issues.append(f"sandbox root is a symlink: {path}")
    return issues


def validate_sandbox_path_safety(storage: LocalStorage) -> dict[str, Any]:
    sandbox_root = _sandbox_root_abs(storage)
    dev_root = _data_dev_root_abs(storage)
    production_root = _production_tile_root_abs(storage)

    under_dev = _path_is_under(dev_root, sandbox_root)
    overlaps_production = _paths_overlap(sandbox_root, production_root)
    symlink_issues = _detect_unsafe_symlinks(sandbox_root)

    return {
        "sandbox_root": _sandbox_root_normalized(storage),
        "sandbox_root_absolute": str(sandbox_root),
        "under_data_dev": under_dev,
        "overlaps_production_tile_paths": overlaps_production,
        "production_tile_root": storage.normalize_path(*PRODUCTION_TILE_ROOT_PARTS),
        "symlink_issues": symlink_issues,
        "isolated_from_production_tile_serving": under_dev
        and not overlaps_production
        and not bool(symlink_issues),
    }


def _scan_subdirectory(storage: LocalStorage, subdir: str) -> dict[str, Any]:
    rel_path = storage.normalize_path(SANDBOX_ROOT_REL, subdir)
    abs_path = storage.absolute_path(rel_path)
    exists = abs_path.is_dir()
    file_count = 0
    total_bytes = 0
    symlink_files: list[str] = []

    if exists:
        for entry in abs_path.rglob("*"):
            if entry.is_symlink():
                symlink_files.append(str(entry.relative_to(abs_path)))
                continue
            if entry.is_file():
                file_count += 1
                try:
                    total_bytes += entry.stat().st_size
                except OSError:
                    pass

    return {
        "name": subdir,
        "relative_path": rel_path,
        "exists": exists,
        "file_count": file_count,
        "total_bytes": total_bytes,
        "symlink_entries": symlink_files,
    }


def _cleanup_candidates(subdir_scans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for scan in subdir_scans:
        name = scan.get("name")
        if name not in {"scratch", "quarantine", "logs"}:
            continue
        file_count = int(scan.get("file_count") or 0)
        if file_count <= 0:
            continue
        candidates.append(
            {
                "path": scan.get("relative_path"),
                "category": name,
                "file_count": file_count,
                "total_bytes": scan.get("total_bytes") or 0,
                "action": CLEANUP_REPORT_ONLY,
                "delete_requires_flag": DELETE_CONFIRM_FLAG,
                "note": "Report-only in Phase 65 — no files deleted by default",
            }
        )
    return candidates


def gather_sandbox_context(storage: LocalStorage) -> dict[str, Any]:
    path_safety = validate_sandbox_path_safety(storage)
    sandbox_root_abs = _sandbox_root_abs(storage)
    root_exists = sandbox_root_abs.is_dir()
    subdir_scans = [_scan_subdirectory(storage, name) for name in EXPECTED_SUBDIRS]
    missing_subdirs = [scan["name"] for scan in subdir_scans if not scan["exists"]]
    existing_subdirs = [scan["name"] for scan in subdir_scans if scan["exists"]]
    cleanup_candidates = _cleanup_candidates(subdir_scans)

    quarantine_scan = next((scan for scan in subdir_scans if scan["name"] == "quarantine"), {})
    return {
        "safety_state": _current_safety_state(),
        "path_safety": path_safety,
        "sandbox_root_exists": root_exists,
        "expected_subdirectories": list(EXPECTED_SUBDIRS),
        "existing_subdirectories": existing_subdirs,
        "missing_subdirectories": missing_subdirs,
        "subdirectory_scans": subdir_scans,
        "cleanup_candidates": cleanup_candidates,
        "quarantine_status": {
            "exists": bool(quarantine_scan.get("exists")),
            "file_count": quarantine_scan.get("file_count") or 0,
            "total_bytes": quarantine_scan.get("total_bytes") or 0,
        },
        "cleanup_mode": CLEANUP_REPORT_ONLY,
    }


def evaluate_sandbox_status(
    context: dict[str, Any],
    *,
    confirm_delete_requested: bool = False,
) -> dict[str, Any]:
    blocking_items: list[str] = []
    warnings: list[str] = []
    safety_gates: list[dict[str, Any]] = []

    safety = context.get("safety_state") or {}
    path_safety = context.get("path_safety") or {}

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
            gate_id="sandbox_under_data_dev",
            passed=bool(path_safety.get("under_data_dev")),
            message="sandbox root must resolve under data/dev/",
            evidence={"sandbox_root": path_safety.get("sandbox_root")},
        )
    )
    safety_gates.append(
        _gate(
            gate_id="sandbox_not_overlapping_production_tiles",
            passed=not bool(path_safety.get("overlaps_production_tile_paths")),
            message="sandbox must not overlap production tile paths",
            evidence={"production_tile_root": path_safety.get("production_tile_root")},
        )
    )
    symlink_issues = path_safety.get("symlink_issues") or []
    safety_gates.append(
        _gate(
            gate_id="no_unsafe_symlinks",
            passed=not symlink_issues,
            message="unsafe symlinks or path traversal must not be present",
            evidence={"symlink_issues": symlink_issues},
        )
    )
    safety_gates.append(
        _gate(
            gate_id="isolated_from_production_tile_serving",
            passed=bool(path_safety.get("isolated_from_production_tile_serving")),
            message="sandbox must remain isolated from production tile serving",
            evidence={
                "under_data_dev": path_safety.get("under_data_dev"),
                "overlaps_production_tile_paths": path_safety.get("overlaps_production_tile_paths"),
            },
        )
    )

    for gate in safety_gates:
        if not gate["passed"]:
            blocking_items.append(gate["message"])

    if confirm_delete_requested:
        warnings.append(
            "delete confirmation requested but Phase 65 performs report-only cleanup — no files deleted"
        )

    missing_subdirs = context.get("missing_subdirectories") or []
    sandbox_root_exists = bool(context.get("sandbox_root_exists"))
    cleanup_candidates = context.get("cleanup_candidates") or []

    if any(not gate["passed"] for gate in safety_gates):
        level = SANDBOX_BLOCKED
        reason = "safety_gate_failure"
    elif not sandbox_root_exists:
        level = SANDBOX_MISSING
        reason = "sandbox_root_missing"
    elif missing_subdirs:
        level = SANDBOX_NEEDS_SETUP
        reason = "expected_subdirectories_missing"
        for name in missing_subdirs:
            warnings.append(f"missing subdirectory: {name}")
    elif cleanup_candidates:
        level = SANDBOX_NEEDS_CLEANUP
        reason = "cleanup_candidates_present"
    else:
        level = SANDBOX_READY
        reason = "sandbox_ready_isolated"

    return {
        "sandbox_status": level,
        "sandbox_reason": reason,
        "blocking_items": blocking_items,
        "warnings": warnings,
        "safety_gates": safety_gates,
        "cleanup_mode": CLEANUP_REPORT_ONLY,
        "delete_performed": False,
        "delete_blocked_reason": "report_only_phase_65",
    }


def create_sandbox_layout(storage: LocalStorage) -> dict[str, Any]:
    path_safety = validate_sandbox_path_safety(storage)
    if not path_safety.get("under_data_dev") or path_safety.get("overlaps_production_tile_paths"):
        raise ValueError("sandbox path safety check failed — layout not created")

    root = _sandbox_root_normalized(storage)
    storage.ensure_directories(root)
    created: list[str] = []
    for subdir in EXPECTED_SUBDIRS:
        rel = storage.normalize_path(SANDBOX_ROOT_REL, subdir)
        storage.ensure_directories(rel)
        created.append(rel)

    readme_rel = storage.normalize_path(SANDBOX_ROOT_REL, "README.local.md")
    readme_abs = storage.absolute_path(readme_rel)
    if not readme_abs.is_file():
        readme_abs.write_text(
            "\n".join(
                [
                    "# MRMS Render Candidate Sandbox (local only)",
                    "",
                    "This directory is for future gated MRMS candidate artifacts only.",
                    "It does NOT verify MRMS, enable production rendering, or serve production tiles.",
                    "Cleanup is report-only unless explicitly confirmed in a future gated phase.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        created.append(readme_rel)

    return {"sandbox_root": root, "created_paths": created}


def build_sandbox_manifest_body(
    storage: LocalStorage,
    context: dict[str, Any],
    *,
    confirm_delete_requested: bool = False,
    layout_created: bool = False,
) -> dict[str, Any]:
    status = evaluate_sandbox_status(context, confirm_delete_requested=confirm_delete_requested)
    path_safety = context.get("path_safety") or {}
    return {
        "created_at": _utc_now(),
        "sandbox_status": status["sandbox_status"],
        "sandbox_reason": status["sandbox_reason"],
        "blocking_items": status["blocking_items"],
        "warnings": status["warnings"],
        "safety_gates": status["safety_gates"],
        "sandbox_root": path_safety.get("sandbox_root") or _sandbox_root_normalized(storage),
        "expected_subdirectories": context.get("expected_subdirectories") or list(EXPECTED_SUBDIRS),
        "existing_subdirectories": context.get("existing_subdirectories") or [],
        "missing_subdirectories": context.get("missing_subdirectories") or [],
        "subdirectory_scans": context.get("subdirectory_scans") or [],
        "cleanup_candidates": context.get("cleanup_candidates") or [],
        "cleanup_mode": status["cleanup_mode"],
        "delete_performed": status["delete_performed"],
        "delete_blocked_reason": status["delete_blocked_reason"],
        "delete_confirm_flag": DELETE_CONFIRM_FLAG,
        "quarantine_status": context.get("quarantine_status") or {},
        "path_safety": path_safety,
        "safety_state": context.get("safety_state") or {},
        "isolation_status": {
            "under_data_dev": path_safety.get("under_data_dev"),
            "overlaps_production_tile_paths": path_safety.get("overlaps_production_tile_paths"),
            "isolated_from_production_tile_serving": path_safety.get(
                "isolated_from_production_tile_serving"
            ),
        },
        "layout_created": layout_created,
        "suggested_command": SUGGESTED_SANDBOX_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_sandbox_report_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# MRMS Render Candidate Artifact Sandbox Report",
        "",
        f"Generated at: {manifest.get('created_at') or _utc_now()}",
        "",
        "> **WARNING:** This is a local candidate artifact sandbox only.",
        "> It does **NOT** verify MRMS, enable production rendering, download/decode/render by default,",
        "> create or serve production tiles, clear validation alerts, mutate catalog/render gates,",
        "> or authorize production use.",
        "> Cleanup is **report-only** unless explicitly confirmed with "
        f"`{DELETE_CONFIRM_FLAG}`.",
        "",
        "## Sandbox status",
        "",
        f"- Advisory status: **{manifest.get('sandbox_status')}**",
        f"- Reason: {manifest.get('sandbox_reason')}",
        f"- Cleanup mode: {manifest.get('cleanup_mode')}",
        f"- Delete performed: {manifest.get('delete_performed')} ({manifest.get('delete_blocked_reason')})",
        "",
        "## Sandbox root",
        "",
        f"- Root: `{manifest.get('sandbox_root')}`",
        "",
        "## Expected subdirectories",
        "",
    ]
    for name in manifest.get("expected_subdirectories") or []:
        marker = "present" if name in (manifest.get("existing_subdirectories") or []) else "missing"
        lines.append(f"- `{name}/` — {marker}")

    lines.extend(["", "## Isolation status", ""])
    isolation = manifest.get("isolation_status") or {}
    lines.extend(
        [
            f"- Under data/dev/: {isolation.get('under_data_dev')}",
            f"- Overlaps production tile paths: {isolation.get('overlaps_production_tile_paths')}",
            f"- Isolated from production tile serving: {isolation.get('isolated_from_production_tile_serving')}",
            "",
            "## Safety gates",
            "",
            "| Gate | Passed | Message |",
            "|---|---|---|",
        ]
    )
    for gate in manifest.get("safety_gates") or []:
        lines.append(f"| {gate.get('id')} | {gate.get('passed')} | {gate.get('message')} |")

    lines.extend(["", "## Blocking items", ""])
    blocking = manifest.get("blocking_items") or []
    if blocking:
        lines.extend(f"- {item}" for item in blocking)
    else:
        lines.append("- None")

    lines.extend(["", "## Warnings", ""])
    warnings = manifest.get("warnings") or []
    if warnings:
        lines.extend(f"- {item}" for item in warnings)
    else:
        lines.append("- None")

    lines.extend(["", "## Cleanup candidates (report-only)", ""])
    candidates = manifest.get("cleanup_candidates") or []
    if candidates:
        for item in candidates:
            lines.append(
                f"- `{item.get('path')}` — {item.get('category')} "
                f"({item.get('file_count')} files, {item.get('total_bytes')} bytes) "
                f"[{item.get('action')}]"
            )
    else:
        lines.append("- None")

    quarantine = manifest.get("quarantine_status") or {}
    lines.extend(
        [
            "",
            "## Quarantine status",
            "",
            f"- Exists: {quarantine.get('exists')}",
            f"- File count: {quarantine.get('file_count')}",
            f"- Total bytes: {quarantine.get('total_bytes')}",
            "",
            "## Suggested local command",
            "",
            f"```bash\n{manifest.get('suggested_command') or SUGGESTED_SANDBOX_COMMAND} --refresh\n```",
        ]
    )
    return "\n".join(lines) + "\n"


def save_sandbox_manifest(storage: LocalStorage, manifest: dict[str, Any]) -> dict[str, Any]:
    json_path = _manifest_json_path(storage)
    md_path = _report_md_path(storage)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    manifest = {
        **manifest,
        "json_path": json_path,
        "markdown_path": md_path,
        "suggested_command": SUGGESTED_SANDBOX_COMMAND,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(
        build_sandbox_report_markdown(manifest),
        encoding="utf-8",
    )
    return manifest


def load_sandbox_manifest(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_manifest_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def generate_render_candidate_sandbox(
    storage: LocalStorage,
    *,
    create_layout: bool = True,
    confirm_delete_requested: bool = False,
) -> dict[str, Any]:
    layout_created = False
    if create_layout:
        path_safety = validate_sandbox_path_safety(storage)
        if path_safety.get("under_data_dev") and not path_safety.get("overlaps_production_tile_paths"):
            create_sandbox_layout(storage)
            layout_created = True

    context = gather_sandbox_context(storage)
    manifest = build_sandbox_manifest_body(
        storage,
        context,
        confirm_delete_requested=confirm_delete_requested,
        layout_created=layout_created,
    )
    return save_sandbox_manifest(storage, manifest)


def compact_render_candidate_sandbox(storage: LocalStorage) -> dict[str, Any]:
    latest = load_sandbox_manifest(storage)
    context = gather_sandbox_context(storage)
    evaluated = evaluate_sandbox_status(context)
    path_safety = context.get("path_safety") or {}
    compact = {
        "available": latest is not None,
        "created_at": (latest or {}).get("created_at"),
        "sandbox_status": (latest or {}).get("sandbox_status") or evaluated.get("sandbox_status"),
        "sandbox_reason": (latest or {}).get("sandbox_reason") or evaluated.get("sandbox_reason"),
        "blocking_items": (latest or {}).get("blocking_items") or evaluated.get("blocking_items") or [],
        "warnings": (latest or {}).get("warnings") or evaluated.get("warnings") or [],
        "sandbox_root": path_safety.get("sandbox_root") or _sandbox_root_normalized(storage),
        "expected_subdirectories": context.get("expected_subdirectories") or list(EXPECTED_SUBDIRS),
        "existing_subdirectories": context.get("existing_subdirectories") or [],
        "missing_subdirectories": context.get("missing_subdirectories") or [],
        "cleanup_candidates": context.get("cleanup_candidates") or [],
        "cleanup_mode": CLEANUP_REPORT_ONLY,
        "delete_performed": False,
        "safety_gates": (latest or {}).get("safety_gates") or evaluated.get("safety_gates") or [],
        "isolation_status": path_safety.get("isolated_from_production_tile_serving"),
        "json_path": _manifest_json_path(storage),
        "markdown_path": _report_md_path(storage),
        "suggested_command": SUGGESTED_SANDBOX_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }
    return compact


def build_render_candidate_sandbox_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_sandbox_manifest(storage)
    if latest is None:
        context = gather_sandbox_context(storage)
        manifest = build_sandbox_manifest_body(storage, context)
    else:
        manifest = latest
    return {
        **_safety_fields(),
        "latest": manifest,
        "compact": compact_render_candidate_sandbox(storage),
    }
