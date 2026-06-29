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


class OperatorGuidanceItemCompact(BaseModel):
    title: str
    path: str
    anchor: str = ""
    section_label: str = ""
    cause: str
    suggested_action: str = ""
    verified_mrms: bool = False
    local_guidance_only: bool = True
    prototype: bool = True


class ValidationAlertCompact(BaseModel):
    status: str = "ok"
    latest_run_at: Optional[str] = None
    updated_at: Optional[str] = None
    failure_count: int = 0
    warning_count: int = 0
    operator_attention_needed: bool = False
    suggested_next_action: Optional[str] = None
    grouped_failure_causes: list[GroupedFailureCauseCompact] = Field(default_factory=list)
    proof_regression_detected: bool = False
    proof_regression_count: int = 0
    proof_regression_still_active: bool = False
    proof_regression_reviewed: bool = False
    latest_signoff_at: Optional[str] = None
    latest_signoff_operator: Optional[str] = None
    proof_bundle_diff_status: Optional[str] = None
    proof_bundle_diff_attention: bool = False
    latest_proof_bundle_id: Optional[str] = None
    latest_proof_bundle_created_at: Optional[str] = None
    proof_bundle_diff_alert_history_count: int = 0
    latest_proof_bundle_diff_alert_at: Optional[str] = None
    latest_proof_bundle_diff_alert_status: Optional[str] = None
    proof_bundle_diff_alert_trend: Optional[str] = None
    diff_acknowledgment_count: int = 0
    latest_diff_acknowledgment_at: Optional[str] = None
    latest_diff_acknowledgment_operator: Optional[str] = None
    diff_alert_acknowledged_but_still_active: bool = False
    proof_bundle_diff_escalation_level: Optional[str] = None
    proof_bundle_diff_escalation_stale_ack: bool = False
    proof_bundle_diff_escalation_reason: Optional[str] = None
    proof_bundle_diff_escalation_suggested_next_action: Optional[str] = None
    proof_bundle_diff_escalation_guidance_items: list[OperatorGuidanceItemCompact] = Field(
        default_factory=list
    )
    proof_bundle_diff_escalation_history_count: int = 0
    latest_proof_bundle_diff_escalation_snapshot_at: Optional[str] = None
    urgent_stdout_notice_triggered: bool = False
    urgent_stdout_notice_at: Optional[str] = None
    operator_guidance: list[OperatorGuidanceItemCompact] = Field(default_factory=list)
    verified_mrms: bool = False
    prototype: bool = True


class ProofBundleDiffEscalationGuidanceItemCompact(BaseModel):
    title: str
    path: str
    anchor: str = ""
    section_label: str = ""
    cause: str
    suggested_action: str = ""
    verified_mrms: bool = False
    local_guidance_only: bool = True
    prototype: bool = True


class ProofBundleDiffEscalationCompact(BaseModel):
    available: bool = False
    escalation_level: str = "none"
    reason: str = ""
    latest_diff_status: Optional[str] = None
    current_attention_streak: int = 0
    acknowledgment_status: str = "none"
    latest_acknowledgment_at: Optional[str] = None
    latest_acknowledgment_operator: Optional[str] = None
    stale_acknowledgment: bool = False
    suggested_next_action: str = ""
    guidance_items: list[ProofBundleDiffEscalationGuidanceItemCompact] = Field(default_factory=list)
    trend: Optional[str] = None
    verified_mrms: bool = False
    local_escalation_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class ProofBundleDiffEscalationResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_escalation_only: bool = True
    does_not_clear_alerts: bool = True
    escalation: ProofBundleDiffEscalationCompact


class ProofBundleDiffEscalationHistoryEntryCompact(BaseModel):
    created_at: Optional[str] = None
    escalation_level: str = "none"
    reason: str = ""
    latest_diff_status: Optional[str] = None
    current_attention_streak: int = 0
    acknowledgment_status: str = "none"
    stale_acknowledgment: bool = False
    suggested_next_action: str = ""
    guidance_item_count: int = 0
    source: Optional[str] = None
    verified_mrms: bool = False
    local_history_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class ProofBundleDiffEscalationHistoryCompact(BaseModel):
    available: bool = False
    count: int = 0
    max_entries: int = 25
    latest_snapshot_at: Optional[str] = None
    latest_escalation_level: Optional[str] = None
    recent: list[ProofBundleDiffEscalationHistoryEntryCompact] = Field(default_factory=list)
    urgent_stdout_notice_triggered: bool = False
    urgent_stdout_notice_at: Optional[str] = None
    urgent_stdout_local_only: bool = True
    verified_mrms: bool = False
    local_history_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class ProofBundleDiffEscalationHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_history_only: bool = True
    does_not_clear_alerts: bool = True
    count: int = 0
    max_entries: int = 25
    latest: Optional[ProofBundleDiffEscalationHistoryEntryCompact] = None
    entries: list[ProofBundleDiffEscalationHistoryEntryCompact] = Field(default_factory=list)


class ProofBundleDiffEscalationMetricsCompact(BaseModel):
    available: bool = False
    total_snapshots: int = 0
    urgent_count: int = 0
    attention_count: int = 0
    watch_count: int = 0
    none_count: int = 0
    latest_level: str = "none"
    latest_at: Optional[str] = None
    first_urgent_at: Optional[str] = None
    last_urgent_at: Optional[str] = None
    longest_urgent_streak: int = 0
    longest_attention_or_urgent_streak: int = 0
    current_urgent_streak: int = 0
    current_attention_or_urgent_streak: int = 0
    acknowledgment_status: Optional[str] = None
    stale_acknowledgment_count: int = 0
    verified_mrms: bool = False
    local_metrics_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class ProofBundleDiffEscalationMetricsResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_metrics_only: bool = True
    does_not_clear_alerts: bool = True
    metrics: ProofBundleDiffEscalationMetricsCompact


class ProofBundleDiffEscalationDigestCompact(BaseModel):
    available: bool = False
    generated_at: Optional[str] = None
    markdown_path: Optional[str] = None
    json_path: Optional[str] = None
    latest_escalation_level: Optional[str] = None
    snapshot_count: int = 0
    urgent_count: int = 0
    attention_count: int = 0
    verified_mrms: bool = False
    local_digest_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class ProofBundleDiffEscalationDigestResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_digest_only: bool = True
    does_not_clear_alerts: bool = True
    digest: Optional[dict[str, Any]] = None
    markdown: Optional[str] = None
    compact: ProofBundleDiffEscalationDigestCompact


class ProofBundleDiffEscalationDigestHistoryEntryCompact(BaseModel):
    created_at: Optional[str] = None
    digest_path: Optional[str] = None
    metadata_path: Optional[str] = None
    latest_escalation_level: Optional[str] = None
    latest_diff_status: Optional[str] = None
    current_attention_or_urgent_streak: int = 0
    urgent_count: int = 0
    attention_count: int = 0
    stale_acknowledgment_count: int = 0
    verified_mrms: bool = False
    local_digest_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class ProofBundleDiffEscalationDigestHistoryCompact(BaseModel):
    available: bool = False
    count: int = 0
    max_entries: int = 25
    latest: Optional[ProofBundleDiffEscalationDigestHistoryEntryCompact] = None
    recent: list[ProofBundleDiffEscalationDigestHistoryEntryCompact] = Field(default_factory=list)
    verified_mrms: bool = False
    local_digest_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class ProofBundleDiffEscalationDigestHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_digest_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    count: int = 0
    max_entries: int = 25
    latest: Optional[ProofBundleDiffEscalationDigestHistoryEntryCompact] = None
    entries: list[ProofBundleDiffEscalationDigestHistoryEntryCompact] = Field(default_factory=list)
    compact: ProofBundleDiffEscalationDigestHistoryCompact


