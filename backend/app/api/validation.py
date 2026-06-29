"""Dev/prototype validation dashboard API — not verified MRMS production."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas.validation import (
    MrmsProofBundleDiffResponse,
    MrmsProofBundlesResponse,
    MrmsProofHistoryResponse,
    ProofBundleDiffAcknowledgmentCreateRequest,
    ProofBundleDiffAcknowledgmentCreateResponse,
    ProofBundleDiffAcknowledgmentsResponse,
    ProofBundleDiffAlertHistoryResponse,
    ProofBundleDiffAlertTrendResponse,
    ProofBundleDiffEscalationResponse,
    ProofBundleDiffEscalationHistoryResponse,
    ProofBundleDiffEscalationMetricsResponse,
    ProofBundleDiffEscalationDigestResponse,
    ProofBundleDiffEscalationDigestHistoryResponse,
    ProofBundleDiffEscalationDigestDiffResponse,
    OperatorHandoffResponse,
    MrmsProofRegressionHistoryResponse,
    MrmsProofRegressionResponse,
    MrmsProofResponse,
    MrmsSignoffCreateRequest,
    MrmsSignoffCreateResponse,
    MrmsSignoffsResponse,
    MrmsReviewSessionCreateRequest,
    MrmsReviewSessionCreateResponse,
    MrmsReviewSessionsResponse,
    MrmsReviewSessionComparisonResponse,
    MrmsReviewSessionComparisonHistoryResponse,
    MrmsReviewSessionExportResponse,
    MrmsReviewSessionExportHistoryResponse,
    MrmsReviewSessionExportDiffResponse,
    MrmsReviewSessionExportDiffHistoryResponse,
    MrmsReviewSessionExportDiffTrendResponse,
    MrmsReviewSessionExportDiffTrendHintResponse,
    MrmsVisualReviewHistoryResponse,
    MrmsVisualReviewComparisonHistoryResponse,
    MrmsVisualReviewComparisonResponse,
    MrmsVisualReviewHintResponse,
    MrmsVisualReviewSampleSetCreateRequest,
    MrmsVisualReviewSampleSetCreateResponse,
    MrmsVisualReviewSampleSetResponse,
    MrmsVisualReviewSampleReadinessResponse,
    MrmsVisualReviewSampleAnnotationUpsertRequest,
    MrmsVisualReviewSampleAnnotationUpsertResponse,
    MrmsRenderCandidatePreflightResponse,
    MrmsRenderCandidateReviewReadinessResponse,
    MrmsRenderCandidatePreflightAttemptResponse,
    MrmsRenderCandidatePreflightBlockersResponse,
    MrmsRenderCandidateTrendHintChainBootstrapResponse,
    MrmsRenderCandidateDryRunPlanResponse,
    MrmsRenderCandidateScaffoldResponse,
    MrmsRenderCandidateSandboxResponse,
    MrmsRenderCandidateSandboxImportExportResponse,
    MrmsRenderCandidateSandboxImportRequest,
    MrmsRenderCandidateSandboxComparisonHistoryResponse,
    MrmsRenderCandidateSandboxComparisonTrendHintResponse,
    MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCreateRequest,
    MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCreateResponse,
    MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentsResponse,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusResponse,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryResponse,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintResponse,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCreateRequest,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentsResponse,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateRequest,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentsResponse,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse,
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse,
    MrmsRenderCandidateTrendHintAckStatusHistoryResponse,
    MrmsRenderCandidateTrendHintAckStatusResponse,
    MrmsRenderCandidateTrendHintReviewDigestHistoryResponse,
    MrmsRenderCandidateTrendHintReviewDigestDiffResponse,
    MrmsRenderCandidateTrendHintReviewDigestResponse,
    MrmsRenderCandidateTrendHintReviewAcknowledgmentCreateRequest,
    MrmsRenderCandidateTrendHintReviewAcknowledgmentCreateResponse,
    MrmsRenderCandidateTrendHintReviewAcknowledgmentsResponse,
    MrmsVisualReviewResponse,
    OperatorReviewStatusResponse,
    OperatorWorkflowPresetsResponse,
    QueueBenchmarkHistoryResponse,
    ScheduledValidationHistoryResponse,
    ValidationAlertsResponse,
    ValidationFailuresResponse,
    ValidationHistoryResponse,
    ValidationLatestResponse,
    ValidationSummaryResponse,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.mrms_proof_bundle import build_proof_bundles_list_payload
from backend.app.services.proof_bundle_diff_alert_history import (
    build_proof_bundle_diff_alert_history_payload,
)
from backend.app.services.mrms_proof_bundle_diff import (
    build_proof_bundle_diff_report,
    load_latest_proof_bundle_diff,
    proof_bundle_diff_requires_attention,
)
from backend.app.services.mrms_operator_handoff import load_latest_operator_handoff
from backend.app.services.proof_bundle_diff_acknowledgment import (
    DiffAcknowledgmentValidationError,
    build_diff_acknowledgments_payload,
    create_diff_acknowledgment,
)
from backend.app.services.proof_bundle_diff_alert_trends import (
    build_proof_bundle_diff_alert_trend_payload,
)
from backend.app.services.proof_bundle_diff_escalation import (
    build_proof_bundle_diff_escalation_payload,
)
from backend.app.services.proof_bundle_diff_escalation_history import (
    build_proof_bundle_diff_escalation_history_payload,
)
from backend.app.services.proof_bundle_diff_escalation_metrics import (
    build_proof_bundle_diff_escalation_metrics_payload,
)
from backend.app.services.proof_bundle_diff_escalation_digest import (
    build_proof_bundle_diff_escalation_digest_payload,
)
from backend.app.services.proof_bundle_diff_escalation_digest_diff import (
    build_digest_diff_payload,
)
from backend.app.services.proof_bundle_diff_escalation_digest_history import (
    build_digest_export_history_payload,
)
from backend.app.services.mrms_proof_history import (
    build_proof_history_payload,
    build_regression_history_payload,
    build_signoffs_list_payload,
)
from backend.app.services.mrms_proof_regression import load_proof_regression_report, run_proof_regression_check
from backend.app.services.mrms_signoff import SignoffValidationError, create_signoff_and_refresh_alert
from backend.app.services.mrms_review_session import (
    ReviewSessionValidationError,
    build_review_sessions_payload,
    create_review_session_record,
)
from backend.app.services.mrms_review_session_compare import (
    build_review_session_comparison_payload,
    record_review_session_comparison,
)
from backend.app.services.mrms_review_session_export import (
    build_review_session_export_payload,
    try_export_after_review_session_create,
)
from backend.app.services.mrms_review_session_export_diff import (
    build_review_session_export_diff_payload,
)
from backend.app.services.mrms_review_session_export_diff_trends import (
    build_review_session_export_diff_trend_payload,
)
from backend.app.services.mrms_review_session_export_diff_trend_hint import (
    build_review_session_export_diff_trend_hint_payload,
)
from backend.app.services.mrms_visual_review import (
    build_mrms_visual_review_history_payload,
    build_mrms_visual_review_payload,
)
from backend.app.services.mrms_visual_review_compare import (
    build_visual_review_comparison_history_payload,
    build_visual_review_comparison_payload,
)
from backend.app.services.mrms_visual_review_hint import build_visual_review_hint_payload
from backend.app.services.mrms_visual_review_sample_set import (
    build_visual_review_sample_set,
    build_visual_review_sample_set_payload,
)
from backend.app.services.mrms_visual_review_sample_readiness import (
    SampleAnnotationValidationError,
    build_visual_review_sample_readiness_payload,
    compact_visual_review_sample_readiness,
    refresh_visual_review_sample_readiness,
    upsert_sample_annotation,
)
from backend.app.services.mrms_render_candidate_preflight_blockers import (
    build_preflight_blockers_payload,
    resolve_preflight_blockers,
)
from backend.app.services.mrms_render_candidate_trend_hint_chain_bootstrap import (
    bootstrap_trend_hint_chain,
    build_trend_hint_chain_bootstrap_payload,
)
from backend.app.services.mrms_render_candidate_preflight_attempt import (
    attempt_gated_preflight,
    build_preflight_attempt_payload,
)
from backend.app.services.mrms_render_candidate_review_readiness import (
    build_candidate_review_readiness_payload,
    generate_candidate_review_readiness,
)
from backend.app.services.mrms_render_candidate_preflight import (
    build_render_candidate_preflight_payload,
    generate_render_candidate_preflight,
)
from backend.app.services.mrms_render_candidate_dry_run_plan import (
    build_render_candidate_dry_run_plan_payload,
    generate_render_candidate_dry_run_plan,
)
from backend.app.services.mrms_render_candidate_scaffold import (
    build_render_candidate_scaffold_payload,
    generate_render_candidate_scaffold,
)
from backend.app.services.mrms_render_candidate_sandbox import (
    build_render_candidate_sandbox_payload,
    generate_render_candidate_sandbox,
)
from backend.app.services.mrms_render_candidate_sandbox_import_export import (
    build_render_candidate_sandbox_import_export_payload,
    export_candidate_sandbox_manifest,
    import_candidate_sandbox_manifest,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_history import (
    build_comparison_history_payload,
    refresh_comparison_history_report,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_trend_hint import (
    build_sandbox_comparison_trend_hint,
    build_sandbox_comparison_trend_hint_payload,
    refresh_sandbox_comparison_trend_hint,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_review_acknowledgment import (
    SandboxComparisonReviewAcknowledgmentValidationError,
    build_sandbox_comparison_review_acknowledgments_payload,
    create_sandbox_comparison_review_acknowledgment,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status import (
    build_sandbox_comparison_acknowledgment_status_payload,
    refresh_sandbox_comparison_acknowledgment_status,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_history import (
    build_ack_status_history_payload,
    refresh_ack_status_history_report,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint import (
    build_ack_status_trend_hint,
    build_ack_status_trend_hint_payload,
    refresh_ack_status_trend_hint,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment import (
    AckStatusTrendReviewAcknowledgmentValidationError,
    build_ack_status_trend_review_acknowledgments_payload,
    create_ack_status_trend_review_acknowledgment,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status import (
    build_ack_status_trend_review_acknowledgment_status_payload,
    refresh_ack_status_trend_review_acknowledgment_status,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_history import (
    build_ack_status_trend_review_acknowledgment_status_history_payload,
    refresh_ack_status_trend_review_acknowledgment_status_history_report,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_hint import (
    build_ack_status_trend_review_acknowledgment_status_trend_hint,
    build_ack_status_trend_review_acknowledgment_status_trend_hint_payload,
    refresh_ack_status_trend_review_acknowledgment_status_trend_hint,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment import (
    AckStatusTrendReviewAckStatusTrendReviewAcknowledgmentValidationError,
    build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgments_payload,
    create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status import (
    build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_payload,
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history import (
    build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history_payload,
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history_report,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint import (
    build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint,
    build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint_payload,
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest_diff import (
    build_trend_hint_review_digest_diff_payload,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest_history import (
    build_trend_hint_review_digest_history_payload,
    refresh_trend_hint_review_digest_history_report,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest import (
    build_trend_hint_review_digest_payload,
    refresh_trend_hint_review_digest,
)
from backend.app.services.mrms_render_candidate_trend_hint_ack_status_history import (
    build_trend_hint_ack_status_history_payload,
    refresh_trend_hint_ack_status_history_report,
)
from backend.app.services.mrms_render_candidate_trend_hint_ack_status import (
    build_trend_hint_ack_status_payload,
    refresh_trend_hint_ack_status,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_acknowledgment import (
    TrendHintReviewAckValidationError,
    build_trend_hint_review_acknowledgments_payload,
    create_trend_hint_review_acknowledgment,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint import (
    build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint as build_candidate_trend_hint,
)
from backend.app.services.operator_review_status import build_operator_review_status_payload
from backend.app.services.operator_workflow_presets import build_operator_workflow_presets_payload
from backend.app.services.mrms_proof_report import load_mrms_proof_report
from backend.app.services.validation_alerts import (
    compact_validation_alert,
    load_validation_alert,
    refresh_validation_alert,
)
from backend.app.services.validation_dashboard import build_validation_latest, build_validation_summary
from backend.app.services.validation_failure_log import (
    MAX_FAILURE_ENTRIES,
    compact_failure,
    count_validation_failures,
    load_recent_validation_failures,
)
from backend.app.services.validation_report_store import (
    load_latest_queue_benchmark_report,
    load_latest_scheduled_validation_report,
    load_queue_benchmark_history,
    load_scheduled_validation_history,
    load_validation_history,
)

router = APIRouter(prefix="/validation", tags=["validation-dev"])


@router.get("/summary", response_model=ValidationSummaryResponse)
def validation_summary(db: Session = Depends(get_db)) -> ValidationSummaryResponse:
    """Compact validation + queue dashboard summary (dev/prototype)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_validation_summary(db, storage)
    return ValidationSummaryResponse(**payload)


