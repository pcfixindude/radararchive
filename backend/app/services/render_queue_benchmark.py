"""Multi-zoom render queue benchmark for small batches (dev/prototype only)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from sqlalchemy.orm import Session

from backend.app.config import MRMS_SOURCE_MODE_REAL, MRMS_SOURCE_MODE_STUB, settings
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.models import RadarFile
from backend.app.models.render_job import (
    JOB_STATUS_FAILED,
    JOB_STATUS_QUEUED,
    JOB_STATUS_RUNNING,
    JOB_STATUS_SUCCEEDED,
    RenderJob,
)
from backend.app.services.grib2_inspect_catalog import find_real_mrms_inspect_candidates
from backend.app.services.production_tile_builder import (
    MAX_ALLOWED_ZOOM,
    clamp_zoom_range,
    plan_production_tile_jobs,
)
from backend.app.services.render_queue import (
    enqueue_render_job,
    get_render_job,
    recover_stale_running_jobs,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_report_store import save_queue_benchmark_report
from backend.app.workers.render_worker import run_render_job

DEFAULT_QUEUE_BENCHMARK_COUNT = 3
MAX_QUEUE_BENCHMARK_COUNT = 10
DEFAULT_MIN_ZOOM = 0
DEFAULT_MAX_ZOOM = 1


@dataclass
class JobBenchmarkSummary:
    timestamp: Optional[str] = None
    radar_file_id: Optional[int] = None
    job_id: Optional[int] = None
    status: str = "planned"
    decode_status: str = "unknown"
    min_zoom: int = 0
    max_zoom: int = 0
    tiles_planned: int = 0
    progress_total: int = 0
    tiles_written: int = 0
    tiles_skipped: int = 0
    output_bytes: int = 0
    elapsed_seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "radar_file_id": self.radar_file_id,
            "job_id": self.job_id,
            "status": self.status,
            "decode_status": self.decode_status,
            "min_zoom": self.min_zoom,
            "max_zoom": self.max_zoom,
            "tiles_planned": self.tiles_planned,
            "progress_total": self.progress_total,
            "tiles_written": self.tiles_written,
            "tiles_skipped": self.tiles_skipped,
            "output_bytes": self.output_bytes,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass
class RenderQueueBenchmarkReport:
    source_mode: str
    requested_count: int = DEFAULT_QUEUE_BENCHMARK_COUNT
    effective_count: int = DEFAULT_QUEUE_BENCHMARK_COUNT
    min_zoom: int = DEFAULT_MIN_ZOOM
    max_zoom: int = DEFAULT_MAX_ZOOM
    force: bool = False
    dry_run: bool = False
    jobs_enqueued: int = 0
    jobs_processed: int = 0
    jobs_succeeded: int = 0
    jobs_failed: int = 0
    total_tiles_written: int = 0
    total_tiles_skipped: int = 0
    total_output_bytes: int = 0
    total_elapsed_seconds: float = 0.0
    stale_jobs_recovered: int = 0
    job_summaries: list[JobBenchmarkSummary] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    production_rendering_enabled: bool = False
    verified_mrms: bool = False
    prototype: bool = True
    benchmarked_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "source_mode": self.source_mode,
            "requested_count": self.requested_count,
            "effective_count": self.effective_count,
            "min_zoom": self.min_zoom,
            "max_zoom": self.max_zoom,
            "force": self.force,
            "dry_run": self.dry_run,
            "jobs_enqueued": self.jobs_enqueued,
            "jobs_processed": self.jobs_processed,
            "jobs_succeeded": self.jobs_succeeded,
            "jobs_failed": self.jobs_failed,
            "total_tiles_written": self.total_tiles_written,
            "total_tiles_skipped": self.total_tiles_skipped,
            "total_output_bytes": self.total_output_bytes,
            "total_elapsed_seconds": round(self.total_elapsed_seconds, 4),
            "stale_jobs_recovered": self.stale_jobs_recovered,
            "job_summaries": [item.to_dict() for item in self.job_summaries],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "production_rendering_enabled": self.production_rendering_enabled,
            "verified_mrms": self.verified_mrms,
            "prototype": self.prototype,
            "benchmarked_at": self.benchmarked_at,
        }


def resolve_benchmark_count(requested: int) -> tuple[int, list[str]]:
    warnings: list[str] = []
    if requested < 1:
        warnings.append(
            f"Invalid count {requested}; using default {DEFAULT_QUEUE_BENCHMARK_COUNT}"
        )
        return DEFAULT_QUEUE_BENCHMARK_COUNT, warnings
    if requested > MAX_QUEUE_BENCHMARK_COUNT:
        warnings.append(
            f"Requested count {requested} exceeds max {MAX_QUEUE_BENCHMARK_COUNT}; capping"
        )
        return MAX_QUEUE_BENCHMARK_COUNT, warnings
    return requested, warnings


def resolve_benchmark_zoom(
    min_zoom: int,
    max_zoom: int,
) -> tuple[int, int, list[str]]:
    warnings: list[str] = []
    lo, hi = clamp_zoom_range(min_zoom, max_zoom)
    if min_zoom != lo or max_zoom != hi:
        warnings.append(
            f"Zoom range clamped to safe bounds {lo}–{hi} (max allowed zoom {MAX_ALLOWED_ZOOM})"
        )
    if lo > hi:
        warnings.append(f"min_zoom {min_zoom} > max_zoom {max_zoom}; using {lo}–{lo}")
        hi = lo
    return lo, hi, warnings


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _select_benchmark_frames(
    session: Session,
    storage: LocalStorage,
    count: int,
) -> list[dict[str, Optional[str | int]]]:
    frames: list[dict[str, Optional[str | int]]] = []
    seen: set[str] = set()

    for candidate in find_real_mrms_inspect_candidates(session, storage, limit=count):
        if candidate.timestamp in seen:
            continue
        seen.add(candidate.timestamp)
        frames.append(
            {
                "timestamp": candidate.timestamp,
                "raw_path": candidate.raw_path,
                "radar_file_id": candidate.radar_file_id,
            }
        )
        if len(frames) >= count:
            return frames

    rows = (
        session.query(RadarFile)
        .filter(RadarFile.product_id == "mrms_reflectivity")
        .order_by(RadarFile.timestamp.desc())
        .limit(count * 2)
        .all()
    )
    for row in rows:
        if row.timestamp in seen:
            continue
        seen.add(row.timestamp)
        frames.append(
            {
                "timestamp": row.timestamp,
                "raw_path": row.raw_path,
                "radar_file_id": row.id,
            }
        )
        if len(frames) >= count:
            break
    return frames


def _decode_status_for_frame(storage: LocalStorage, raw_path: Optional[str]) -> str:
    if not raw_path:
        return "no_raw_path"
    from backend.app.services.decoded_tile_cache import list_decode_artifact_dirs, load_decode_manifest

    for output_dir in list_decode_artifact_dirs(storage):
        manifest = load_decode_manifest(storage, output_dir)
        if manifest is not None and manifest.raw_path == raw_path:
            return "decoded"
    return "not_decoded"


def _estimate_planned_tiles(
    storage: LocalStorage,
    session: Session,
    *,
    min_zoom: int,
    max_zoom: int,
    limit: int,
) -> int:
    planned, _errors = plan_production_tile_jobs(
        storage,
        session,
        layer="mrms_reflectivity",
        min_zoom=min_zoom,
        max_zoom=max_zoom,
        limit=limit,
    )
    return len(planned)


def _claim_and_run_job(
    session: Session,
    storage: LocalStorage,
    job_id: int,
    worker_fn: Callable[[Session, LocalStorage, RenderJob], RenderJob],
) -> Optional[RenderJob]:
    job = get_render_job(session, job_id)
    if job is None or job.status != JOB_STATUS_QUEUED:
        return job
    job.status = JOB_STATUS_RUNNING
    job.attempt_count += 1
    job.started_at = _utc_now()
    job.next_retry_at = None
    session.commit()
    session.refresh(job)
    return worker_fn(session, storage, job)


def _job_summary_from_render_job(
    job: Optional[RenderJob],
    *,
    timestamp: Optional[str],
    radar_file_id: Optional[int],
    decode_status: str,
    min_zoom: int,
    max_zoom: int,
    elapsed_seconds: float,
    tiles_planned: int = 0,
    warnings: Optional[list[str]] = None,
    errors: Optional[list[str]] = None,
) -> JobBenchmarkSummary:
    if job is None:
        return JobBenchmarkSummary(
            timestamp=timestamp,
            radar_file_id=radar_file_id,
            status="missing",
            decode_status=decode_status,
            min_zoom=min_zoom,
            max_zoom=max_zoom,
            tiles_planned=tiles_planned,
            elapsed_seconds=elapsed_seconds,
            errors=errors or ["job not found"],
        )
    job_warnings = list(warnings or [])
    job_errors = list(errors or [])
    if job.error_message:
        job_errors.append(job.error_message)
    planned = tiles_planned or job.progress_total
    return JobBenchmarkSummary(
        timestamp=timestamp or job.timestamp,
        radar_file_id=radar_file_id,
        job_id=job.id,
        status=job.status,
        decode_status=decode_status,
        min_zoom=job.min_zoom,
        max_zoom=job.max_zoom,
        tiles_planned=planned,
        progress_total=job.progress_total,
        tiles_written=job.tiles_written,
        tiles_skipped=job.tiles_skipped,
        output_bytes=job.output_bytes,
        elapsed_seconds=elapsed_seconds,
        warnings=job_warnings,
        errors=job_errors,
    )


def run_render_queue_benchmark(
    session: Session,
    storage: LocalStorage,
    *,
    count: int = DEFAULT_QUEUE_BENCHMARK_COUNT,
    min_zoom: int = DEFAULT_MIN_ZOOM,
    max_zoom: int = DEFAULT_MAX_ZOOM,
    force: bool = False,
    dry_run: bool = False,
    source_mode: Optional[str] = None,
    persist: bool = True,
    worker_fn: Optional[Callable[[Session, LocalStorage, RenderJob], RenderJob]] = None,
) -> RenderQueueBenchmarkReport:
    """Enqueue one render job per frame and process through the worker (bounded)."""
    start = time.perf_counter()
    mode = source_mode or settings.mrms_source_mode
    effective_count, count_warnings = resolve_benchmark_count(count)
    lo, hi, zoom_warnings = resolve_benchmark_zoom(min_zoom, max_zoom)
    worker = worker_fn or run_render_job

    report = RenderQueueBenchmarkReport(
        source_mode=mode,
        requested_count=count,
        effective_count=effective_count,
        min_zoom=lo,
        max_zoom=hi,
        force=force,
        dry_run=dry_run,
        production_rendering_enabled=settings.enable_production_radar_tiles,
        verified_mrms=False,
        prototype=True,
    )
    report.warnings.extend(count_warnings)
    report.warnings.extend(zoom_warnings)
    report.warnings.append(
        "Queue benchmark is experimental prototype tooling — not verified MRMS production output"
    )
    if not settings.enable_production_radar_tiles:
        report.warnings.append(
            "Production tile serving remains disabled (ENABLE_PRODUCTION_RADAR_TILES=false)"
        )
    if dry_run:
        report.warnings.append("Dry run: jobs planned only; nothing enqueued or processed")
    if mode == MRMS_SOURCE_MODE_STUB:
        report.warnings.append(
            "Stub/offline mode: using local catalog only; no network discovery/download"
        )
    elif mode == MRMS_SOURCE_MODE_REAL:
        report.warnings.append(
            "Real mode selected: ensure local MRMS files exist (run batch validation first)"
        )

    if catalog_is_empty(session):
        seed_demo_catalog(session, storage=storage)

    report.stale_jobs_recovered = recover_stale_running_jobs(session)
    frames = _select_benchmark_frames(session, storage, effective_count)
    if not frames:
        report.errors.append("No catalog frames available for queue benchmark")
        report.total_elapsed_seconds = time.perf_counter() - start
        report.benchmarked_at = _utc_now()
        if persist:
            save_queue_benchmark_report(storage, report.to_dict())
        return report

    if len(frames) < effective_count:
        report.warnings.append(
            f"Only {len(frames)} frame(s) available (requested {effective_count})"
        )
        report.effective_count = len(frames)

    enqueued_ids: list[int] = []

    for frame in frames:
        frame_start = time.perf_counter()
        timestamp = str(frame["timestamp"])
        raw_path = frame.get("raw_path")
        radar_file_id = frame.get("radar_file_id")
        if isinstance(radar_file_id, str):
            radar_file_id = int(radar_file_id) if radar_file_id.isdigit() else None
        decode_status = _decode_status_for_frame(storage, str(raw_path) if raw_path else None)

        if dry_run:
            planned_tiles = _estimate_planned_tiles(
                storage,
                session,
                min_zoom=lo,
                max_zoom=hi,
                limit=1,
            )
            summary = JobBenchmarkSummary(
                timestamp=timestamp,
                radar_file_id=int(radar_file_id) if radar_file_id is not None else None,
                job_id=None,
                status="dry_run",
                decode_status=decode_status,
                min_zoom=lo,
                max_zoom=hi,
                tiles_planned=planned_tiles,
                progress_total=planned_tiles,
                elapsed_seconds=time.perf_counter() - frame_start,
            )
            if planned_tiles == 0:
                summary.warnings.append(
                    "No decode artifacts for tile planning; worker would likely write 0 tiles"
                )
            report.job_summaries.append(summary)
            continue

        job = enqueue_render_job(
            session,
            timestamp=timestamp,
            min_zoom=lo,
            max_zoom=hi,
            force=force,
            mark_catalog=False,
            artifact_limit=1,
        )
        enqueued_ids.append(job.id)
        report.jobs_enqueued += 1

    if not dry_run:
        for job_id in enqueued_ids:
            frame_start = time.perf_counter()
            timestamp = None
            radar_file_id = None
            decode_status = "unknown"
            pending = get_render_job(session, job_id)
            if pending is not None:
                timestamp = pending.timestamp
                for frame in frames:
                    if frame.get("timestamp") == pending.timestamp:
                        radar_file_id = frame.get("radar_file_id")
                        decode_status = _decode_status_for_frame(
                            storage,
                            str(frame.get("raw_path")) if frame.get("raw_path") else None,
                        )
                        break
            planned_tiles = _estimate_planned_tiles(
                storage,
                session,
                min_zoom=lo,
                max_zoom=hi,
                limit=1,
            )
            finished = _claim_and_run_job(session, storage, job_id, worker)
            report.jobs_processed += 1
            summary = _job_summary_from_render_job(
                finished,
                timestamp=timestamp,
                radar_file_id=int(radar_file_id) if isinstance(radar_file_id, int) else None,
                decode_status=decode_status,
                min_zoom=lo,
                max_zoom=hi,
                elapsed_seconds=time.perf_counter() - frame_start,
                tiles_planned=planned_tiles,
            )
            report.job_summaries.append(summary)
            if finished is None:
                report.jobs_failed += 1
                continue
            if finished.status == JOB_STATUS_SUCCEEDED:
                report.jobs_succeeded += 1
            elif finished.status == JOB_STATUS_FAILED:
                report.jobs_failed += 1
            report.total_tiles_written += finished.tiles_written
            report.total_tiles_skipped += finished.tiles_skipped
            report.total_output_bytes += finished.output_bytes

    report.total_elapsed_seconds = time.perf_counter() - start
    report.benchmarked_at = _utc_now()
    if persist:
        save_queue_benchmark_report(storage, report.to_dict())
    return report
