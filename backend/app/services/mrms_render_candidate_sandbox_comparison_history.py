"""MRMS render candidate sandbox comparison history — local advisory only."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox_import_export import (
    EXPORT_DIR,
    SCHEMA_VERSION,
    STATUS_BLOCKED,
    compare_sandbox_manifests,
    load_import_export_status,
)
from backend.app.services.storage import LocalStorage

COMPARISON_HISTORY_JSON = "dev/mrms_render_candidate_sandbox_comparison_history.json"
COMPARISON_LATEST_JSON = "dev/mrms_render_candidate_sandbox_comparison_latest.json"
COMPARISON_HISTORY_MD = "dev/mrms_render_candidate_sandbox_comparison_history.md"

MAX_COMPARISON_HISTORY = 25

SUGGESTED_COMMAND = "make mrms-render-candidate-sandbox-comparison-history"

COMPARISON_TYPE_CURRENT_VS_IMPORTED = "current_vs_imported"
COMPARISON_TYPE_EXPORT_VS_PREVIOUS = "export_vs_previous_export"

COMPARISON_UNCHANGED = "unchanged"
COMPARISON_CHANGED = "changed"
COMPARISON_BLOCKED = "blocked"

HISTORY_MISSING = "missing"
HISTORY_READY = "ready"
HISTORY_BLOCKED = "blocked"

NEXT_PHASE_RECOMMENDATION = (
    "Phase 82 — Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status "
    "trend review acknowledgment status trend review acknowledgment status (local rollup linking trend hints "
    "to acknowledgments without production authorization)"
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_comparison_history_only": True,
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


def _history_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(COMPARISON_HISTORY_JSON)


def _latest_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(COMPARISON_LATEST_JSON)


def _history_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(COMPARISON_HISTORY_MD)


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


def load_comparison_history(storage: LocalStorage, *, limit: int = MAX_COMPARISON_HISTORY) -> list[dict[str, Any]]:
    abs_path = storage.absolute_path(_history_json_path(storage))
    if not abs_path.is_file():
        return []
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data[:limit] if isinstance(item, dict)]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save_comparison_history(storage: LocalStorage, entries: list[dict[str, Any]]) -> None:
    repo_path = _history_json_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(entries[:MAX_COMPARISON_HISTORY], indent=2, sort_keys=True),
        encoding="utf-8",
    )


def load_comparison_latest(storage: LocalStorage) -> Optional[dict[str, Any]]:
    return _load_optional_json(storage, COMPARISON_LATEST_JSON)


def _extract_sandbox_manifest_from_export(export_data: dict[str, Any]) -> dict[str, Any]:
    for report in export_data.get("included_reports") or []:
        if report.get("kind") == "sandbox_manifest":
            content = report.get("content")
            if isinstance(content, dict):
                return content
    return {}


def _comparison_has_changes(comparison: dict[str, Any]) -> bool:
    return bool(
        comparison.get("changed_sandbox_status")
        or comparison.get("changed_blockers")
        or comparison.get("changed_warnings")
        or comparison.get("changed_safety_gate_summary")
        or comparison.get("changed_file_counts")
    )


def _classify_comparison(comparison: dict[str, Any], *, blocked: bool = False) -> str:
    if blocked:
        return COMPARISON_BLOCKED
    return COMPARISON_CHANGED if _comparison_has_changes(comparison) else COMPARISON_UNCHANGED


def _sorted_export_json_paths(storage: LocalStorage) -> list[str]:
    export_dir = storage.absolute_path(storage.normalize_path(EXPORT_DIR))
    if not export_dir.is_dir():
        return []
    files = sorted(export_dir.glob("candidate_sandbox_export_*.json"), key=lambda path: path.stat().st_mtime)
    return [f"data/{path.relative_to(storage.storage_root).as_posix()}" for path in files]


def build_comparison_history_entry(
    *,
    comparison_type: str,
    comparison: dict[str, Any],
    comparison_status: str,
    source_paths: dict[str, Optional[str]],
    notes: Optional[list[str]] = None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "recorded_at": _utc_now(),
        "comparison_type": comparison_type,
        "comparison_status": comparison_status,
        "comparison": comparison,
        "source_paths": source_paths,
        "safety_state": _current_safety_state(),
        "notes": notes or [],
        **_safety_fields(),
    }


def append_comparison_history_entry(storage: LocalStorage, entry: dict[str, Any]) -> dict[str, Any]:
    safety = _current_safety_state()
    if bool(safety.get("verified_mrms")) or bool(safety.get("enable_production_radar_tiles")):
        entry = {
            **entry,
            "comparison_status": COMPARISON_BLOCKED,
            "blocked_reason": "safety_gate_failure",
        }

    history = load_comparison_history(storage, limit=MAX_COMPARISON_HISTORY)
    history.insert(0, entry)
    _save_comparison_history(storage, history)

    latest = {
        **entry,
        "history_count": len(history),
        "history_json_path": _history_json_path(storage),
        "history_markdown_path": _history_md_path(storage),
        **_safety_fields(),
    }
    storage.absolute_path(_latest_json_path(storage)).write_text(
        json.dumps(latest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(_history_md_path(storage)).write_text(
        build_comparison_history_markdown(history, latest),
        encoding="utf-8",
    )
    return latest


def record_import_comparison_history(
    storage: LocalStorage,
    import_record: dict[str, Any],
) -> Optional[dict[str, Any]]:
    comparison = import_record.get("comparison") or {}
    blocked = import_record.get("import_export_status") == STATUS_BLOCKED
    if blocked and not comparison:
        return None

    entry = build_comparison_history_entry(
        comparison_type=COMPARISON_TYPE_CURRENT_VS_IMPORTED,
        comparison=comparison,
        comparison_status=_classify_comparison(comparison, blocked=blocked),
        source_paths={
            "import_json_path": import_record.get("json_path"),
            "export_json_path": import_record.get("imported_from"),
        },
        notes=["Recorded from metadata-only import comparison"],
    )
    return append_comparison_history_entry(storage, entry)


def record_export_comparison_history(
    storage: LocalStorage,
    *,
    export_json_path: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    export_paths = _sorted_export_json_paths(storage)
    if len(export_paths) < 2:
        return None

    latest_path = export_json_path or export_paths[-1]
    if latest_path not in export_paths:
        return None
    idx = export_paths.index(latest_path)
    if idx < 1:
        return None
    previous_path = export_paths[idx - 1]

    latest_export = _load_optional_json(storage, latest_path)
    previous_export = _load_optional_json(storage, previous_path)
    if latest_export is None or previous_export is None:
        return None

    comparison = compare_sandbox_manifests(
        _extract_sandbox_manifest_from_export(previous_export),
        _extract_sandbox_manifest_from_export(latest_export),
    )
    entry = build_comparison_history_entry(
        comparison_type=COMPARISON_TYPE_EXPORT_VS_PREVIOUS,
        comparison=comparison,
        comparison_status=_classify_comparison(comparison),
        source_paths={
            "previous_export_json_path": previous_path,
            "latest_export_json_path": latest_path,
        },
        notes=["Recorded from export-vs-previous-export metadata comparison"],
    )
    return append_comparison_history_entry(storage, entry)


def evaluate_comparison_history_status(storage: LocalStorage) -> dict[str, Any]:
    safety = _current_safety_state()
    blockers: list[str] = []
    if bool(safety.get("verified_mrms")):
        blockers.append("verified_mrms must remain false")
    if bool(safety.get("enable_production_radar_tiles")):
        blockers.append("production rendering must remain disabled")
    if not bool(safety.get("placeholder_default")):
        blockers.append("placeholder-first default must be preserved")

    history = load_comparison_history(storage)
    if blockers:
        return {
            "history_status": HISTORY_BLOCKED,
            "history_reason": "safety_gate_failure",
            "blockers": blockers,
            "warnings": [],
            "history_count": len(history),
        }
    if not history:
        return {
            "history_status": HISTORY_MISSING,
            "history_reason": "no_comparison_history_entries",
            "blockers": [],
            "warnings": ["run import/export workflow to record comparison history"],
            "history_count": 0,
        }
    return {
        "history_status": HISTORY_READY,
        "history_reason": "comparison_history_available",
        "blockers": [],
        "warnings": [],
        "history_count": len(history),
    }


def build_comparison_history_markdown(
    history: list[dict[str, Any]],
    latest: dict[str, Any],
) -> str:
    lines = [
        "# MRMS Render Candidate Sandbox Comparison History",
        "",
        f"Generated at: {_utc_now()}",
        "",
        "> **WARNING:** Local comparison history only. Advisory metadata — does **NOT** verify MRMS, "
        "enable production rendering, download/decode/render, create or serve production tiles, "
        "clear alerts, or authorize production use.",
        "",
        f"- History status: **{latest.get('history_status', 'missing')}**",
        f"- History count: {latest.get('history_count', len(history))}",
        f"- Latest comparison type: {latest.get('comparison_type')}",
        f"- Latest comparison status: {latest.get('comparison_status')}",
        "",
        "## Recent entries",
        "",
    ]
    if not history:
        lines.append("- None")
    else:
        for item in history[:10]:
            lines.append(
                f"- {item.get('recorded_at')} — {item.get('comparison_type')} "
                f"({item.get('comparison_status')})"
            )
    return "\n".join(lines) + "\n"


def refresh_comparison_history_report(storage: LocalStorage) -> dict[str, Any]:
    history = load_comparison_history(storage)
    evaluated = evaluate_comparison_history_status(storage)
    latest = load_comparison_latest(storage) or {}
    body = {
        "generated_at": _utc_now(),
        "history_status": evaluated["history_status"],
        "history_reason": evaluated["history_reason"],
        "history_count": evaluated["history_count"],
        "blockers": evaluated["blockers"],
        "warnings": evaluated["warnings"],
        "latest_entry": history[0] if history else None,
        "recent_entries": history[:10],
        "schema_version": SCHEMA_VERSION,
        "json_path": _history_json_path(storage),
        "markdown_path": _history_md_path(storage),
        "latest_json_path": _latest_json_path(storage),
        "suggested_command": SUGGESTED_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }
    storage.ensure_directories(_history_json_path(storage).rsplit("/", 1)[0])
    if history:
        storage.absolute_path(_history_md_path(storage)).write_text(
            build_comparison_history_markdown(history, {**latest, **body}),
            encoding="utf-8",
        )
    else:
        storage.absolute_path(_history_md_path(storage)).write_text(
            build_comparison_history_markdown([], body),
            encoding="utf-8",
        )
    return body


def compact_comparison_history(storage: LocalStorage) -> dict[str, Any]:
    history = load_comparison_history(storage, limit=10)
    latest = load_comparison_latest(storage)
    evaluated = evaluate_comparison_history_status(storage)
    import_export = load_import_export_status(storage) or {}
    return {
        "available": bool(history),
        "history_status": evaluated.get("history_status"),
        "history_reason": evaluated.get("history_reason"),
        "history_count": evaluated.get("history_count", len(history)),
        "blockers": evaluated.get("blockers") or [],
        "warnings": evaluated.get("warnings") or [],
        "schema_version": SCHEMA_VERSION,
        "latest_comparison_type": (latest or {}).get("comparison_type"),
        "latest_comparison_status": (latest or {}).get("comparison_status"),
        "latest_recorded_at": (latest or {}).get("recorded_at"),
        "recent_entries": [
            {
                "recorded_at": item.get("recorded_at"),
                "comparison_type": item.get("comparison_type"),
                "comparison_status": item.get("comparison_status"),
                "changed_sandbox_status": (item.get("comparison") or {}).get("changed_sandbox_status"),
            }
            for item in history[:5]
        ],
        "latest_import_export_status": import_export.get("import_export_status"),
        "json_path": _history_json_path(storage),
        "markdown_path": _history_md_path(storage),
        "latest_json_path": _latest_json_path(storage),
        "suggested_command": SUGGESTED_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_comparison_history_payload(storage: LocalStorage) -> dict[str, Any]:
    history = load_comparison_history(storage)
    latest = load_comparison_latest(storage)
    evaluated = evaluate_comparison_history_status(storage)
    body = refresh_comparison_history_report(storage) if history else {
        "generated_at": _utc_now(),
        "history_status": evaluated["history_status"],
        "history_reason": evaluated["history_reason"],
        "history_count": evaluated["history_count"],
        "blockers": evaluated["blockers"],
        "warnings": evaluated["warnings"],
        "latest_entry": latest,
        "recent_entries": history,
        "schema_version": SCHEMA_VERSION,
        "json_path": _history_json_path(storage),
        "markdown_path": _history_md_path(storage),
        "latest_json_path": _latest_json_path(storage),
        "suggested_command": SUGGESTED_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }
    return {
        **_safety_fields(),
        "latest": body,
        "compact": compact_comparison_history(storage),
    }