@router.get("/latest", response_model=ValidationLatestResponse)
def validation_latest() -> ValidationLatestResponse:
    """Full latest persisted validation and benchmark reports (dev/prototype)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_validation_latest(storage)
    return ValidationLatestResponse(**payload)


@router.get("/history", response_model=ValidationHistoryResponse)
def validation_history() -> ValidationHistoryResponse:
    """Bounded validation history (dev/prototype, last 10)."""
    storage = LocalStorage(settings.local_storage_root)
    entries = load_validation_history(storage)
    return ValidationHistoryResponse(
        prototype=True,
        verified_mrms=False,
        count=len(entries),
        max_entries=10,
        entries=entries,
    )


@router.get("/benchmarks", response_model=QueueBenchmarkHistoryResponse)
def validation_benchmarks() -> QueueBenchmarkHistoryResponse:
    """Latest queue benchmark report and bounded history (dev/prototype)."""
    storage = LocalStorage(settings.local_storage_root)
    entries = load_queue_benchmark_history(storage)
    latest = load_latest_queue_benchmark_report(storage)
    return QueueBenchmarkHistoryResponse(
        prototype=True,
        verified_mrms=False,
        count=len(entries),
        max_entries=10,
        latest=latest,
        entries=entries,
    )


@router.get("/scheduled", response_model=ScheduledValidationHistoryResponse)
def validation_scheduled() -> ScheduledValidationHistoryResponse:
    """Latest scheduled validation run and bounded history (dev/prototype)."""
    storage = LocalStorage(settings.local_storage_root)
    entries = load_scheduled_validation_history(storage)
    latest = load_latest_scheduled_validation_report(storage)
    return ScheduledValidationHistoryResponse(
        prototype=True,
        verified_mrms=False,
        count=len(entries),
        max_entries=10,
        latest=latest,
        entries=entries,
    )


@router.get("/failures", response_model=ValidationFailuresResponse)
def validation_failures(limit: int = 10) -> ValidationFailuresResponse:
    """Recent validation failure log entries (dev/prototype, append-only JSONL)."""
    storage = LocalStorage(settings.local_storage_root)
    bounded_limit = max(1, min(limit, 25))
    entries = load_recent_validation_failures(storage, limit=bounded_limit)
    return ValidationFailuresResponse(
        prototype=True,
        verified_mrms=False,
        count=count_validation_failures(storage),
        max_entries=MAX_FAILURE_ENTRIES,
        entries=[compact_failure(item) for item in entries],
    )


@router.get("/alerts", response_model=ValidationAlertsResponse)
def validation_alerts(refresh: bool = False) -> ValidationAlertsResponse:
    """Latest validation alert marker and grouped failure causes (dev/prototype)."""
    storage = LocalStorage(settings.local_storage_root)
    if refresh:
        alert = refresh_validation_alert(storage)
    else:
        alert = load_validation_alert(storage)
        if alert is None:
            alert = refresh_validation_alert(storage)
    return ValidationAlertsResponse(
        prototype=True,
        verified_mrms=False,
        alert=alert,
    )


@router.get("/proof/history", response_model=MrmsProofHistoryResponse)
def validation_proof_history() -> MrmsProofHistoryResponse:
    """Bounded MRMS proof report history (dev/prototype, read-only)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_proof_history_payload(storage)
    return MrmsProofHistoryResponse(**payload)


