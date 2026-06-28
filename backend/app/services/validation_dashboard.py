"""Dev validation dashboard summary — prototype only, not verified MRMS."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.catalog_status import build_catalog_status
from backend.app.services.grib2_inspector import detect_decoder_availability
from backend.app.services.render_queue import get_queue_summary
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_report_store import (
    load_latest_benchmark_report,
    load_latest_queue_benchmark_report,
    load_latest_validation_report,
    load_queue_benchmark_history,
    load_validation_history,
)


def build_validation_summary(session: Session, storage: LocalStorage) -> dict[str, Any]:
    """Compact dashboard summary for dev UI and GET /api/validation/summary."""
    availability = detect_decoder_availability()
    queue = get_queue_summary(session)
    validation = load_latest_validation_report(storage)
    benchmark = load_latest_benchmark_report(storage)
    queue_benchmark = load_latest_queue_benchmark_report(storage)
    history = load_validation_history(storage)
    queue_benchmark_history = load_queue_benchmark_history(storage)
    catalog = build_catalog_status(session)

    return {
        "prototype": True,
        "verified_mrms": False,
        "production_rendering_enabled": settings.enable_production_radar_tiles,
        "placeholder_default": not settings.enable_production_radar_tiles
        and not settings.enable_decoded_tiles,
        "decoder_available": availability.any_decoder,
        "decoder_summary": availability.summary_message(),
        "stale_running_job_seconds": settings.stale_running_job_seconds,
        "validation_available": validation is not None,
        "validation": _compact_validation(validation),
        "benchmark_available": benchmark is not None,
        "benchmark": _compact_benchmark(benchmark),
        "queue_benchmark_available": queue_benchmark is not None,
        "queue_benchmark": _compact_queue_benchmark(queue_benchmark),
        "render_queue": queue.to_dict(),
        "validation_history_count": len(history),
        "validation_history": history[:5],
        "queue_benchmark_history_count": len(queue_benchmark_history),
        "catalog": catalog,
    }


def build_validation_latest(storage: LocalStorage) -> dict[str, Any]:
    """Full latest persisted reports for GET /api/validation/latest."""
    return {
        "prototype": True,
        "verified_mrms": False,
        "production_rendering_enabled": settings.enable_production_radar_tiles,
        "validation": load_latest_validation_report(storage),
        "benchmark": load_latest_benchmark_report(storage),
        "queue_benchmark": load_latest_queue_benchmark_report(storage),
    }


def _compact_validation(validation: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if validation is None:
        return None
    tile_cache = validation.get("tile_cache") or {}
    return {
        "validated_at": validation.get("validated_at"),
        "source_mode": validation.get("source_mode"),
        "batch": validation.get("batch", False),
        "requested_frame_count": validation.get("requested_frame_count"),
        "effective_frame_count": validation.get("effective_frame_count"),
        "discovered_count": validation.get("discovered_count", 0),
        "downloaded_count": validation.get("downloaded_count", 0),
        "inspected_count": validation.get("inspected_count", 0),
        "decoded_count": validation.get("decoded_count", 0),
        "render_jobs_enqueued": validation.get("render_jobs_enqueued", 0),
        "worker_jobs_processed": validation.get("worker_jobs_processed", 0),
        "tiles_planned": validation.get("tiles_planned", 0),
        "tiles_written": validation.get("tiles_written", tile_cache.get("tiles_written", 0)),
        "tiles_skipped": validation.get("tiles_skipped", tile_cache.get("tiles_skipped", 0)),
        "output_bytes": validation.get("output_bytes", tile_cache.get("output_bytes", 0)),
        "elapsed_seconds": validation.get("elapsed_seconds"),
        "decoder_available": validation.get("decoder_available", False),
        "tile_cache": tile_cache,
        "warnings": validation.get("warnings", [])[:5],
        "errors": validation.get("errors", [])[:5],
        "verified_mrms": False,
        "prototype": True,
    }


def _compact_benchmark(benchmark: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if benchmark is None:
        return None
    return {
        "benchmarked_at": benchmark.get("benchmarked_at"),
        "source_mode": benchmark.get("source_mode"),
        "stage_timings": benchmark.get("stage_timings", []),
        "min_zoom": benchmark.get("min_zoom"),
        "max_zoom": benchmark.get("max_zoom"),
        "tiles_planned": benchmark.get("tiles_planned", 0),
        "tiles_written": benchmark.get("tiles_written", 0),
        "tiles_skipped": benchmark.get("tiles_skipped", 0),
        "output_bytes": benchmark.get("output_bytes", 0),
        "tile_build_elapsed_seconds": benchmark.get("tile_build_elapsed_seconds", 0.0),
        "decoder_used": benchmark.get("decoder_used"),
        "warnings": benchmark.get("warnings", [])[:5],
        "errors": benchmark.get("errors", [])[:5],
        "verified_mrms": False,
        "prototype": True,
    }


def _compact_queue_benchmark(
    queue_benchmark: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    if queue_benchmark is None:
        return None
    job_summaries = queue_benchmark.get("job_summaries", [])
    compact_jobs = [
        {
            "timestamp": item.get("timestamp"),
            "job_id": item.get("job_id"),
            "status": item.get("status"),
            "min_zoom": item.get("min_zoom"),
            "max_zoom": item.get("max_zoom"),
            "tiles_written": item.get("tiles_written", 0),
            "tiles_skipped": item.get("tiles_skipped", 0),
            "output_bytes": item.get("output_bytes", 0),
            "elapsed_seconds": item.get("elapsed_seconds"),
        }
        for item in job_summaries[:5]
    ]
    return {
        "benchmarked_at": queue_benchmark.get("benchmarked_at"),
        "source_mode": queue_benchmark.get("source_mode"),
        "effective_count": queue_benchmark.get("effective_count"),
        "min_zoom": queue_benchmark.get("min_zoom"),
        "max_zoom": queue_benchmark.get("max_zoom"),
        "dry_run": queue_benchmark.get("dry_run", False),
        "jobs_enqueued": queue_benchmark.get("jobs_enqueued", 0),
        "jobs_processed": queue_benchmark.get("jobs_processed", 0),
        "jobs_succeeded": queue_benchmark.get("jobs_succeeded", 0),
        "jobs_failed": queue_benchmark.get("jobs_failed", 0),
        "total_tiles_written": queue_benchmark.get("total_tiles_written", 0),
        "total_tiles_skipped": queue_benchmark.get("total_tiles_skipped", 0),
        "total_output_bytes": queue_benchmark.get("total_output_bytes", 0),
        "total_elapsed_seconds": queue_benchmark.get("total_elapsed_seconds"),
        "job_summaries": compact_jobs,
        "warnings": queue_benchmark.get("warnings", [])[:5],
        "errors": queue_benchmark.get("errors", [])[:5],
        "verified_mrms": False,
        "prototype": True,
    }
