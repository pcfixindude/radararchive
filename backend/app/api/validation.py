"""Dev/prototype validation dashboard API — not verified MRMS production."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas.validation import (
    MrmsProofResponse,
    QueueBenchmarkHistoryResponse,
    ScheduledValidationHistoryResponse,
    ValidationAlertsResponse,
    ValidationFailuresResponse,
    ValidationHistoryResponse,
    ValidationLatestResponse,
    ValidationSummaryResponse,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.mrms_proof_report import load_mrms_proof_report
from backend.app.services.validation_alerts import load_validation_alert, refresh_validation_alert
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