@router.get("/proof", response_model=MrmsProofResponse)
def validation_proof() -> MrmsProofResponse:
    """Latest draft MRMS proof report (evidence only — not verified MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    report = load_mrms_proof_report(storage)
    return MrmsProofResponse(
        prototype=True,
        verified_mrms=False,
        proof_only=True,
        operator_review_required=True,
        report=report,
    )


@router.get("/proof-regression/history", response_model=MrmsProofRegressionHistoryResponse)
def validation_proof_regression_history() -> MrmsProofRegressionHistoryResponse:
    """Bounded MRMS proof regression history (dev/prototype, read-only)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_regression_history_payload(storage)
    return MrmsProofRegressionHistoryResponse(**payload)


@router.get("/proof-regression", response_model=MrmsProofRegressionResponse)
def validation_proof_regression(refresh: bool = False) -> MrmsProofRegressionResponse:
    """Latest MRMS proof regression report (dev/prototype)."""
    storage = LocalStorage(settings.local_storage_root)
    if refresh:
        report = run_proof_regression_check(storage)
        refresh_validation_alert(storage)
    else:
        report = load_proof_regression_report(storage)
    return MrmsProofRegressionResponse(
        prototype=True,
        verified_mrms=False,
        report=report,
    )


@router.get("/signoffs", response_model=MrmsSignoffsResponse)
def validation_signoffs(limit: int = 25) -> MrmsSignoffsResponse:
    """Local operator sign-off records (read-only; does not set verified_mrms)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_signoffs_list_payload(storage, limit=limit)
    return MrmsSignoffsResponse(**payload)


@router.post("/signoffs", response_model=MrmsSignoffCreateResponse)
def validation_signoffs_create(body: MrmsSignoffCreateRequest) -> MrmsSignoffCreateResponse:
    """Dev/local only — record operator proof review; does NOT verify MRMS or enable production."""
    storage = LocalStorage(settings.local_storage_root)
    try:
        record, alert = create_signoff_and_refresh_alert(
            storage,
            operator_name=body.operator_name,
            operator_initials=body.operator_initials,
            operator_notes=body.operator_notes,
            accepted_limitations=body.accepted_limitations,
            proof_report_timestamp=body.proof_report_timestamp,
            frame_count_reviewed=body.frame_count_reviewed,
        )
    except SignoffValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return MrmsSignoffCreateResponse(
        verified_mrms=False,
        local_signoff_only=True,
        does_not_enable_production=True,
        production_enabled=settings.enable_production_radar_tiles,
        proof_regression_still_active=bool(record.get("proof_regression_still_active_after_signoff")),
        signoff=record,
        alert=compact_validation_alert(alert),
    )


@router.get("/operator-review-status", response_model=OperatorReviewStatusResponse)
def validation_operator_review_status() -> OperatorReviewStatusResponse:
    """Consolidated local operator review status (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_operator_review_status_payload(storage)
    return OperatorReviewStatusResponse(**payload)


@router.get("/operator-workflow-presets", response_model=OperatorWorkflowPresetsResponse)
def validation_operator_workflow_presets() -> OperatorWorkflowPresetsResponse:
    """Local operator workflow presets (read-only guidance; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_operator_workflow_presets_payload(storage)
    return OperatorWorkflowPresetsResponse(**payload)


@router.get("/mrms-render-candidate/preflight", response_model=MrmsRenderCandidatePreflightResponse)
def validation_mrms_render_candidate_preflight() -> MrmsRenderCandidatePreflightResponse:
    """Local MRMS render candidate preflight (read-only advisory; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_render_candidate_preflight_payload(storage)
    return MrmsRenderCandidatePreflightResponse(**payload)


@router.post("/mrms-render-candidate/preflight", response_model=MrmsRenderCandidatePreflightResponse)
def validation_mrms_render_candidate_preflight_refresh() -> MrmsRenderCandidatePreflightResponse:
    """Dev/local only — regenerate render candidate preflight report; does NOT verify MRMS."""
    storage = LocalStorage(settings.local_storage_root)
    generate_render_candidate_preflight(storage)
    payload = build_render_candidate_preflight_payload(storage)
    return MrmsRenderCandidatePreflightResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/review-readiness",
    response_model=MrmsRenderCandidateReviewReadinessResponse,
)
def validation_mrms_render_candidate_review_readiness() -> MrmsRenderCandidateReviewReadinessResponse:
    """Local candidate trend-hint review chain readiness summary (does not clear alerts)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_candidate_review_readiness_payload(storage)
    return MrmsRenderCandidateReviewReadinessResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/review-readiness",
    response_model=MrmsRenderCandidateReviewReadinessResponse,
)
def validation_mrms_render_candidate_review_readiness_refresh() -> (
    MrmsRenderCandidateReviewReadinessResponse
):
    """Dev/local only — refresh review readiness summary; does NOT clear alerts."""
    storage = LocalStorage(settings.local_storage_root)
    generate_candidate_review_readiness(storage)
    payload = build_candidate_review_readiness_payload(storage)
    return MrmsRenderCandidateReviewReadinessResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/preflight-attempt",
    response_model=MrmsRenderCandidatePreflightAttemptResponse,
)
def validation_mrms_render_candidate_preflight_attempt() -> MrmsRenderCandidatePreflightAttemptResponse:
    """Latest gated preflight attempt (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_preflight_attempt_payload(storage)
    return MrmsRenderCandidatePreflightAttemptResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/preflight-attempt",
    response_model=MrmsRenderCandidatePreflightAttemptResponse,
)
def validation_mrms_render_candidate_preflight_attempt_run() -> (
    MrmsRenderCandidatePreflightAttemptResponse
):
    """Dev/local only — gated preflight attempt; does NOT clear alerts or enable production."""
    storage = LocalStorage(settings.local_storage_root)
    attempt_gated_preflight(storage)
    payload = build_preflight_attempt_payload(storage)
    return MrmsRenderCandidatePreflightAttemptResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/preflight-blockers",
    response_model=MrmsRenderCandidatePreflightBlockersResponse,
)
def validation_mrms_render_candidate_preflight_blockers() -> (
    MrmsRenderCandidatePreflightBlockersResponse
):
    """Latest preflight blocker resolution report (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_preflight_blockers_payload(storage)
    return MrmsRenderCandidatePreflightBlockersResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/preflight-blockers",
    response_model=MrmsRenderCandidatePreflightBlockersResponse,
)
def validation_mrms_render_candidate_preflight_blockers_resolve() -> (
    MrmsRenderCandidatePreflightBlockersResponse
):
    """Dev/local only — run blocker resolution flow; does NOT force preflight when gated."""
    storage = LocalStorage(settings.local_storage_root)
    resolve_preflight_blockers(storage)
    payload = build_preflight_blockers_payload(storage)
    return MrmsRenderCandidatePreflightBlockersResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/trend-hint-chain-bootstrap",
    response_model=MrmsRenderCandidateTrendHintChainBootstrapResponse,
)
def validation_mrms_render_candidate_trend_hint_chain_bootstrap() -> (
    MrmsRenderCandidateTrendHintChainBootstrapResponse
):
    """Latest trend-hint chain bootstrap report (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_trend_hint_chain_bootstrap_payload(storage)
    return MrmsRenderCandidateTrendHintChainBootstrapResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/trend-hint-chain-bootstrap",
    response_model=MrmsRenderCandidateTrendHintChainBootstrapResponse,
)
def validation_mrms_render_candidate_trend_hint_chain_bootstrap_run() -> (
    MrmsRenderCandidateTrendHintChainBootstrapResponse
):
    """Dev/local only — seed comparison history and refresh trend-hint chain; does NOT force preflight."""
    storage = LocalStorage(settings.local_storage_root)
    bootstrap_trend_hint_chain(storage)
    payload = build_trend_hint_chain_bootstrap_payload(storage)
    return MrmsRenderCandidateTrendHintChainBootstrapResponse(**payload)


