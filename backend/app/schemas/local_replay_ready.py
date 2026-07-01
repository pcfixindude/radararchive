"""Schemas for one-shot local replay setup (local dev only)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class LocalReplayReadyChecklistItem(BaseModel):
    id: str
    label: str
    status: str
    message: str
    next_command: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


class LocalReplayReadyResponse(BaseModel):
    ran_at: str
    ready: bool
    ready_label: str
    dry_run: bool = True
    frame_count: int = 0
    window_source: Optional[str] = None
    ingest_report_available: bool = False
    cache_status: Optional[dict[str, Any]] = None
    decode_retry_status: Optional[str] = None
    checklist: list[LocalReplayReadyChecklistItem] = Field(default_factory=list)
    next_command: Optional[str] = None
    next_commands: list[str] = Field(default_factory=list)
    operator_steps: list[str] = Field(default_factory=list)
    suggested_run_command: str = "make local-replay-ready RUN=1"
    verified_mrms: bool = False
    local_dev_only: bool = True
    prototype: bool = True
    does_not_run_real_ingest: bool = True
    production_tile_serving: bool = False
    run_mode: Optional[str] = None
    run_message: Optional[str] = None
    actions_run: list[dict[str, Any]] = Field(default_factory=list)
    warm_report_status: Optional[str] = None
