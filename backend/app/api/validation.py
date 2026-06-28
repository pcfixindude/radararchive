"""Dev/prototype validation dashboard API — not verified MRMS production."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas.validation import ValidationLatestResponse, ValidationSummaryResponse
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_dashboard import build_validation_latest, build_validation_summary

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