@router.get(
    "/mrms-render-candidate/dry-run-plan",
    response_model=MrmsRenderCandidateDryRunPlanResponse,
)
def validation_mrms_render_candidate_dry_run_plan() -> MrmsRenderCandidateDryRunPlanResponse:
    """Local MRMS render candidate dry-run plan (read-only advisory; does not execute steps)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_render_candidate_dry_run_plan_payload(storage)
    return MrmsRenderCandidateDryRunPlanResponse(**payload)


@router.post(
    "/mrms-render-candidate/dry-run-plan",
    response_model=MrmsRenderCandidateDryRunPlanResponse,
)
def validation_mrms_render_candidate_dry_run_plan_refresh() -> MrmsRenderCandidateDryRunPlanResponse:
    """Dev/local only — regenerate render candidate dry-run plan; does NOT download/decode/render."""
    storage = LocalStorage(settings.local_storage_root)
    generate_render_candidate_dry_run_plan(storage)
    payload = build_render_candidate_dry_run_plan_payload(storage)
    return MrmsRenderCandidateDryRunPlanResponse(**payload)


@router.get(
    "/mrms-render-candidate/scaffold",
    response_model=MrmsRenderCandidateScaffoldResponse,
)
def validation_mrms_render_candidate_scaffold() -> MrmsRenderCandidateScaffoldResponse:
    """Local MRMS render candidate scaffold (read-only advisory; disabled by default)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_render_candidate_scaffold_payload(storage)
    return MrmsRenderCandidateScaffoldResponse(**payload)


@router.post(
    "/mrms-render-candidate/scaffold",
    response_model=MrmsRenderCandidateScaffoldResponse,
)
def validation_mrms_render_candidate_scaffold_refresh() -> MrmsRenderCandidateScaffoldResponse:
    """Dev/local only — regenerate render candidate scaffold; does NOT download/decode/render."""
    storage = LocalStorage(settings.local_storage_root)
    generate_render_candidate_scaffold(storage)
    payload = build_render_candidate_scaffold_payload(storage)
    return MrmsRenderCandidateScaffoldResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox",
    response_model=MrmsRenderCandidateSandboxResponse,
)
def validation_mrms_render_candidate_sandbox() -> MrmsRenderCandidateSandboxResponse:
    """Local MRMS render candidate sandbox status (read-only advisory; local-only)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_render_candidate_sandbox_payload(storage)
    return MrmsRenderCandidateSandboxResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox",
    response_model=MrmsRenderCandidateSandboxResponse,
)
def validation_mrms_render_candidate_sandbox_refresh() -> MrmsRenderCandidateSandboxResponse:
    """Dev/local only — create/validate sandbox layout and regenerate report; does NOT delete by default."""
    storage = LocalStorage(settings.local_storage_root)
    generate_render_candidate_sandbox(storage)
    payload = build_render_candidate_sandbox_payload(storage)
    return MrmsRenderCandidateSandboxResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/import-export",
    response_model=MrmsRenderCandidateSandboxImportExportResponse,
)
def validation_mrms_render_candidate_sandbox_import_export() -> MrmsRenderCandidateSandboxImportExportResponse:
    """Local MRMS render candidate sandbox import/export status (read-only advisory)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_render_candidate_sandbox_import_export_payload(storage)
    return MrmsRenderCandidateSandboxImportExportResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/import-export/export",
    response_model=MrmsRenderCandidateSandboxImportExportResponse,
)
def validation_mrms_render_candidate_sandbox_export() -> MrmsRenderCandidateSandboxImportExportResponse:
    """Dev/local only — export sandbox manifest metadata; does NOT include binary artifacts."""
    storage = LocalStorage(settings.local_storage_root)
    export_candidate_sandbox_manifest(storage)
    payload = build_render_candidate_sandbox_import_export_payload(storage)
    return MrmsRenderCandidateSandboxImportExportResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/import-export/import",
    response_model=MrmsRenderCandidateSandboxImportExportResponse,
)
def validation_mrms_render_candidate_sandbox_import(
    request: MrmsRenderCandidateSandboxImportRequest = MrmsRenderCandidateSandboxImportRequest(),
) -> MrmsRenderCandidateSandboxImportExportResponse:
    """Dev/local only — validate/import exported sandbox manifest metadata."""
    storage = LocalStorage(settings.local_storage_root)
    import_path = request.import_json_path
    import_candidate_sandbox_manifest(storage, source_json_path=import_path)
    payload = build_render_candidate_sandbox_import_export_payload(storage)
    return MrmsRenderCandidateSandboxImportExportResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/import-export/comparison-history",
    response_model=MrmsRenderCandidateSandboxComparisonHistoryResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_history() -> (
    MrmsRenderCandidateSandboxComparisonHistoryResponse
):
    """Local MRMS render candidate sandbox comparison history (read-only advisory)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_comparison_history_payload(storage)
    return MrmsRenderCandidateSandboxComparisonHistoryResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/import-export/comparison-history",
    response_model=MrmsRenderCandidateSandboxComparisonHistoryResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_history_refresh() -> (
    MrmsRenderCandidateSandboxComparisonHistoryResponse
):
    """Dev/local only — refresh sandbox comparison history summary report."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_comparison_history_report(storage)
    payload = build_comparison_history_payload(storage)
    return MrmsRenderCandidateSandboxComparisonHistoryResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/import-export/comparison-trend-hint",
    response_model=MrmsRenderCandidateSandboxComparisonTrendHintResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_trend_hint() -> (
    MrmsRenderCandidateSandboxComparisonTrendHintResponse
):
    """Local MRMS render candidate sandbox comparison trend hint (read-only advisory)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_sandbox_comparison_trend_hint_payload(storage)
    return MrmsRenderCandidateSandboxComparisonTrendHintResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/import-export/comparison-trend-hint",
    response_model=MrmsRenderCandidateSandboxComparisonTrendHintResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_trend_hint_refresh() -> (
    MrmsRenderCandidateSandboxComparisonTrendHintResponse
):
    """Dev/local only — refresh sandbox comparison trend hint report."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_sandbox_comparison_trend_hint(storage)
    payload = build_sandbox_comparison_trend_hint_payload(storage)
    return MrmsRenderCandidateSandboxComparisonTrendHintResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/import-export/comparison-review-acknowledgments",
    response_model=MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentsResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_review_acknowledgments(
    limit: int = 25,
) -> MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentsResponse:
    """Bounded local sandbox comparison trend hint review acknowledgments (does not clear alerts)."""
    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(limit, 50))
    payload = build_sandbox_comparison_review_acknowledgments_payload(storage, limit=bounded)
    return MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentsResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/import-export/comparison-review-acknowledgments",
    response_model=MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCreateResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_review_acknowledgments_create(
    body: MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCreateRequest,
) -> MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCreateResponse:
    """Dev/local only — record sandbox comparison review acknowledgment; does NOT clear alerts."""
    storage = LocalStorage(settings.local_storage_root)
    try:
        record = create_sandbox_comparison_review_acknowledgment(
            storage,
            operator_name=body.operator_name,
            operator_initials=body.operator_initials,
            note=body.note,
            related_trend=body.related_trend,
            related_hint_status=body.related_hint_status,
            related_hint_reason=body.related_hint_reason,
            related_trend_review_recommended=body.related_trend_review_recommended,
            acknowledged_trend_review=body.acknowledged_trend_review,
        )
    except SandboxComparisonReviewAcknowledgmentValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    hint = build_sandbox_comparison_trend_hint(storage)
    return MrmsRenderCandidateSandboxComparisonReviewAcknowledgmentCreateResponse(
        verified_mrms=False,
        local_acknowledgment_only=True,
        does_not_clear_alerts=True,
        does_not_enable_production=True,
        does_not_authorize_production_use=True,
        production_enabled=settings.enable_production_radar_tiles,
        trend_review_still_recommended=bool(hint.get("trend_review_recommended")),
        acknowledgment=record,
    )


