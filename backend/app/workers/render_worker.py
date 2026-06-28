"""Process queued production tile render jobs using Phase 16 builder."""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional

from sqlalchemy.orm import Session

from backend.app.models.render_job import (
    JOB_STATUS_FAILED,
    JOB_STATUS_QUEUED,
    JOB_TYPE_PRODUCTION_TILES,
    RenderJob,
)
from backend.app.services.production_tile_builder import build_production_tiles
from backend.app.services.render_queue import (
    claim_next_queued_job,
    mark_job_failed,
    mark_job_succeeded,
    recover_stale_running_jobs,
    update_job_progress,
)
from backend.app.services.storage import LocalStorage

logger = logging.getLogger(__name__)

ShouldStopFn = Callable[[], bool]


def _interruptible_sleep(seconds: float, should_stop: ShouldStopFn) -> bool:
    """Sleep in short chunks; return True when stop is requested."""
    if seconds <= 0:
        return should_stop()
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if should_stop():
            return True
        remaining = deadline - time.monotonic()
        time.sleep(min(0.25, max(remaining, 0)))
    return should_stop()


def run_render_job(session: Session, storage: LocalStorage, job: RenderJob) -> RenderJob:
    """Execute one render job (caller must set status to running or use claim_next)."""
    logger.info(
        "Processing render job id=%s status=%s attempt=%s/%s",
        job.id,
        job.status,
        job.attempt_count,
        job.max_attempts,
    )
    if job.job_type != JOB_TYPE_PRODUCTION_TILES:
        mark_job_failed(session, job, f"Unsupported job_type: {job.job_type}")
        logger.warning("Render job id=%s failed: unsupported job_type", job.id)
        return job

    progress_state = {"written": 0, "skipped": 0, "bytes": 0}

    def on_progress(current: int, total: int) -> None:
        update_job_progress(
            session,
            job,
            progress_current=current,
            progress_total=total,
            tiles_written=progress_state["written"],
            tiles_skipped=progress_state["skipped"],
            output_bytes=progress_state["bytes"],
        )

    def on_tile_outcome(outcome_status: str, output_bytes: int = 0) -> None:
        if outcome_status == "written":
            progress_state["written"] += 1
            progress_state["bytes"] += output_bytes
        elif outcome_status == "skipped_existing":
            progress_state["skipped"] += 1

    try:
        result = build_production_tiles(
            storage,
            session,
            layer=job.layer,
            min_zoom=job.min_zoom,
            max_zoom=job.max_zoom,
            force=job.force,
            dry_run=False,
            limit=job.artifact_limit,
            mark_catalog=job.mark_catalog,
            on_progress=on_progress,
            on_tile_outcome=on_tile_outcome,
        )
    except Exception as exc:
        mark_job_failed(session, job, str(exc))
        logger.exception("Render job id=%s raised during build", job.id)
        return job

    total = max(result.tiles_planned, 1)
    if result.tiles_failed > 0 and result.tiles_written == 0:
        error = "; ".join(result.errors[:5]) if result.errors else "tile build failed"
        mark_job_failed(session, job, error)
        update_job_progress(
            session,
            job,
            progress_current=total,
            progress_total=total,
            tiles_written=result.tiles_written,
            tiles_skipped=result.tiles_skipped_existing,
            output_bytes=result.output_bytes,
        )
        logger.warning("Render job id=%s failed: %s", job.id, error)
        return job

    mark_job_succeeded(
        session,
        job,
        progress_total=total,
        tiles_written=result.tiles_written,
        tiles_skipped=result.tiles_skipped_existing,
        output_bytes=result.output_bytes,
    )
    logger.info(
        "Render job id=%s succeeded tiles_written=%s output_bytes=%s",
        job.id,
        result.tiles_written,
        result.output_bytes,
    )
    return job


def process_next_render_job(session: Session, storage: LocalStorage) -> Optional[RenderJob]:
    """Claim and process the next queued job, or return None if queue empty."""
    job = claim_next_queued_job(session)
    if job is None:
        return None
    return run_render_job(session, storage, job)


def run_worker_loop(
    session: Session,
    storage: LocalStorage,
    *,
    max_jobs: Optional[int] = None,
    sleep_seconds: float = 1.0,
    should_stop: Optional[ShouldStopFn] = None,
) -> int:
    """Process queued jobs in a loop until max_jobs reached or stop requested."""
    stop_check: ShouldStopFn = should_stop or (lambda: False)
    recover_stale_running_jobs(session)
    processed = 0
    logger.info(
        "Render worker loop starting (max_jobs=%s, sleep_seconds=%s)",
        max_jobs,
        sleep_seconds,
    )
    while max_jobs is None or processed < max_jobs:
        if stop_check():
            logger.info("Render worker stop requested; exiting after %s job(s)", processed)
            break

        job = process_next_render_job(session, storage)
        if job is None:
            if _interruptible_sleep(sleep_seconds, stop_check):
                logger.info("Render worker stop requested during idle sleep")
                break
            continue

        processed += 1
        logger.info(
            "Render worker processed job id=%s status=%s (%s/%s)",
            job.id,
            job.status,
            processed,
            max_jobs if max_jobs is not None else "∞",
        )
        if job.status == JOB_STATUS_FAILED and job.attempt_count < job.max_attempts:
            continue

    logger.info("Render worker loop finished: processed %s job(s)", processed)
    return processed
