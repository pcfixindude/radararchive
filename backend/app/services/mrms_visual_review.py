"""MRMS visual review artifacts — local tile evidence inspection only, not verified MRMS."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import (
    PROCESSED_STATUS_PLACEHOLDER_FOR_REAL_RAW,
    RENDER_STATUS_PLACEHOLDER,
    RENDER_STATUS_PRODUCTION_RENDERED,
    is_placeholder_tile_status,
)
from backend.app.services.decoded_tile_cache import (
    TILE_CACHE_ROOT,
    find_decode_artifact_for_frame,
)
from backend.app.services.operator_guidance import RUNBOOK_PATH
from backend.app.services.render_status import classify_frame_render_status
from backend.app.services.storage import LocalStorage
from backend.app.services.tile_pyramid import build_production_tile_repo_path

VISUAL_REVIEW_LATEST_JSON = "dev/mrms_visual_review_latest.json"
VISUAL_REVIEW_PREVIOUS_JSON = "dev/mrms_visual_review_previous.json"
VISUAL_REVIEW_LATEST_MD = "dev/mrms_visual_review_latest.md"
VISUAL_REVIEW_HISTORY = "dev/mrms_visual_review_history.json"
MAX_VISUAL_REVIEW_HISTORY = 25

SUGGESTED_VISUAL_REVIEW_COMMAND = "make mrms-visual-review"
RUNBOOK_SECTION = "MRMS visual review artifacts"
RUNBOOK_ANCHOR = "mrms-visual-review-artifacts"

TILE_MODE_PLACEHOLDER = "placeholder"
TILE_MODE_PLACEHOLDER_FOR_REAL_RAW = "placeholder_for_real_raw"
TILE_MODE_DECODED_PROTOTYPE = "decoded_prototype"
TILE_MODE_PRODUCTION_GATED = "production_gated"
TILE_MODE_PRODUCTION_RENDERED_CACHE = "production_rendered_cache"
TILE_MODE_UNKNOWN = "unknown"

TILE_MODE_EXPLANATIONS: dict[str, str] = {
    TILE_MODE_PLACEHOLDER: (
        "Placeholder processed PNG or catalog render_status=placeholder — default map tiles, "
        "not decoded MRMS imagery."
    ),
    TILE_MODE_PLACEHOLDER_FOR_REAL_RAW: (
        "Placeholder preview for a real raw download — still not decoded MRMS tiles."
    ),
    TILE_MODE_DECODED_PROTOTYPE: (
        "Decoded prototype artifacts and/or decoded_prototype tile cache — prototype warp only."
    ),
    TILE_MODE_PRODUCTION_GATED: (
        "Production rendering flagged or pending but no production tile cache served — "
        "production remains gated/disabled."
    ),
    TILE_MODE_PRODUCTION_RENDERED_CACHE: (
        "Production tile cache file exists locally — still prototype and gated unless flags allow serving."
    ),
    TILE_MODE_UNKNOWN: "Artifact classification inconclusive from existing local paths.",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _latest_json_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(VISUAL_REVIEW_LATEST_JSON)


def _latest_md_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(VISUAL_REVIEW_LATEST_MD)


def _history_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(VISUAL_REVIEW_HISTORY)


def _timestamp_token(timestamp: str) -> str:
    return timestamp.replace(":", "").replace("-", "")


def _decoded_tile_cache_path(storage: LocalStorage, timestamp: str) -> str:
    token = _timestamp_token(timestamp)
    return storage.normalize_path(TILE_CACHE_ROOT, token, "0", "0", "0.png")


def _path_exists(storage: LocalStorage, path: Optional[str]) -> bool:
    return bool(path and storage.path_exists(path))


def classify_visual_tile_mode(
    *,
    frame: RadarFile,
    has_decode_artifact: bool,
    has_decoded_tile: bool,
    has_production_tile: bool,
    has_processed_path: bool,
) -> str:
    if has_production_tile:
        return TILE_MODE_PRODUCTION_RENDERED_CACHE
    if bool(frame.production_rendering) or frame.render_status in (
        RENDER_STATUS_PRODUCTION_RENDERED,
        "production_pending",
        "production_failed",
    ):
        return TILE_MODE_PRODUCTION_GATED
    if has_decode_artifact or has_decoded_tile:
        return TILE_MODE_DECODED_PROTOTYPE
    if frame.processed_status == PROCESSED_STATUS_PLACEHOLDER_FOR_REAL_RAW:
        return TILE_MODE_PLACEHOLDER_FOR_REAL_RAW
    if is_placeholder_tile_status(frame.processed_status) or frame.render_status == RENDER_STATUS_PLACEHOLDER:
        return TILE_MODE_PLACEHOLDER
    if has_processed_path:
        return TILE_MODE_PLACEHOLDER
    return TILE_MODE_UNKNOWN


def inspect_frame_visual_artifacts(storage: LocalStorage, frame: RadarFile) -> dict[str, Any]:
    """Inspect one catalog frame's existing tile/render artifacts (read-only)."""
    artifact = find_decode_artifact_for_frame(storage, frame)
    decode_output_dir = artifact.output_dir if artifact else None
    decoded_tile_path = _decoded_tile_cache_path(storage, frame.timestamp)
    production_tile_path = build_production_tile_repo_path(
        storage, frame.product_id, frame.timestamp, 0, 0, 0
    )

    has_processed_path = _path_exists(storage, frame.processed_path)
    has_decode_artifact = artifact is not None
    has_decoded_tile = _path_exists(storage, decoded_tile_path)
    has_production_tile = _path_exists(storage, production_tile_path)
    has_render_artifact = _path_exists(storage, frame.render_artifact_path)

    render_info = classify_frame_render_status(storage, frame)
    tile_mode = classify_visual_tile_mode(
        frame=frame,
        has_decode_artifact=has_decode_artifact,
        has_decoded_tile=has_decoded_tile,
        has_production_tile=has_production_tile,
        has_processed_path=has_processed_path,
    )

    paths_found: list[str] = []
    for path in (
        frame.processed_path,
        decode_output_dir,
        decoded_tile_path if has_decoded_tile else None,
        production_tile_path if has_production_tile else None,
        frame.render_artifact_path if has_render_artifact else None,
        render_info.render_metadata_path,
    ):
        if path and path not in paths_found:
            paths_found.append(path)

    missing: list[str] = []
    if frame.processed_path and not has_processed_path:
        missing.append(frame.processed_path)
    if has_decode_artifact and not has_decoded_tile:
        missing.append(decoded_tile_path)
    if bool(frame.production_rendering) and not has_production_tile:
        missing.append(production_tile_path)
    if frame.render_artifact_path and not has_render_artifact:
        missing.append(frame.render_artifact_path)

    return {
        "radar_file_id": frame.id,
        "layer": frame.product_id,
        "timestamp": frame.timestamp,
        "tile_mode": tile_mode,
        "render_status": render_info.render_status,
        "raw_kind": frame.raw_kind,
        "production_rendering": bool(frame.production_rendering),
        "processed_status": frame.processed_status,
        "artifact_paths": {
            "processed_path": frame.processed_path,
            "decode_output_dir": decode_output_dir,
            "decoded_tile_cache_path": decoded_tile_path,
            "production_tile_cache_path": production_tile_path,
            "render_artifact_path": frame.render_artifact_path,
            "render_metadata_path": render_info.render_metadata_path,
        },
        "artifact_paths_found": paths_found,
        "missing_artifacts": missing,
    }


