"""Playback window cache status for local dev overlay (prototype only)."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.frame_cache_warmer import load_cache_warm_report
from backend.app.services.frame_playback import is_frame_cached
from backend.app.services.overlay_sync import normalize_timestamp_iso
from backend.app.services.selected_frame_decode import (
    FRAME_STATUS_DECODE_FAILED,
    FRAME_STATUS_DECODER_MISSING,
    FRAME_STATUS_NO_LOCAL_CANDIDATE,
    FRAME_STATUS_STUB_INPUT,
    find_local_mrms_candidate,
    load_frame_cache,
)
from backend.app.services.storage import LocalStorage

CACHE_STATE_READY = "ready"
CACHE_STATE_MISSING_RAW = "missing_raw"
CACHE_STATE_COLD = "cold_decodable"
CACHE_STATE_FAILED = "failed"
CACHE_STATE_STUB = "stub"

SUGGESTED_WARM_COMMAND = "make mrms-warm-frame-cache"


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_dev_only": True,
        "prototype": True,
        "production_tile_serving": settings.enable_production_radar_tiles,
    }


def _failed_timestamps_from_warm_report(storage: LocalStorage) -> set[str]:
    report = load_cache_warm_report(storage)
    if not report:
        return set()
    failed: set[str] = set()
    for item in report.get("failed_frames") or []:
        ts = normalize_timestamp_iso(item.get("timestamp"))
        if ts:
            failed.add(ts)
    return failed


def resolve_frame_cache_state(
    session: Session,
    storage: LocalStorage,
    timestamp: str,
    *,
    failed_timestamps: Optional[set[str]] = None,
) -> str:
    """Classify one timestamp for playback cache UI."""
    normalized = normalize_timestamp_iso(timestamp)
    if not normalized:
        return CACHE_STATE_MISSING_RAW

    if is_frame_cached(storage, normalized):
        return CACHE_STATE_READY

    cached_manifest = load_frame_cache(storage, normalized)
    if cached_manifest:
        status = cached_manifest.get("frame_status")
        if status == FRAME_STATUS_DECODE_FAILED:
            return CACHE_STATE_FAILED
        if status == FRAME_STATUS_DECODER_MISSING:
            return CACHE_STATE_FAILED
        if status == FRAME_STATUS_STUB_INPUT:
            return CACHE_STATE_STUB
        if status == FRAME_STATUS_NO_LOCAL_CANDIDATE:
            return CACHE_STATE_MISSING_RAW

    if failed_timestamps and normalized in failed_timestamps:
        return CACHE_STATE_FAILED

    candidate = find_local_mrms_candidate(session, storage, normalized)
    if candidate is None or not candidate.get("raw_path"):
        return CACHE_STATE_MISSING_RAW
    if candidate.get("is_placeholder") or not candidate.get("is_real_grib2"):
        return CACHE_STATE_STUB
    return CACHE_STATE_COLD


def build_playback_cache_status(
    session: Session,
    storage: LocalStorage,
    timestamps: list[str],
) -> dict[str, Any]:
    """Summarize cache readiness for a playback timestamp window."""
    failed_ts = _failed_timestamps_from_warm_report(storage)
    warm_report = load_cache_warm_report(storage)

    frames: list[dict[str, Any]] = []
    counts = {
        CACHE_STATE_READY: 0,
        CACHE_STATE_MISSING_RAW: 0,
        CACHE_STATE_COLD: 0,
        CACHE_STATE_FAILED: 0,
        CACHE_STATE_STUB: 0,
    }

    seen: set[str] = set()
    for raw_ts in timestamps:
        normalized = normalize_timestamp_iso(raw_ts)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        state = resolve_frame_cache_state(
            session,
            storage,
            normalized,
            failed_timestamps=failed_ts,
        )
        counts[state] = counts.get(state, 0) + 1
        frames.append({"timestamp": normalized, "cache_state": state})

    warmed = counts[CACHE_STATE_READY]
    cold = counts[CACHE_STATE_COLD]
    playback_ready = warmed > 0 and cold == 0 and counts[CACHE_STATE_FAILED] == 0

    next_commands: list[str] = []
    if cold > 0 or (warmed == 0 and counts[CACHE_STATE_MISSING_RAW] == 0):
        next_commands.append(SUGGESTED_WARM_COMMAND)
    if counts[CACHE_STATE_MISSING_RAW] > 0:
        next_commands.append("make mrms-bulk-local-ingest ARGS='--real --limit 8'")

    return {
        "frames": frames,
        "frame_count": len(frames),
        "warmed_count": warmed,
        "missing_count": counts[CACHE_STATE_MISSING_RAW],
        "cold_count": cold,
        "failed_count": counts[CACHE_STATE_FAILED],
        "stub_count": counts[CACHE_STATE_STUB],
        "playback_ready": playback_ready,
        "cache_warm_available": warm_report is not None,
        "cache_warm_ran_at": warm_report.get("ran_at") if warm_report else None,
        "cache_warm_status": warm_report.get("warm_status") if warm_report else None,
        "next_commands": next_commands,
        **_safety_fields(),
    }
