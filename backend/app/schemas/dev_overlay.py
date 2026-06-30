"""Schemas for local dev decoded map overlay (prototype only)."""

from typing import Optional

from pydantic import BaseModel, Field


class DecodedOverlayResponse(BaseModel):
    available: bool = False
    overlay_status: str = "missing"
    render_mode: Optional[str] = None
    pipeline_status: Optional[str] = None
    preview_url: Optional[str] = None
    preview_path: Optional[str] = None
    ran_at: Optional[str] = None
    preview_mtime: Optional[str] = None
    stale_hint: Optional[str] = None
    bounds: list[float] = Field(default_factory=lambda: [-125.0, 24.0, -66.0, 50.0])
    georef_mode: str = "prototype_bounds"
    geo_accurate: bool = False
    candidate_raw_path: Optional[str] = None
    decode_output_dir: Optional[str] = None
    labels: list[str] = Field(default_factory=list)
    refresh_commands: list[str] = Field(default_factory=list)
    color_scale_mode: Optional[str] = None
    tile_mode: str = "single_image"
    tile_url_template: Optional[str] = None
    tile_max_z: int = 0
    tile_count: int = 0
    tile_root: Optional[str] = None
    artifact_available: bool = False
    overlay_visible: bool = False
    candidate_timestamp: Optional[str] = None
    selected_timestamp: Optional[str] = None
    sync_status: str = "no_selection"
    sync_message: Optional[str] = None
    georef_quality: str = "prototype_bounds"
    georef_notes: list[str] = Field(default_factory=list)
    verified_mrms: bool = False
    local_dev_only: bool = True
    prototype: bool = True
    production_tile_serving: bool = False
