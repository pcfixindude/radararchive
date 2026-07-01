"""Schemas for per-frame quality drill-down (prototype only)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class FrameQualityPathHints(BaseModel):
    cache_dir: Optional[str] = None
    manifest_path: Optional[str] = None
    manifest_present: bool = False
    decode_output_dir: Optional[str] = None
    raw_path: Optional[str] = None
    preview_paths: list[str] = Field(default_factory=list)
    preview_available: bool = False
    preview_path_count: int = 0
    tile_root: Optional[str] = None


class FrameQualityCandidateHints(BaseModel):
    selection: Optional[str] = None
    raw_kind: Optional[str] = None
    is_real_grib2: bool = False
    is_placeholder: bool = False


class FrameQualityCheckItem(BaseModel):
    name: str
    status: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class FrameQualityAssessment(BaseModel):
    status: str
    checks: list[FrameQualityCheckItem] = Field(default_factory=list)
    measured: dict[str, Any] = Field(default_factory=dict)
    diagnostic_only: bool = True
    verified_mrms: bool = False
    local_dev_only: bool = True
    prototype: bool = True


class FrameQualityDetail(BaseModel):
    timestamp: str
    valid: bool = True
    layer_id: str = "mrms_reflectivity"
    cache_state: str = "missing_raw"
    cache_ready: bool = False
    decode_ready: bool = False
    decode_status: Optional[str] = None
    frame_status: Optional[str] = None
    readiness_summary: str = "invalid"
    sync_message: Optional[str] = None
    path_hints: FrameQualityPathHints = Field(default_factory=FrameQualityPathHints)
    candidate: FrameQualityCandidateHints = Field(default_factory=FrameQualityCandidateHints)
    frame_quality: FrameQualityAssessment = Field(default_factory=FrameQualityAssessment)
    suggested_commands: list[str] = Field(default_factory=list)
    assessed_at: Optional[str] = None
    verified_mrms: bool = False
    local_dev_only: bool = True
    prototype: bool = True
    production_tile_serving: bool = False
    status_only: bool = True
    does_not_run_ingest: bool = True
    does_not_run_decode: bool = True


class FrameQualityReportResponse(BaseModel):
    layer_id: str = "mrms_reflectivity"
    frame_count: int = 0
    requested_count: int = 0
    truncated: bool = False
    ready_count: int = 0
    partial_count: int = 0
    cold_count: int = 0
    missing_count: int = 0
    failed_count: int = 0
    stub_count: int = 0
    invalid_count: int = 0
    frames: list[FrameQualityDetail] = Field(default_factory=list)
    assessed_at: Optional[str] = None
    verified_mrms: bool = False
    local_dev_only: bool = True
    prototype: bool = True
    production_tile_serving: bool = False
    status_only: bool = True
    does_not_run_ingest: bool = True
    does_not_run_decode: bool = True
