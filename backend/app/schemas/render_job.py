from typing import Optional

from pydantic import BaseModel, Field


class RenderJobCreate(BaseModel):
    job_type: str = Field(default="production_tiles", description="Render job type (prototype)")
    layer: str = Field(default="mrms_reflectivity")
    timestamp: Optional[str] = Field(default=None, description="Optional catalog timestamp filter")
    min_zoom: int = Field(default=0, ge=0, le=4)
    max_zoom: int = Field(default=0, ge=0, le=4)
    force: bool = False
    mark_catalog: bool = Field(
        default=False,
        description="Prototype only — marks catalog production_rendered (fixture/test)",
    )
    artifact_limit: Optional[int] = Field(default=None, ge=1)
    max_attempts: int = Field(default=3, ge=1, le=10)


class RenderJobResponse(BaseModel):
    id: int
    job_type: str
    layer: str
    timestamp: Optional[str]
    min_zoom: int
    max_zoom: int
    force: bool
    mark_catalog: bool
    artifact_limit: Optional[int]
    status: str
    attempt_count: int
    max_attempts: int
    progress_current: int
    progress_total: int
    tiles_written: int
    tiles_skipped: int
    output_bytes: int
    error_message: Optional[str]
    created_at: str
    started_at: Optional[str]
    finished_at: Optional[str]
    last_error_at: Optional[str]
    next_retry_at: Optional[str]
    canceled_at: Optional[str]
    prototype: bool = True
    verified_mrms: bool = False

    model_config = {"from_attributes": True}


class RenderQueueSummaryResponse(BaseModel):
    queued: int
    running: int
    succeeded: int
    failed: int
    canceled: int
    total_tiles_written: int
    total_output_bytes: int
    prototype: bool = True
    verified_mrms: bool = False
