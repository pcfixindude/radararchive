"""Per-frame quality drill-down API — status/plan only, no decode work."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas.frame_quality_report import FrameQualityReportResponse
from backend.app.services.catalog import MRMS_REFLECTIVITY_LAYER_ID
from backend.app.services.frame_quality_report import (
    MAX_FRAME_QUALITY_REPORT,
    build_frame_quality_report,
)
from backend.app.services.storage import LocalStorage

router = APIRouter(prefix="/dev", tags=["dev-local"])


def _storage() -> LocalStorage:
    return LocalStorage(settings.local_storage_root)


@router.get("/frame-quality", response_model=FrameQualityReportResponse)
def get_frame_quality(
    timestamps: str = Query(..., description="Comma-separated UTC ISO timestamps to inspect"),
    layer: str = Query(MRMS_REFLECTIVITY_LAYER_ID, description="Catalog layer id"),
    limit: int = Query(MAX_FRAME_QUALITY_REPORT, ge=1, le=MAX_FRAME_QUALITY_REPORT),
    session: Session = Depends(get_db),
) -> FrameQualityReportResponse:
    """Return per-frame cache/decode/quality detail without running ingest or decode."""
    ts_list = [part.strip() for part in timestamps.split(",") if part.strip()]
    if not ts_list:
        raise HTTPException(status_code=400, detail="timestamps query parameter is required")

    payload = build_frame_quality_report(
        session,
        _storage(),
        timestamps=ts_list,
        layer_id=layer,
        limit=limit,
    )
    return FrameQualityReportResponse(**payload)