@router.get(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusResponse
):
    """Local sandbox comparison acknowledgment status rollup (read-only advisory)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_sandbox_comparison_acknowledgment_status_payload(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_refresh() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusResponse
):
    """Dev/local only — refresh sandbox comparison acknowledgment status rollup."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_sandbox_comparison_acknowledgment_status(storage)
    payload = build_sandbox_comparison_acknowledgment_status_payload(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/history",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_history() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryResponse
):
    """Bounded sandbox comparison acknowledgment status history (read-only advisory)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_ack_status_history_payload(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/history",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_history_refresh() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryResponse
):
    """Dev/local only — refresh acknowledgment status history summary report."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_ack_status_history_report(storage)
    payload = build_ack_status_history_payload(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusHistoryResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-hint",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintResponse
):
    """Local sandbox comparison acknowledgment status trend hint (read-only advisory)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_ack_status_trend_hint_payload(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-hint",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint_refresh() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintResponse
):
    """Dev/local only — refresh sandbox comparison acknowledgment status trend hint."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_ack_status_trend_hint(storage)
    payload = build_ack_status_trend_hint_payload(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendHintResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgments",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentsResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgments() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentsResponse
):
    """Bounded local acknowledgment status trend hint review acknowledgments (does not clear alerts)."""
    storage = LocalStorage(settings.local_storage_root)
    bounded = 25
    payload = build_ack_status_trend_review_acknowledgments_payload(storage, limit=bounded)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentsResponse(
        **payload
    )


