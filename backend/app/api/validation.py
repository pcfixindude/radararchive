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
    OperatorHandoffResponse,
    MrmsProofRegressionHistoryResponse,
    MrmsProofRegressionResponse,
    MrmsProofResponse,
    MrmsSignoffCreateRequest,
    MrmsSignoffCreateResponse,
    MrmsSignoffsResponse,
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
from backend.app.services.mrms_proof_history import (
    build_proof_history_payload,
    build_regression_history_payload,
    build_signoffs_list_payload,
)
from backend.app.services.mrms_proof_regression import load_proof_regression_report, run_proof_regression_check
from backend.app.services.mrms_signoff import SignoffValidationError, create_signoff_and_refresh_alert
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
