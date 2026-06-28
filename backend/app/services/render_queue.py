"""Render job queue service — SQLite local dev, no Redis/Celery."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.render_job import (
    JOB_STATUS_CANCELED,
    JOB_STATUS_FAILED,
    JOB_STATUS_QUEUED,
    JOB_STATUS_RUNNING,
    JOB_STATUS_SUCCEEDED,
    JOB_TYPE_PRODUCTION_TILES,
    RenderJob,
    TERMINAL_JOB_STATUSES,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def enqueue_render_job(
    session: Session,
    *,
    job_type: str = JOB_TYPE_PRODUCTION_TILES,
    layer: str = "mrms_reflectivity",
    timestamp: Optional[str] = None,
    min_zoom: int = 0,
    max_zoom: int = 0,
    force: bool = False,
    mark_catalog: bool = False,
    artifact_limit: Optional[int] = None,
) -> RenderJob:
    """Create a queued render job."""
    job = RenderJob(
        job_type=job_type,
        layer=layer,
        timestamp=timestamp,
        min_zoom=min_zoom,
        max_zoom=max_zoom,
        force=force,
        mark_catalog=mark_catalog,
        artifact_limit=artifact_limit,
        status=JOB_STATUS_QUEUED,
        created_at=_utc_now(),
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_render_job(session: Session, job_id: int) -> Optional[RenderJob]:
    return session.get(RenderJob, job_id)


def list_render_jobs(session: Session, *, limit: int = 50) -> list[RenderJob]:
    return (
        session.query(RenderJob)
        .order_by(RenderJob.id.desc())
        .limit(limit)
        .all()
    )


def claim_next_queued_job(session: Session) -> Optional[RenderJob]:
    """Atomically claim the oldest queued job for processing."""
    job = (
        session.query(RenderJob)
        .filter(RenderJob.status == JOB_STATUS_QUEUED)
        .order_by(RenderJob.id.asc())
        .first()
    )
    if job is None:
        return None
    job.status = JOB_STATUS_RUNNING
    job.started_at = _utc_now()
    session.commit()
    session.refresh(job)
    return job


def update_job_progress(
    session: Session,
    job: RenderJob,
    *,
    progress_current: int,
    progress_total: int,
    tiles_written: Optional[int] = None,
    tiles_skipped: Optional[int] = None,
    output_bytes: Optional[int] = None,
) -> None:
    job.progress_current = progress_current
    job.progress_total = progress_total
    if tiles_written is not None:
        job.tiles_written = tiles_written
    if tiles_skipped is not None:
        job.tiles_skipped = tiles_skipped
    if output_bytes is not None:
        job.output_bytes = output_bytes
    session.commit()


def mark_job_succeeded(
    session: Session,
    job: RenderJob,
    *,
    progress_total: int,
    tiles_written: int,
    tiles_skipped: int,
    output_bytes: int,
) -> None:
    job.status = JOB_STATUS_SUCCEEDED
    job.progress_current = progress_total
    job.progress_total = progress_total
    job.tiles_written = tiles_written
    job.tiles_skipped = tiles_skipped
    job.output_bytes = output_bytes
    job.error_message = None
    job.finished_at = _utc_now()
    session.commit()
    session.refresh(job)


def mark_job_failed(session: Session, job: RenderJob, error_message: str) -> None:
    job.status = JOB_STATUS_FAILED
    job.error_message = error_message[:2000]
    job.finished_at = _utc_now()
    session.commit()
    session.refresh(job)


def cancel_render_job(session: Session, job: RenderJob) -> RenderJob:
    if job.status in TERMINAL_JOB_STATUSES:
        return job
    job.status = JOB_STATUS_CANCELED
    job.finished_at = _utc_now()
    session.commit()
    session.refresh(job)
    return job
