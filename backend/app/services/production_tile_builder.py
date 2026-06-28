"""Build geo-warped production tile cache from decode artifacts + geo_metadata.json."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from backend.app.models import RadarFile
from backend.app.models.radar_file import (
    RENDER_MODE_PRODUCTION,
    RENDER_STATUS_PRODUCTION_RENDERED,
)
from backend.app.services.decoded_tile_cache import (
    DecodeArtifact,
    list_decode_artifact_dirs,
    load_decode_manifest,
)
from backend.app.services.render_metadata import (
    GeoRenderMetadata,
    geo_metadata_path,
    load_geo_metadata,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.tile_pyramid import (
    TILE_SIZE,
    build_production_tile_repo_path,
    count_tiles_for_zoom_range,
    iter_tiles_for_bounds,
    validate_geo_metadata,
    warp_grid_to_tile_values,
)
from backend.app.services.tile_service import encode_normalized_grid_png

PRODUCTION_TILE_ROOT = "data/tiles/production"

DEFAULT_MIN_ZOOM = 0
DEFAULT_MAX_ZOOM = 0
MAX_ALLOWED_ZOOM = 4
MAX_TILES_PER_BUILD = 256


@dataclass
class ProductionTileJob:
    layer: str
    timestamp: str
    z: int
    x: int
    y: int
    artifact: DecodeArtifact
    metadata: GeoRenderMetadata
    output_dir: str
    geo_path: str


@dataclass
class TileBuildOutcome:
    status: str
    cache_path: Optional[str] = None
    output_bytes: int = 0
    error: Optional[str] = None


@dataclass
class BuildProductionTilesResult:
    frames_considered: int = 0
    frames_skipped: int = 0
    zooms_built: list[int] = field(default_factory=list)
    tiles_written: int = 0
    tiles_skipped_existing: int = 0
    tiles_planned: int = 0
    tiles_failed: int = 0
    elapsed_seconds: float = 0.0
    output_bytes: int = 0
    errors: list[str] = field(default_factory=list)
    artifacts_found: int = 0
    catalog_marked: int = 0
    dry_run: bool = False
    force: bool = False
    notes: list[str] = field(default_factory=list)

    # Legacy aliases used by earlier phases/tests.
    @property
    def built(self) -> int:
        return self.tiles_written

    @property
    def skipped(self) -> int:
        return self.frames_skipped + self.tiles_skipped_existing + self.tiles_failed

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["built"] = self.built
        payload["skipped"] = self.skipped
        payload["prototype"] = True
        payload["verified_mrms"] = False
        return payload


def clamp_zoom_range(min_zoom: int, max_zoom: int) -> tuple[int, int]:
    lo = max(0, min_zoom)
    hi = min(MAX_ALLOWED_ZOOM, max_zoom)
    if lo > hi:
        lo = hi
    return lo, hi


def read_normalized_grid_from_artifact(
    storage: LocalStorage,
    artifact: DecodeArtifact,
) -> Optional[list[list[float]]]:
    """Read normalized float32 grid from a decode artifact (.raw only for prototype)."""
    import struct

    if not artifact.raster_path.endswith(".raw"):
        return None
    try:
        raw_bytes = storage.absolute_path(artifact.raster_path).read_bytes()
    except OSError:
        return None
    if len(raw_bytes) % 4 != 0:
        return None

    count = len(raw_bytes) // 4
    values = struct.unpack(f"{count}f", raw_bytes)
    width = max(1, artifact.width)
    height = max(1, artifact.height)
    if width * height != count:
        if height == 1 and width == count:
            return [list(values)]
        return None

    grid: list[list[float]] = []
    idx = 0
    for _ in range(height):
        grid.append(list(values[idx : idx + width]))
        idx += width
    return grid


def render_production_warped_tile_png(
    grid: list[list[float]],
    metadata: GeoRenderMetadata,
    *,
    z: int,
    x: int,
    y: int,
    tile_size: int = TILE_SIZE,
) -> Optional[bytes]:
    """Warp grid to EPSG:3857 tile and encode PNG."""
    warped = warp_grid_to_tile_values(grid, metadata, z=z, x=x, y=y, tile_size=tile_size)
    if warped is None:
        return None
    return encode_normalized_grid_png(warped, width=tile_size, height=tile_size)


def build_production_tile_for_frame(
    storage: LocalStorage,
    *,
    layer: str,
    timestamp: str,
    artifact: DecodeArtifact,
    metadata: GeoRenderMetadata,
    z: int,
    x: int,
    y: int,
    force: bool = False,
    dry_run: bool = False,
) -> TileBuildOutcome:
    """Build one production tile; idempotent unless force=True."""
    cache_path = build_production_tile_repo_path(storage, layer, timestamp, z, x, y)

    if dry_run:
        return TileBuildOutcome(status="planned", cache_path=cache_path)

    if not force and storage.path_exists(cache_path):
        return TileBuildOutcome(status="skipped_existing", cache_path=cache_path)

    validation = validate_geo_metadata(metadata)
    if not validation.valid:
        return TileBuildOutcome(
            status="failed",
            cache_path=cache_path,
            error="; ".join(validation.errors),
        )

    grid = read_normalized_grid_from_artifact(storage, artifact)
    if grid is None:
        return TileBuildOutcome(status="failed", cache_path=cache_path, error="grid unreadable")

    png_bytes = render_production_warped_tile_png(grid, metadata, z=z, x=x, y=y)
    if png_bytes is None:
        return TileBuildOutcome(status="failed", cache_path=cache_path, error="warp failed")

    storage.write_bytes(cache_path, png_bytes, overwrite=True)
    return TileBuildOutcome(status="written", cache_path=cache_path, output_bytes=len(png_bytes))


def plan_production_tile_jobs(
    storage: LocalStorage,
    session: Optional[Session],
    *,
    layer: str,
    min_zoom: int,
    max_zoom: int,
    limit: Optional[int] = None,
) -> tuple[list[ProductionTileJob], list[str]]:
    """Plan tile jobs for decode artifacts (worker-style batch input)."""
    jobs: list[ProductionTileJob] = []
    errors: list[str] = []
    artifact_dirs = list_decode_artifact_dirs(storage)
    considered = 0

    for output_dir in artifact_dirs:
        if limit is not None and considered >= limit:
            break

        artifact = load_decode_manifest(storage, output_dir)
        if artifact is None:
            continue

        geo_path = geo_metadata_path(storage, output_dir)
        if not storage.path_exists(geo_path):
            errors.append(f"{output_dir}: missing geo_metadata.json")
            continue

        metadata = load_geo_metadata(storage, output_dir)
        if metadata is None:
            errors.append(f"{output_dir}: geo metadata unreadable")
            continue

        validation = validate_geo_metadata(metadata)
        if not validation.valid:
            errors.append(f"{output_dir}: {'; '.join(validation.errors)}")
            continue

        considered += 1
        timestamp = artifact.raw_path.rsplit("/", 1)[-1]
        if session is not None:
            frame = _find_catalog_frame_for_artifact(session, artifact)
            if frame is not None:
                timestamp = frame.timestamp

        lo, hi = clamp_zoom_range(min_zoom, max_zoom)
        tile_count = count_tiles_for_zoom_range(metadata.bounds, lo, hi)
        if tile_count > MAX_TILES_PER_BUILD:
            errors.append(
                f"{output_dir}: planned {tile_count} tiles exceeds cap {MAX_TILES_PER_BUILD}; skipped"
            )
            continue

        for z in range(lo, hi + 1):
            for tz, tx, ty in iter_tiles_for_bounds(metadata.bounds, z):
                jobs.append(
                    ProductionTileJob(
                        layer=layer,
                        timestamp=timestamp,
                        z=tz,
                        x=tx,
                        y=ty,
                        artifact=artifact,
                        metadata=metadata,
                        output_dir=output_dir,
                        geo_path=geo_path,
                    )
                )

    return jobs, errors


def execute_production_tile_batch(
    storage: LocalStorage,
    jobs: list[ProductionTileJob],
    *,
    force: bool = False,
    dry_run: bool = False,
    on_progress: Optional[Callable[[int, int], None]] = None,
    on_tile_outcome: Optional[Callable[[str, int], None]] = None,
) -> list[TileBuildOutcome]:
    """Worker-style batch executor for planned production tile jobs."""
    outcomes: list[TileBuildOutcome] = []
    total = len(jobs)
    for index, job in enumerate(jobs):
        outcome = build_production_tile_for_frame(
            storage,
            layer=job.layer,
            timestamp=job.timestamp,
            artifact=job.artifact,
            metadata=job.metadata,
            z=job.z,
            x=job.x,
            y=job.y,
            force=force,
            dry_run=dry_run,
        )
        outcomes.append(outcome)
        if on_tile_outcome is not None and outcome.status != "planned":
            on_tile_outcome(outcome.status, outcome.output_bytes)
        if on_progress is not None:
            on_progress(index + 1, total)
    return outcomes


def _find_catalog_frame_for_artifact(session: Session, artifact: DecodeArtifact) -> Optional[RadarFile]:
    return (
        session.query(RadarFile)
        .filter(RadarFile.raw_path == artifact.raw_path)
        .order_by(RadarFile.timestamp.asc())
        .first()
    )


def mark_frame_production_prototype(
    frame: RadarFile,
    *,
    artifact: DecodeArtifact,
    metadata_path: str,
    rendered_at: Optional[str] = None,
) -> None:
    """Mark catalog row as production_rendered for warping prototype (fixture/test use)."""
    frame.render_status = RENDER_STATUS_PRODUCTION_RENDERED
    frame.render_mode = RENDER_MODE_PRODUCTION
    frame.production_rendering = True
    frame.render_artifact_path = artifact.raster_path
    frame.render_metadata_path = metadata_path
    frame.render_error = None
    frame.rendered_at = rendered_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_production_tiles(
    storage: LocalStorage,
    session: Optional[Session] = None,
    *,
    layer: str = "mrms_reflectivity",
    min_zoom: int = DEFAULT_MIN_ZOOM,
    max_zoom: int = DEFAULT_MAX_ZOOM,
    z_levels: Optional[list[int]] = None,
    xy_limit: Optional[int] = None,
    force: bool = False,
    dry_run: bool = False,
    limit: Optional[int] = None,
    mark_catalog: bool = False,
    on_progress: Optional[Callable[[int, int], None]] = None,
    on_tile_outcome: Optional[Callable[[str, int], None]] = None,
) -> BuildProductionTilesResult:
    """Build production tile cache from decode artifacts with geo_metadata.json."""
    started = time.perf_counter()
    storage.ensure_directories(PRODUCTION_TILE_ROOT)

    lo, hi = clamp_zoom_range(min_zoom, max_zoom)
    if z_levels is not None:
        lo, hi = min(z_levels), max(z_levels)

    result = BuildProductionTilesResult(
        dry_run=dry_run,
        force=force,
        zooms_built=list(range(lo, hi + 1)),
    )
    artifact_dirs = list_decode_artifact_dirs(storage)
    result.artifacts_found = len(artifact_dirs)

    if not artifact_dirs:
        result.notes.append("No decode artifacts found under data/staging/grib2_decode/.")
        result.notes.append("Run: make decode-grib2  (or use test fixtures)")
        result.elapsed_seconds = round(time.perf_counter() - started, 4)
        return result

    jobs: list[ProductionTileJob] = []
    plan_errors: list[str] = []

    if xy_limit is not None:
        dirs = artifact_dirs[: limit if limit is not None else len(artifact_dirs)]
        result.frames_considered = len(dirs)
        for output_dir in dirs:
            artifact = load_decode_manifest(storage, output_dir)
            if artifact is None:
                result.frames_skipped += 1
                continue
            geo_path = geo_metadata_path(storage, output_dir)
            if not storage.path_exists(geo_path):
                result.frames_skipped += 1
                plan_errors.append(f"{output_dir}: missing geo_metadata.json")
                continue
            metadata = load_geo_metadata(storage, output_dir)
            if metadata is None:
                result.frames_skipped += 1
                continue
            validation = validate_geo_metadata(metadata)
            if not validation.valid:
                result.frames_skipped += 1
                plan_errors.append(f"{output_dir}: {'; '.join(validation.errors)}")
                continue
            timestamp = artifact.raw_path.rsplit("/", 1)[-1]
            if session is not None:
                frame = _find_catalog_frame_for_artifact(session, artifact)
                if frame is not None:
                    timestamp = frame.timestamp
            for x in range(xy_limit):
                for y in range(xy_limit):
                    jobs.append(
                        ProductionTileJob(
                            layer=layer,
                            timestamp=timestamp,
                            z=lo,
                            x=x,
                            y=y,
                            artifact=artifact,
                            metadata=metadata,
                            output_dir=output_dir,
                            geo_path=geo_path,
                        )
                    )
    else:
        jobs, plan_errors = plan_production_tile_jobs(
            storage,
            session,
            layer=layer,
            min_zoom=lo,
            max_zoom=hi,
            limit=limit,
        )
        planned_dirs = {job.output_dir for job in jobs}
        result.frames_considered = len(planned_dirs) + len(
            [e for e in plan_errors if "missing geo_metadata" in e or "unreadable" in e or "unsupported" in e]
        )
        result.frames_skipped = max(0, len(artifact_dirs) - len(planned_dirs))

    result.errors.extend(plan_errors)
    result.tiles_planned = len(jobs)
    outcomes = execute_production_tile_batch(
        storage,
        jobs,
        force=force,
        dry_run=dry_run,
        on_progress=on_progress,
        on_tile_outcome=on_tile_outcome,
    )

    frames_with_writes: set[str] = set()
    catalog_marked = 0

    for job, outcome in zip(jobs, outcomes):
        if outcome.status == "planned":
            continue
        if outcome.status == "written":
            result.tiles_written += 1
            result.output_bytes += outcome.output_bytes
            frames_with_writes.add(job.output_dir)
        elif outcome.status == "skipped_existing":
            result.tiles_skipped_existing += 1
        elif outcome.status == "failed":
            result.tiles_failed += 1
            if outcome.error:
                result.errors.append(f"{job.cache_path or job.output_dir}: {outcome.error}")

    if mark_catalog and session is not None and not dry_run:
        for output_dir in frames_with_writes:
            artifact = load_decode_manifest(storage, output_dir)
            if artifact is None:
                continue
            frame = _find_catalog_frame_for_artifact(session, artifact)
            if frame is None:
                continue
            mark_frame_production_prototype(
                frame,
                artifact=artifact,
                metadata_path=geo_metadata_path(storage, output_dir),
            )
            catalog_marked += 1
        if catalog_marked > 0:
            session.commit()

    result.catalog_marked = catalog_marked
    result.elapsed_seconds = round(time.perf_counter() - started, 4)
    result.notes.append(f"Artifacts found: {len(artifact_dirs)}")
    result.notes.append("Production warping prototype — not verified real MRMS output.")
    if dry_run:
        result.notes.append(f"Dry run: {result.tiles_planned} tile(s) planned, none written.")
    if mark_catalog and not dry_run:
        result.notes.append(f"Catalog marked production_rendered (prototype): {catalog_marked} frame(s)")
    elif not mark_catalog:
        result.notes.append("Catalog not modified (use --mark-catalog to update matching frames).")

    return result
