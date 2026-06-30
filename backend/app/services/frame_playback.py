"""Adjacent-frame prefetch for local decoded overlay playback (prototype only)."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.overlay_sync import normalize_timestamp_iso
from backend.app.services.selected_frame_decode import (
    FRAME_STATUS_MATCHED,
    load_frame_cache,
    resolve_selected_frame,
)
from backend.app.services.storage import LocalStorage

MAX_PREFETCH_FRAMES = 3


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_dev_only": True,
        "prototype": True,
        "production_tile_serving": settings.enable_production_radar_tiles,
    }


def _compact_prefetch_item(report: dict[str, Any]) -> dict[str, Any]:
    frame_status = report.get("frame_status")
    return {
        "timestamp": report.get("selected_timestamp"),
        "frame_status": frame_status,
        "cached": frame_status == FRAME_STATUS_MATCHED,
        "overlay_visible": frame_status == FRAME_STATUS_MATCHED,
        "sync_status": "matched" if frame_status == FRAME_STATUS_MATCHED else frame_status,
        "sync_message": report.get("sync_message"),
    }


def prefetch_frames(
    session: Session,
    storage: LocalStorage,
    timestamps: list[str],
    *,
    max_count: int = MAX_PREFETCH_FRAMES,
) -> dict[str, Any]:
    """Resolve/decode up to max_count frames for playback prefetch (adjacent frames only)."""
    frames: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw_ts in timestamps:
        if len(frames) >= max_count:
            break
        normalized = normalize_timestamp_iso(raw_ts)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)

        cached = load_frame_cache(storage, normalized)
        if cached and cached.get("frame_status") == FRAME_STATUS_MATCHED:
            preview_paths = cached.get("preview_paths") or []
            if preview_paths and storage.path_exists(preview_paths[0]):
                frames.append(_compact_prefetch_item(cached))
                continue

        report = resolve_selected_frame(session, storage, normalized)
        frames.append(_compact_prefetch_item(report))

    matched = sum(1 for row in frames if row.get("frame_status") == FRAME_STATUS_MATCHED)
    return {
        "requested": len(seen),
        "prefetched": len(frames),
        "matched": matched,
        "frames": frames,
        **_safety_fields(),
    }


def is_frame_cached(storage: LocalStorage, timestamp: str) -> bool:
    normalized = normalize_timestamp_iso(timestamp)
    if not normalized:
        return False
    cached = load_frame_cache(storage, normalized)
    if not cached or cached.get("frame_status") != FRAME_STATUS_MATCHED:
        return False
    preview_paths = cached.get("preview_paths") or []
    return bool(preview_paths and storage.path_exists(preview_paths[0]))
