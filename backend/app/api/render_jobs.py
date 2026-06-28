"""Dev/prototype render job queue API — not production radar verification."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.render_job import RenderJobCreate, RenderJobResponse
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
    )
    return _to_response(job)


@router.get("/jobs", response_model=list[RenderJobResponse])
def list_render_jobs(
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[RenderJobResponse]:
    """List recent render jobs (dev/prototype)."""
    jobs = render_queue_service.list_render_jobs(db, limit=limit)
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