@router.post(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgments",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgments_create(
    body: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCreateRequest,
) -> MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse:
    """Dev/local only — record status trend review acknowledgment; does NOT clear alerts."""
    storage = LocalStorage(settings.local_storage_root)
    try:
        record = create_ack_status_trend_review_acknowledgment(
            storage,
            operator_name=body.operator_name,
            operator_initials=body.operator_initials,
            note=body.note,
            related_trend=body.related_trend,
            related_hint_status=body.related_hint_status,
            related_hint_reason=body.related_hint_reason,
            related_trend_review_recommended=body.related_trend_review_recommended,
            acknowledged_trend_review=body.acknowledged_trend_review,
        )
    except AckStatusTrendReviewAcknowledgmentValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    hint = build_ack_status_trend_hint(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse(
        verified_mrms=False,
        local_acknowledgment_only=True,
        does_not_clear_alerts=True,
        does_not_enable_production=True,
        does_not_authorize_production_use=True,
        production_enabled=settings.enable_production_radar_tiles,
        trend_review_still_recommended=bool(hint.get("trend_review_recommended")),
        acknowledgment=record,
    )


@router.get(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse
):
    """Local sandbox comparison status trend review acknowledgment status rollup (read-only advisory)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_ack_status_trend_review_acknowledgment_status_payload(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse(
        **payload
    )


@router.post(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_refresh() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse
):
    """Dev/local only — refresh status trend review acknowledgment status rollup."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_ack_status_trend_review_acknowledgment_status(storage)
    payload = build_ack_status_trend_review_acknowledgment_status_payload(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse(
        **payload
    )


@router.get(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/history",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_history() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse
):
    """Bounded sandbox comparison status trend review acknowledgment status history (read-only advisory)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_ack_status_trend_review_acknowledgment_status_history_payload(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse(
        **payload
    )


@router.post(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/history",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_history_refresh() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse
):
    """Dev/local only — refresh status trend review acknowledgment status history summary report."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_ack_status_trend_review_acknowledgment_status_history_report(storage)
    payload = build_ack_status_trend_review_acknowledgment_status_history_payload(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse(
        **payload
    )


@router.get(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-hint",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_hint() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse
):
    """Local sandbox comparison status trend review acknowledgment status trend hint (read-only advisory)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_ack_status_trend_review_acknowledgment_status_trend_hint_payload(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse(
        **payload
    )


@router.post(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-hint",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_hint_refresh() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse
):
    """Dev/local only — refresh status trend review acknowledgment status trend hint."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_ack_status_trend_review_acknowledgment_status_trend_hint(storage)
    payload = build_ack_status_trend_review_acknowledgment_status_trend_hint_payload(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse(
        **payload
    )


@router.get(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgments",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentsResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgments() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentsResponse
):
    """Bounded local trend review acknowledgment status trend hint review acknowledgments (does not clear alerts)."""
    storage = LocalStorage(settings.local_storage_root)
    bounded = 25
    payload = build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgments_payload(
        storage,
        limit=bounded,
    )
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentsResponse(
        **payload
    )


@router.post(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgments",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgments_create(
    body: MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateRequest,
) -> MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse:
    """Dev/local only — record trend review acknowledgment status trend review acknowledgment; does NOT clear alerts."""
    storage = LocalStorage(settings.local_storage_root)
    try:
        record = create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
            storage,
            operator_name=body.operator_name,
            operator_initials=body.operator_initials,
            note=body.note,
            related_trend=body.related_trend,
            related_hint_status=body.related_hint_status,
            related_hint_reason=body.related_hint_reason,
            related_trend_review_recommended=body.related_trend_review_recommended,
            acknowledged_trend_review=body.acknowledged_trend_review,
        )
    except AckStatusTrendReviewAckStatusTrendReviewAcknowledgmentValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    hint = build_ack_status_trend_review_acknowledgment_status_trend_hint(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentCreateResponse(
        verified_mrms=False,
        local_acknowledgment_only=True,
        does_not_clear_alerts=True,
        does_not_enable_production=True,
        does_not_authorize_production_use=True,
        production_enabled=settings.enable_production_radar_tiles,
        trend_review_still_recommended=bool(hint.get("trend_review_recommended")),
        acknowledgment=record,
    )


@router.get(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse
):
    """Local sandbox comparison trend review acknowledgment status rollup (read-only advisory)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_payload(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse(
        **payload
    )


@router.post(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_refresh() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse
):
    """Dev/local only — refresh trend review acknowledgment status rollup."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status(storage)
    payload = build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_payload(storage)
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusResponse(
        **payload
    )


@router.get(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status/history",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse
):
    """Bounded sandbox comparison trend review acknowledgment status history (read-only advisory)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history_payload(
        storage
    )
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse(
        **payload
    )


@router.post(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status/history",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history_refresh() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse
):
    """Dev/local only — refresh trend review acknowledgment status history report."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history_report(storage)
    payload = build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history_payload(
        storage
    )
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusHistoryResponse(
        **payload
    )


@router.get(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status/trend-hint",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse
):
    """Local sandbox comparison trend review acknowledgment status trend hints (read-only advisory)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint_payload(
        storage
    )
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse(
        **payload
    )


@router.post(
    "/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status/trend-hint",
    response_model=MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse,
)
def validation_mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint_refresh() -> (
    MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse
):
    """Dev/local only — refresh trend review acknowledgment status trend hints."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)
    payload = build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint_payload(
        storage
    )
    return MrmsRenderCandidateSandboxComparisonAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendReviewAcknowledgmentStatusTrendHintResponse(
        **payload
    )


@router.get(
    "/mrms-render-candidate/sandbox/trend-hint-review-acknowledgments",
    response_model=MrmsRenderCandidateTrendHintReviewAcknowledgmentsResponse,
)
def validation_mrms_render_candidate_trend_hint_review_acknowledgments() -> (
    MrmsRenderCandidateTrendHintReviewAcknowledgmentsResponse
):
    """Bounded local candidate trend-hint review acknowledgments (does not clear alerts)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_trend_hint_review_acknowledgments_payload(storage, limit=25)
    return MrmsRenderCandidateTrendHintReviewAcknowledgmentsResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/trend-hint-review-acknowledgments",
    response_model=MrmsRenderCandidateTrendHintReviewAcknowledgmentCreateResponse,
)
def validation_mrms_render_candidate_trend_hint_review_acknowledgments_create(
    body: MrmsRenderCandidateTrendHintReviewAcknowledgmentCreateRequest,
) -> MrmsRenderCandidateTrendHintReviewAcknowledgmentCreateResponse:
    """Dev/local only — record candidate trend-hint review acknowledgment; does NOT clear alerts."""
    storage = LocalStorage(settings.local_storage_root)
    try:
        record = create_trend_hint_review_acknowledgment(
            storage,
            operator_name=body.operator_name,
            operator_initials=body.operator_initials,
            note=body.note,
            related_trend=body.related_trend,
            related_hint_status=body.related_hint_status,
            related_hint_reason=body.related_hint_reason,
            related_trend_review_recommended=body.related_trend_review_recommended,
            acknowledged_trend_review=body.acknowledged_trend_review,
        )
    except TrendHintReviewAckValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    hint = build_candidate_trend_hint(storage)
    return MrmsRenderCandidateTrendHintReviewAcknowledgmentCreateResponse(
        verified_mrms=False,
        local_acknowledgment_only=True,
        does_not_clear_alerts=True,
        does_not_enable_production=True,
        does_not_authorize_production_use=True,
        production_enabled=settings.enable_production_radar_tiles,
        trend_review_still_recommended=bool(hint.get("trend_review_recommended")),
        acknowledgment=record,
    )


@router.get(
    "/mrms-render-candidate/sandbox/trend-hint-ack-status",
    response_model=MrmsRenderCandidateTrendHintAckStatusResponse,
)
def validation_mrms_render_candidate_trend_hint_ack_status() -> MrmsRenderCandidateTrendHintAckStatusResponse:
    """Local candidate trend-hint acknowledgment status rollup (does not clear alerts)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_trend_hint_ack_status_payload(storage)
    return MrmsRenderCandidateTrendHintAckStatusResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/trend-hint-ack-status",
    response_model=MrmsRenderCandidateTrendHintAckStatusResponse,
)
def validation_mrms_render_candidate_trend_hint_ack_status_refresh() -> (
    MrmsRenderCandidateTrendHintAckStatusResponse
):
    """Dev/local only — refresh trend-hint acknowledgment status rollup; does NOT clear alerts."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_trend_hint_ack_status(storage)
    payload = build_trend_hint_ack_status_payload(storage)
    return MrmsRenderCandidateTrendHintAckStatusResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/trend-hint-ack-status/history",
    response_model=MrmsRenderCandidateTrendHintAckStatusHistoryResponse,
)
def validation_mrms_render_candidate_trend_hint_ack_status_history() -> (
    MrmsRenderCandidateTrendHintAckStatusHistoryResponse
):
    """Bounded local candidate trend-hint acknowledgment status history (does not clear alerts)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_trend_hint_ack_status_history_payload(storage)
    return MrmsRenderCandidateTrendHintAckStatusHistoryResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/trend-hint-ack-status/history",
    response_model=MrmsRenderCandidateTrendHintAckStatusHistoryResponse,
)
def validation_mrms_render_candidate_trend_hint_ack_status_history_refresh() -> (
    MrmsRenderCandidateTrendHintAckStatusHistoryResponse
):
    """Dev/local only — refresh trend-hint acknowledgment status history report; does NOT clear alerts."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_trend_hint_ack_status_history_report(storage)
    payload = build_trend_hint_ack_status_history_payload(storage)
    return MrmsRenderCandidateTrendHintAckStatusHistoryResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/trend-hint-review-digest",
    response_model=MrmsRenderCandidateTrendHintReviewDigestResponse,
)
def validation_mrms_render_candidate_trend_hint_review_digest() -> (
    MrmsRenderCandidateTrendHintReviewDigestResponse
):
    """Local candidate trend-hint review chain digest (does not clear alerts)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_trend_hint_review_digest_payload(storage)
    return MrmsRenderCandidateTrendHintReviewDigestResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/trend-hint-review-digest",
    response_model=MrmsRenderCandidateTrendHintReviewDigestResponse,
)
def validation_mrms_render_candidate_trend_hint_review_digest_refresh() -> (
    MrmsRenderCandidateTrendHintReviewDigestResponse
):
    """Dev/local only — refresh trend-hint review chain digest; does NOT clear alerts."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_trend_hint_review_digest(storage)
    payload = build_trend_hint_review_digest_payload(storage)
    return MrmsRenderCandidateTrendHintReviewDigestResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/trend-hint-review-digest/history",
    response_model=MrmsRenderCandidateTrendHintReviewDigestHistoryResponse,
)
def validation_mrms_render_candidate_trend_hint_review_digest_history() -> (
    MrmsRenderCandidateTrendHintReviewDigestHistoryResponse
):
    """Bounded local candidate trend-hint review digest history (does not clear alerts)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_trend_hint_review_digest_history_payload(storage)
    return MrmsRenderCandidateTrendHintReviewDigestHistoryResponse(**payload)


@router.post(
    "/mrms-render-candidate/sandbox/trend-hint-review-digest/history",
    response_model=MrmsRenderCandidateTrendHintReviewDigestHistoryResponse,
)
def validation_mrms_render_candidate_trend_hint_review_digest_history_refresh() -> (
    MrmsRenderCandidateTrendHintReviewDigestHistoryResponse
):
    """Dev/local only — refresh trend-hint review digest history report; does NOT clear alerts."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_trend_hint_review_digest_history_report(storage)
    payload = build_trend_hint_review_digest_history_payload(storage)
    return MrmsRenderCandidateTrendHintReviewDigestHistoryResponse(**payload)


@router.get(
    "/mrms-render-candidate/sandbox/trend-hint-review-digest/diff",
    response_model=MrmsRenderCandidateTrendHintReviewDigestDiffResponse,
)
def validation_mrms_render_candidate_trend_hint_review_digest_diff() -> (
    MrmsRenderCandidateTrendHintReviewDigestDiffResponse
):
    """Latest local candidate trend-hint review digest diff (read-only; does not clear alerts)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_trend_hint_review_digest_diff_payload(storage)
    return MrmsRenderCandidateTrendHintReviewDigestDiffResponse(**payload)


@router.get(
    "/mrms-visual-review/sample-set/readiness",
    response_model=MrmsVisualReviewSampleReadinessResponse,
)
def validation_mrms_visual_review_sample_readiness() -> MrmsVisualReviewSampleReadinessResponse:
    """Local sample-set readiness summary (read-only advisory; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_visual_review_sample_readiness_payload(storage)
    return MrmsVisualReviewSampleReadinessResponse(**payload)


@router.post(
    "/mrms-visual-review/sample-set/readiness",
    response_model=MrmsVisualReviewSampleReadinessResponse,
)
def validation_mrms_visual_review_sample_readiness_refresh() -> MrmsVisualReviewSampleReadinessResponse:
    """Dev/local only — refresh sample-set readiness Markdown; does NOT verify MRMS."""
    storage = LocalStorage(settings.local_storage_root)
    refresh_visual_review_sample_readiness(storage)
    payload = build_visual_review_sample_readiness_payload(storage)
    return MrmsVisualReviewSampleReadinessResponse(**payload)


@router.post(
    "/mrms-visual-review/sample-set/annotations",
    response_model=MrmsVisualReviewSampleAnnotationUpsertResponse,
)
def validation_mrms_visual_review_sample_annotation_upsert(
    body: MrmsVisualReviewSampleAnnotationUpsertRequest,
) -> MrmsVisualReviewSampleAnnotationUpsertResponse:
    """Dev/local only — record sample annotation; does NOT verify MRMS or clear alerts."""
    storage = LocalStorage(settings.local_storage_root)
    try:
        annotation = upsert_sample_annotation(
            storage,
            sample_key=body.sample_key,
            status=body.status,
            operator_notes=body.operator_notes,
            reviewer_label=body.reviewer_label,
            issue_tags=body.issue_tags,
        )
    except SampleAnnotationValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    compact = compact_visual_review_sample_readiness(storage)
    return MrmsVisualReviewSampleAnnotationUpsertResponse(
        verified_mrms=False,
        local_advisory_only=True,
        does_not_clear_alerts=True,
        does_not_enable_production=True,
        does_not_download_or_decode=True,
        no_external_notifications=True,
        candidate_ready_is_not_production_authorization=True,
        production_enabled=settings.enable_production_radar_tiles,
        annotation=annotation,
        compact=compact,
    )


@router.get("/mrms-visual-review/sample-set", response_model=MrmsVisualReviewSampleSetResponse)
def validation_mrms_visual_review_sample_set() -> MrmsVisualReviewSampleSetResponse:
    """Latest MRMS visual review sample set (read-only; local drilldown only)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_visual_review_sample_set_payload(storage)
    return MrmsVisualReviewSampleSetResponse(**payload)


@router.post(
    "/mrms-visual-review/sample-set",
    response_model=MrmsVisualReviewSampleSetCreateResponse,
)
def validation_mrms_visual_review_sample_set_create(
    body: MrmsVisualReviewSampleSetCreateRequest,
) -> MrmsVisualReviewSampleSetCreateResponse:
    """Dev/local only — build MRMS visual review sample set; does NOT verify MRMS or clear alerts."""
    storage = LocalStorage(settings.local_storage_root)
    sample_set = build_visual_review_sample_set(
        storage,
        selection_mode=body.selection_mode,
        limit=body.limit,
        timestamps=body.timestamps or None,
        notes=body.notes,
    )
    compact = build_visual_review_sample_set_payload(storage)["compact"]
    return MrmsVisualReviewSampleSetCreateResponse(
        verified_mrms=False,
        local_sample_set_only=True,
        does_not_clear_alerts=True,
        does_not_enable_production=True,
        does_not_download_or_decode=True,
        no_external_notifications=True,
        production_enabled=settings.enable_production_radar_tiles,
        sample_set=sample_set,
        compact=compact,
    )


@router.get("/mrms-visual-review/hint", response_model=MrmsVisualReviewHintResponse)
def validation_mrms_visual_review_hint() -> MrmsVisualReviewHintResponse:
    """Stale visual review regeneration hint (read-only; local hint only)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_visual_review_hint_payload(storage)
    return MrmsVisualReviewHintResponse(**payload)


@router.get(
    "/mrms-visual-review/comparison/history",
    response_model=MrmsVisualReviewComparisonHistoryResponse,
)
def validation_mrms_visual_review_comparison_history(
    limit: int = 25,
) -> MrmsVisualReviewComparisonHistoryResponse:
    """Bounded MRMS visual review comparison history (read-only; local review only)."""
    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(limit, 25))
    payload = build_visual_review_comparison_history_payload(storage, limit=bounded)
    return MrmsVisualReviewComparisonHistoryResponse(**payload)


@router.get("/mrms-visual-review/comparison", response_model=MrmsVisualReviewComparisonResponse)
def validation_mrms_visual_review_comparison() -> MrmsVisualReviewComparisonResponse:
    """Latest MRMS visual review comparison (read-only; local visual evidence only)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_visual_review_comparison_payload(storage)
    return MrmsVisualReviewComparisonResponse(**payload)


@router.get("/mrms-visual-review", response_model=MrmsVisualReviewResponse)
def validation_mrms_visual_review() -> MrmsVisualReviewResponse:
    """Latest MRMS visual review manifest (read-only; local visual evidence only)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_mrms_visual_review_payload(storage)
    return MrmsVisualReviewResponse(**payload)


@router.get("/mrms-visual-review/history", response_model=MrmsVisualReviewHistoryResponse)
def validation_mrms_visual_review_history(
    limit: int = 25,
) -> MrmsVisualReviewHistoryResponse:
    """Bounded MRMS visual review history (read-only; local visual evidence only)."""
    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(limit, 25))
    payload = build_mrms_visual_review_history_payload(storage, limit=bounded)
    return MrmsVisualReviewHistoryResponse(**payload)


@router.get(
    "/review-sessions/export/diff/trend-hint",
    response_model=MrmsReviewSessionExportDiffTrendHintResponse,
)
def validation_review_sessions_export_diff_trend_hint() -> MrmsReviewSessionExportDiffTrendHintResponse:
    """Review session export diff trend regeneration hint (read-only; local review only)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_review_session_export_diff_trend_hint_payload(storage)
    return MrmsReviewSessionExportDiffTrendHintResponse(**payload)


@router.get(
    "/review-sessions/export/diff/trend",
    response_model=MrmsReviewSessionExportDiffTrendResponse,
)
def validation_review_sessions_export_diff_trend(
    window: int = 10,
) -> MrmsReviewSessionExportDiffTrendResponse:
    """Review session export diff trend summary (read-only; local review only)."""
    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(window, 25))
    payload = build_review_session_export_diff_trend_payload(storage, window=bounded)
    return MrmsReviewSessionExportDiffTrendResponse(**payload)


