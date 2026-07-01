"""Local frame catalog browser API — status/plan only, no decode work."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas.frame_catalog import FrameCatalogResponse
from backend.app.services.catalog import MRMS_REFLECTIVITY_LAYER_ID
from backend.app.services.frame_cache_warmer import DEFAULT_LIMIT, MAX_LIMIT
from backend.app.services.frame_catalog import build_frame_catalog
from backend.app.services.storage import LocalStorage

router = APIRouter(prefix="/dev", tags=["dev-local"])


def _storage() -> LocalStorage:
    return LocalStorage(settings.local_storage_root)


@router.get("/frame-catalog", response_model=FrameCatalogResponse)
def get_frame_catalog(
    layer: str = Query(MRMS_REFLECTIVITY_LAYER_ID, description="Catalog layer id"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Max frames to return"),
    start_time: Optional[str] = Query(None, description="Optional window start (UTC ISO)"),
    end_time: Optional[str] = Query(None, description="Optional window end (UTC ISO)"),
    timestamps: Optional[str] = Query(
        None,
        description="Comma-separated playback timestamps; when set, assesses this window",
    ),
    session: Session = Depends(get_db),
) -> FrameCatalogResponse:
    """Return local frames with cache/decode readiness for replay navigation."""
    ts_list = None
    if timestamps:
        ts_list = [part.strip() for part in timestamps.split(",") if part.strip()]

    payload = build_frame_catalog(
        session,
        _storage(),
        layer_id=layer,
        timestamps=ts_list,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    return FrameCatalogResponse(**payload)