class ProofBundleDiffEscalationDigestDiffCompact(BaseModel):
    available: bool = False
    overall_digest_diff_status: Optional[str] = None
    checked_at: Optional[str] = None
    history_count: int = 0
    changes: Optional[dict[str, Any]] = None
    verified_mrms: bool = False
    local_digest_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class DigestRegenerationHintCompact(BaseModel):
    digest_regeneration_recommended: bool = False
    reason: Optional[str] = None
    suggested_command: Optional[str] = None
    latest_escalation_level: Optional[str] = None
    current_attention_or_urgent_streak: int = 0
    latest_digest_at: Optional[str] = None
    latest_escalation_snapshot_at: Optional[str] = None
    latest_digest_diff_status: Optional[str] = None
    verified_mrms: bool = False
    local_digest_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class ProofBundleDiffEscalationDigestDiffResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_digest_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    latest: Optional[dict[str, Any]] = None
    count: int = 0
    max_entries: int = 25
    entries: list[dict[str, Any]] = Field(default_factory=list)
    compact: ProofBundleDiffEscalationDigestDiffCompact
    regeneration_hint: DigestRegenerationHintCompact


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


class MrmsProofRegressionCompact(BaseModel):
    checked_at: Optional[str] = None
    regression_status: str = "inconclusive"
    regression_detected: bool = False
    regression_count: int = 0
    summary: Optional[str] = None
    current_overall_status: Optional[str] = None
    previous_overall_status: Optional[str] = None
    verified_mrms: bool = False
    prototype: bool = True


class MrmsProofRegressionResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    report: Optional[dict[str, Any]] = None


class MrmsSignoffSummaryCompact(BaseModel):
    signoff_count: int = 0
    latest_signoff_at: Optional[str] = None
    latest_operator: Optional[str] = None
    proof_regression_still_active: bool = False
    proof_regression_reviewed: bool = False
    verified_mrms: bool = False
    local_signoff_only: bool = True
    does_not_set_verified_mrms: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class MrmsSignoffCreateRequest(BaseModel):
    operator_name: Optional[str] = None
    operator_initials: Optional[str] = None
    operator_notes: Optional[str] = None
    accepted_limitations: Optional[str] = None
    proof_report_timestamp: Optional[str] = None
    frame_count_reviewed: Optional[int] = None


class MrmsSignoffCreateResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_signoff_only: bool = True
    does_not_enable_production: bool = True
    production_enabled: bool = False
    proof_regression_still_active: bool = False
    signoff: dict[str, Any]
    alert: Optional[ValidationAlertCompact] = None


class MrmsReviewSessionEntryCompact(BaseModel):
    session_id: Optional[str] = None
    created_at: Optional[str] = None
    operator: Optional[str] = None
    session_notes: Optional[str] = None
    latest_escalation_level: Optional[str] = None
    latest_escalation_snapshot_at: Optional[str] = None
    latest_digest_path: Optional[str] = None
    latest_operator_handoff_path: Optional[str] = None
    latest_proof_bundle_diff_status: Optional[str] = None
    latest_proof_report_status: Optional[str] = None
    open_attention_count: int = 0
    checklist_items_reviewed: list[str] = Field(default_factory=list)
    checklist_items_not_reviewed: list[str] = Field(default_factory=list)
    verified_mrms: bool = False
    local_review_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class OpenAttentionGuidanceItemCompact(BaseModel):
    title: str
    path: str
    anchor: str = ""
    section_label: str = ""
    cause: str
    attention_item: str = ""
    suggested_action: str = ""
    verified_mrms: bool = False
    local_guidance_only: bool = True
    prototype: bool = True


class MrmsReviewSessionComparisonCompact(BaseModel):
    available: bool = False
    overall_review_diff_status: Optional[str] = None
    compared_at: Optional[str] = None
    latest_created_at: Optional[str] = None
    baseline_created_at: Optional[str] = None
    latest_operator: Optional[str] = None
    baseline_operator: Optional[str] = None
    open_attention_count_change: Optional[dict[str, Any]] = None
    checklist_reviewed_count_change: Optional[dict[str, Any]] = None
    checklist_not_reviewed_count_change: Optional[dict[str, Any]] = None
    improvements: list[str] = Field(default_factory=list)
    regressions: list[str] = Field(default_factory=list)
    history_count: int = 0
    verified_mrms: bool = False
    local_comparison_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class MrmsReviewSessionSummaryCompact(BaseModel):
    available: bool = False
    session_count: int = 0
    latest_created_at: Optional[str] = None
    latest_operator: Optional[str] = None
    latest_escalation_level: Optional[str] = None
    open_attention_count: int = 0
    open_attention_guidance: list[OpenAttentionGuidanceItemCompact] = Field(default_factory=list)
    comparison: Optional[MrmsReviewSessionComparisonCompact] = None
    verified_mrms: bool = False
    local_review_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class MrmsReviewSessionComparisonResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_comparison_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    latest: Optional[dict[str, Any]] = None
    count: int = 0
    max_entries: int = 25
    entries: list[dict[str, Any]] = Field(default_factory=list)
    compact: MrmsReviewSessionComparisonCompact


class MrmsReviewSessionComparisonHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_comparison_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    count: int = 0
    max_entries: int = 25
    latest: Optional[dict[str, Any]] = None
    entries: list[dict[str, Any]] = Field(default_factory=list)
    compact: MrmsReviewSessionComparisonCompact


class MrmsReviewSessionsResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_review_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    count: int = 0
    max_entries: int = 50
    latest: Optional[MrmsReviewSessionEntryCompact] = None
    entries: list[MrmsReviewSessionEntryCompact] = Field(default_factory=list)
    compact: MrmsReviewSessionSummaryCompact


class MrmsReviewSessionCreateRequest(BaseModel):
    operator_name: Optional[str] = None
    operator_initials: Optional[str] = None
    session_notes: Optional[str] = None
    checklist_items_reviewed: list[str] = Field(default_factory=list)
    accepted_limitations: bool = False
    accepted_limitations_text: Optional[str] = None
    export_after_create: bool = False


class MrmsReviewSessionCreateResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_review_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    production_enabled: bool = False
    review_session: dict[str, Any]
    export_after_create_requested: bool = False
    export_generated: bool = False
    export_path: Optional[str] = None
    export_metadata_path: Optional[str] = None
    export_error: Optional[str] = None
    export_compact: Optional[dict[str, Any]] = None


class MrmsReviewSessionExportCompact(BaseModel):
    available: bool = False
    created_at: Optional[str] = None
    export_path: Optional[str] = None
    metadata_path: Optional[str] = None
    session_id: Optional[str] = None
    operator: Optional[str] = None
    comparison_status: Optional[str] = None
    open_attention_count: int = 0
    history_count: int = 0
    verified_mrms: bool = False
    local_export_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class ReviewExportRegenerationHintCompact(BaseModel):
    review_export_regeneration_recommended: bool = False
    reason: Optional[str] = None
    suggested_command: Optional[str] = None
    latest_export_at: Optional[str] = None
    latest_session_at: Optional[str] = None
    latest_comparison_at: Optional[str] = None
    digest_regeneration_recommended: bool = False
    digest_regeneration_reason: Optional[str] = None
    verified_mrms: bool = False
    local_export_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class ScheduledVisualReviewCompact(BaseModel):
    visual_review_requested: bool = False
    visual_review_generated: bool = False
    visual_review_path: Optional[str] = None
    visual_review_markdown_path: Optional[str] = None
    visual_review_history_count: Optional[int] = None
    visual_review_reason: Optional[str] = None
    visual_review_elapsed_seconds: Optional[float] = None
    visual_review_error: Optional[str] = None
    verified_mrms: bool = False
    local_visual_review_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class OperatorReviewStatusCompact(BaseModel):
    available: bool = True
    created_at: Optional[str] = None
    status_level: str = "unknown"
    status_reason: Optional[str] = None
    top_recommended_action: Optional[str] = None
    top_suggested_command: Optional[str] = None
    review_session_recommended: bool = False
    review_export_recommended: bool = False
    digest_regeneration_recommended: bool = False
    visual_review_regeneration_recommended: bool = False
    visual_review_hint_reason: Optional[str] = None
    evidence_trend: str = "unknown"
    latest_review_session_at: Optional[str] = None
    latest_review_export_at: Optional[str] = None
    latest_digest_at: Optional[str] = None
    latest_export_diff_status: Optional[str] = None
    latest_export_diff_trend: Optional[str] = None
    open_attention_count: Optional[int] = None
    active_guidance_count: int = 0
    guidance_items: list[OperatorGuidanceItemCompact] = Field(default_factory=list)
    top_guidance_item: Optional[OperatorGuidanceItemCompact] = None
    runbook_path: Optional[str] = None
    runbook_section: Optional[str] = None
    suggested_action: Optional[str] = None
    verified_mrms: bool = False
    local_status_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True
    latest_visual_review_at: Optional[str] = None
    latest_visual_review_path: Optional[str] = None
    latest_visual_review_json_path: Optional[str] = None
    latest_visual_review_markdown_path: Optional[str] = None
    latest_visual_review_comparison_status: Optional[str] = None
    visual_review_artifact_count: Optional[int] = None
    visual_review_missing_artifact_count: Optional[int] = None
    scheduled_visual_review: Optional[ScheduledVisualReviewCompact] = None