@router.get(
    "/review-sessions/export/diff/history",
    response_model=MrmsReviewSessionExportDiffHistoryResponse,
)
def validation_review_sessions_export_diff_history() -> MrmsReviewSessionExportDiffHistoryResponse:
    """Bounded review session export diff history (read-only; local review only)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_review_session_export_diff_payload(storage)
    return MrmsReviewSessionExportDiffHistoryResponse(**payload)


@router.get(
    "/review-sessions/export/diff",
    response_model=MrmsReviewSessionExportDiffResponse,
)
def validation_review_sessions_export_diff() -> MrmsReviewSessionExportDiffResponse:
    """Latest review session export diff metadata (read-only; local review only)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_review_session_export_diff_payload(storage)
    return MrmsReviewSessionExportDiffResponse(**payload)


@router.get(
    "/review-sessions/export/history",
    response_model=MrmsReviewSessionExportHistoryResponse,
)
def validation_review_sessions_export_history() -> MrmsReviewSessionExportHistoryResponse:
    """Bounded review session export history (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_review_session_export_payload(storage)
    return MrmsReviewSessionExportHistoryResponse(**payload)


@router.get(
    "/review-sessions/export",
    response_model=MrmsReviewSessionExportResponse,
)
def validation_review_sessions_export() -> MrmsReviewSessionExportResponse:
    """Latest review session Markdown export metadata (read-only; local review only)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_review_session_export_payload(storage)
    return MrmsReviewSessionExportResponse(**payload)


@router.get(
    "/review-sessions/comparison/history",
    response_model=MrmsReviewSessionComparisonHistoryResponse,
)
def validation_review_sessions_comparison_history() -> MrmsReviewSessionComparisonHistoryResponse:
    """Bounded review session comparison history (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_review_session_comparison_payload(storage)
    return MrmsReviewSessionComparisonHistoryResponse(
        prototype=True,
        verified_mrms=False,
        local_comparison_only=True,
        does_not_clear_alerts=True,
        does_not_enable_production=True,
        no_external_notifications=True,
        count=payload.get("count", 0),
        max_entries=payload.get("max_entries", 25),
        latest=payload.get("latest"),
        entries=payload.get("entries") or [],
        compact=payload.get("compact") or {},
    )


@router.get(
    "/review-sessions/comparison",
    response_model=MrmsReviewSessionComparisonResponse,
)
def validation_review_sessions_comparison() -> MrmsReviewSessionComparisonResponse:
    """Latest review session comparison vs previous session (read-only; local review only)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_review_session_comparison_payload(storage)
    return MrmsReviewSessionComparisonResponse(**payload)


