"""Per-frame quality/readiness drill-down for replay UI (status only, no decode work)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.catalog import MRMS_REFLECTIVITY_LAYER_ID
from backend.app.services.decoder_setup import SUGGESTED_DECODE_RETRY_COMMAND
from backend.app.services.frame_catalog import resolve_frame_decode_state
from backend.app.services.frame_quality import QUALITY_OK, assess_frame_quality
from backend.app.services.georef_overlay import resolve_georef_overlay
from backend.app.services.grib2_decoder import build_decode_output_dir
from backend.app.services.mrms_ingest_window import SUGGESTED_GUIDED_COMMAND
from backend.app.services.overlay_sync import normalize_timestamp_iso
from backend.app.services.playback_cache_status import (
    CACHE_STATE_COLD,
    CACHE_STATE_FAILED,
    CACHE_STATE_MISSING_RAW,
    CACHE_STATE_READY,
    CACHE_STATE_STUB,
    SUGGESTED_WARM_COMMAND,
    resolve_frame_cache_state,
)
from backend.app.services.selected_frame_decode import (
    DOWNLOAD_MRMS_COMMAND,
    find_local_mrms_candidate,
    frame_cache_dir,
    frame_manifest_path,
    load_frame_cache,
)
from backend.app.services.storage import LocalStorage

MAX_FRAME_QUALITY_REPORT = 50

READINESS_READY = "ready"
READINESS_PARTIAL = "partial"
READINESS_COLD = "cold"
READINESS_MISSING = "missing"
READINESS_FAILED = "failed"
READINESS_STUB = "stub"
READINESS_INVALID = "invalid"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_dev_only": True,
        "prototype": True,
        "production_tile_serving": settings.enable_production_radar_tiles,
        "status_only": True,
        "does_not_run_ingest": True,
        "does_not_run_decode": True,
    }


def _dedupe_commands(commands: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for command in commands:
        if command and command not in seen:
            seen.add(command)
            result.append(command)
    return result


def _resolve_readiness_summary(
    *,
    cache_state: str,
    decode_ready: bool,
    quality_status: str,
) -> str:
    if cache_state == CACHE_STATE_MISSING_RAW:
        return READINESS_MISSING
    if cache_state == CACHE_STATE_STUB:
        return READINESS_STUB
    if cache_state == CACHE_STATE_FAILED:
        return READINESS_FAILED
    if cache_state == CACHE_STATE_COLD:
        return READINESS_COLD
    if decode_ready and quality_status == QUALITY_OK:
        return READINESS_READY
    if decode_ready or cache_state == CACHE_STATE_READY:
        return READINESS_PARTIAL
    return READINESS_PARTIAL


def _suggest_commands(
    *,
    cache_state: str,
    decode_ready: bool,
    cached_manifest: Optional[dict[str, Any]],
) -> list[str]:
    commands: list[str] = []
    if cached_manifest:
        commands.extend(cached_manifest.get("action_commands") or [])

    if cache_state == CACHE_STATE_MISSING_RAW:
        commands.extend([SUGGESTED_GUIDED_COMMAND, DOWNLOAD_MRMS_COMMAND])
    elif cache_state == CACHE_STATE_STUB:
        commands.extend([DOWNLOAD_MRMS_COMMAND, SUGGESTED_DECODE_RETRY_COMMAND])
    elif cache_state == CACHE_STATE_COLD:
        commands.extend([SUGGESTED_WARM_COMMAND, SUGGESTED_DECODE_RETRY_COMMAND])
    elif cache_state == CACHE_STATE_FAILED:
        commands.append(SUGGESTED_DECODE_RETRY_COMMAND)
    elif cache_state == CACHE_STATE_READY and not decode_ready:
        commands.append(SUGGESTED_DECODE_RETRY_COMMAND)

    if not commands:
        commands.append(SUGGESTED_DECODE_RETRY_COMMAND)
    return _dedupe_commands(commands)


def build_frame_quality_detail(
    session: Session,
    storage: LocalStorage,
    timestamp: str,
    *,
    layer_id: str = MRMS_REFLECTIVITY_LAYER_ID,
) -> dict[str, Any]:
    """Summarize one frame's cache/decode/quality state without running ingest or decode."""
    normalized = normalize_timestamp_iso(timestamp)
    if not normalized:
        return {
            "timestamp": timestamp,
            "valid": False,
            "readiness_summary": READINESS_INVALID,
            "sync_message": "Invalid timestamp format.",
            "suggested_commands": [SUGGESTED_DECODE_RETRY_COMMAND],
            **_safety_fields(),
        }

    cache_state = resolve_frame_cache_state(session, storage, normalized)
    decode_ready, decode_status = resolve_frame_decode_state(storage, normalized)
    cached = load_frame_cache(storage, normalized)
    candidate = find_local_mrms_candidate(session, storage, normalized, layer_id=layer_id)

    cache_dir = frame_cache_dir(storage, normalized)
    manifest_path = frame_manifest_path(storage, normalized)
    manifest_present = storage.path_exists(manifest_path)

    decode_output_dir: Optional[str] = None
    if cached and cached.get("decode_output_dir"):
        decode_output_dir = cached["decode_output_dir"]
    elif candidate and candidate.get("raw_path"):
        decode_output_dir = build_decode_output_dir(storage, candidate["raw_path"])

    preview_paths: list[str] = []
    if cached:
        preview_paths = [
            path for path in (cached.get("preview_paths") or []) if storage.path_exists(path)
        ]

    georef: Optional[dict[str, Any]] = None
    if decode_output_dir and storage.path_exists(decode_output_dir):
        try:
            georef = resolve_georef_overlay(storage, decode_output_dir)
        except (OSError, ValueError, TypeError):
            georef = None

    tile_preview = cached.get("tile_preview") if cached else None
    frame_quality = assess_frame_quality(
        storage,
        decode_output_dir=decode_output_dir,
        preview_path=preview_paths[0] if preview_paths else None,
        georef=georef,
        tile_preview=tile_preview,
        overlay_visible=decode_ready,
        frame_report=cached,
    )

    readiness_summary = _resolve_readiness_summary(
        cache_state=cache_state,
        decode_ready=decode_ready,
        quality_status=frame_quality.get("status") or "unavailable",
    )
    suggested_commands = _suggest_commands(
        cache_state=cache_state,
        decode_ready=decode_ready,
        cached_manifest=cached,
    )

    raw_path = None
    if cached and cached.get("candidate_raw_path"):
        raw_path = cached["candidate_raw_path"]
    elif candidate and candidate.get("raw_path"):
        raw_path = candidate["raw_path"]

    sync_message = cached.get("sync_message") if cached else None
    if not sync_message:
        if readiness_summary == READINESS_READY:
            sync_message = "Frame cached and decoded for local overlay playback."
        elif readiness_summary == READINESS_COLD:
            sync_message = "Local raw GRIB2 present but frame cache not warmed — warm or decode retry."
        elif readiness_summary == READINESS_MISSING:
            sync_message = "No local raw MRMS file for this timestamp."
        elif readiness_summary == READINESS_FAILED:
            sync_message = "Previous decode or warm attempt failed — inspect logs and retry."
        elif readiness_summary == READINESS_STUB:
            sync_message = "Catalog row has stub/placeholder raw only."

    return {
        "timestamp": normalized,
        "valid": True,
        "layer_id": layer_id,
        "cache_state": cache_state,
        "cache_ready": cache_state == CACHE_STATE_READY,
        "decode_ready": decode_ready,
        "decode_status": decode_status,
        "frame_status": (cached or {}).get("frame_status") or decode_status,
        "readiness_summary": readiness_summary,
        "sync_message": sync_message,
        "path_hints": {
            "cache_dir": cache_dir,
            "manifest_path": manifest_path if manifest_present else None,
            "manifest_present": manifest_present,
            "decode_output_dir": decode_output_dir,
            "raw_path": raw_path,
            "preview_paths": preview_paths,
            "preview_available": bool(preview_paths),
            "preview_path_count": len(preview_paths),
            "tile_root": cached.get("tile_root") if cached else None,
        },
        "candidate": {
            "selection": candidate.get("selection") if candidate else None,
            "raw_kind": candidate.get("raw_kind") if candidate else None,
            "is_real_grib2": candidate.get("is_real_grib2") if candidate else False,
            "is_placeholder": candidate.get("is_placeholder") if candidate else False,
        },
        "frame_quality": frame_quality,
        "suggested_commands": suggested_commands,
        "assessed_at": _utc_now(),
        **_safety_fields(),
    }


