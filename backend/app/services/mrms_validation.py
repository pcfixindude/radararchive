"""Orchestrate experimental real MRMS validation pipeline (dev/prototype only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional, Protocol

from sqlalchemy.orm import Session

from backend.app.config import MRMS_SOURCE_MODE_REAL, MRMS_SOURCE_MODE_STUB, settings
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.services.grib2_decoder import Grib2DecodeResult, decode_grib2_file
from backend.app.services.grib2_inspect_catalog import find_real_mrms_inspect_candidates
from backend.app.services.grib2_inspector import Grib2InspectResult, detect_decoder_availability, inspect_grib2_file
from backend.app.services.mrms_discovery import register_discovered_files
from backend.app.services.mrms_downloader import DownloadBatchResult, download_pending_mrms
from backend.app.services.render_queue import enqueue_render_job, recover_stale_running_jobs
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_report_store import save_latest_validation_report
from backend.app.sources.mrms import MrmsDiscoveredFile, MrmsDiscoveryError, discover_latest_mrms
from backend.app.workers.render_worker import process_next_render_job

DiscoverFn = Callable[[str, int, str], list[MrmsDiscoveredFile]]
DownloadFn = Callable[[Session, LocalStorage, int, str], DownloadBatchResult]
InspectFn = Callable[[LocalStorage, str], Grib2InspectResult]
DecodeFn = Callable[[LocalStorage, str], Grib2DecodeResult]
WorkerFn = Callable[[Session, LocalStorage], object]


class DiscoverProtocol(Protocol):
    def __call__(
        self,
        product: str,
        *,
        limit: Optional[int] = None,
        mode: Optional[str] = None,
    ) -> list[MrmsDiscoveredFile]: ...


@dataclass
class TileCacheResult:
    tiles_written: int = 0
    tiles_skipped: int = 0
    output_bytes: int = 0
    job_id: Optional[int] = None
    job_status: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "tiles_written": self.tiles_written,
            "tiles_skipped": self.tiles_skipped,
            "output_bytes": self.output_bytes,
            "job_id": self.job_id,
            "job_status": self.job_status,
        }


@dataclass
class MrmsValidationReport:
    source_mode: str
    discovered_count: int = 0
    registered_created: int = 0
    registered_skipped: int = 0
    downloaded_count: int = 0
    download_skipped: int = 0
    inspected_count: int = 0
    decoded_count: int = 0
    render_jobs_enqueued: int = 0
    worker_jobs_processed: int = 0
    stale_jobs_recovered: int = 0
    tile_cache: TileCacheResult = field(default_factory=TileCacheResult)
    decoder_available: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    production_rendering_enabled: bool = False
    verified_mrms: bool = False
    prototype: bool = True
    validated_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "source_mode": self.source_mode,
            "discovered_count": self.discovered_count,
            "registered_created": self.registered_created,
            "registered_skipped": self.registered_skipped,
            "downloaded_count": self.downloaded_count,
            "download_skipped": self.download_skipped,
            "inspected_count": self.inspected_count,
            "decoded_count": self.decoded_count,
            "render_jobs_enqueued": self.render_jobs_enqueued,
            "worker_jobs_processed": self.worker_jobs_processed,
            "stale_jobs_recovered": self.stale_jobs_recovered,
            "tile_cache": self.tile_cache.to_dict(),
            "decoder_available": self.decoder_available,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "production_rendering_enabled": self.production_rendering_enabled,
            "verified_mrms": self.verified_mrms,
            "prototype": self.prototype,
            "validated_at": self.validated_at,
        }


def resolve_validation_source_mode(*, real_requested: bool) -> str:
    """Return stub by default; real only when explicitly requested."""
    if real_requested or settings.mrms_source_mode == MRMS_SOURCE_MODE_REAL:
        return MRMS_SOURCE_MODE_REAL
    return MRMS_SOURCE_MODE_STUB


def _finalize_validation_report(
    report: MrmsValidationReport,
    storage: LocalStorage,
    *,
    persist: bool,
) -> MrmsValidationReport:
    report.validated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if persist:
        save_latest_validation_report(storage, report.to_dict())
    return report


def run_mrms_validation(
    session: Session,
    storage: LocalStorage,
    *,
    product: str = "MRMS_ReflectivityAtLowestAltitude",
    limit: int = 1,
    source_mode: Optional[str] = None,
    run_worker: bool = False,
    discover_fn: Optional[DiscoverProtocol] = None,
    download_fn: Optional[DownloadFn] = None,
    inspect_fn: Optional[InspectFn] = None,
    decode_fn: Optional[DecodeFn] = None,
    worker_fn: Optional[WorkerFn] = None,
    persist: bool = True,
) -> MrmsValidationReport:
    """Run discover → register → download → inspect → decode → enqueue → optional worker."""
    mode = source_mode or settings.mrms_source_mode
    report = MrmsValidationReport(
        source_mode=mode,
        production_rendering_enabled=settings.enable_production_radar_tiles,
        verified_mrms=False,
        prototype=True,
    )

    availability = detect_decoder_availability()
    report.decoder_available = availability.any_decoder

    if catalog_is_empty(session):
        seed_demo_catalog(session, storage=storage)

    report.stale_jobs_recovered = recover_stale_running_jobs(session)

    if mode == MRMS_SOURCE_MODE_STUB:
        report.warnings.append(
            "Stub/offline mode: downloads use local stub files, not NOAA AWS GRIB2. "
            "Inspect/decode/render steps require a real .grib2.gz file."
        )
        report.warnings.append(
            "For network validation use: MRMS_SOURCE_MODE=real make validate-real-mrms ARGS='--real'"
        )

    discover = discover_fn or discover_latest_mrms
    try:
        discoveries = discover(product, limit=limit, mode=mode)
    except MrmsDiscoveryError as exc:
        report.errors.append(f"discovery failed: {exc}")
        return _finalize_validation_report(report, storage, persist=persist)

    report.discovered_count = len(discoveries)
    if not discoveries:
        report.warnings.append("No MRMS candidates discovered.")
        return _finalize_validation_report(report, storage, persist=persist)

    reg = register_discovered_files(session, discoveries)
    report.registered_created = reg.created
    report.registered_skipped = reg.skipped

    do_download = download_fn or (
        lambda sess, stor, lim, m: download_pending_mrms(sess, stor, limit=lim, mode=m)
    )
    try:
        batch = do_download(session, storage, limit, mode)
    except Exception as exc:
        report.errors.append(f"download failed: {exc}")
        return _finalize_validation_report(report, storage, persist=persist)

    report.downloaded_count = len(batch.downloaded)
    report.download_skipped = batch.skipped
    for radar_id, timestamp, message in batch.failed:
        report.errors.append(f"download failed id={radar_id} {timestamp}: {message}")

    candidates = find_real_mrms_inspect_candidates(session, storage, limit=limit)
    if not candidates:
        if mode == MRMS_SOURCE_MODE_STUB:
            report.warnings.append(
                "No real local .grib2.gz catalog candidates after download (expected in stub mode)."
            )
        else:
            report.warnings.append("No inspectable real MRMS files in catalog after download.")
        return _finalize_validation_report(report, storage, persist=persist)

    inspect = inspect_fn or inspect_grib2_file
    decode = decode_fn or decode_grib2_file

    decoded_artifacts = 0
    for candidate in candidates:
        inspect_result = inspect(storage, candidate.raw_path)
        if inspect_result.inspectable or inspect_result.file_exists:
            report.inspected_count += 1
        if inspect_result.error:
            report.warnings.append(f"inspect {candidate.raw_path}: {inspect_result.error}")
            continue
        if not inspect_result.inspectable:
            report.warnings.append(
                f"inspect skipped non-inspectable file: {candidate.raw_path} ({inspect_result.raw_kind})"
            )
            continue

        if not availability.any_decoder:
            report.warnings.append(
                "No optional GRIB2 decoder installed; decode step skipped (safe offline behavior)."
            )
            break

        decode_result = decode(storage, candidate.raw_path)
        if decode_result.decoder_unavailable:
            report.warnings.append("Decoder reported unavailable during decode step.")
            break
        if decode_result.error:
            report.warnings.append(f"decode {candidate.raw_path}: {decode_result.error}")
            continue
        if decode_result.success:
            decoded_artifacts += 1

    report.decoded_count = decoded_artifacts

    if decoded_artifacts == 0:
        report.warnings.append("No decode artifacts produced; render job not enqueued.")
        return _finalize_validation_report(report, storage, persist=persist)

    job = enqueue_render_job(
        session,
        layer="mrms_reflectivity",
        min_zoom=0,
        max_zoom=0,
        force=False,
        mark_catalog=False,
        artifact_limit=limit,
    )
    report.render_jobs_enqueued = 1

    if not run_worker:
        report.warnings.append("Worker not run; use --run-worker to process the enqueued job.")
        return _finalize_validation_report(report, storage, persist=persist)

    worker = worker_fn or process_next_render_job
    processed = worker(session, storage)
    if processed is None:
        report.warnings.append("Worker found no queued jobs to process.")
        return _finalize_validation_report(report, storage, persist=persist)

    report.worker_jobs_processed = 1
    report.tile_cache = TileCacheResult(
        tiles_written=getattr(processed, "tiles_written", 0),
        tiles_skipped=getattr(processed, "tiles_skipped", 0),
        output_bytes=getattr(processed, "output_bytes", 0),
        job_id=getattr(processed, "id", None),
        job_status=getattr(processed, "status", None),
    )
    if getattr(processed, "status", None) == "failed":
        report.warnings.append(
            f"Worker job {processed.id} failed: {getattr(processed, 'error_message', '')}"
        )

    report.validated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if persist:
        save_latest_validation_report(storage, report.to_dict())
    return report
