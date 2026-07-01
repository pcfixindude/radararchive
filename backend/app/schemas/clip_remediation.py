"""Schemas for imported clip batch remediation plan (prototype only)."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ClipRemediationProblemGroup(BaseModel):
    readiness_type: str
    label: str
    count: int = 0
    assessed_count: int = 0
    truncated: bool = False
    timestamps: list[str] = Field(default_factory=list)


class ClipRemediationGroupSummary(BaseModel):
    total_problem_count: int = 0
    assessed_count: int = 0
    cold_count: int = 0
    missing_count: int = 0
    failed_count: int = 0
    stub_count: int = 0
    partial_count: int = 0
    invalid_count: int = 0


class ClipRemediationCommandStep(BaseModel):
    step: int
    category: str
    label: str
    command: str
    frame_count: Optional[int] = None
    note: Optional[str] = None


class ClipRemediationPlan(BaseModel):
    clip_id: Optional[str] = None
    valid: bool = False
    plan_status: str = "invalid"
    problem_groups: list[ClipRemediationProblemGroup] = Field(default_factory=list)
    group_summary: ClipRemediationGroupSummary = Field(default_factory=ClipRemediationGroupSummary)
    commands: list[ClipRemediationCommandStep] = Field(default_factory=list)
    command_block: str = ""
    operator_note: str = ""
    bounded_frame_limit: int = 8
    truncated: bool = False
    assessed_at: Optional[str] = None
    verified_mrms: bool = False
    local_dev_only: bool = True
    prototype: bool = True
    production_tile_serving: bool = False
    status_only: bool = True
    does_not_run_ingest: bool = True
    does_not_run_decode: bool = True
    does_not_run_real_downloads: bool = True
    commands_not_auto_run: bool = True


class ClipRemediationRequest(BaseModel):
    manifest: Optional[dict[str, Any]] = Field(
        default=None,
        description="Playback clip manifest JSON (from export or UI)",
    )
    import_report: Optional[dict[str, Any]] = Field(
        default=None,
        description="Existing clip import report JSON (from make clip-import)",
    )
    limit: int = Field(default=8, ge=1, le=20, description="Max problem frames to assess for commands")


class ClipRemediationResponse(ClipRemediationPlan):
    import_report: Optional[dict[str, Any]] = None