def build_visual_review_report(session: Session, storage: LocalStorage) -> dict[str, Any]:
    """Build visual review manifest from existing catalog and tile artifacts."""
    frames = (
        session.query(RadarFile)
        .order_by(RadarFile.timestamp.desc())
        .all()
    )
    artifacts = [inspect_frame_visual_artifacts(storage, frame) for frame in frames]
    layers = sorted({item["layer"] for item in artifacts if item.get("layer")})
    timestamps = [item["timestamp"] for item in artifacts if item.get("timestamp")]
    tile_modes = sorted({item["tile_mode"] for item in artifacts if item.get("tile_mode")})
    missing_artifact_count = sum(len(item.get("missing_artifacts") or []) for item in artifacts)
    artifact_count = sum(len(item.get("artifact_paths_found") or []) for item in artifacts)

    json_path = _latest_json_repo_path(storage)
    markdown_path = _latest_md_repo_path(storage)

    return {
        "created_at": _utc_now(),
        "layers_inspected": layers,
        "timestamps_inspected": timestamps,
        "frame_count": len(artifacts),
        "artifact_count": artifact_count,
        "missing_artifact_count": missing_artifact_count,
        "tile_modes_found": tile_modes,
        "artifacts": artifacts,
        "json_path": json_path,
        "markdown_path": markdown_path,
        "suggested_next_command": SUGGESTED_VISUAL_REVIEW_COMMAND,
        "runbook_path": RUNBOOK_PATH,
        "runbook_section": RUNBOOK_SECTION,
        "runbook_anchor": RUNBOOK_ANCHOR,
        "production_rendering_enabled": settings.enable_production_radar_tiles,
        "verified_mrms": False,
        "local_visual_review_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def _build_visual_review_markdown(report: dict[str, Any]) -> str:
    created_at = report.get("created_at") or _utc_now()
    lines = [
        "# MRMS Visual Review (Local Visual Evidence Only)",
        "",
        f"Generated at: {created_at}",
        "",
        "> **WARNING:** This visual review is local operator evidence only.",
        "> It does **NOT** verify MRMS, clear validation alerts, enable production rendering,",
        "> or send external notifications (email, SMS, Slack, webhooks, push).",
        "> Copy suggested commands manually — this report does not execute commands.",
        "",
        "## Inspected scope",
        "",
        f"- Layers inspected: {', '.join(report.get('layers_inspected') or []) or '—'}",
        f"- Timestamps inspected: {len(report.get('timestamps_inspected') or [])}",
        f"- Frames inspected: {int(report.get('frame_count', 0))}",
        f"- Artifact paths found: {int(report.get('artifact_count', 0))}",
        f"- Missing artifact warnings: {int(report.get('missing_artifact_count', 0))}",
        f"- Tile modes found: {', '.join(report.get('tile_modes_found') or []) or '—'}",
        f"- Production rendering enabled: {'yes' if report.get('production_rendering_enabled') else 'no'}",
        "",
        "## Tile mode explanation",
        "",
    ]
    for mode in report.get("tile_modes_found") or []:
        explanation = TILE_MODE_EXPLANATIONS.get(str(mode), TILE_MODE_EXPLANATIONS[TILE_MODE_UNKNOWN])
        lines.append(f"- `{mode}` — {explanation}")
    if not report.get("tile_modes_found"):
        lines.append("- No tile modes classified — catalog may be empty.")

    lines.extend(["", "## Artifact table", ""])
    artifacts = report.get("artifacts") or []
    if not artifacts:
        lines.append("No catalog frames found — run seed/demo or discovery locally first.")
    else:
        lines.append(
            "| Timestamp | Layer | Tile mode | Render status | Raw kind | Paths found | Missing |"
        )
        lines.append("|---|---|---|---|---|---|---|")
        for item in artifacts:
            paths_found = item.get("artifact_paths_found") or []
            missing = item.get("missing_artifacts") or []
            paths_cell = "; ".join(paths_found[:3])
            if len(paths_found) > 3:
                paths_cell += f" (+{len(paths_found) - 3} more)"
            missing_cell = "; ".join(missing[:2]) if missing else "—"
            lines.append(
                f"| {item.get('timestamp')} | {item.get('layer')} | {item.get('tile_mode')} | "
                f"{item.get('render_status')} | {item.get('raw_kind') or '—'} | "
                f"{paths_cell or '—'} | {missing_cell} |"
            )

    if int(report.get("missing_artifact_count", 0)) > 0:
        lines.extend(
            [
                "",
                "## Missing artifact warnings",
                "",
                "Some expected paths are absent on disk. This is informational only — "
                "visual review does not download, decode, or render new artifacts.",
            ]
        )
        for item in artifacts:
            missing = item.get("missing_artifacts") or []
            if not missing:
                continue
            lines.append(f"- `{item.get('timestamp')}`: {', '.join(missing)}")

    lines.extend(
        [
            "",
            "## Suggested next local command",
            "",
            f"```bash\n{report.get('suggested_next_command') or SUGGESTED_VISUAL_REVIEW_COMMAND}\n```",
            "",
            "## Runbook reference",
            "",
            f"- `{report.get('runbook_path') or RUNBOOK_PATH}` — "
            f"{report.get('runbook_section') or RUNBOOK_SECTION}",
        ]
    )
    return "\n".join(lines) + "\n"


def _history_entry_from_report(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "created_at": report.get("created_at"),
        "layers_inspected": report.get("layers_inspected") or [],
        "timestamp_count": len(report.get("timestamps_inspected") or []),
        "frame_count": int(report.get("frame_count", 0)),
        "artifact_count": int(report.get("artifact_count", 0)),
        "missing_artifact_count": int(report.get("missing_artifact_count", 0)),
        "tile_modes_found": report.get("tile_modes_found") or [],
        "json_path": report.get("json_path"),
        "markdown_path": report.get("markdown_path"),
        "verified_mrms": False,
        "local_visual_review_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def _load_history(storage: LocalStorage) -> list[dict[str, Any]]:
    abs_path = storage.absolute_path(_history_repo_path(storage))
    if not abs_path.is_file():
        return []
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def load_visual_review_history(storage: LocalStorage, *, limit: int = MAX_VISUAL_REVIEW_HISTORY) -> list[dict[str, Any]]:
    bounded = max(1, min(limit, MAX_VISUAL_REVIEW_HISTORY))
    return _load_history(storage)[:bounded]


def load_latest_visual_review(storage: LocalStorage) -> Optional[dict[str, Any]]:
    repo_path = _latest_json_repo_path(storage)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _previous_json_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(VISUAL_REVIEW_PREVIOUS_JSON)


def snapshot_previous_visual_review(storage: LocalStorage) -> None:
    """Copy current latest visual review to previous snapshot before overwrite."""
    latest = load_latest_visual_review(storage)
    if latest is None:
        return
    repo_path = _previous_json_repo_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(latest, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def load_previous_visual_review(storage: LocalStorage) -> Optional[dict[str, Any]]:
    repo_path = _previous_json_repo_path(storage)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def save_visual_review_report(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
    snapshot_previous_visual_review(storage)
    json_repo = _latest_json_repo_path(storage)
    md_repo = _latest_md_repo_path(storage)
    storage.ensure_directories(json_repo.rsplit("/", 1)[0])
    storage.absolute_path(json_repo).write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    markdown = _build_visual_review_markdown(report)
    storage.absolute_path(md_repo).write_text(markdown, encoding="utf-8")

    history = _load_history(storage)
    history.insert(0, _history_entry_from_report(report))
    history_repo = _history_repo_path(storage)
    storage.absolute_path(history_repo).write_text(
        json.dumps(history[:MAX_VISUAL_REVIEW_HISTORY], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


def generate_mrms_visual_review(session: Session, storage: LocalStorage) -> dict[str, Any]:
    report = build_visual_review_report(session, storage)
    return save_visual_review_report(storage, report)


def compact_mrms_visual_review(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_visual_review(storage)
    empty = {
        "available": False,
        "created_at": None,
        "json_path": _latest_json_repo_path(storage),
        "markdown_path": _latest_md_repo_path(storage),
        "layers_inspected": [],
        "timestamp_count": 0,
        "frame_count": 0,
        "artifact_count": 0,
        "missing_artifact_count": 0,
        "tile_modes_found": [],
        "suggested_next_command": SUGGESTED_VISUAL_REVIEW_COMMAND,
        "runbook_path": RUNBOOK_PATH,
        "history_count": len(_load_history(storage)),
        "verified_mrms": False,
        "local_visual_review_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }
    if latest is None:
        return empty
    return {
        "available": True,
        "created_at": latest.get("created_at"),
        "json_path": latest.get("json_path") or _latest_json_repo_path(storage),
        "markdown_path": latest.get("markdown_path") or _latest_md_repo_path(storage),
        "layers_inspected": latest.get("layers_inspected") or [],
        "timestamp_count": len(latest.get("timestamps_inspected") or []),
        "frame_count": int(latest.get("frame_count", 0)),
        "artifact_count": int(latest.get("artifact_count", 0)),
        "missing_artifact_count": int(latest.get("missing_artifact_count", 0)),
        "tile_modes_found": latest.get("tile_modes_found") or [],
        "suggested_next_command": latest.get("suggested_next_command")
        or SUGGESTED_VISUAL_REVIEW_COMMAND,
        "runbook_path": latest.get("runbook_path") or RUNBOOK_PATH,
        "history_count": len(_load_history(storage)),
        "verified_mrms": False,
        "local_visual_review_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def compact_scheduled_visual_review(
    scheduled: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    """Compact visual review step status from the latest scheduled validation report."""
    if scheduled is None:
        return None
    return {
        "visual_review_requested": bool(scheduled.get("visual_review_requested")),
        "visual_review_generated": bool(scheduled.get("visual_review_generated")),
        "visual_review_path": scheduled.get("visual_review_path"),
        "visual_review_markdown_path": scheduled.get("visual_review_markdown_path"),
        "visual_review_history_count": scheduled.get("visual_review_history_count"),
        "visual_review_reason": scheduled.get("visual_review_reason"),
        "visual_review_elapsed_seconds": scheduled.get("visual_review_elapsed_seconds"),
        "visual_review_error": scheduled.get("visual_review_error"),
        "verified_mrms": False,
        "local_visual_review_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def build_mrms_visual_review_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_visual_review(storage)
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_visual_review_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "latest": latest,
        "compact": compact_mrms_visual_review(storage),
    }


def build_mrms_visual_review_history_payload(
    storage: LocalStorage,
    *,
    limit: int = MAX_VISUAL_REVIEW_HISTORY,
) -> dict[str, Any]:
    bounded = max(1, min(limit, MAX_VISUAL_REVIEW_HISTORY))
    entries = load_visual_review_history(storage, limit=bounded)
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_visual_review_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "count": len(entries),
        "max_entries": MAX_VISUAL_REVIEW_HISTORY,
        "entries": entries,
        "compact": compact_mrms_visual_review(storage),
    }
