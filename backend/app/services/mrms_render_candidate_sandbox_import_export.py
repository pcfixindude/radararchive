"""MRMS render candidate sandbox manifest import/export — local metadata only."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox import load_sandbox_manifest
from backend.app.services.storage import LocalStorage

SCHEMA_VERSION = "1.0"
SUPPORTED_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION})

EXPORT_DIR = "dev/mrms_render_candidate_exports"
IMPORT_DIR = "dev/mrms_render_candidate_imports"
STATUS_JSON = "dev/mrms_render_candidate_import_export_latest.json"
STATUS_MD = "dev/mrms_render_candidate_import_export_latest.md"

SUGGESTED_EXPORT_COMMAND = "make mrms-render-candidate-sandbox-export"
SUGGESTED_IMPORT_EXPORT_COMMAND = "make mrms-render-candidate-sandbox-import-export"

PRODUCTION_TILE_PATH_TOKEN = "tiles/production"

STATUS_MISSING = "missing"
STATUS_EXPORT_READY = "export_ready"
STATUS_IMPORT_READY = "import_ready"
STATUS_IMPORTED = "imported"
STATUS_INVALID = "invalid"
STATUS_BLOCKED = "blocked"

NEXT_PHASE_RECOMMENDATION = (
    "Phase 77 — Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status "
    "trend review acknowledgment (local acknowledgment of reviewed trend review acknowledgment status trend hints "
    "without production authorization)"
)

INPUT_DEFINITIONS: tuple[dict[str, str], ...] = (
    {
        "path": "dev/mrms_render_candidate_sandbox_manifest.json",
        "kind": "sandbox_manifest",
        "format": "json",
    },
    {
        "path": "dev/mrms_render_candidate_sandbox_report.md",
        "kind": "sandbox_report",
        "format": "markdown",
    },
    {
        "path": "dev/mrms_render_candidate_scaffold.json",
        "kind": "scaffold",
        "format": "json",
    },
    {
        "path": "dev/mrms_render_candidate_preflight.json",
        "kind": "preflight",
        "format": "json",
    },
    {
        "path": "dev/mrms_render_candidate_dry_run_plan.json",
        "kind": "dry_run_plan",
        "format": "json",
    },
)

_PATH_TRAVERSAL_RE = re.compile(r"(^|/)\.\.(/|$)|^\.\.$")


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _timestamp_token() -> str:
    return _utc_now().replace(":", "").replace("-", "")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_import_export_only": True,
        "metadata_report_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "does_not_download_or_decode": True,
        "does_not_create_production_tiles": True,
        "does_not_serve_production_tiles": True,
        "does_not_delete_by_default": True,
        "binary_artifacts_included": False,
        "no_external_notifications": True,
        "does_not_authorize_production_use": True,
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


def _status_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(STATUS_JSON)


def _status_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(STATUS_MD)


def _export_dir(storage: LocalStorage) -> str:
    return storage.normalize_path(EXPORT_DIR)


def _import_dir(storage: LocalStorage) -> str:
    return storage.normalize_path(IMPORT_DIR)


def _path_under_data_dev(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("/")
    return (
        normalized.startswith("dev/")
        or normalized == "dev"
        or normalized.startswith("data/dev/")
    )


def _path_references_production_tiles(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return PRODUCTION_TILE_PATH_TOKEN in normalized


def _path_has_traversal(path: str) -> bool:
    return bool(_PATH_TRAVERSAL_RE.search(path.replace("\\", "/")))


def _load_optional_json(storage: LocalStorage, repo_path: str) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(storage.normalize_path(repo_path))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _load_optional_text(storage: LocalStorage, repo_path: str) -> Optional[str]:
    abs_path = storage.absolute_path(storage.normalize_path(repo_path))
    if not abs_path.is_file():
        return None
    try:
        return abs_path.read_text(encoding="utf-8")
    except OSError:
        return None


def gather_export_inputs(storage: LocalStorage) -> dict[str, Any]:
    included_reports: list[dict[str, Any]] = []
    missing_inputs: list[str] = []

    for definition in INPUT_DEFINITIONS:
        repo_path = definition["path"]
        normalized = storage.normalize_path(repo_path)
        if definition["format"] == "json":
            content = _load_optional_json(storage, repo_path)
            if content is None:
                missing_inputs.append(normalized)
                continue
            included_reports.append(
                {
                    "path": normalized,
                    "kind": definition["kind"],
                    "format": "json",
                    "content": content,
                }
            )
        else:
            text = _load_optional_text(storage, repo_path)
            if text is None:
                missing_inputs.append(normalized)
                continue
            included_reports.append(
                {
                    "path": normalized,
                    "kind": definition["kind"],
                    "format": "markdown",
                    "markdown": text,
                }
            )

    sandbox_manifest = next(
        (item for item in included_reports if item.get("kind") == "sandbox_manifest"),
        None,
    )
    sandbox_status = None
    if sandbox_manifest:
        sandbox_status = (sandbox_manifest.get("content") or {}).get("sandbox_status")

    return {
        "included_reports": included_reports,
        "missing_inputs": missing_inputs,
        "sandbox_status": sandbox_status,
    }


def _safety_gate_summary_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    gates = manifest.get("safety_gates") or []
    if not gates and manifest.get("kind") == "sandbox_manifest":
        gates = (manifest.get("content") or {}).get("safety_gates") or []
    passed = sum(1 for gate in gates if gate.get("passed"))
    failed = sum(1 for gate in gates if not gate.get("passed"))
    return {"passed": passed, "failed": failed, "total": len(gates)}


def _file_count_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    scans = manifest.get("subdirectory_scans") or []
    if not scans and manifest.get("kind") == "sandbox_manifest":
        scans = (manifest.get("content") or {}).get("subdirectory_scans") or []
    summary: dict[str, Any] = {}
    for scan in scans:
        name = scan.get("name")
        if not name:
            continue
        summary[name] = {
            "file_count": scan.get("file_count") or 0,
            "total_bytes": scan.get("total_bytes") or 0,
        }
    return summary


def compare_sandbox_manifests(
    current: Optional[dict[str, Any]],
    imported: Optional[dict[str, Any]],
) -> dict[str, Any]:
    current = current or {}
    imported = imported or {}
    current_status = current.get("sandbox_status")
    imported_status = imported.get("sandbox_status")
    current_blockers = current.get("blocking_items") or []
    imported_blockers = imported.get("blocking_items") or []
    current_warnings = current.get("warnings") or []
    imported_warnings = imported.get("warnings") or []
    current_gate_summary = _safety_gate_summary_from_manifest(current)
    imported_gate_summary = _safety_gate_summary_from_manifest(imported)
    current_counts = _file_count_summary(current)
    imported_counts = _file_count_summary(imported)

    matching_fields: list[str] = []
    missing_fields: list[str] = []
    for field in ("sandbox_status", "sandbox_reason", "sandbox_root", "cleanup_mode"):
        if field in current and field in imported:
            if current.get(field) == imported.get(field):
                matching_fields.append(field)
        elif field in imported and field not in current:
            missing_fields.append(field)

    changed_file_counts: list[dict[str, Any]] = []
    for name in sorted(set(current_counts) | set(imported_counts)):
        left = current_counts.get(name) or {}
        right = imported_counts.get(name) or {}
        if left != right:
            changed_file_counts.append(
                {
                    "subdirectory": name,
                    "current": left,
                    "imported": right,
                }
            )

    return {
        "advisory_only": True,
        "changed_sandbox_status": current_status != imported_status,
        "current_sandbox_status": current_status,
        "imported_sandbox_status": imported_status,
        "changed_blockers": sorted(set(current_blockers) ^ set(imported_blockers)),
        "changed_warnings": sorted(set(current_warnings) ^ set(imported_warnings)),
        "matching_fields": matching_fields,
        "missing_fields": missing_fields,
        "current_safety_gate_summary": current_gate_summary,
        "imported_safety_gate_summary": imported_gate_summary,
        "changed_safety_gate_summary": current_gate_summary != imported_gate_summary,
        "changed_file_counts": changed_file_counts,
        "current_generated_at": current.get("created_at") or current.get("generated_at"),
        "imported_generated_at": imported.get("created_at") or imported.get("generated_at"),
        "imported_source": imported.get("source"),
    }


def validate_import_manifest(data: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    schema_version = str(data.get("schema_version") or "")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        blockers.append(f"unsupported schema_version: {schema_version or 'missing'}")

    if bool(data.get("verified_mrms")):
        blockers.append("import manifest claims verified_mrms=true")

    safety_state = data.get("safety_state") or {}
    if bool(safety_state.get("verified_mrms")):
        blockers.append("import safety_state claims verified_mrms=true")
    if bool(safety_state.get("enable_production_radar_tiles")):
        blockers.append("import safety_state claims production rendering enabled")
    if bool(safety_state.get("production_tile_serving_enabled")):
        blockers.append("import safety_state claims production tile serving enabled")

    if bool(data.get("binary_artifacts_included")):
        blockers.append("import manifest includes binary artifacts by default")

    for report in data.get("included_reports") or []:
        path = str(report.get("path") or "")
        if not path:
            blockers.append("included report missing path")
            continue
        if _path_has_traversal(path):
            blockers.append(f"path traversal detected in included report: {path}")
        if not _path_under_data_dev(path):
            blockers.append(f"included report path escapes data/dev/: {path}")
        if _path_references_production_tiles(path):
            blockers.append(f"included report references production tile path: {path}")

    sandbox_root = str(data.get("sandbox_root") or "")
    if sandbox_root:
        if _path_has_traversal(sandbox_root):
            blockers.append(f"path traversal detected in sandbox_root: {sandbox_root}")
        if not _path_under_data_dev(sandbox_root):
            blockers.append(f"sandbox_root escapes data/dev/: {sandbox_root}")
        if _path_references_production_tiles(sandbox_root):
            blockers.append(f"sandbox_root references production tile path: {sandbox_root}")

    export_json_path = str(data.get("json_path") or data.get("export_json_path") or "")
    if export_json_path:
        if _path_has_traversal(export_json_path):
            blockers.append(f"path traversal detected in export path: {export_json_path}")
        if not _path_under_data_dev(export_json_path):
            blockers.append(f"export path escapes data/dev/: {export_json_path}")

    if not data.get("included_reports"):
        blockers.append("import manifest has no included_reports entries")

    status = STATUS_IMPORTED
    if blockers:
        status = STATUS_BLOCKED if any(
            token in " ".join(blockers).lower()
            for token in (
                "verified_mrms",
                "production",
                "traversal",
                "escapes data/dev",
                "binary artifacts",
                "unsupported schema",
            )
        ) else STATUS_INVALID

    return {
        "valid": not blockers,
        "import_status": status,
        "blockers": blockers,
        "warnings": warnings,
    }


def build_export_manifest(storage: LocalStorage) -> dict[str, Any]:
    inputs = gather_export_inputs(storage)
    safety_state = _current_safety_state()
    blockers: list[str] = []
    warnings: list[str] = []

    if bool(safety_state.get("verified_mrms")):
        blockers.append("verified_mrms must remain false")
    if bool(safety_state.get("enable_production_radar_tiles")):
        blockers.append("production rendering must remain disabled for export")
    if not bool(safety_state.get("placeholder_default")):
        blockers.append("placeholder-first default must be preserved")

    if inputs["missing_inputs"]:
        for path in inputs["missing_inputs"]:
            warnings.append(f"optional upstream report missing: {path}")

    export_status = STATUS_BLOCKED if blockers else STATUS_EXPORT_READY
    if not inputs["included_reports"]:
        export_status = STATUS_MISSING
        warnings.append("no candidate sandbox reports available to export")

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "radararchive_local_export",
        "safety_state": safety_state,
        "sandbox_status": inputs.get("sandbox_status"),
        "included_reports": inputs["included_reports"],
        "missing_inputs": inputs["missing_inputs"],
        "blockers": blockers,
        "warnings": warnings,
        "notes": [
            "Metadata/report-only export — no binary artifacts included",
            "Does not verify MRMS or authorize production use",
        ],
        "import_export_status": export_status,
        **_safety_fields(),
    }


def build_export_markdown(export_manifest: dict[str, Any]) -> str:
    lines = [
        "# MRMS Render Candidate Sandbox Export",
        "",
        f"Generated at: {export_manifest.get('generated_at')}",
        "",
        "> **WARNING:** Local manifest import/export only. Does **NOT** verify MRMS, enable production "
        "rendering, download/decode/render, create or serve production tiles, clear alerts, or "
        "authorize production use. Imports are metadata/report-only.",
        "",
        "## Export metadata",
        "",
        f"- Schema version: `{export_manifest.get('schema_version')}`",
        f"- Source: {export_manifest.get('source')}",
        f"- Advisory status: **{export_manifest.get('import_export_status')}**",
        f"- Sandbox status: {export_manifest.get('sandbox_status')}",
        f"- Binary artifacts included: {export_manifest.get('binary_artifacts_included')}",
        "",
        "## Included reports",
        "",
    ]
    for report in export_manifest.get("included_reports") or []:
        lines.append(f"- `{report.get('path')}` ({report.get('kind')}, {report.get('format')})")
    lines.extend(["", "## Missing inputs", ""])
    missing = export_manifest.get("missing_inputs") or []
    if missing:
        lines.extend(f"- {path}" for path in missing)
    else:
        lines.append("- None")
    lines.extend(["", "## Blockers", ""])
    blockers = export_manifest.get("blockers") or []
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    warnings = export_manifest.get("warnings") or []
    if warnings:
        lines.extend(f"- {item}" for item in warnings)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def _latest_file_in_dir(storage: LocalStorage, repo_dir: str, suffix: str) -> Optional[str]:
    abs_dir = storage.absolute_path(repo_dir)
    if not abs_dir.is_dir():
        return None
    candidates = sorted(abs_dir.glob(f"*{suffix}"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        return None
    rel = candidates[0].relative_to(storage.storage_root)
    return f"data/{rel.as_posix()}"


def export_candidate_sandbox_manifest(storage: LocalStorage) -> dict[str, Any]:
    export_body = build_export_manifest(storage)
    if export_body.get("import_export_status") == STATUS_BLOCKED:
        return save_import_export_status(storage, export_body, export_json=None, export_md=None)

    token = _timestamp_token()
    export_json = storage.normalize_path(EXPORT_DIR, f"candidate_sandbox_export_{token}.json")
    export_md = storage.normalize_path(EXPORT_DIR, f"candidate_sandbox_export_{token}.md")
    storage.ensure_directories(_export_dir(storage))

    export_body = {
        **export_body,
        "json_path": export_json,
        "markdown_path": export_md,
    }
    storage.absolute_path(export_json).write_text(
        json.dumps(export_body, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(export_md).write_text(
        build_export_markdown(export_body),
        encoding="utf-8",
    )
    result = save_import_export_status(storage, export_body, export_json=export_json, export_md=export_md)
    from backend.app.services.mrms_render_candidate_sandbox_comparison_history import (
        record_export_comparison_history,
    )

    record_export_comparison_history(storage, export_json_path=export_json)
    return result


def import_candidate_sandbox_manifest(
    storage: LocalStorage,
    *,
    source_json_path: Optional[str] = None,
) -> dict[str, Any]:
    source_json_path = source_json_path or _latest_file_in_dir(storage, _export_dir(storage), ".json")
    if not source_json_path:
        invalid = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": _utc_now(),
            "import_export_status": STATUS_MISSING,
            "blockers": ["no export manifest available to import"],
            "warnings": [],
            **_safety_fields(),
        }
        return save_import_export_status(storage, invalid)

    data = _load_optional_json(storage, source_json_path)
    if data is None:
        invalid = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": _utc_now(),
            "import_export_status": STATUS_INVALID,
            "blockers": [f"unable to read export manifest: {source_json_path}"],
            "warnings": [],
            **_safety_fields(),
        }
        return save_import_export_status(storage, invalid)

    validation = validate_import_manifest(data)
    current_manifest = load_sandbox_manifest(storage) or {}
    imported_sandbox_manifest = next(
        (
            (report.get("content") or {})
            for report in data.get("included_reports") or []
            if report.get("kind") == "sandbox_manifest"
        ),
        {},
    )
    comparison = compare_sandbox_manifests(current_manifest, imported_sandbox_manifest)

    token = _timestamp_token()
    import_json = storage.normalize_path(IMPORT_DIR, f"imported_candidate_sandbox_{token}.json")
    import_md = storage.normalize_path(IMPORT_DIR, f"imported_candidate_sandbox_{token}.md")
    storage.ensure_directories(_import_dir(storage))

    import_record = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": data.get("source") or "radararchive_local_import",
        "imported_from": source_json_path,
        "import_export_status": validation["import_status"],
        "validation": validation,
        "comparison": comparison,
        "safety_state": _current_safety_state(),
        "sandbox_status": imported_sandbox_manifest.get("sandbox_status") or data.get("sandbox_status"),
        "included_reports": data.get("included_reports") or [],
        "missing_inputs": data.get("missing_inputs") or [],
        "blockers": validation["blockers"],
        "warnings": validation["warnings"] + (data.get("warnings") or []),
        "notes": [
            "Metadata/report-only import — no production tiles created or served",
            "Does not verify MRMS or authorize production use",
        ],
        "json_path": import_json,
        "markdown_path": import_md,
        **_safety_fields(),
    }
    storage.absolute_path(import_json).write_text(
        json.dumps(import_record, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(import_md).write_text(
        build_import_markdown(import_record),
        encoding="utf-8",
    )
    status_body = {
        **import_record,
        "latest_export_json_path": source_json_path,
        "latest_import_json_path": import_json,
        "latest_import_markdown_path": import_md,
        "comparison": comparison,
    }
    result = save_import_export_status(
        storage,
        status_body,
        export_json=source_json_path,
        export_md=_latest_file_in_dir(storage, _export_dir(storage), ".md"),
        import_json=import_json,
        import_md=import_md,
    )
    if validation.get("valid"):
        from backend.app.services.mrms_render_candidate_sandbox_comparison_history import (
            record_import_comparison_history,
        )

        record_import_comparison_history(storage, import_record)
    return result


def build_import_markdown(import_record: dict[str, Any]) -> str:
    lines = [
        "# MRMS Render Candidate Sandbox Import",
        "",
        f"Generated at: {import_record.get('generated_at')}",
        "",
        "> **WARNING:** Local metadata/report-only import. Does **NOT** verify MRMS or authorize production use.",
        "",
        f"- Import status: **{import_record.get('import_export_status')}**",
        f"- Imported from: `{import_record.get('imported_from')}`",
        f"- Schema version: `{import_record.get('schema_version')}`",
        "",
        "## Validation",
        "",
    ]
    validation = import_record.get("validation") or {}
    lines.append(f"- Valid: {validation.get('valid')}")
    lines.extend(["", "## Blockers", ""])
    blockers = import_record.get("blockers") or []
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None")

    comparison = import_record.get("comparison") or {}
    lines.extend(
        [
            "",
            "## Comparison (advisory)",
            "",
            f"- Changed sandbox status: {comparison.get('changed_sandbox_status')}",
            f"- Current sandbox status: {comparison.get('current_sandbox_status')}",
            f"- Imported sandbox status: {comparison.get('imported_sandbox_status')}",
            f"- Changed safety gate summary: {comparison.get('changed_safety_gate_summary')}",
        ]
    )
    changed_counts = comparison.get("changed_file_counts") or []
    if changed_counts:
        lines.append("")
        lines.append("### Changed file counts")
        for item in changed_counts:
            lines.append(
                f"- {item.get('subdirectory')}: current={item.get('current')} imported={item.get('imported')}"
            )
    return "\n".join(lines) + "\n"


def build_status_markdown(status: dict[str, Any]) -> str:
    lines = [
        "# MRMS Render Candidate Sandbox Import/Export Status",
        "",
        f"Generated at: {status.get('generated_at') or _utc_now()}",
        "",
        "> **WARNING:** Local manifest import/export only. Metadata/report-only. Does **NOT** verify MRMS.",
        "",
        f"- Advisory status: **{status.get('import_export_status')}**",
        f"- Schema version: `{status.get('schema_version')}`",
        f"- Latest export JSON: `{status.get('latest_export_json_path')}`",
        f"- Latest import JSON: `{status.get('latest_import_json_path')}`",
        "",
        "## Included reports",
        "",
    ]
    for report in status.get("included_reports") or []:
        lines.append(f"- `{report.get('path')}` ({report.get('kind')})")
    lines.extend(["", "## Missing inputs", ""])
    missing = status.get("missing_inputs") or []
    if missing:
        lines.extend(f"- {path}" for path in missing)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def save_import_export_status(
    storage: LocalStorage,
    body: dict[str, Any],
    *,
    export_json: Optional[str] = None,
    export_md: Optional[str] = None,
    import_json: Optional[str] = None,
    import_md: Optional[str] = None,
) -> dict[str, Any]:
    json_path = _status_json_path(storage)
    md_path = _status_md_path(storage)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])

    status = {
        **body,
        "generated_at": body.get("generated_at") or _utc_now(),
        "schema_version": body.get("schema_version") or SCHEMA_VERSION,
        "latest_export_json_path": export_json or body.get("latest_export_json_path") or _latest_file_in_dir(
            storage, _export_dir(storage), ".json"
        ),
        "latest_export_markdown_path": export_md
        or body.get("latest_export_markdown_path")
        or _latest_file_in_dir(storage, _export_dir(storage), ".md"),
        "latest_import_json_path": import_json
        or body.get("latest_import_json_path")
        or _latest_file_in_dir(storage, _import_dir(storage), ".json"),
        "latest_import_markdown_path": import_md
        or body.get("latest_import_markdown_path")
        or _latest_file_in_dir(storage, _import_dir(storage), ".md"),
        "status_json_path": json_path,
        "status_markdown_path": md_path,
        "suggested_export_command": SUGGESTED_EXPORT_COMMAND,
        "suggested_import_export_command": SUGGESTED_IMPORT_EXPORT_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(status, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(build_status_markdown(status), encoding="utf-8")
    return status


def load_import_export_status(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_status_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def evaluate_import_export_status(storage: LocalStorage) -> dict[str, Any]:
    safety_state = _current_safety_state()
    blockers: list[str] = []
    if bool(safety_state.get("verified_mrms")):
        blockers.append("verified_mrms must remain false")
    if bool(safety_state.get("enable_production_radar_tiles")):
        blockers.append("production rendering must remain disabled")
    if not bool(safety_state.get("placeholder_default")):
        blockers.append("placeholder-first default must be preserved")

    latest = load_import_export_status(storage)
    if latest and latest.get("import_export_status") == STATUS_IMPORTED:
        return {
            "import_export_status": STATUS_IMPORTED,
            "import_export_reason": "latest_import_valid",
            "blockers": blockers,
            "warnings": [],
        }

    inputs = gather_export_inputs(storage)
    latest_export = _latest_file_in_dir(storage, _export_dir(storage), ".json")
    if blockers:
        return {
            "import_export_status": STATUS_BLOCKED,
            "import_export_reason": "safety_gate_failure",
            "blockers": blockers,
            "warnings": [f"optional upstream report missing: {path}" for path in inputs["missing_inputs"]]
            if inputs["missing_inputs"]
            else [],
        }
    if not inputs["included_reports"]:
        return {
            "import_export_status": STATUS_MISSING,
            "import_export_reason": "no_reports_available",
            "blockers": [],
            "warnings": ["no candidate sandbox reports available"],
        }
    if latest_export:
        return {
            "import_export_status": STATUS_IMPORT_READY,
            "import_export_reason": "export_available_for_import",
            "blockers": [],
            "warnings": [],
        }
    return {
        "import_export_status": STATUS_EXPORT_READY,
        "import_export_reason": "reports_available_for_export",
        "blockers": [],
        "warnings": [f"optional upstream report missing: {path}" for path in inputs["missing_inputs"]],
    }


def _summarize_included_reports(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "path": report.get("path"),
            "kind": report.get("kind"),
            "format": report.get("format"),
        }
        for report in reports
    ]


def compact_render_candidate_sandbox_import_export(storage: LocalStorage) -> dict[str, Any]:
    latest = load_import_export_status(storage)
    evaluated = evaluate_import_export_status(storage)
    inputs = gather_export_inputs(storage)
    comparison = (latest or {}).get("comparison") or {}
    included = (latest or {}).get("included_reports") or inputs.get("included_reports") or []
    return {
        "available": latest is not None,
        "import_export_status": (latest or {}).get("import_export_status")
        or evaluated.get("import_export_status"),
        "import_export_reason": evaluated.get("import_export_reason"),
        "schema_version": (latest or {}).get("schema_version") or SCHEMA_VERSION,
        "blockers": (latest or {}).get("blockers") or evaluated.get("blockers") or [],
        "warnings": (latest or {}).get("warnings") or evaluated.get("warnings") or [],
        "included_reports": _summarize_included_reports(included),
        "missing_inputs": (latest or {}).get("missing_inputs") or inputs.get("missing_inputs") or [],
        "latest_export_json_path": (latest or {}).get("latest_export_json_path")
        or _latest_file_in_dir(storage, _export_dir(storage), ".json"),
        "latest_export_markdown_path": (latest or {}).get("latest_export_markdown_path")
        or _latest_file_in_dir(storage, _export_dir(storage), ".md"),
        "latest_import_json_path": (latest or {}).get("latest_import_json_path")
        or _latest_file_in_dir(storage, _import_dir(storage), ".json"),
        "latest_import_markdown_path": (latest or {}).get("latest_import_markdown_path")
        or _latest_file_in_dir(storage, _import_dir(storage), ".md"),
        "comparison": comparison,
        "status_json_path": _status_json_path(storage),
        "status_markdown_path": _status_md_path(storage),
        "suggested_export_command": SUGGESTED_EXPORT_COMMAND,
        "suggested_import_export_command": SUGGESTED_IMPORT_EXPORT_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_render_candidate_sandbox_import_export_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_import_export_status(storage)
    if latest is None:
        export_preview = build_export_manifest(storage)
        latest = export_preview
    return {
        **_safety_fields(),
        "latest": latest,
        "compact": compact_render_candidate_sandbox_import_export(storage),
    }


def run_import_export_workflow(
    storage: LocalStorage,
    *,
    export: bool = True,
    import_after_export: bool = False,
    source_json_path: Optional[str] = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if export:
        result["export"] = export_candidate_sandbox_manifest(storage)
    if import_after_export or source_json_path:
        result["import"] = import_candidate_sandbox_manifest(
            storage,
            source_json_path=source_json_path or (result.get("export") or {}).get("json_path"),
        )
    return result.get("import") or result.get("export") or build_export_manifest(storage)