class MrmsVisualReviewCompact(BaseModel):
    available: bool = False
    created_at: Optional[str] = None
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    layers_inspected: list[str] = Field(default_factory=list)
    timestamp_count: int = 0
    frame_count: int = 0
    artifact_count: int = 0
    missing_artifact_count: int = 0
    tile_modes_found: list[str] = Field(default_factory=list)
    suggested_next_command: Optional[str] = None
    runbook_path: Optional[str] = None
    history_count: int = 0
    verified_mrms: bool = False
    local_visual_review_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class MrmsVisualReviewHistoryEntryCompact(BaseModel):
    created_at: Optional[str] = None
    layers_inspected: list[str] = Field(default_factory=list)
    timestamp_count: int = 0
    frame_count: int = 0
    artifact_count: int = 0
    missing_artifact_count: int = 0
    tile_modes_found: list[str] = Field(default_factory=list)
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    verified_mrms: bool = False
    local_visual_review_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class MrmsVisualReviewResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_visual_review_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    latest: Optional[dict[str, Any]] = None
    compact: MrmsVisualReviewCompact


class MrmsVisualReviewHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_visual_review_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    count: int = 0
    max_entries: int = 25
    entries: list[MrmsVisualReviewHistoryEntryCompact] = Field(default_factory=list)
    compact: MrmsVisualReviewCompact


class MrmsVisualReviewComparisonCompact(BaseModel):
    available: bool = False
    overall_visual_review_diff_status: Optional[str] = None
    compared_at: Optional[str] = None
    latest_created_at: Optional[str] = None
    baseline_created_at: Optional[str] = None
    artifact_count_change: Optional[dict[str, Any]] = None
    missing_artifact_count_change: Optional[dict[str, Any]] = None
    tile_modes_added: list[str] = Field(default_factory=list)
    tile_modes_removed: list[str] = Field(default_factory=list)
    history_count: int = 0
    verified_mrms: bool = False
    local_visual_review_comparison_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class MrmsVisualReviewHintCompact(BaseModel):
    available: bool = True
    visual_review_regeneration_recommended: bool = False
    reason: Optional[str] = None
    suggested_command: Optional[str] = None
    latest_visual_review_at: Optional[str] = None
    latest_relevant_evidence_at: Optional[str] = None
    stale_visual_review: bool = False
    verified_mrms: bool = False
    local_hint_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class MrmsVisualReviewComparisonResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_visual_review_comparison_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    latest: Optional[dict[str, Any]] = None
    count: int = 0
    max_entries: int = 25
    entries: list[dict[str, Any]] = Field(default_factory=list)
    compact: MrmsVisualReviewComparisonCompact


class MrmsVisualReviewComparisonHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_visual_review_comparison_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    count: int = 0
    max_entries: int = 25
    entries: list[dict[str, Any]] = Field(default_factory=list)
    compact: MrmsVisualReviewComparisonCompact


class MrmsVisualReviewHintResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_hint_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    hint: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsVisualReviewHintCompact


class MrmsVisualReviewSampleSetContextCompact(BaseModel):
    visual_review_regeneration_recommended: bool = False
    visual_review_hint_reason: Optional[str] = None
    stale_visual_review: bool = False
    latest_visual_review_comparison_status: Optional[str] = None
    comparison_available: bool = False


class MrmsVisualReviewSampleSetCompact(BaseModel):
    available: bool = False
    created_at: Optional[str] = None
    selection_mode: Optional[str] = None
    entry_count: int = 0
    limit: int = 5
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    source_visual_review_at: Optional[str] = None
    source_visual_review_path: Optional[str] = None
    reason: Optional[str] = None
    suggested_command: Optional[str] = None
    context: MrmsVisualReviewSampleSetContextCompact = Field(
        default_factory=MrmsVisualReviewSampleSetContextCompact
    )
    verified_mrms: bool = False
    local_sample_set_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class MrmsVisualReviewSampleSetResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_sample_set_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    no_external_notifications: bool = True
    latest: Optional[dict[str, Any]] = None
    compact: MrmsVisualReviewSampleSetCompact


class MrmsVisualReviewSampleSetCreateRequest(BaseModel):
    selection_mode: str = "recommended"
    limit: int = 5
    timestamps: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class MrmsVisualReviewSampleSetCreateResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_sample_set_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    no_external_notifications: bool = True
    production_enabled: bool = False
    sample_set: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsVisualReviewSampleSetCompact


class MrmsVisualReviewSampleEntrySummaryCompact(BaseModel):
    sample_key: Optional[str] = None
    timestamp: Optional[str] = None
    layer: Optional[str] = None
    tile_mode: Optional[str] = None
    primary_artifact_path: Optional[str] = None
    status: Optional[str] = None
    operator_notes: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewer_label: Optional[str] = None
    issue_tags: list[str] = Field(default_factory=list)
    missing_artifacts: list[str] = Field(default_factory=list)
    stale_visual_review: bool = False


class MrmsVisualReviewSampleReadinessCompact(BaseModel):
    available: bool = False
    readiness_level: Optional[str] = None
    readiness_reason: Optional[str] = None
    total_selected_samples: int = 0
    reviewed_samples: int = 0
    unreviewed_samples: int = 0
    acceptable_count: int = 0
    questionable_count: int = 0
    rejected_count: int = 0
    missing_artifact_samples: int = 0
    stale_samples: int = 0
    needs_followup_samples: int = 0
    suspicious_visual_samples: int = 0
    computed_at: Optional[str] = None
    annotations_path: Optional[str] = None
    markdown_path: Optional[str] = None
    suggested_command: Optional[str] = None
    entry_summaries: list[MrmsVisualReviewSampleEntrySummaryCompact] = Field(default_factory=list)
    verified_mrms: bool = False
    local_advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    no_external_notifications: bool = True
    candidate_ready_is_not_production_authorization: bool = True
    prototype: bool = True


class MrmsVisualReviewSampleReadinessResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    no_external_notifications: bool = True
    candidate_ready_is_not_production_authorization: bool = True
    readiness: dict[str, Any] = Field(default_factory=dict)
    annotations: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsVisualReviewSampleReadinessCompact


class MrmsVisualReviewSampleAnnotationUpsertRequest(BaseModel):
    sample_key: str
    status: str = "unreviewed"
    operator_notes: Optional[str] = None
    reviewer_label: Optional[str] = None
    issue_tags: list[str] = Field(default_factory=list)


class MrmsVisualReviewSampleAnnotationUpsertResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    no_external_notifications: bool = True
    candidate_ready_is_not_production_authorization: bool = True
    production_enabled: bool = False
    annotation: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsVisualReviewSampleReadinessCompact


class MrmsRenderCandidatePreflightEvidenceFoundCompact(BaseModel):
    visual_review: bool = False
    sample_set: bool = False
    sample_readiness: bool = False
    required_docs: bool = False


class MrmsRenderCandidatePreflightCompact(BaseModel):
    available: bool = False
    preflight_level: Optional[str] = None
    preflight_reason: Optional[str] = None
    blocking_items: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    computed_at: Optional[str] = None
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    suggested_command: Optional[str] = None
    evidence_found: MrmsRenderCandidatePreflightEvidenceFoundCompact = Field(
        default_factory=MrmsRenderCandidatePreflightEvidenceFoundCompact
    )
    verified_mrms: bool = False
    local_advisory_preflight_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    no_external_notifications: bool = True
    candidate_preflight_ready_is_not_production_authorization: bool = True
    prototype: bool = True


class MrmsRenderCandidatePreflightResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_advisory_preflight_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    no_external_notifications: bool = True
    candidate_preflight_ready_is_not_production_authorization: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidatePreflightCompact


class MrmsRenderCandidateDryRunPlanCompact(BaseModel):
    available: bool = False
    plan_status: Optional[str] = None
    plan_reason: Optional[str] = None
    blocking_items: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    suggested_command: Optional[str] = None
    prerequisites: list[str] = Field(default_factory=list)
    stop_conditions: list[str] = Field(default_factory=list)
    expected_artifacts: list[dict[str, Any]] = Field(default_factory=list)
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_advisory_dry_run_plan_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_execute_candidate_steps: bool = True
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateDryRunPlanResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_advisory_dry_run_plan_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_execute_candidate_steps: bool = True
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateDryRunPlanCompact


class MrmsRenderCandidateScaffoldCompact(BaseModel):
    available: bool = False
    scaffold_status: Optional[str] = None
    scaffold_reason: Optional[str] = None
    blocking_items: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    dry_run_mode: bool = True
    execute_performed: bool = False
    created_at: Optional[str] = None
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    suggested_command: Optional[str] = None
    safety_gates: list[dict[str, Any]] = Field(default_factory=list)
    future_candidate_commands: list[dict[str, str]] = Field(default_factory=list)
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_scaffold_only: bool = True
    disabled_by_default: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_execute_by_default: bool = True
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateScaffoldResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_scaffold_only: bool = True
    disabled_by_default: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_execute_by_default: bool = True
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateScaffoldCompact


class MrmsRenderCandidateSandboxCompact(BaseModel):
    available: bool = False
    sandbox_status: Optional[str] = None
    sandbox_reason: Optional[str] = None
    blocking_items: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    sandbox_root: Optional[str] = None
    expected_subdirectories: list[str] = Field(default_factory=list)
    existing_subdirectories: list[str] = Field(default_factory=list)
    missing_subdirectories: list[str] = Field(default_factory=list)
    cleanup_candidates: list[dict[str, Any]] = Field(default_factory=list)
    cleanup_mode: str = "report_only"
    delete_performed: bool = False
    safety_gates: list[dict[str, Any]] = Field(default_factory=list)
    isolation_status: Optional[bool] = None
    created_at: Optional[str] = None
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    suggested_command: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_sandbox_only: bool = True
    disabled_by_default: bool = True
    cleanup_report_only_by_default: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_sandbox_only: bool = True
    disabled_by_default: bool = True
    cleanup_report_only_by_default: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateSandboxCompact


class MrmsRenderCandidateSandboxImportExportCompact(BaseModel):
    available: bool = False
    import_export_status: Optional[str] = None
    import_export_reason: Optional[str] = None
    schema_version: Optional[str] = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    included_reports: list[dict[str, Any]] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    latest_export_json_path: Optional[str] = None
    latest_export_markdown_path: Optional[str] = None
    latest_import_json_path: Optional[str] = None
    latest_import_markdown_path: Optional[str] = None
    comparison: dict[str, Any] = Field(default_factory=dict)
    status_json_path: Optional[str] = None
    status_markdown_path: Optional[str] = None
    suggested_export_command: Optional[str] = None
    suggested_import_export_command: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_import_export_only: bool = True
    metadata_report_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxImportExportResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_import_export_only: bool = True
    metadata_report_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateSandboxImportExportCompact


class MrmsRenderCandidateSandboxImportRequest(BaseModel):
    import_json_path: Optional[str] = None


class MrmsRenderCandidateSandboxComparisonHistoryCompact(BaseModel):
    available: bool = False
    history_status: Optional[str] = None
    history_reason: Optional[str] = None
    history_count: int = 0
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    schema_version: Optional[str] = None
    latest_comparison_type: Optional[str] = None
    latest_comparison_status: Optional[str] = None
    latest_recorded_at: Optional[str] = None
    recent_entries: list[dict[str, Any]] = Field(default_factory=list)
    latest_import_export_status: Optional[str] = None
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    latest_json_path: Optional[str] = None
    suggested_command: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_comparison_history_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_comparison_history_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateSandboxComparisonHistoryCompact


class MrmsRenderCandidateSandboxComparisonTrendHintCompact(BaseModel):
    available: bool = False
    hint_status: Optional[str] = None
    hint_reason: Optional[str] = None
    trend: Optional[str] = None
    trend_review_recommended: bool = False
    history_count: Optional[int] = None
    changed_count: Optional[int] = None
    unchanged_count: Optional[int] = None
    current_changed_streak: Optional[int] = None
    recurring_signals: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggested_action: Optional[str] = None
    suggested_command: Optional[str] = None
    schema_version: Optional[str] = None
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_trend_hint_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonTrendHintResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_trend_hint_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateSandboxComparisonTrendHintCompact


class MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCompact(BaseModel):
    available: bool = False
    count: int = 0
    acknowledgment_id: Optional[str] = None
    created_at: Optional[str] = None
    operator: Optional[str] = None
    operator_name: Optional[str] = None
    operator_initials: Optional[str] = None
    note: Optional[str] = None
    related_trend: Optional[str] = None
    related_hint_status: Optional[str] = None
    related_hint_reason: Optional[str] = None
    related_trend_review_recommended: bool = False
    acknowledged_trend_review: bool = False
    trend_review_still_recommended: bool = False
    suggested_command: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCreateRequest(BaseModel):
    operator_name: Optional[str] = None
    operator_initials: Optional[str] = None
    note: str = ""
    related_trend: Optional[str] = None
    related_hint_status: Optional[str] = None
    related_hint_reason: Optional[str] = None
    related_trend_review_recommended: Optional[bool] = None
    acknowledged_trend_review: Optional[bool] = None


class MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCreateResponse(BaseModel):
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_authorize_production_use: bool = True
    production_enabled: bool = False
    trend_review_still_recommended: bool = False
    acknowledgment: dict[str, Any]


class MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentsResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_authorize_production_use: bool = True
    count: int = 0
    max_entries: int = 50
    trend_review_still_recommended: bool = False
    suggested_command: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    latest: Optional[MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCompact] = None
    entries: list[MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCompact] = Field(
        default_factory=list
    )


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCompact(
    BaseModel
):
    available: bool = False
    count: int = 0
    acknowledgment_id: Optional[str] = None
    created_at: Optional[str] = None
    operator: Optional[str] = None
    operator_name: Optional[str] = None
    operator_initials: Optional[str] = None
    note: Optional[str] = None
    related_trend: Optional[str] = None
    related_hint_status: Optional[str] = None
    related_hint_reason: Optional[str] = None
    related_trend_review_recommended: bool = False
    acknowledged_trend_review: bool = False
    latest_rollup_status: Optional[str] = None
    trend_review_still_recommended: bool = False
    suggested_command: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCreateRequest(
    BaseModel
):
    operator_name: Optional[str] = None
    operator_initials: Optional[str] = None
    note: str = ""
    related_trend: Optional[str] = None
    related_hint_status: Optional[str] = None
    related_hint_reason: Optional[str] = None
    related_trend_review_recommended: Optional[bool] = None
    acknowledged_trend_review: Optional[bool] = None


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse(
    BaseModel
):
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_authorize_production_use: bool = True
    production_enabled: bool = False
    trend_review_still_recommended: bool = False
    acknowledgment: dict[str, Any]


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentsResponse(
    BaseModel
):
    prototype: bool = True
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_authorize_production_use: bool = True
    count: int = 0
    max_entries: int = 50
    trend_review_still_recommended: bool = False
    suggested_command: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    latest: Optional[MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCompact] = (
        None
    )
    entries: list[MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCompact] = (
        Field(default_factory=list)
    )


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusCompact(
    BaseModel
):
    available: bool = False
    rollup_status: Optional[str] = None
    acknowledgment_status: Optional[str] = None
    status_reason: Optional[str] = None
    stale_acknowledgment: bool = False
    trend: Optional[str] = None
    hint_status: Optional[str] = None
    trend_review_recommended: bool = False
    acknowledgment_count: Optional[int] = None
    latest_acknowledgment_id: Optional[str] = None
    latest_acknowledgment_created_at: Optional[str] = None
    latest_acknowledgment_operator: Optional[str] = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggested_action: Optional[str] = None
    suggested_command: Optional[str] = None
    schema_version: Optional[str] = None
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_status_rollup_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse(
    BaseModel
):
    prototype: bool = True
    verified_mrms: bool = False
    local_status_rollup_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusCompact


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryCompact(
    BaseModel
):
    available: bool = False
    history_count: int = 0
    latest_rollup_status: Optional[str] = None
    latest_acknowledgment_status: Optional[str] = None
    latest_coverage_change: Optional[str] = None
    latest_recorded_at: Optional[str] = None
    recent_entries: list[dict[str, Any]] = Field(default_factory=list)
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    suggested_command: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_status_history_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse(
    BaseModel
):
    prototype: bool = True
    verified_mrms: bool = False
    local_status_history_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryCompact
    entries: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    max_entries: int = 25


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintCompact(
    BaseModel
):
    available: bool = False
    hint_status: Optional[str] = None
    hint_reason: Optional[str] = None
    trend: Optional[str] = None
    trend_review_recommended: bool = False
    history_count: Optional[int] = None
    worsened_count: Optional[int] = None
    improved_count: Optional[int] = None
    unchanged_count: Optional[int] = None
    current_needs_ack_streak: Optional[int] = None
    current_stale_streak: Optional[int] = None
    latest_rollup_status: Optional[str] = None
    recurring_signals: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggested_action: Optional[str] = None
    suggested_command: Optional[str] = None
    schema_version: Optional[str] = None
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_trend_hint_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse(
    BaseModel
):
    prototype: bool = True
    verified_mrms: bool = False
    local_trend_hint_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintCompact


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCompact(
    BaseModel
):
    available: bool = False
    count: int = 0
    acknowledgment_id: Optional[str] = None
    created_at: Optional[str] = None
    operator: Optional[str] = None
    operator_name: Optional[str] = None
    operator_initials: Optional[str] = None
    note: Optional[str] = None
    related_trend: Optional[str] = None
    related_hint_status: Optional[str] = None
    related_hint_reason: Optional[str] = None
    related_trend_review_recommended: bool = False
    acknowledged_trend_review: bool = False
    latest_rollup_status: Optional[str] = None
    trend_review_still_recommended: bool = False
    suggested_command: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateRequest(
    BaseModel
):
    operator_name: Optional[str] = None
    operator_initials: Optional[str] = None
    note: str = ""
    related_trend: Optional[str] = None
    related_hint_status: Optional[str] = None
    related_hint_reason: Optional[str] = None
    related_trend_review_recommended: Optional[bool] = None
    acknowledged_trend_review: Optional[bool] = None


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse(
    BaseModel
):
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_authorize_production_use: bool = True
    production_enabled: bool = False
    trend_review_still_recommended: bool = False
    acknowledgment: dict[str, Any]


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentsResponse(
    BaseModel
):
    prototype: bool = True
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_authorize_production_use: bool = True
    count: int = 0
    max_entries: int = 50
    trend_review_still_recommended: bool = False
    suggested_command: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    latest: Optional[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCompact
    ] = None
    entries: list[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCompact
    ] = Field(default_factory=list)


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusCompact(
    BaseModel
):
    available: bool = False
    rollup_status: Optional[str] = None
    acknowledgment_status: Optional[str] = None
    status_reason: Optional[str] = None
    stale_acknowledgment: bool = False
    trend: Optional[str] = None
    hint_status: Optional[str] = None
    trend_review_recommended: bool = False
    acknowledgment_count: Optional[int] = None
    latest_acknowledgment_id: Optional[str] = None
    latest_acknowledgment_created_at: Optional[str] = None
    latest_acknowledgment_operator: Optional[str] = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggested_action: Optional[str] = None
    suggested_command: Optional[str] = None
    schema_version: Optional[str] = None
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_status_rollup_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse(
    BaseModel
):
    prototype: bool = True
    verified_mrms: bool = False
    local_status_rollup_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusCompact


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryCompact(
    BaseModel
):
    available: bool = False
    history_count: int = 0
    latest_rollup_status: Optional[str] = None
    latest_acknowledgment_status: Optional[str] = None
    latest_coverage_change: Optional[str] = None
    latest_recorded_at: Optional[str] = None
    recent_entries: list[dict[str, Any]] = Field(default_factory=list)
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    suggested_command: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_status_history_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse(
    BaseModel
):
    prototype: bool = True
    verified_mrms: bool = False
    local_status_history_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryCompact
    entries: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    max_entries: int = 25


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintCompact(
    BaseModel
):
    available: bool = False
    hint_status: Optional[str] = None
    hint_reason: Optional[str] = None
    trend: Optional[str] = None
    trend_review_recommended: bool = False
    history_count: Optional[int] = None
    worsened_count: Optional[int] = None
    improved_count: Optional[int] = None
    unchanged_count: Optional[int] = None
    current_needs_ack_streak: Optional[int] = None
    current_stale_streak: Optional[int] = None
    latest_rollup_status: Optional[str] = None
    recurring_signals: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggested_action: Optional[str] = None
    suggested_command: Optional[str] = None
    schema_version: Optional[str] = None
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_trend_hint_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse(
    BaseModel
):
    prototype: bool = True
    verified_mrms: bool = False
    local_trend_hint_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintCompact


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCompact(
    BaseModel
):
    available: bool = False
    count: int = 0
    acknowledgment_id: Optional[str] = None
    created_at: Optional[str] = None
    operator: Optional[str] = None
    operator_name: Optional[str] = None
    operator_initials: Optional[str] = None
    note: Optional[str] = None
    related_trend: Optional[str] = None
    related_hint_status: Optional[str] = None
    related_hint_reason: Optional[str] = None
    related_trend_review_recommended: bool = False
    acknowledged_trend_review: bool = False
    latest_rollup_status: Optional[str] = None
    trend_review_still_recommended: bool = False
    suggested_command: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateRequest(
    BaseModel
):
    operator_name: Optional[str] = None
    operator_initials: Optional[str] = None
    note: str = ""
    related_trend: Optional[str] = None
    related_hint_status: Optional[str] = None
    related_hint_reason: Optional[str] = None
    related_trend_review_recommended: Optional[bool] = None
    acknowledged_trend_review: Optional[bool] = None


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse(
    BaseModel
):
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_authorize_production_use: bool = True
    production_enabled: bool = False
    trend_review_still_recommended: bool = False
    acknowledgment: dict[str, Any]


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentsResponse(
    BaseModel
):
    prototype: bool = True
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_authorize_production_use: bool = True
    count: int = 0
    max_entries: int = 50
    trend_review_still_recommended: bool = False
    suggested_command: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    latest: Optional[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCompact
    ] = None
    entries: list[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCompact
    ] = Field(default_factory=list)


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusCompact(BaseModel):
    available: bool = False
    rollup_status: Optional[str] = None
    acknowledgment_status: Optional[str] = None
    status_reason: Optional[str] = None
    stale_acknowledgment: bool = False
    trend: Optional[str] = None
    hint_status: Optional[str] = None
    trend_review_recommended: bool = False
    acknowledgment_count: Optional[int] = None
    latest_acknowledgment_id: Optional[str] = None
    latest_acknowledgment_created_at: Optional[str] = None
    latest_acknowledgment_operator: Optional[str] = None
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggested_action: Optional[str] = None
    suggested_command: Optional[str] = None
    schema_version: Optional[str] = None
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_status_rollup_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_status_rollup_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusCompact


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryCompact(BaseModel):
    available: bool = False
    history_count: int = 0
    latest_rollup_status: Optional[str] = None
    latest_acknowledgment_status: Optional[str] = None
    latest_coverage_change: Optional[str] = None
    latest_recorded_at: Optional[str] = None
    recent_entries: list[dict[str, Any]] = Field(default_factory=list)
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    suggested_command: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_status_history_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_status_history_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryCompact
    entries: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    max_entries: int = 25


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintCompact(BaseModel):
    available: bool = False
    hint_status: Optional[str] = None
    hint_reason: Optional[str] = None
    trend: Optional[str] = None
    trend_review_recommended: bool = False
    history_count: Optional[int] = None
    worsened_count: Optional[int] = None
    improved_count: Optional[int] = None
    unchanged_count: Optional[int] = None
    current_needs_ack_streak: Optional[int] = None
    current_stale_streak: Optional[int] = None
    latest_rollup_status: Optional[str] = None
    recurring_signals: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggested_action: Optional[str] = None
    suggested_command: Optional[str] = None
    schema_version: Optional[str] = None
    json_path: Optional[str] = None
    markdown_path: Optional[str] = None
    next_phase_recommendation: Optional[str] = None
    verified_mrms: bool = False
    local_trend_hint_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    prototype: bool = True


class MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_trend_hint_only: bool = True
    advisory_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    does_not_download_or_decode: bool = True
    does_not_create_production_tiles: bool = True
    does_not_serve_production_tiles: bool = True
    does_not_delete_by_default: bool = True
    binary_artifacts_included: bool = False
    no_external_notifications: bool = True
    does_not_authorize_production_use: bool = True
    latest: dict[str, Any] = Field(default_factory=dict)
    compact: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintCompact


class ScheduledOperatorStatusCompact(BaseModel):
    operator_status_requested: bool = False
    operator_status_generated: bool = False
    operator_status_level: Optional[str] = None
    operator_status_reason: Optional[str] = None
    operator_status_top_recommended_action: Optional[str] = None
    operator_status_top_suggested_command: Optional[str] = None
    operator_status_evidence_trend: Optional[str] = None
    operator_status_elapsed_seconds: Optional[float] = None
    operator_status_error: Optional[str] = None
    verified_mrms: bool = False
    local_status_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class OperatorReviewStatusResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_status_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    status: OperatorReviewStatusCompact


class OperatorWorkflowPresetGroupEntryCompact(BaseModel):
    preset_id: str
    title: str
    recommended: bool = False
    recommended_priority: Optional[int] = None
    short_reason: Optional[str] = None
    priority: int = 999


class OperatorWorkflowPresetGroupCompact(BaseModel):
    group_id: str
    group_title: Optional[str] = None
    preset_count: int = 0
    recommended_count: int = 0
    presets: list[OperatorWorkflowPresetGroupEntryCompact] = Field(default_factory=list)
    verified_mrms: bool = False
    local_workflow_only: bool = True
    prototype: bool = True


class OperatorWorkflowPresetCompact(BaseModel):
    preset_id: str
    title: str
    description: str
    when_to_use: str
    command: str
    expected_outputs: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    recommended: bool = False
    recommendation_reason: Optional[str] = None
    group_id: Optional[str] = None
    group_title: Optional[str] = None
    priority: int = 999
    recommended_priority: Optional[int] = None
    short_reason: Optional[str] = None
    runbook_path: Optional[str] = None
    runbook_section: Optional[str] = None
    runbook_anchor: Optional[str] = None
    suggested_action: Optional[str] = None
    verified_mrms: bool = False
    local_workflow_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class OperatorWorkflowPresetsCompact(BaseModel):
    available: bool = True
    recommended_count: int = 0
    presets: list[OperatorWorkflowPresetCompact] = Field(default_factory=list)
    operator_workflow_preset_groups: list[OperatorWorkflowPresetGroupCompact] = Field(
        default_factory=list
    )
    verified_mrms: bool = False
    local_workflow_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class OperatorWorkflowPresetsResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_workflow_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    recommended_count: int = 0
    presets: list[OperatorWorkflowPresetCompact] = Field(default_factory=list)
    recommended_presets: list[OperatorWorkflowPresetCompact] = Field(default_factory=list)
    operator_workflow_preset_groups: list[OperatorWorkflowPresetGroupCompact] = Field(
        default_factory=list
    )


class MrmsReviewSessionExportResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_export_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    latest: Optional[dict[str, Any]] = None
    count: int = 0
    max_entries: int = 25
    entries: list[dict[str, Any]] = Field(default_factory=list)
    compact: MrmsReviewSessionExportCompact
    regeneration_hint: ReviewExportRegenerationHintCompact


class MrmsReviewSessionExportHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_export_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    count: int = 0
    max_entries: int = 25
    latest: Optional[dict[str, Any]] = None
    entries: list[dict[str, Any]] = Field(default_factory=list)
    compact: MrmsReviewSessionExportCompact
    regeneration_hint: ReviewExportRegenerationHintCompact


class MrmsReviewSessionExportDiffCompact(BaseModel):
    available: bool = False
    overall_export_diff_status: Optional[str] = None
    compared_at: Optional[str] = None
    latest_export_created_at: Optional[str] = None
    baseline_export_created_at: Optional[str] = None
    session_changed: bool = False
    open_attention_count_change: Optional[dict[str, Any]] = None
    improvements: list[str] = Field(default_factory=list)
    regressions: list[str] = Field(default_factory=list)
    history_count: int = 0
    verified_mrms: bool = False
    local_export_diff_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class MrmsReviewSessionExportDiffResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_export_diff_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    latest: Optional[dict[str, Any]] = None
    count: int = 0
    max_entries: int = 25
    entries: list[dict[str, Any]] = Field(default_factory=list)
    compact: MrmsReviewSessionExportDiffCompact


class MrmsReviewSessionExportDiffHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_export_diff_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    count: int = 0
    max_entries: int = 25
    latest: Optional[dict[str, Any]] = None
    entries: list[dict[str, Any]] = Field(default_factory=list)
    compact: MrmsReviewSessionExportDiffCompact


class MrmsReviewSessionExportDiffTrendCompact(BaseModel):
    available: bool = False
    total_diffs: int = 0
    latest_status: Optional[str] = None
    latest_at: Optional[str] = None
    last_worsened_at: Optional[str] = None
    last_improved_at: Optional[str] = None
    last_mixed_at: Optional[str] = None
    last_unchanged_at: Optional[str] = None
    worsened_count: int = 0
    improved_count: int = 0
    mixed_count: int = 0
    unchanged_count: int = 0
    no_baseline_count: int = 0
    current_worsened_streak: int = 0
    current_improved_streak: int = 0
    current_mixed_or_worsened_streak: int = 0
    longest_worsened_streak: int = 0
    longest_mixed_or_worsened_streak: int = 0
    trend: str = "no_data"
    window_size: int = 10
    history_count: int = 0
    suggested_next_action: Optional[str] = None
    verified_mrms: bool = False
    local_trend_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class MrmsReviewSessionExportDiffTrendResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_trend_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    trend: MrmsReviewSessionExportDiffTrendCompact


class MrmsReviewSessionExportDiffTrendHintCompact(BaseModel):
    available: bool = True
    review_trend_regeneration_recommended: bool = False
    reason: Optional[str] = None
    suggested_command: Optional[str] = None
    trend: str = "no_data"
    latest_export_diff_status: Optional[str] = None
    current_mixed_or_worsened_streak: int = 0
    current_worsened_streak: int = 0
    latest_review_session_id: Optional[str] = None
    latest_export_session_id: Optional[str] = None
    export_is_stale: bool = False
    latest_session_at: Optional[str] = None
    latest_export_at: Optional[str] = None
    digest_regeneration_recommended: bool = False
    session_summary_available: bool = False
    verified_mrms: bool = False
    local_hint_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class MrmsReviewSessionExportDiffTrendHintResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_hint_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    hint: MrmsReviewSessionExportDiffTrendHintCompact


class MrmsReviewSessionExportDiffHistoryEntryCompact(BaseModel):
    created_at: Optional[str] = None
    overall_export_diff_status: Optional[str] = None
    latest_session_id: Optional[str] = None
    baseline_session_id: Optional[str] = None
    session_changed: bool = False
    open_attention_count_change: Optional[dict[str, Any]] = None
    comparison_status_change: Optional[dict[str, Any]] = None
    escalation_level_change: Optional[dict[str, Any]] = None
    digest_regeneration_recommended_change: Optional[dict[str, Any]] = None
    improvements_count: int = 0
    regressions_count: int = 0
    verified_mrms: bool = False
    local_export_diff_history_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class MrmsReviewSessionExportDiffHistorySummaryCompact(BaseModel):
    available: bool = False
    count: int = 0
    max_entries: int = 25
    latest_status: Optional[str] = None
    latest_created_at: Optional[str] = None
    latest: Optional[MrmsReviewSessionExportDiffHistoryEntryCompact] = None
    recent: list[MrmsReviewSessionExportDiffHistoryEntryCompact] = Field(default_factory=list)
    verified_mrms: bool = False
    local_export_diff_history_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class MrmsProofHistoryEntryCompact(BaseModel):
    generated_at: Optional[str] = None
    overall_status: str = "not_started"
    source_mode: Optional[str] = None
    frame_count: int = 0
    criteria_counts: MrmsProofCriteriaCounts = Field(default_factory=MrmsProofCriteriaCounts)
    operator_review_required: bool = True
    proof_only: bool = True
    verified_mrms: bool = False
    prototype: bool = True


class MrmsProofHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    proof_only: bool = True
    operator_review_required: bool = True
    count: int = 0
    max_entries: int = 10
    latest: Optional[MrmsProofCompact] = None
    entries: list[MrmsProofHistoryEntryCompact] = Field(default_factory=list)


class MrmsProofRegressionHistoryEntryCompact(BaseModel):
    checked_at: Optional[str] = None
    regression_status: str = "inconclusive"
    regression_detected: bool = False
    regression_count: int = 0
    summary: str = ""
    verified_mrms: bool = False
    prototype: bool = True


class MrmsProofRegressionHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    count: int = 0
    max_entries: int = 10
    latest: Optional[MrmsProofRegressionCompact] = None
    entries: list[MrmsProofRegressionHistoryEntryCompact] = Field(default_factory=list)


class MrmsSignoffItemCompact(BaseModel):
    signoff_id: Optional[str] = None
    created_at: Optional[str] = None
    operator_name: Optional[str] = None
    operator_initials: Optional[str] = None
    operator: Optional[str] = None
    proof_report_timestamp: Optional[str] = None
    frame_count_reviewed: int = 0
    accepted_limitations: Optional[str] = None
    verified_mrms: bool = False
    does_not_set_verified_mrms: bool = True
    local_signoff_only: bool = True
    prototype: bool = True


class MrmsSignoffsResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_signoff_only: bool = True
    does_not_set_verified_mrms: bool = True
    count: int = 0
    entries: list[MrmsSignoffItemCompact] = Field(default_factory=list)


class ScheduledProofStepCompact(BaseModel):
    ran: bool = False
    proof_requested: bool = False
    status: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    proof_regression_status: Optional[str] = None
    proof_regression_detected: bool = False
    verified_mrms: bool = False
    prototype: bool = True


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
    proof_step: Optional[ScheduledProofStepCompact] = None
    verified_mrms: bool = False
    prototype: bool = True


class ScheduledValidationHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    count: int = 0
    max_entries: int = 10
    latest: Optional[dict[str, Any]] = None
    entries: list[dict[str, Any]] = Field(default_factory=list)


class MrmsProofBundleCompact(BaseModel):
    available: bool = False
    bundle_id: Optional[str] = None
    created_at: Optional[str] = None
    bundle_folder: Optional[str] = None
    zip_path: Optional[str] = None
    file_count: int = 0
    files_missing_count: int = 0
    bundle_count: int = 0
    include_history: bool = False
    verified_mrms: bool = False
    local_bundle_only: bool = True
    proof_only: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class RunbookReferenceCompact(BaseModel):
    title: str
    path: str
    anchor: str = ""


class MrmsProofBundlesResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_bundle_only: bool = True
    proof_only: bool = True
    count: int = 0
    latest: Optional[MrmsProofBundleCompact] = None
    entries: list[dict[str, Any]] = Field(default_factory=list)
    runbook_references: list[RunbookReferenceCompact] = Field(default_factory=list)


class MrmsProofBundleDiffCompact(BaseModel):
    available: bool = False
    diff_id: Optional[str] = None
    checked_at: Optional[str] = None
    overall_diff_status: str = "unknown"
    evidence_changes_count: int = 0
    has_baseline: bool = False
    current_bundle_id: Optional[str] = None
    baseline_bundle_id: Optional[str] = None
    verified_mrms: bool = False
    local_diff_only: bool = True
    proof_only: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class MrmsProofBundleDiffResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_diff_only: bool = True
    proof_only: bool = True
    report: Optional[dict[str, Any]] = None


class ProofBundleDiffAlertEntryCompact(BaseModel):
    created_at: Optional[str] = None
    diff_status: Optional[str] = None
    operator_attention_needed: bool = False
    evidence_changes_count: int = 0
    bundle_id: Optional[str] = None
    baseline_bundle_id: Optional[str] = None
    suggested_next_action: Optional[str] = None
    guidance_cause: Optional[str] = None
    verified_mrms: bool = False
    local_history_only: bool = True
    prototype: bool = True


class ProofBundleDiffAlertCompact(BaseModel):
    available: bool = False
    count: int = 0
    created_at: Optional[str] = None
    diff_status: Optional[str] = None
    operator_attention_needed: bool = False
    evidence_changes_count: int = 0
    bundle_id: Optional[str] = None
    baseline_bundle_id: Optional[str] = None
    suggested_next_action: Optional[str] = None
    guidance_cause: Optional[str] = None
    verified_mrms: bool = False
    local_history_only: bool = True
    prototype: bool = True


class ProofBundleDiffAlertHistoryResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_history_only: bool = True
    count: int = 0
    max_entries: int = 25
    latest: Optional[ProofBundleDiffAlertEntryCompact] = None
    entries: list[ProofBundleDiffAlertEntryCompact] = Field(default_factory=list)


class ProofBundleDiffAlertTrendCompact(BaseModel):
    available: bool = False
    latest_status: Optional[str] = None
    latest_at: Optional[str] = None
    last_worsened_at: Optional[str] = None
    last_mixed_at: Optional[str] = None
    last_improved_at: Optional[str] = None
    last_unchanged_at: Optional[str] = None
    current_attention_streak: int = 0
    current_non_attention_streak: int = 0
    recent_worsened_count: int = 0
    recent_mixed_count: int = 0
    recent_improved_count: int = 0
    recent_unchanged_count: int = 0
    trend: str = "no_data"
    window_size: int = 10
    history_count: int = 0
    suggested_next_action: Optional[str] = None
    verified_mrms: bool = False
    local_trend_only: bool = True
    prototype: bool = True


class ProofBundleDiffAlertTrendResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_trend_only: bool = True
    trend: ProofBundleDiffAlertTrendCompact


class ProofBundleDiffAcknowledgmentCompact(BaseModel):
    available: bool = False
    count: int = 0
    acknowledgment_id: Optional[str] = None
    created_at: Optional[str] = None
    operator: Optional[str] = None
    operator_name: Optional[str] = None
    operator_initials: Optional[str] = None
    note: Optional[str] = None
    related_diff_status: Optional[str] = None
    related_bundle_id: Optional[str] = None
    related_baseline_bundle_id: Optional[str] = None
    acknowledged_attention: bool = False
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class ProofBundleDiffAcknowledgmentCreateRequest(BaseModel):
    operator_name: Optional[str] = None
    operator_initials: Optional[str] = None
    note: str = ""
    related_diff_status: Optional[str] = None
    related_bundle_id: Optional[str] = None
    related_baseline_bundle_id: Optional[str] = None
    acknowledged_attention: Optional[bool] = None


class ProofBundleDiffAcknowledgmentCreateResponse(BaseModel):
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    production_enabled: bool = False
    diff_alert_still_active: bool = False
    acknowledgment: dict[str, Any]


class ProofBundleDiffAcknowledgmentsResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_acknowledgment_only: bool = True
    does_not_clear_alerts: bool = True
    count: int = 0
    max_entries: int = 50
    latest: Optional[ProofBundleDiffAcknowledgmentCompact] = None
    entries: list[ProofBundleDiffAcknowledgmentCompact] = Field(default_factory=list)


