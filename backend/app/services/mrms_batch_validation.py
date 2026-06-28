"""Batch MRMS validation for multiple frames (dev/prototype only)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from sqlalchemy.orm import Session

from backend.app.config import MRMS_SOURCE_MODE_REAL, MRMS_SOURCE_MODE_STUB, settings
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.services.grib2_decoder import Grib2DecodeResult, decode_grib2_file
from backend.app.services.grib2_inspect_catalog import find_real_mrms_inspect_candidates
from backend.app.services.grib2_inspector import Grib2InspectResult, detect_decoder_availability, inspect_grib2_file
from backend.app.services.mrms_discovery import register_discovered_files
from backend.app.services.mrms_downloader import DownloadBatchResult, download_pending_mrms
from backend.app.services.mrms_validation import DiscoverProtocol, DownloadFn, resolve_validation_source_mode
from backend.app.services.production_tile_builder import build_production_tiles, plan_production_tile_jobs
from backend.app.services.render_queue import enqueue_render_job, recover_stale_running_jobs
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_report_store import save_validation_report
from backend.app.sources.mrms import MrmsDiscoveryError, discover_latest_mrms
from backend.app.workers.render_worker import process_next_render_job

DEFAULT_BATCH_FRAME_COUNT = 3
MAX_BATCH_FRAME_COUNT = 10


@dataclass
class FrameValidationSummary:
    timestamp: str
    radar_file_id: Optional[int] = None
    raw_path: Optional[str] = None
    downloaded: bool = False
    inspected: bool = False
    decoded: bool = False
    decode_status: str = "pending"
    render_job_id: Optional[int] = None
    min_zoom: int = 0
    max_zoom: int = 0
    tiles_planned: int = 0
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
            "raw_path": self.raw_path,
            "downloaded": self.downloaded,
            "inspected": self.inspected,
            "decoded": self.decoded,
            "decode_status": self.decode_status,
            "render_job_id": self.render_job_id,
            "min_zoom": self.min_zoom,
            "max_zoom": self.max_zoom,
            "tiles_planned": self.tiles_planned,
            "tiles_written": self.tiles_written,
            "tiles_skipped": self.tiles_skipped,
            "output_bytes": self.output_bytes,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass
class BatchValidationReport:
    source_mode: str
    requested_frame_count: int = DEFAULT_BATCH_FRAME_COUNT
    effective_frame_count: int = DEFAULT_BATCH_FRAME_COUNT
    discovered_count: int = 0
    registered_created: int = 0
    registered_skipped: int = 0
    downloaded_count: int = 0
    download_skipped: int = 0
    inspected_count: int = 0
    decoded_count: int = 0
    render_jobs_enqueued: int = 0
    worker_jobs_processed: int = 0
    tiles_planned: int = 0
    tiles_written: int = 0
    tiles_skipped: int = 0
    output_bytes: int = 0
    elapsed_seconds: float = 0.0
    stale_jobs_recovered: int = 0
    decoder_available: bool = False
    frame_summaries: list[FrameValidationSummary] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    production_rendering_enabled: bool = False
    verified_mrms: bool = False
    prototype: bool = True
    batch: bool = True
    validated_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "source_mode": self.source_mode,
            "requested_frame_count": self.requested_frame_count,
            "effective_frame_count": self.effective_frame_count,
            "discovered_count": self.discovered_count,
            "registered_created": self.registered_created,
            "registered_skipped": self.registered_skipped,
            "downloaded_count": self.downloaded_count,
            "download_skipped": self.download_skipped,
            "inspected_count": self.inspected_count,
            "decoded_count": self.decoded_count,
            "render_jobs_enqueued": self.render_jobs_enqueued,
            "worker_jobs_processed": self.worker_jobs_processed,
            "tiles_planned": self.tiles_planned,
            "tiles_written": self.tiles_written,
            "tiles_skipped": self.tiles_skipped,
            "output_bytes": self.output_bytes,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
            "stale_jobs_recovered": self.stale_jobs_recovered,
            "decoder_available": self.decoder_available,
            "frame_summaries": [frame.to_dict() for frame in self.frame_summaries],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "production_rendering_enabled": self.production_rendering_enabled,
            "verified_mrms": self.verified_mrms,
            "prototype": self.prototype,
            "batch": self.batch,
            "validated_at": self.validated_at,
            "tile_cache": {
                "tiles_written": self.tiles_written,
                "tiles_skipped": self.tiles_skipped,
                "output_bytes": self.output_bytes,
            },
        }


def resolve_batch_frame_count(requested: int) -> tuple[int, list[str]]:
    """Cap batch size to a safe maximum."""
    warnings: list[str] = []
    if requested < 1:
        warnings.append(
            f"Invalid frame count {requested}; using default {DEFAULT_BATCH_FRAME_COUNT}"
        )
        return DEFAULT_BATCH_FRAME_COUNT, warnings
    if requested > MAX_BATCH_FRAME_COUNT:
        warnings.append(
            f"Requested {requested} frames exceeds max {MAX_BATCH_FRAME_COUNT}; capping"
        )
        return MAX_BATCH_FRAME_COUNT, warnings
    return requested, warnings


def run_mrms_batch_validation(
    session: Session,
    storage: LocalStorage,
    *,
    frame_count: int = DEFAULT_BATCH_FRAME_COUNT,
    product: str = "MRMS_ReflectivityAtLowestAltitude",
    source_mode: Optional[str] = None,
    run_worker: bool = False,
    discover_fn: Optional[DiscoverProtocol] = None,
    download_fn: Optional[DownloadFn] = None,
    inspect_fn: Optional[Callable] = None,
    decode_fn: Optional[Callable] = None,
    worker_fn: Optional[Callable] = None,
    persist: bool = True,
) -> BatchValidationReport:
    """Discover/register/download/inspect/decode up to N MRMS frames."""
    start = time.perf_counter()
    mode = source_mode or settings.mrms_source_mode
    effective_count, cap_warnings = resolve_batch_frame_count(frame_count)

    report = BatchValidationReport(
        source_mode=mode,
        requested_frame_count=frame_count,
        effective_frame_count=effective_count,
        production_rendering_enabled=settings.enable_production_radar_tiles,
        verified_mrms=False,
        prototype=True,
    )
    report.warnings.extend(cap_warnings)

    availability = detect_decoder_availability()
    report.decoder_available = availability.any_decoder

    if catalog_is_empty(session):
        seed_demo_catalog(session, storage=storage)

    report.stale_jobs_recovered = recover_stale_running_jobs(session)

    if mode == MRMS_SOURCE_MODE_STUB:
        report.warnings.append(
            "Stub/offline mode: stub downloads are not real GRIB2; inspect/decode need real .grib2.gz"
        )
        report.warnings.append(
            "Real mode: MRMS_SOURCE_MODE=real make validate-real-mrms-batch ARGS='--real'"
        )

    discover = discover_fn or discover_latest_mrms
    try:
        discoveries = discover(product, limit=effective_count, mode=mode)
    except MrmsDiscoveryError as exc:
        report.errors.append(f"discovery failed: {exc}")
        return _finalize_batch_report(report, storage, start, persist=persist)

    report.discovered_count = len(discoveries)
    if not discoveries:
        report.warnings.append("No MRMS candidates discovered.")
        return _finalize_batch_report(report, storage, start, persist=persist)

    reg = register_discovered_files(session, discoveries)
    report.registered_created = reg.created
    report.registered_skipped = reg.skipped

    do_download = download_fn or (
        lambda sess, stor, lim, m: download_pending_mrms(sess, stor, limit=lim, mode=m)
    )
    try:
        batch = do_download(session, storage, effective_count, mode)
    except Exception as exc:
        report.errors.append(f"download failed: {exc}")
        return _finalize_batch_report(report, storage, start, persist=persist)

    report.downloaded_count = len(batch.downloaded)
    report.download_skipped = batch.skipped
    downloaded_timestamps = {item.timestamp for item in batch.downloaded}
    for radar_id, timestamp, message in batch.failed:
        report.errors.append(f"download failed id={radar_id} {timestamp}: {message}")

    inspect = inspect_fn or inspect_grib2_file
    decode = decode_fn or decode_grib2_file
    candidates = find_real_mrms_inspect_candidates(session, storage, limit=effective_count)

    if not candidates:
        for item in discoveries[:effective_count]:
            frame_start = time.perf_counter()
            frame = FrameValidationSummary(timestamp=item.timestamp)
            if item.timestamp in downloaded_timestamps:
                frame.downloaded = True
                frame.decode_status = "downloaded"
            frame.warnings.append("No inspectable real .grib2.gz on disk for this frame")
            frame.elapsed_seconds = time.perf_counter() - frame_start
            report.frame_summaries.append(frame)
        report.warnings.append("No inspectable real MRMS catalog candidates after download.")
        return _finalize_batch_report(report, storage, start, persist=persist)

    for candidate in candidates:
        frame_start = time.perf_counter()
        radar_file_id = getattr(candidate, "radar_file_id", None)
        if not isinstance(radar_file_id, int):
            radar_file_id = None
        frame = FrameValidationSummary(
            timestamp=candidate.timestamp,
            radar_file_id=radar_file_id,
            raw_path=candidate.raw_path,
            downloaded=candidate.timestamp in downloaded_timestamps,
            min_zoom=0,
            max_zoom=0,
        )
        if frame.downloaded:
            frame.decode_status = "downloaded"
        inspect_result = inspect(storage, candidate.raw_path)
        if isinstance(inspect_result, Grib2InspectResult):
            if inspect_result.inspectable or inspect_result.file_exists:
                frame.inspected = True
                frame.decode_status = "inspected"
                report.inspected_count += 1
            if inspect_result.error:
                frame.errors.append(inspect_result.error)
            if not inspect_result.inspectable:
                frame.warnings.append(f"not inspectable ({inspect_result.raw_kind})")
                frame.elapsed_seconds = time.perf_counter() - frame_start
                report.frame_summaries.append(frame)
                continue

        if not availability.any_decoder:
            frame.warnings.append("no optional decoder installed")
            frame.decode_status = "inspected" if frame.inspected else frame.decode_status
            frame.elapsed_seconds = time.perf_counter() - frame_start
            report.frame_summaries.append(frame)
            if report.inspected_count and report.decoded_count == 0:
                report.warnings.append("No optional GRIB2 decoder; decode skipped for all frames.")
            continue

        decode_result = decode(storage, candidate.raw_path)
        if isinstance(decode_result, Grib2DecodeResult):
            if decode_result.decoder_unavailable:
                frame.warnings.append("decoder unavailable")
                frame.decode_status = "decoder_unavailable"
            elif decode_result.error:
                frame.errors.append(decode_result.error)
                frame.decode_status = "decode_failed"
            elif decode_result.success:
                frame.decoded = True
                frame.decode_status = "decoded"
                report.decoded_count += 1
        frame.elapsed_seconds = time.perf_counter() - frame_start
        report.frame_summaries.append(frame)

    if report.decoded_count > 0:
        planned_jobs, _plan_errors = plan_production_tile_jobs(
            storage,
            session,
            layer="mrms_reflectivity",
            min_zoom=0,
            max_zoom=0,
        )
        planned_by_timestamp: dict[str, int] = {}
        for job in planned_jobs:
            planned_by_timestamp[job.timestamp] = planned_by_timestamp.get(job.timestamp, 0) + 1
        for frame in report.frame_summaries:
            if frame.decoded:
                frame.tiles_planned = planned_by_timestamp.get(frame.timestamp, 0)

    if report.decoded_count > 0:
        try:
            build_result = build_production_tiles(
                storage,
                session,
                layer="mrms_reflectivity",
                min_zoom=0,
                max_zoom=0,
                force=False,
                dry_run=False,
                limit=report.decoded_count,
                mark_catalog=False,
            )
            report.tiles_planned = build_result.tiles_planned
            report.tiles_written = build_result.tiles_written
            report.tiles_skipped = build_result.tiles_skipped_existing
            report.output_bytes = build_result.output_bytes
            if build_result.errors:
                report.warnings.extend(build_result.errors[:5])
        except Exception as exc:
            report.errors.append(f"tile build failed: {exc}")

        job = enqueue_render_job(
            session,
            layer="mrms_reflectivity",
            min_zoom=0,
            max_zoom=0,
            force=False,
            mark_catalog=False,
            artifact_limit=report.decoded_count,
        )
        report.render_jobs_enqueued = 1
        for frame in report.frame_summaries:
            if frame.decoded:
                frame.render_job_id = job.id

        if run_worker:
            worker = worker_fn or process_next_render_job
            processed = worker(session, storage)
            if processed is not None:
                report.worker_jobs_processed = 1
                if report.tiles_written == 0:
                    report.tiles_written = getattr(processed, "tiles_written", 0)
                    report.tiles_skipped = getattr(processed, "tiles_skipped", 0)
                    report.output_bytes = getattr(processed, "output_bytes", 0)
                for frame in report.frame_summaries:
                    if frame.decoded and frame.render_job_id == processed.id:
                        frame.tiles_written = getattr(processed, "tiles_written", 0)
                        frame.tiles_skipped = getattr(processed, "tiles_skipped", 0)
                        frame.output_bytes = getattr(processed, "output_bytes", 0)
            else:
                report.warnings.append("Worker found no queued jobs to process.")
        else:
            report.warnings.append("Worker not run; use --run-worker to process enqueued job.")
    else:
        report.warnings.append("No decode artifacts produced across batch.")

    return _finalize_batch_report(report, storage, start, persist=persist)


def _finalize_batch_report(
    report: BatchValidationReport,
    storage: LocalStorage,
    start_time: float,
    *,
    persist: bool,
) -> BatchValidationReport:
    report.elapsed_seconds = time.perf_counter() - start_time
    report.validated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if persist:
        save_validation_report(storage, report.to_dict())
    return report
