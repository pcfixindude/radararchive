"""Schemas for guided MRMS ingest window planning (local dev only)."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class IngestWindowPlanResponse(BaseModel):
    preset: str
    preset_label: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    limit: int = 8
    warm_cache: bool = False
    estimated_frames_in_window: Optional[int] = None
    ready: bool = False
    warnings: list[str] = Field(default_factory=list)
    bulk_ingest_command: Optional[str] = None
    guided_command: str
    next_commands: list[str] = Field(default_factory=list)
    operator_steps: list[str] = Field(default_factory=list)
    verified_mrms: bool = False
    local_dev_only: bool = True
    prototype: bool = True
    requires_real_flag: bool = True
    does_not_enable_production: bool = True