class ScheduledDigestCompact(BaseModel):
    digest_requested: bool = False
    digest_generated: bool = False
    digest_path: Optional[str] = None
    digest_metadata_path: Optional[str] = None
    digest_reason: Optional[str] = None
    digest_elapsed_seconds: Optional[float] = None
    verified_mrms: bool = False
    local_digest_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class ScheduledReviewExportCompact(BaseModel):
    review_export_requested: bool = False
    review_export_generated: bool = False
    review_export_path: Optional[str] = None
    review_export_metadata_path: Optional[str] = None
    review_export_reason: Optional[str] = None
    review_export_elapsed_seconds: Optional[float] = None
    review_export_trend_hint: Optional[MrmsReviewSessionExportDiffTrendHintCompact] = None
    verified_mrms: bool = False
    local_export_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    no_external_notifications: bool = True
    prototype: bool = True


class OperatorHandoffCompact(BaseModel):
    available: bool = False
    created_at: Optional[str] = None
    markdown_path: Optional[str] = None
    json_path: Optional[str] = None
    question_count: int = 0
    diff_status: Optional[str] = None
    auto_generated: bool = False
    trigger_reason: Optional[str] = None
    handoff_requested: bool = False
    handoff_generated: bool = False
    handoff_reason: Optional[str] = None
    scheduled_handoff_path: Optional[str] = None
    diff_status_that_triggered_handoff: Optional[str] = None
    include_escalation_review: bool = False
    digest_path: Optional[str] = None
    digest_metadata_path: Optional[str] = None
    acknowledgment_status: Optional[str] = None
    stale_acknowledgment: Optional[bool] = None
    escalation_level: Optional[str] = None
    review_checklist_count: int = 0
    verified_mrms: bool = False
    local_handoff_only: bool = True
    does_not_enable_production: bool = True
    prototype: bool = True


class OperatorHandoffResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_handoff_only: bool = True
    does_not_enable_production: bool = True
    handoff: Optional[dict[str, Any]] = None


class ScheduledProofBundleCompact(BaseModel):
    bundle_exported: bool = False
    bundle_id: Optional[str] = None
    bundle_created_at: Optional[str] = None
    diff_ran: bool = False
    diff_status: Optional[str] = None
    evidence_changes_count: int = 0
    operator_attention_needed: bool = False
    handoff_requested: bool = False
    handoff_generated: bool = False
    handoff_path: Optional[str] = None
    handoff_reason: Optional[str] = None
    diff_status_that_triggered_handoff: Optional[str] = None
    verified_mrms: bool = False
    local_evidence_monitoring_only: bool = True
    prototype: bool = True


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
    scheduled_proof_bundle: Optional[ScheduledProofBundleCompact] = None
    scheduled_digest: Optional[ScheduledDigestCompact] = None
    scheduled_review_export: Optional[ScheduledReviewExportCompact] = None
    scheduled_visual_review: Optional[ScheduledVisualReviewCompact] = None
    validation_failures_count: int = 0
    validation_failures_recent: list[ValidationFailureCompact] = Field(default_factory=list)
    validation_alert: Optional[ValidationAlertCompact] = None
    grouped_failure_causes: list[GroupedFailureCauseCompact] = Field(default_factory=list)
    mrms_proof: Optional[MrmsProofCompact] = None
    mrms_proof_available: bool = False
    mrms_proof_regression: Optional[MrmsProofRegressionCompact] = None
    mrms_proof_regression_available: bool = False
    mrms_signoff: Optional[MrmsSignoffSummaryCompact] = None
    mrms_proof_bundle: Optional[MrmsProofBundleCompact] = None
    mrms_proof_bundle_diff: Optional[MrmsProofBundleDiffCompact] = None
    operator_handoff: Optional[OperatorHandoffCompact] = None
    operator_guidance: list[OperatorGuidanceItemCompact] = Field(default_factory=list)
    proof_bundle_diff_alert: Optional[ProofBundleDiffAlertCompact] = None
    proof_bundle_diff_alert_history: list[ProofBundleDiffAlertEntryCompact] = Field(
        default_factory=list
    )
    proof_bundle_diff_alert_trend: Optional[ProofBundleDiffAlertTrendCompact] = None
    proof_bundle_diff_acknowledgment: Optional[ProofBundleDiffAcknowledgmentCompact] = None
    proof_bundle_diff_escalation: Optional[ProofBundleDiffEscalationCompact] = None
    proof_bundle_diff_escalation_history: Optional[ProofBundleDiffEscalationHistoryCompact] = None
    proof_bundle_diff_escalation_metrics: Optional[ProofBundleDiffEscalationMetricsCompact] = None
    proof_bundle_diff_escalation_digest: Optional[ProofBundleDiffEscalationDigestCompact] = None
    proof_bundle_diff_escalation_digest_history: Optional[
        ProofBundleDiffEscalationDigestHistoryCompact
    ] = None
    proof_bundle_diff_escalation_digest_diff: Optional[
        ProofBundleDiffEscalationDigestDiffCompact
    ] = None
    digest_regeneration_hint: Optional[DigestRegenerationHintCompact] = None
    mrms_review_session: Optional[MrmsReviewSessionSummaryCompact] = None
    mrms_review_session_export: Optional[MrmsReviewSessionExportCompact] = None
    mrms_review_session_export_diff: Optional[MrmsReviewSessionExportDiffCompact] = None
    mrms_review_session_export_diff_trend: Optional[MrmsReviewSessionExportDiffTrendCompact] = None
    mrms_review_session_export_diff_trend_hint: Optional[MrmsReviewSessionExportDiffTrendHintCompact] = None
    mrms_review_session_export_diff_history: Optional[MrmsReviewSessionExportDiffHistorySummaryCompact] = None
    review_export_regeneration_hint: Optional[ReviewExportRegenerationHintCompact] = None
    operator_review_status: Optional[OperatorReviewStatusCompact] = None
    operator_workflow_presets: Optional[OperatorWorkflowPresetsCompact] = None
    mrms_visual_review: Optional[MrmsVisualReviewCompact] = None
    mrms_visual_review_comparison: Optional[MrmsVisualReviewComparisonCompact] = None
    mrms_visual_review_hint: Optional[MrmsVisualReviewHintCompact] = None
    mrms_visual_review_sample_set: Optional[MrmsVisualReviewSampleSetCompact] = None
    mrms_visual_review_sample_readiness: Optional[MrmsVisualReviewSampleReadinessCompact] = None
    mrms_render_candidate_preflight: Optional[MrmsRenderCandidatePreflightCompact] = None
    mrms_render_candidate_dry_run_plan: Optional[MrmsRenderCandidateDryRunPlanCompact] = None
    mrms_render_candidate_scaffold: Optional[MrmsRenderCandidateScaffoldCompact] = None
    mrms_render_candidate_sandbox: Optional[MrmsRenderCandidateSandboxCompact] = None
    mrms_render_candidate_sandbox_import_export: Optional[
        MrmsRenderCandidateSandboxImportExportCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_history: Optional[
        MrmsRenderCandidateSandboxComparisonHistoryCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_trend_hint: Optional[
        MrmsRenderCandidateSandboxComparisonTrendHintCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_review_acknowledgment: Optional[
        MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_acknowledgment_status: Optional[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_acknowledgment_status_history: Optional[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint: Optional[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment: Optional[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status: Optional[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_history: Optional[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_hint: Optional[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment: Optional[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status: Optional[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history: Optional[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint: Optional[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintCompact
    ] = None
    mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment: Optional[
        MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCompact
    ] = None
    scheduled_operator_status: Optional[ScheduledOperatorStatusCompact] = None
    runbook_references: list[RunbookReferenceCompact] = Field(default_factory=list)
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
    mrms_proof_regression: Optional[dict[str, Any]] = None
    mrms_signoffs: list[dict[str, Any]] = Field(default_factory=list)
    mrms_proof_bundle: Optional[dict[str, Any]] = None
    mrms_proof_bundle_diff: Optional[dict[str, Any]] = None
    operator_handoff: Optional[dict[str, Any]] = None
    proof_bundle_diff_alert_history: list[dict[str, Any]] = Field(default_factory=list)
    proof_bundle_diff_alert_trend: Optional[dict[str, Any]] = None
    proof_bundle_diff_acknowledgments: list[dict[str, Any]] = Field(default_factory=list)


class ValidationFailuresResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    count: int = 0
    max_entries: int = 100
    entries: list[ValidationFailureCompact] = Field(default_factory=list)
