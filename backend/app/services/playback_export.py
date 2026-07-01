"""Build bounded playback clip manifests from replay range (prototype only)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.catalog import MRMS_REFLECTIVITY_LAYER_ID
from backend.app.services.frame_cache_warmer import list_real_local_mrms_timestamps
from backend.app.services.frame_catalog import resolve_frame_decode_state
from backend.app.services.overlay_sync import normalize_timestamp_iso
from backend.app.services.playback_cache_status import (
    CACHE_STATE_READY,
    build_playback_cache_status,
    resolve_frame_cache_state,
)
from backend.app.services.selected_frame_decode import load_frame_cache
from backend.app.services.storage import LocalStorage

EXPORT_KIND = "playback_clip_manifest"
MAX_CLIP_FRAMES = 200


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_dev_only": True,
        "prototype": True,
        "production_tile_serving": settings.enable_production_radar_tiles,
    }


def _timestamp_token(timestamp: str) -> str:
    return normalize_timestamp_iso(timestamp).replace(":", "").replace("-", "")


def build_clip_id(range_start: str, range_end: str) -> str:
    return f"clip_{_timestamp_token(range_start)}_{_timestamp_token(range_end)}"


def resolve_clip_timestamps(
    range_start: str,
    range_end: str,
    *,
    timestamps: Optional[list[str]] = None,
    session: Optional[Session] = None,
    storage: Optional[LocalStorage] = None,
) -> tuple[list[str], bool]:
    """Return ordered playback timestamps between start and end (inclusive)."""
    start = normalize_timestamp_iso(range_start)
    end = normalize_timestamp_iso(range_end)
    if not start or not end:
        return [], False

    order_adjusted = False
    if timestamps:
        normalized_times = [normalize_timestamp_iso(ts) for ts in timestamps]
        normalized_times = [ts for ts in normalized_times if ts]
        start_index = normalized_times.index(start) if start in normalized_times else -1
        end_index = normalized_times.index(end) if end in normalized_times else -1
        if start_index == -1 or end_index == -1:
            return [], False
        if start_index > end_index:
            start_index, end_index = end_index, start_index
            order_adjusted = True
        return normalized_times[start_index : end_index + 1], order_adjusted

    if session is None or storage is None:
        return [], False

    catalog_times = list_real_local_mrms_timestamps(session, storage)
    if not catalog_times:
        return [], False

    in_range = [ts for ts in catalog_times if start <= ts <= end]
    if not in_range:
        in_range = [ts for ts in catalog_times if end <= ts <= start]
        if in_range:
            order_adjusted = True
    return in_range, order_adjusted


def _existing_preview_paths(storage: LocalStorage, timestamp: str) -> list[str]:
    cached = load_frame_cache(storage, timestamp)
    if not cached:
        return []
    paths = cached.get("preview_paths") or []
    return [path for path in paths if storage.path_exists(path)]


def build_playback_export(
    session: Session,
    storage: LocalStorage,
    *,
    range_start: str,
    range_end: str,
    timestamps: Optional[list[str]] = None,
    loop_suggested: bool = False,
    layer_id: str = MRMS_REFLECTIVITY_LAYER_ID,
) -> dict[str, Any]:
    """Summarize replay range as a clip manifest — status only, no decode work."""
    start = normalize_timestamp_iso(range_start)
    end = normalize_timestamp_iso(range_end)
    if not start or not end:
        return {
            "clip_id": "clip_incomplete",
            "export_kind": EXPORT_KIND,
            "layer_id": layer_id,
            "range_start": range_start,
            "range_end": range_end,
            "range_order_adjusted": False,
            "loop_suggested": loop_suggested,
            "frame_count": 0,
            "cache_ready_count": 0,
            "decode_ready_count": 0,
            "missing_cache_count": 0,
            "cold_count": 0,
            "failed_count": 0,
            "frames": [],
            "exported_at": _utc_now(),
            "status": "incomplete_range",
            **_safety_fields(),
        }

    clip_times, order_adjusted = resolve_clip_timestamps(
        start,
        end,
        timestamps=timestamps,
        session=session,
        storage=storage,
    )
    if len(clip_times) > MAX_CLIP_FRAMES:
        clip_times = clip_times[:MAX_CLIP_FRAMES]

    cache_status = build_playback_cache_status(session, storage, clip_times) if clip_times else None
    cache_by_ts = {
        frame["timestamp"]: frame["cache_state"]
        for frame in (cache_status or {}).get("frames") or []
    }

    frames: list[dict[str, Any]] = []
    cache_ready_count = 0
    decode_ready_count = 0
    missing_cache_count = 0
    cold_count = 0
    failed_count = 0

    for index, ts in enumerate(clip_times):
        cache_state = cache_by_ts.get(ts) or resolve_frame_cache_state(session, storage, ts)
        decode_ready, decode_status = resolve_frame_decode_state(storage, ts)
        preview_paths = _existing_preview_paths(storage, ts)

        if cache_state == CACHE_STATE_READY:
            cache_ready_count += 1
        elif cache_state in {"missing_raw", "missing"}:
            missing_cache_count += 1
        elif cache_state.startswith("cold"):
            cold_count += 1
        elif cache_state.startswith("failed"):
            failed_count += 1

        if decode_ready:
            decode_ready_count += 1

        frames.append(
            {
                "timestamp": ts,
                "index": index,
                "cache_state": cache_state,
                "cache_ready": cache_state == CACHE_STATE_READY,
                "decode_ready": decode_ready,
                "decode_status": decode_status,
                "preview_paths": preview_paths,
                "preview_path_count": len(preview_paths),
            }
        )

    resolved_start = clip_times[0] if clip_times else start
    resolved_end = clip_times[-1] if clip_times else end

    return {
        "clip_id": build_clip_id(resolved_start, resolved_end),
        "export_kind": EXPORT_KIND,
        "layer_id": layer_id,
        "range_start": resolved_start,
        "range_end": resolved_end,
        "range_order_adjusted": order_adjusted,
        "loop_suggested": loop_suggested,
        "frame_count": len(frames),
        "cache_ready_count": cache_ready_count,
        "decode_ready_count": decode_ready_count,
        "missing_cache_count": missing_cache_count,
        "cold_count": cold_count,
        "failed_count": failed_count,
        "frames": frames,
        "exported_at": _utc_now(),
        "status": "ready" if clip_times else "empty_range",
        **_safety_fields(),
    }
