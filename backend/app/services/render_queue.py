"""Render job queue service — SQLite local dev, no Redis/Celery."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.render_job import (
    DEFAULT_MAX_ATTEMPTS,
    JOB_STATUS_CANCELED,
    JOB_STATUS_FAILED,
    JOB_STATUS_QUEUED,
    JOB_STATUS_RUNNING,
    JOB_STATUS_SUCCEEDED,
    JOB_TYPE_PRODUCTION_TILES,
    RenderJob,
    TERMINAL_JOB_STATUSES,
)

from backend.app.config import settings

RETRY_DELAY_SECONDS = 1


@dataclass
class RenderQueueSummary:
    queued: int = 0
    running: int = 0
    succeeded: int = 0
    failed: int = 0
    canceled: int = 0
    total_tiles_written: int = 0
    total_output_bytes: int = 0

    def to_dict(self) -> dict:
        return {
            "queued": self.queued,
            "running": self.running,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "canceled": self.canceled,
            "total_tiles_written": self.total_tiles_written,
            "total_output_bytes": self.total_output_bytes,
            "prototype": True,
            "verified_mrms": False,
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_utc(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _retry_at_from_now(seconds: int = RETRY_DELAY_SECONDS) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
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
        max_attempts=max_attempts,
        status=JOB_STATUS_QUEUED,
        created_at=_utc_now(),
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_render_job(session: Session, job_id: int) -> Optional[RenderJob]:
    return session.get(RenderJob, job_id)


def list_render_jobs(
    session: Session,
    *,
    limit: int = 50,
    status: Optional[str] = None,
    layer: Optional[str] = None,
    timestamp: Optional[str] = None,
    job_type: Optional[str] = None,
) -> list[RenderJob]:
    query = session.query(RenderJob)
    if status is not None:
        query = query.filter(RenderJob.status == status)
    if layer is not None:
        query = query.filter(RenderJob.layer == layer)
    if timestamp is not None:
        query = query.filter(RenderJob.timestamp == timestamp)
    if job_type is not None:
        query = query.filter(RenderJob.job_type == job_type)
    return query.order_by(RenderJob.id.desc()).limit(limit).all()


def get_queue_summary(session: Session) -> RenderQueueSummary:
    summary = RenderQueueSummary()
    rows = session.query(RenderJob.status, func.count(RenderJob.id)).group_by(RenderJob.status).all()
    for status, count in rows:
        if status == JOB_STATUS_QUEUED:
            summary.queued = count
        elif status == JOB_STATUS_RUNNING:
            summary.running = count
        elif status == JOB_STATUS_SUCCEEDED:
            summary.succeeded = count
        elif status == JOB_STATUS_FAILED:
            summary.failed = count
        elif status == JOB_STATUS_CANCELED:
            summary.canceled = count

    totals = session.query(
        func.coalesce(func.sum(RenderJob.tiles_written), 0),
        func.coalesce(func.sum(RenderJob.output_bytes), 0),
    ).one()
    summary.total_tiles_written = int(totals[0] or 0)
    summary.total_output_bytes = int(totals[1] or 0)
    return summary


def _is_retry_ready(job: RenderJob, now: datetime) -> bool:
    if job.next_retry_at is None:
        return True
    return _parse_utc(job.next_retry_at) <= now


def recover_stale_running_jobs(
    session: Session,
    *,
    stale_seconds: Optional[int] = None,
    now: Optional[datetime] = None,
) -> int:
    """Re-queue or fail jobs stuck in running past a safe threshold."""
    resolved_stale_seconds = (
        stale_seconds if stale_seconds is not None else settings.stale_running_job_seconds
    )
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=resolved_stale_seconds)
    recovered = 0

    running_jobs = (
        session.query(RenderJob)
        .filter(RenderJob.status == JOB_STATUS_RUNNING)
        .all()
    )
    for job in running_jobs:
        if not job.started_at:
            continue
        if _parse_utc(job.started_at) > cutoff:
            continue
        schedule_job_retry(session, job, "stale running job recovered (worker crash or timeout)")
        recovered += 1
    return recovered


def claim_next_queued_job(session: Session) -> Optional[RenderJob]:
    """Atomically claim the oldest runnable queued job."""
    recover_stale_running_jobs(session)
    now = datetime.now(timezone.utc)
    candidates = (
        session.query(RenderJob)
        .filter(RenderJob.status == JOB_STATUS_QUEUED)
        .order_by(RenderJob.id.asc())
        .all()
    )
    job = None
    for candidate in candidates:
        if _is_retry_ready(candidate, now):
            job = candidate
            break
    if job is None:
        return None

    job.status = JOB_STATUS_RUNNING
    job.attempt_count += 1
    job.started_at = _utc_now()
    job.next_retry_at = None
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
    job.next_retry_at = None
    session.commit()
    session.refresh(job)


def schedule_job_retry(session: Session, job: RenderJob, error_message: str) -> RenderJob:
    """Re-queue a failed attempt when retries remain, else mark terminal failed."""
    job.error_message = error_message[:2000]
    job.last_error_at = _utc_now()
    if job.attempt_count < job.max_attempts:
        job.status = JOB_STATUS_QUEUED
        job.next_retry_at = _retry_at_from_now()
        job.finished_at = None
    else:
        job.status = JOB_STATUS_FAILED
        job.finished_at = _utc_now()
        job.next_retry_at = None
    session.commit()
    session.refresh(job)
    return job


def mark_job_failed(session: Session, job: RenderJob, error_message: str) -> RenderJob:
    """Fail job with retry scheduling when attempts remain."""
    return schedule_job_retry(session, job, error_message)


def retry_render_job(session: Session, job: RenderJob) -> RenderJob:
    """Explicitly re-queue a failed job if retries remain."""
    if job.status != JOB_STATUS_FAILED:
        raise ValueError("Only failed jobs can be retried")
    if job.attempt_count >= job.max_attempts:
        raise ValueError("Job has exhausted max_attempts")
    job.status = JOB_STATUS_QUEUED
    job.next_retry_at = _utc_now()
    job.finished_at = None
    job.error_message = None
    session.commit()
    session.refresh(job)
    return job


def cancel_render_job(session: Session, job: RenderJob) -> RenderJob:
    if job.status in TERMINAL_JOB_STATUSES:
        return job
    job.status = JOB_STATUS_CANCELED
    job.canceled_at = _utc_now()
    job.finished_at = _utc_now()
    job.next_retry_at = None
    session.commit()
    session.refresh(job)
    return job
