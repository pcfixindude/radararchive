"""Guided MRMS ingest window API — plan only, no download."""

from typing import Optional

from fastapi import APIRouter, Query

from backend.app.schemas.ingest_window import IngestWindowPlanResponse
from backend.app.services.mrms_ingest_window import (
    PRESET_CUSTOM,
    PRESET_LAST_3H,
    PRESET_REPLAY_RANGE,
    build_ingest_window_plan,
)

router = APIRouter(prefix="/dev", tags=["dev-local"])


@router.get("/ingest-window/plan", response_model=IngestWindowPlanResponse)
def get_ingest_window_plan(
    preset: str = Query(PRESET_LAST_3H, description="Window preset"),
    limit: int = Query(8, ge=1, le=20, description="Max frames to ingest"),
    warm_cache: bool = Query(False, description="Include --warm-cache in bulk command"),
    start: Optional[str] = Query(None, description="Custom window start (ISO)"),
    end: Optional[str] = Query(None, description="Custom window end (ISO)"),
    replay_start: Optional[str] = Query(None, description="Replay range start timestamp"),
    replay_end: Optional[str] = Query(None, description="Replay range end timestamp"),
) -> IngestWindowPlanResponse:
    """Return a bounded ingest command plan without running network download."""
    payload = build_ingest_window_plan(
        preset=preset,
        limit=limit,
        warm_cache=warm_cache,
        custom_start=start if preset == PRESET_CUSTOM else None,
        custom_end=end if preset == PRESET_CUSTOM else None,
        replay_start=replay_start if preset == PRESET_REPLAY_RANGE else None,
        replay_end=replay_end if preset == PRESET_REPLAY_RANGE else None,
    )
    return IngestWindowPlanResponse(**payload)
