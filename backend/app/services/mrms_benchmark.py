"""Benchmark one MRMS frame through experimental pipeline with per-stage timing."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.grib2_decoder import Grib2DecodeResult, decode_grib2_file
from backend.app.services.grib2_inspect_catalog import find_real_mrms_inspect_candidates
from backend.app.services.grib2_inspector import detect_decoder_availability
from backend.app.services.mrms_validation import (
    DiscoverProtocol,
    DownloadFn,
    MrmsValidationReport,
    resolve_validation_source_mode,
    run_mrms_validation,
)
from backend.app.services.production_tile_builder import build_production_tiles
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_report_store import save_latest_benchmark_report


@dataclass
class StageTiming:
    stage: str
    elapsed_seconds: float

    def to_dict(self) -> dict:
        return {"stage": self.stage, "elapsed_seconds": round(self.elapsed_seconds, 4)}


@dataclass
class MrmsBenchmarkReport:
    source_mode: str
    stage_timings: list[StageTiming] = field(default_factory=list)
    min_zoom: int = 0
    max_zoom: int = 0
    tiles_planned: int = 0
    tiles_written: int = 0
    tiles_skipped: int = 0
    output_bytes: int = 0
    tile_build_elapsed_seconds: float = 0.0
    decoder_used: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    validation: Optional[dict] = None
    verified_mrms: bool = False
    prototype: bool = True

    def to_dict(self) -> dict:
        return {
            "source_mode": self.source_mode,
            "stage_timings": [item.to_dict() for item in self.stage_timings],
            "min_zoom": self.min_zoom,
            "max_zoom": self.max_zoom,
            "tiles_planned": self.tiles_planned,
            "tiles_written": self.tiles_written,
            "tiles_skipped": self.tiles_skipped,
            "output_bytes": self.output_bytes,
            "tile_build_elapsed_seconds": round(self.tile_build_elapsed_seconds, 4),
            "decoder_used": self.decoder_used,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "validation": self.validation,
            "verified_mrms": self.verified_mrms,
            "prototype": self.prototype,
        }


def _timed_stage(timings: list[StageTiming], stage: str, fn: Callable[[], object]) -> object:
    start = time.perf_counter()
    result = fn()
    timings.append(StageTiming(stage=stage, elapsed_seconds=time.perf_counter() - start))
    return result


def run_mrms_benchmark(
    session: Session,
    storage: LocalStorage,
    *,
    product: str = "MRMS_ReflectivityAtLowestAltitude",
    limit: int = 1,
    source_mode: Optional[str] = None,
    min_zoom: int = 0,
    max_zoom: int = 0,
    persist: bool = True,
    discover_fn: Optional[DiscoverProtocol] = None,
    download_fn: Optional[DownloadFn] = None,
    inspect_fn: Optional[Callable] = None,
    decode_fn: Optional[Callable] = None,
) -> MrmsBenchmarkReport:
    """Run validation with timing and optional timed tile build."""
    mode = source_mode or settings.mrms_source_mode
    benchmark = MrmsBenchmarkReport(source_mode=mode, min_zoom=min_zoom, max_zoom=max_zoom)
    timings: list[StageTiming] = []

    def run_validation() -> MrmsValidationReport:
        return run_mrms_validation(
            session,
            storage,
            product=product,
            limit=limit,
            source_mode=mode,
            run_worker=False,
            discover_fn=discover_fn,
            download_fn=download_fn,
            inspect_fn=inspect_fn,
            decode_fn=decode_fn,
        )

    validation_report = _timed_stage(timings, "validation_pipeline", run_validation)
    benchmark.validation = validation_report.to_dict()
    benchmark.warnings.extend(validation_report.warnings)
    benchmark.errors.extend(validation_report.errors)

    availability = detect_decoder_availability()
    if validation_report.decoded_count > 0 and availability.any_decoder:
        decode_fn_actual = decode_fn or decode_grib2_file
        candidates = find_real_mrms_inspect_candidates(session, storage, limit=limit)
        if candidates:
            decode_result = decode_fn_actual(storage, candidates[0].raw_path)
            if isinstance(decode_result, Grib2DecodeResult):
                benchmark.decoder_used = decode_result.decoder_used

    if validation_report.decoded_count > 0:
        build_start = time.perf_counter()
        try:
            build_result = build_production_tiles(
                storage,
                session,
                layer="mrms_reflectivity",
                min_zoom=min_zoom,
                max_zoom=max_zoom,
                force=False,
                dry_run=False,
                limit=limit,
                mark_catalog=False,
            )
            benchmark.tile_build_elapsed_seconds = time.perf_counter() - build_start
            benchmark.tiles_planned = build_result.tiles_planned
            benchmark.tiles_written = build_result.tiles_written
            benchmark.tiles_skipped = build_result.tiles_skipped_existing
            benchmark.output_bytes = build_result.output_bytes
            timings.append(
                StageTiming(stage="tile_build", elapsed_seconds=benchmark.tile_build_elapsed_seconds)
            )
            if build_result.errors:
                benchmark.warnings.extend(build_result.errors[:5])
        except Exception as exc:
            benchmark.tile_build_elapsed_seconds = time.perf_counter() - build_start
            benchmark.errors.append(f"tile build failed: {exc}")
            timings.append(
                StageTiming(stage="tile_build", elapsed_seconds=benchmark.tile_build_elapsed_seconds)
            )
    else:
        benchmark.warnings.append("No decode artifacts; tile build benchmark skipped.")

    benchmark.stage_timings = timings
    if persist:
        save_latest_benchmark_report(storage, benchmark.to_dict())
    return benchmark


def resolve_benchmark_source_mode(*, real_requested: bool) -> str:
    return resolve_validation_source_mode(real_requested=real_requested)
