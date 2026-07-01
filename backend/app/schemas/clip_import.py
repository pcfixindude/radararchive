"""Schemas for playback clip manifest import (prototype only)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from backend.app.schemas.playback_export import PlaybackExportResponse


class ClipImportReadinessSummary(BaseModel):
    frame_count: int = 0
    cache_ready_count: int = 0
    decode_ready_count: int = 0
    missing_count: int = 0
    cold_count: int = 0
    failed_count: int = 0
    stub_count: int = 0
    partial_count: int = 0
    ready_count: int = 0
    problem_count: int = 0
    truncated: bool = False


class ClipImportProblemFrame(BaseModel):
    timestamp: str
    readiness_summary: str
    cache_state: str
    decode_ready: bool = False
    sync_message: Optional[str] = None


class ClipImportRequest(BaseModel):
    manifest: dict[str, Any] = Field(..., description="Playback clip manifest JSON from export")


class ClipImportResponse(BaseModel):
    valid: bool = False
    import_status: str = "invalid"
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    manifest: Optional[PlaybackExportResponse] = None
    readiness_summary: ClipImportReadinessSummary = Field(default_factory=ClipImportReadinessSummary)
    problem_frames: list[ClipImportProblemFrame] = Field(default_factory=list)
    suggested_commands: list[str] = Field(default_factory=list)
    assessed_at: Optional[str] = None
    verified_mrms: bool = False
    local_dev_only: bool = True
    prototype: bool = True
    production_tile_serving: bool = False
    status_only: bool = True
    does_not_run_ingest: bool = True
    does_not_run_decode: bool = True
