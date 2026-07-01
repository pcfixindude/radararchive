"""Playback clip export API — status/plan only, no decode work."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas.playback_export import PlaybackExportResponse
from backend.app.services.catalog import MRMS_REFLECTIVITY_LAYER_ID
from backend.app.services.playback_export import build_playback_export
from backend.app.services.storage import LocalStorage

router = APIRouter(prefix="/dev", tags=["dev-local"])


def _storage() -> LocalStorage:
    return LocalStorage(settings.local_storage_root)


@router.get("/playback-export", response_model=PlaybackExportResponse)
def get_playback_export(
    range_start: str = Query(..., description="Replay range start timestamp (UTC ISO)"),
    range_end: str = Query(..., description="Replay range end timestamp (UTC ISO)"),
    layer: str = Query(MRMS_REFLECTIVITY_LAYER_ID, description="Catalog layer id"),
    loop: bool = Query(False, description="Whether loop playback is active for this range"),
    timestamps: Optional[str] = Query(
        None,
        description="Comma-separated playback timestamps; when set, selects frames between start/end",
    ),
    session: Session = Depends(get_db),
) -> PlaybackExportResponse:
    """Return a bounded clip manifest for the active replay range."""
    if not range_start.strip() or not range_end.strip():
        raise HTTPException(status_code=400, detail="range_start and range_end are required")

    ts_list = None
    if timestamps:
        ts_list = [part.strip() for part in timestamps.split(",") if part.strip()]

    payload = build_playback_export(
        session,
        _storage(),
        range_start=range_start.strip(),
        range_end=range_end.strip(),
        timestamps=ts_list,
        loop_suggested=loop,
        layer_id=layer,
    )
    if payload["status"] == "incomplete_range":
        raise HTTPException(status_code=400, detail="Invalid range_start or range_end timestamps")
    return PlaybackExportResponse(**payload)
