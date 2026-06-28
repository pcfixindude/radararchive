"""Process queued production tile render jobs using Phase 16 builder."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.render_job import JOB_TYPE_PRODUCTION_TILES, RenderJob
from backend.app.services.production_tile_builder import build_production_tiles
from backend.app.services.render_queue import (
    claim_next_queued_job,
    mark_job_failed,
    mark_job_succeeded,
    update_job_progress,
)
from backend.app.services.storage import LocalStorage


def run_render_job(session: Session, storage: LocalStorage, job: RenderJob) -> RenderJob:
    """Execute one render job (caller must set status to running or use claim_next)."""
    if job.job_type != JOB_TYPE_PRODUCTION_TILES:
        mark_job_failed(session, job, f"Unsupported job_type: {job.job_type}")
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
        return job

    mark_job_succeeded(
        session,
        job,
        progress_total=total,
        tiles_written=result.tiles_written,
        tiles_skipped=result.tiles_skipped_existing,
        output_bytes=result.output_bytes,
    )
    return job


def process_next_render_job(session: Session, storage: LocalStorage) -> Optional[RenderJob]:
    """Claim and process the next queued job, or return None if queue empty."""
    job = claim_next_queued_job(session)
    if job is None:
        return None
    return run_render_job(session, storage, job)