@router.get("/review-sessions", response_model=MrmsReviewSessionsResponse)
def validation_review_sessions(limit: int = 50) -> MrmsReviewSessionsResponse:
    """Bounded local MRMS proof review sessions (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(limit, 50))
    payload = build_review_sessions_payload(storage, limit=bounded)
    return MrmsReviewSessionsResponse(**payload)


@router.post("/review-sessions", response_model=MrmsReviewSessionCreateResponse)
def validation_review_sessions_create(
    body: MrmsReviewSessionCreateRequest,
) -> MrmsReviewSessionCreateResponse:
    """Dev/local only — record MRMS proof review session; does NOT verify MRMS or clear alerts."""
    storage = LocalStorage(settings.local_storage_root)
    try:
        record = create_review_session_record(
            storage,
            operator_name=body.operator_name,
            operator_initials=body.operator_initials,
            session_notes=body.session_notes,
            checklist_items_reviewed=body.checklist_items_reviewed,
            accepted_limitations=body.accepted_limitations,
            accepted_limitations_text=body.accepted_limitations_text,
        )
    except ReviewSessionValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    export_status: dict = {}
    if body.export_after_create:
        export_status = try_export_after_review_session_create(storage, record)

    return MrmsReviewSessionCreateResponse(
        verified_mrms=False,
        local_review_only=True,
        does_not_clear_alerts=True,
        does_not_enable_production=True,
        production_enabled=settings.enable_production_radar_tiles,
        review_session=record,
        export_after_create_requested=bool(export_status.get("export_after_create_requested")),
        export_generated=bool(export_status.get("export_generated")),
        export_path=export_status.get("export_path"),
        export_metadata_path=export_status.get("export_metadata_path"),
        export_error=export_status.get("export_error"),
        export_compact=export_status.get("export_compact"),
    )


@router.get("/proof-bundles", response_model=MrmsProofBundlesResponse)
def validation_proof_bundles(limit: int = 10) -> MrmsProofBundlesResponse:
    """Bounded local MRMS proof bundle export history (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_proof_bundles_list_payload(storage, limit=limit)
    return MrmsProofBundlesResponse(**payload)


@router.get("/proof-bundle-diff", response_model=MrmsProofBundleDiffResponse)
def validation_proof_bundle_diff(refresh: bool = False) -> MrmsProofBundleDiffResponse:
    """Latest local proof bundle diff report (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    if refresh:
        report = build_proof_bundle_diff_report(storage)
    else:
        report = load_latest_proof_bundle_diff(storage)
        if report is None:
            report = build_proof_bundle_diff_report(storage)
    return MrmsProofBundleDiffResponse(
        verified_mrms=False,
        local_diff_only=True,
        proof_only=True,
        report=report,
    )


@router.get("/operator-handoff", response_model=OperatorHandoffResponse)
def validation_operator_handoff() -> OperatorHandoffResponse:
    """Latest local operator handoff checklist metadata (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    handoff = load_latest_operator_handoff(storage)
    return OperatorHandoffResponse(
        verified_mrms=False,
        local_handoff_only=True,
        does_not_enable_production=True,
        handoff=handoff,
    )


@router.get(
    "/proof-bundle-diff-alert-history",
    response_model=ProofBundleDiffAlertHistoryResponse,
)
def validation_proof_bundle_diff_alert_history(
    limit: int = 25,
) -> ProofBundleDiffAlertHistoryResponse:
    """Bounded proof bundle diff alert timeline (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(limit, 25))
    payload = build_proof_bundle_diff_alert_history_payload(storage, limit=bounded)
    return ProofBundleDiffAlertHistoryResponse(**payload)


@router.get(
    "/proof-bundle-diff-alert-trend",
    response_model=ProofBundleDiffAlertTrendResponse,
)
def validation_proof_bundle_diff_alert_trend(
    window: int = 10,
) -> ProofBundleDiffAlertTrendResponse:
    """Proof bundle diff alert trend summary (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(window, 25))
    payload = build_proof_bundle_diff_alert_trend_payload(storage, window=bounded)
    return ProofBundleDiffAlertTrendResponse(**payload)


@router.get(
    "/proof-bundle-diff-escalation",
    response_model=ProofBundleDiffEscalationResponse,
)
def validation_proof_bundle_diff_escalation() -> ProofBundleDiffEscalationResponse:
    """Proof bundle diff alert escalation hints (read-only; does not verify MRMS or clear alerts)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_proof_bundle_diff_escalation_payload(storage)
    return ProofBundleDiffEscalationResponse(**payload)


@router.get(
    "/proof-bundle-diff-escalation-history",
    response_model=ProofBundleDiffEscalationHistoryResponse,
)
def validation_proof_bundle_diff_escalation_history(
    limit: int = 25,
) -> ProofBundleDiffEscalationHistoryResponse:
    """Bounded proof bundle diff escalation history (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(limit, 25))
    payload = build_proof_bundle_diff_escalation_history_payload(storage, limit=bounded)
    return ProofBundleDiffEscalationHistoryResponse(**payload)


@router.get(
    "/proof-bundle-diff-escalation-metrics",
    response_model=ProofBundleDiffEscalationMetricsResponse,
)
def validation_proof_bundle_diff_escalation_metrics() -> ProofBundleDiffEscalationMetricsResponse:
    """Proof bundle diff escalation history metrics (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_proof_bundle_diff_escalation_metrics_payload(storage)
    return ProofBundleDiffEscalationMetricsResponse(**payload)


@router.get(
    "/proof-bundle-diff-escalation-digest",
    response_model=ProofBundleDiffEscalationDigestResponse,
)
def validation_proof_bundle_diff_escalation_digest() -> ProofBundleDiffEscalationDigestResponse:
    """Latest local escalation digest metadata/Markdown (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_proof_bundle_diff_escalation_digest_payload(storage)
    return ProofBundleDiffEscalationDigestResponse(**payload)


@router.get(
    "/proof-bundle-diff-escalation-digest-history",
    response_model=ProofBundleDiffEscalationDigestHistoryResponse,
)
def validation_proof_bundle_diff_escalation_digest_history(
    limit: int = 25,
) -> ProofBundleDiffEscalationDigestHistoryResponse:
    """Bounded digest export history (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(limit, 25))
    payload = build_digest_export_history_payload(storage, limit=bounded)
    return ProofBundleDiffEscalationDigestHistoryResponse(**payload)


@router.get(
    "/proof-bundle-diff-escalation-digest-diff",
    response_model=ProofBundleDiffEscalationDigestDiffResponse,
)
def validation_proof_bundle_diff_escalation_digest_diff() -> ProofBundleDiffEscalationDigestDiffResponse:
    """Latest digest diff metadata and regeneration hint (read-only; does not verify MRMS)."""
    storage = LocalStorage(settings.local_storage_root)
    payload = build_digest_diff_payload(storage)
    return ProofBundleDiffEscalationDigestDiffResponse(**payload)


@router.get(
    "/proof-bundle-diff-acknowledgments",
    response_model=ProofBundleDiffAcknowledgmentsResponse,
)
def validation_proof_bundle_diff_acknowledgments(
    limit: int = 25,
) -> ProofBundleDiffAcknowledgmentsResponse:
    """Bounded local diff alert acknowledgments (read-only; does not clear alerts)."""
    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(limit, 50))
    payload = build_diff_acknowledgments_payload(storage, limit=bounded)
    return ProofBundleDiffAcknowledgmentsResponse(**payload)


@router.post(
    "/proof-bundle-diff-acknowledgments",
    response_model=ProofBundleDiffAcknowledgmentCreateResponse,
)
def validation_proof_bundle_diff_acknowledgments_create(
    body: ProofBundleDiffAcknowledgmentCreateRequest,
) -> ProofBundleDiffAcknowledgmentCreateResponse:
    """Dev/local only — record diff alert acknowledgment; does NOT clear alerts or verify MRMS."""
    storage = LocalStorage(settings.local_storage_root)
    try:
        record = create_diff_acknowledgment(
            storage,
            operator_name=body.operator_name,
            operator_initials=body.operator_initials,
            note=body.note,
            related_diff_status=body.related_diff_status,
            related_bundle_id=body.related_bundle_id,
            related_baseline_bundle_id=body.related_baseline_bundle_id,
            acknowledged_attention=body.acknowledged_attention,
        )
    except DiffAcknowledgmentValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    alert = load_validation_alert(storage)
    diff_status = (alert or {}).get("proof_bundle_diff_status")
    diff_alert_still_active = bool(
        proof_bundle_diff_requires_attention(diff_status)
        or (alert or {}).get("proof_bundle_diff_attention")
    )

    return ProofBundleDiffAcknowledgmentCreateResponse(
        verified_mrms=False,
        local_acknowledgment_only=True,
        does_not_clear_alerts=True,
        does_not_enable_production=True,
        production_enabled=settings.enable_production_radar_tiles,
        diff_alert_still_active=diff_alert_still_active,
        acknowledgment=record,
    )
