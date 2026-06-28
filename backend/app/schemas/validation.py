"""Pydantic schemas for dev validation dashboard API (prototype only)."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ValidationTileCacheSummary(BaseModel):
    tiles_written: int = 0
    tiles_skipped: int = 0
    output_bytes: int = 0
    job_id: Optional[int] = None
    job_status: Optional[str] = None


class ValidationCompact(BaseModel):
    validated_at: Optional[str] = None
    source_mode: Optional[str] = None
    batch: bool = False
    requested_frame_count: Optional[int] = None
    effective_frame_count: Optional[int] = None
    discovered_count: int = 0
    downloaded_count: int = 0
    inspected_count: int = 0
    decoded_count: int = 0
    render_jobs_enqueued: int = 0
    worker_jobs_processed: int = 0
    tiles_planned: int = 0
    tiles_written: int = 0
    tiles_skipped: int = 0
    output_bytes: int = 0
    elapsed_seconds: Optional[float] = None
    decoder_available: bool = False
    tile_cache: ValidationTileCacheSummary = Field(default_factory=ValidationTileCacheSummary)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    verified_mrms: bool = False
    prototype: bool = True


class BenchmarkStageTiming(BaseModel):
    stage: str
    elapsed_seconds: float


class BenchmarkCompact(BaseModel):
    benchmarked_at: Optional[str] = None
    source_mode: Optional[str] = None
    stage_timings: list[BenchmarkStageTiming] = Field(default_factory=list)
    min_zoom: Optional[int] = None
    max_zoom: Optional[int] = None
    tiles_planned: int = 0
    tiles_written: int = 0
    tiles_skipped: int = 0
    output_bytes: int = 0
    tile_build_elapsed_seconds: float = 0.0
    decoder_used: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    verified_mrms: bool = False
    prototype: bool = True


class RenderQueueCompact(BaseModel):
    queued: int = 0
    running: int = 0
    succeeded: int = 0
    failed: int = 0
    canceled: int = 0
    total_tiles_written: int = 0
    total_output_bytes: int = 0
    prototype: bool = True
    verified_mrms: bool = False


class CatalogStatusResponse(BaseModel):
    product_id: str
    total_frames: int = 0
    mrms_discovered_frames: int = 0
    download_status: dict[str, int] = Field(default_factory=dict)
    processed_status: dict[str, int] = Field(default_factory=dict)
    render_status: dict[str, int] = Field(default_factory=dict)
    latest_timestamp: Optional[str] = None
    earliest_timestamp: Optional[str] = None
    latest_downloaded_timestamp: Optional[str] = None
    prototype: bool = True
    verified_mrms: bool = False


class ValidationHistoryEntry(BaseModel):
    validated_at: Optional[str] = None
    source_mode: Optional[str] = None
    batch: bool = False
    requested_frame_count: Optional[int] = None
    effective_frame_count: Optional[int] = None
    discovered_count: int = 0
    downloaded_count: int = 0
    decoded_count: int = 0
    elapsed_seconds: Optional[float] = None
    verified_mrms: bool = False
    prototype: bool = True


class ValidationHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    count: int = 0
    max_entries: int = 10
    entries: list[ValidationHistoryEntry] = Field(default_factory=list)


class ValidationSummaryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    production_rendering_enabled: bool = False
    placeholder_default: bool = True
    decoder_available: bool = False
    decoder_summary: str = ""
    stale_running_job_seconds: int = 3600
    validation_available: bool = False
    validation: Optional[ValidationCompact] = None
    benchmark_available: bool = False
    benchmark: Optional[BenchmarkCompact] = None
    render_queue: RenderQueueCompact
    validation_history_count: int = 0
    catalog: CatalogStatusResponse


class ValidationLatestResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    production_rendering_enabled: bool = False
    validation: Optional[dict[str, Any]] = None
    benchmark: Optional[dict[str, Any]] = None
