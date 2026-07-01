"""Schemas for local frame catalog browser (prototype only)."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class FrameCatalogItem(BaseModel):
    timestamp: str
    cache_state: str
    cache_ready: bool = False
    decode_ready: bool = False
    decode_status: Optional[str] = None


class FrameCatalogResponse(BaseModel):
    layer_id: str = "mrms_reflectivity"
    frame_count: int = 0
    cache_ready_count: int = 0
    decode_ready_count: int = 0
    missing_count: int = 0
    cold_count: int = 0
    failed_count: int = 0
    window_source: str = "catalog_real_local"
    frames: list[FrameCatalogItem] = Field(default_factory=list)
    playback_ready: bool = False
    verified_mrms: bool = False
    local_dev_only: bool = True
    prototype: bool = True
    production_tile_serving: bool = False
