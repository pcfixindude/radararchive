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


class MrmsReviewSessionCreateResponse(BaseModel):
    prototype: bool = True
    verified_mrms: bool = False
    local_review_only: bool = True
    does_not_clear_alerts: bool = True
    does_not_enable_production: bool = True
    production_enabled: bool = False
    review_session: dict[str, Any]


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
    review_export_regeneration_hint: Optional[ReviewExportRegenerationHintCompact] = None
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