def build_frame_quality_report(
    session: Session,
    storage: LocalStorage,
    *,
    timestamps: list[str],
    layer_id: str = MRMS_REFLECTIVITY_LAYER_ID,
    limit: int = MAX_FRAME_QUALITY_REPORT,
) -> dict[str, Any]:
    """Build quality drill-down for one or more timestamps — status only."""
    bounded_limit = max(1, min(limit, MAX_FRAME_QUALITY_REPORT))
    normalized_times = sorted(
        {normalize_timestamp_iso(ts) for ts in timestamps if normalize_timestamp_iso(ts)}
    )
    truncated = len(normalized_times) > bounded_limit
    if truncated:
        normalized_times = normalized_times[:bounded_limit]

    frames = [
        build_frame_quality_detail(session, storage, ts, layer_id=layer_id)
        for ts in normalized_times
    ]

    summary_counts = {
        READINESS_READY: 0,
        READINESS_PARTIAL: 0,
        READINESS_COLD: 0,
        READINESS_MISSING: 0,
        READINESS_FAILED: 0,
        READINESS_STUB: 0,
        READINESS_INVALID: 0,
    }
    for frame in frames:
        key = frame.get("readiness_summary") or READINESS_INVALID
        summary_counts[key] = summary_counts.get(key, 0) + 1

    return {
        "layer_id": layer_id,
        "frame_count": len(frames),
        "requested_count": len(timestamps),
        "truncated": truncated,
        "ready_count": summary_counts[READINESS_READY],
        "partial_count": summary_counts[READINESS_PARTIAL],
        "cold_count": summary_counts[READINESS_COLD],
        "missing_count": summary_counts[READINESS_MISSING],
        "failed_count": summary_counts[READINESS_FAILED],
        "stub_count": summary_counts[READINESS_STUB],
        "invalid_count": summary_counts[READINESS_INVALID],
        "frames": frames,
        "assessed_at": _utc_now(),
        **_safety_fields(),
    }
