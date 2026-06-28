"""Dev/prototype render job queue API — not production radar verification."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.render_job import (
    RenderJobCreate,
    RenderJobResponse,
    RenderQueueSummaryResponse,
)
from backend.app.services import render_queue as render_queue_service

router = APIRouter(prefix="/render", tags=["render-jobs-dev"])


def _to_response(job) -> RenderJobResponse:
    return RenderJobResponse.model_validate(job)


@router.post("/jobs", response_model=RenderJobResponse)
def create_render_job(
    payload: RenderJobCreate,
    db: Session = Depends(get_db),
) -> RenderJobResponse:
    """Enqueue a production tile build job (dev/prototype — not verified MRMS)."""
    job = render_queue_service.enqueue_render_job(
        db,
        job_type=payload.job_type,
        layer=payload.layer,
        timestamp=payload.timestamp,
        min_zoom=payload.min_zoom,
        max_zoom=payload.max_zoom,
        force=payload.force,
        mark_catalog=payload.mark_catalog,
        artifact_limit=payload.artifact_limit,
        max_attempts=payload.max_attempts,
    )
    return _to_response(job)


@router.get("/jobs/summary", response_model=RenderQueueSummaryResponse)
def render_jobs_summary(db: Session = Depends(get_db)) -> RenderQueueSummaryResponse:
    """Queue summary metrics (dev/prototype)."""
    summary = render_queue_service.get_queue_summary(db)
    return RenderQueueSummaryResponse(**summary.to_dict())


@router.get("/jobs", response_model=list[RenderJobResponse])
def list_render_jobs(
    limit: int = 50,
    status: Optional[str] = Query(default=None),
    layer: Optional[str] = Query(default=None),
    timestamp: Optional[str] = Query(default=None),
    job_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> list[RenderJobResponse]:
    """List render jobs with optional filters (dev/prototype)."""
    jobs = render_queue_service.list_render_jobs(
        db,
        limit=limit,
        status=status,
        layer=layer,
        timestamp=timestamp,
        job_type=job_type,
    )
    return [_to_response(job) for job in jobs]


@router.get("/jobs/{job_id}", response_model=RenderJobResponse)
def get_render_job(
    job_id: int,
    db: Session = Depends(get_db),
) -> RenderJobResponse:
    """Get one render job by id."""
    job = render_queue_service.get_render_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Render job not found")
    return _to_response(job)


@router.post("/jobs/{job_id}/retry", response_model=RenderJobResponse)
def retry_render_job(
    job_id: int,
    db: Session = Depends(get_db),
) -> RenderJobResponse:
    """Explicitly re-queue a failed job when retries remain."""
    job = render_queue_service.get_render_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Render job not found")
    try:
        retried = render_queue_service.retry_render_job(db, job)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(retried)


@router.post("/jobs/{job_id}/cancel", response_model=RenderJobResponse)
def cancel_render_job(
    job_id: int,
    db: Session = Depends(get_db),
) -> RenderJobResponse:
    """Cancel a queued or running job (dev/prototype)."""
    job = render_queue_service.get_render_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Render job not found")
    canceled = render_queue_service.cancel_render_job(db, job)
    return _to_response(canceled)
