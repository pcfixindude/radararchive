"""Schemas for playback clip export manifest (prototype only)."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PlaybackExportFrame(BaseModel):
    timestamp: str
    index: int = 0
    cache_state: str
    cache_ready: bool = False
    decode_ready: bool = False
    decode_status: Optional[str] = None
    preview_paths: list[str] = Field(default_factory=list)
    preview_path_count: int = 0


class PlaybackExportResponse(BaseModel):
    clip_id: str
    export_kind: str = "playback_clip_manifest"
    layer_id: str = "mrms_reflectivity"
    range_start: str
    range_end: str
    range_order_adjusted: bool = False
    loop_suggested: bool = False
    frame_count: int = 0
    cache_ready_count: int = 0
    decode_ready_count: int = 0
    missing_cache_count: int = 0
    cold_count: int = 0
    failed_count: int = 0
    frames: list[PlaybackExportFrame] = Field(default_factory=list)
    exported_at: str
    status: str = "ready"
    verified_mrms: bool = False
    local_dev_only: bool = True
    prototype: bool = True
    production_tile_serving: bool = False
