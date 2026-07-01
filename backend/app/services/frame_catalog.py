"""Local frame catalog with cache/decode readiness for replay browser (prototype only)."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.catalog import MRMS_REFLECTIVITY_LAYER_ID
from backend.app.services.frame_cache_warmer import DEFAULT_LIMIT, MAX_LIMIT, select_cache_window
from backend.app.services.overlay_sync import normalize_timestamp_iso
from backend.app.services.playback_cache_status import (
    CACHE_STATE_READY,
    build_playback_cache_status,
    resolve_frame_cache_state,
)
from backend.app.services.selected_frame_decode import (
    FRAME_STATUS_MATCHED,
    load_frame_cache,
)
from backend.app.services.storage import LocalStorage

DECODE_READY_STATUSES = {FRAME_STATUS_MATCHED}


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_dev_only": True,
        "prototype": True,
        "production_tile_serving": settings.enable_production_radar_tiles,
    }


def resolve_frame_decode_state(storage: LocalStorage, timestamp: str) -> tuple[bool, Optional[str]]:
    """Return decode-ready flag and frame_status label for one timestamp."""
    normalized = normalize_timestamp_iso(timestamp)
    if not normalized:
        return False, None

    cached = load_frame_cache(storage, normalized)
    if cached:
        status = cached.get("frame_status")
        if status in DECODE_READY_STATUSES:
            preview_paths = cached.get("preview_paths") or []
            if preview_paths and storage.path_exists(preview_paths[0]):
                return True, status
        return False, status

    return False, None


def build_frame_catalog(
    session: Session,
    storage: LocalStorage,
    *,
    layer_id: str = MRMS_REFLECTIVITY_LAYER_ID,
    timestamps: Optional[list[str]] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Summarize local frames with cache/decode flags — status only, no decode work."""
    bounded_limit = max(1, min(limit, MAX_LIMIT))
    window_source = "request_timestamps"

    if timestamps:
        ts_list = sorted(
            {normalize_timestamp_iso(ts) for ts in timestamps if normalize_timestamp_iso(ts)}
        )
        if len(ts_list) > bounded_limit:
            ts_list = ts_list[-bounded_limit:]
    else:
        ts_list, window_source = select_cache_window(
            session,
            storage,
            start_time=start_time,
            end_time=end_time,
            limit=bounded_limit,
        )

    cache_status = build_playback_cache_status(session, storage, ts_list) if ts_list else None
    cache_by_ts = {
        frame["timestamp"]: frame["cache_state"]
        for frame in (cache_status or {}).get("frames") or []
    }

    frames: list[dict[str, Any]] = []
    decode_ready_count = 0
    cache_ready_count = 0

    for ts in reversed(ts_list):
        cache_state = cache_by_ts.get(ts) or resolve_frame_cache_state(session, storage, ts)
        decode_ready, decode_status = resolve_frame_decode_state(storage, ts)
        if cache_state == CACHE_STATE_READY:
            cache_ready_count += 1
        if decode_ready:
            decode_ready_count += 1
        frames.append(
            {
                "timestamp": ts,
                "cache_state": cache_state,
                "cache_ready": cache_state == CACHE_STATE_READY,
                "decode_ready": decode_ready,
                "decode_status": decode_status,
            }
        )

    return {
        "layer_id": layer_id,
        "frame_count": len(frames),
        "cache_ready_count": cache_ready_count,
        "decode_ready_count": decode_ready_count,
        "missing_count": (cache_status or {}).get("missing_count", 0),
        "cold_count": (cache_status or {}).get("cold_count", 0),
        "failed_count": (cache_status or {}).get("failed_count", 0),
        "window_source": window_source,
        "frames": frames,
        "playback_ready": bool(cache_status and cache_status.get("playback_ready")),
        **_safety_fields(),
    }
