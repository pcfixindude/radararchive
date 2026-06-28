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


class QueueBenchmarkJobCompact(BaseModel):
    timestamp: Optional[str] = None
    radar_file_id: Optional[int] = None
    job_id: Optional[int] = None
    status: Optional[str] = None
    decode_status: Optional[str] = None
    min_zoom: Optional[int] = None
    max_zoom: Optional[int] = None
    tiles_planned: int = 0
    tiles_written: int = 0
    tiles_skipped: int = 0
    output_bytes: int = 0
    elapsed_seconds: Optional[float] = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class QueueBenchmarkCompact(BaseModel):
    benchmarked_at: Optional[str] = None
    source_mode: Optional[str] = None
    effective_count: Optional[int] = None
    min_zoom: Optional[int] = None
    max_zoom: Optional[int] = None
    dry_run: bool = False
    jobs_enqueued: int = 0
    jobs_processed: int = 0
    jobs_succeeded: int = 0
    jobs_failed: int = 0
    total_tiles_written: int = 0
    total_tiles_skipped: int = 0
    total_output_bytes: int = 0
    total_elapsed_seconds: Optional[float] = None
    job_summaries: list[QueueBenchmarkJobCompact] = Field(default_factory=list)
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


class FrameTileMetricsCompact(BaseModel):
    timestamp: Optional[str] = None
    radar_file_id: Optional[int] = None
    decode_status: Optional[str] = None
    render_job_id: Optional[int] = None
    min_zoom: Optional[int] = None
    max_zoom: Optional[int] = None
    tiles_planned: int = 0
    tiles_written: int = 0
    tiles_skipped: int = 0
    output_bytes: int = 0
    elapsed_seconds: Optional[float] = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ScheduledValidationStepCompact(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    summary: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ValidationFailureCompact(BaseModel):
    logged_at: Optional[str] = None
    phase: Optional[str] = None
    step: Optional[str] = None
    source_mode: Optional[str] = None
    command_context: Optional[str] = None
    error_message: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    verified_mrms: bool = False
    prototype: bool = True


class GroupedFailureCauseCompact(BaseModel):
    step: str = "unknown"
    cause: str = "unknown"
    message: str = ""
    normalized_message: str = ""
    count: int = 0
    latest_logged_at: Optional[str] = None


class ValidationAlertCompact(BaseModel):
    status: str = "ok"
    latest_run_at: Optional[str] = None
    updated_at: Optional[str] = None
    failure_count: int = 0
    warning_count: int = 0
    operator_attention_needed: bool = False
    suggested_next_action: Optional[str] = None
    grouped_failure_causes: list[GroupedFailureCauseCompact] = Field(default_factory=list)
    verified_mrms: bool = False
    prototype: bool = True


class ValidationAlertsResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    alert: Optional[dict[str, Any]] = None


class MrmsProofCriteriaCounts(BaseModel):
    passed: int = 0
    failed: int = 0
    warning: int = 0
    skipped: int = 0
    unknown: int = 0


class MrmsProofCompact(BaseModel):
    generated_at: Optional[str] = None
    overall_status: str = "not_started"
    source_mode: Optional[str] = None
    frame_count: int = 0
    criteria_counts: MrmsProofCriteriaCounts = Field(default_factory=MrmsProofCriteriaCounts)
    operator_review_required: bool = True
    proof_only: bool = True
    verified_mrms: bool = False
    prototype: bool = True


class MrmsProofResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    proof_only: bool = True
    operator_review_required: bool = True
    report: Optional[dict[str, Any]] = None


class ScheduledValidationCompact(BaseModel):
    ran_at: Optional[str] = None
    source_mode: Optional[str] = None
    success: bool = False
    exit_code: int = 1
    effective_count: Optional[int] = None
    min_zoom: Optional[int] = None
    max_zoom: Optional[int] = None
    elapsed_seconds: Optional[float] = None
    steps_ok: int = 0
    steps_failed: int = 0
    steps: list[ScheduledValidationStepCompact] = Field(default_factory=list)
    batch_decoded_count: int = 0
    queue_jobs_succeeded: int = 0
    queue_jobs_failed: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    verified_mrms: bool = False
    prototype: bool = True


class ScheduledValidationHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    count: int = 0
    max_entries: int = 10
    latest: Optional[dict[str, Any]] = None
    entries: list[dict[str, Any]] = Field(default_factory=list)


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
    queue_benchmark_available: bool = False
    queue_benchmark: Optional[QueueBenchmarkCompact] = None
    render_queue: RenderQueueCompact
    validation_history_count: int = 0
    validation_history: list[ValidationHistoryEntry] = Field(default_factory=list)
    queue_benchmark_history_count: int = 0
    scheduled_validation_available: bool = False
    scheduled_validation: Optional[ScheduledValidationCompact] = None
    validation_failures_count: int = 0
    validation_failures_recent: list[ValidationFailureCompact] = Field(default_factory=list)
    validation_alert: Optional[ValidationAlertCompact] = None
    grouped_failure_causes: list[GroupedFailureCauseCompact] = Field(default_factory=list)
    mrms_proof: Optional[MrmsProofCompact] = None
    mrms_proof_available: bool = False
    frame_summaries: list[FrameTileMetricsCompact] = Field(default_factory=list)
    catalog: CatalogStatusResponse


class QueueBenchmarkHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    count: int = 0
    max_entries: int = 10
    latest: Optional[dict[str, Any]] = None
    entries: list[dict[str, Any]] = Field(default_factory=list)


class ValidationLatestResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    production_rendering_enabled: bool = False
    validation: Optional[dict[str, Any]] = None
    benchmark: Optional[dict[str, Any]] = None
    queue_benchmark: Optional[dict[str, Any]] = None
    scheduled_validation: Optional[dict[str, Any]] = None
    validation_alert: Optional[dict[str, Any]] = None
    mrms_proof: Optional[dict[str, Any]] = None


class ValidationFailuresResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    count: int = 0
    max_entries: int = 100
    entries: list[ValidationFailureCompact] = Field(default_factory=list)
