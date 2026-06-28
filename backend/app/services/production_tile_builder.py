"""Build geo-warped production tile cache from decode artifacts + geo_metadata.json."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

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
    validate_geo_metadata,
    warp_grid_to_tile_values,
)
from backend.app.services.tile_service import encode_normalized_grid_png

PRODUCTION_TILE_ROOT = "data/tiles/production"


@dataclass
class BuildProductionTilesResult:
    built: int
    skipped: int
    artifacts_found: int
    catalog_marked: int
    notes: list[str] = field(default_factory=list)


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
    """Warp grid to EPSG:3857 tile and encode PNG (uses tile_service color ramp)."""
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
) -> Optional[str]:
    """Build one production tile; returns repo path when written."""
    validation = validate_geo_metadata(metadata)
    if not validation.valid:
        return None

    grid = read_normalized_grid_from_artifact(storage, artifact)
    if grid is None:
        return None

    png_bytes = render_production_warped_tile_png(grid, metadata, z=z, x=x, y=y)
    if png_bytes is None:
        return None

    cache_path = build_production_tile_repo_path(storage, layer, timestamp, z, x, y)
    storage.write_bytes(cache_path, png_bytes, overwrite=True)
    return cache_path


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
    z_levels: Optional[list[int]] = None,
    xy_limit: int = 1,
    mark_catalog: bool = False,
) -> BuildProductionTilesResult:
    """Build production tile cache from decode artifacts with geo_metadata.json."""
    storage.ensure_directories(PRODUCTION_TILE_ROOT)
    z_levels = z_levels or [0]
    built = 0
    skipped = 0
    catalog_marked = 0
    notes: list[str] = []
    artifact_dirs = list_decode_artifact_dirs(storage)

    if not artifact_dirs:
        notes.append("No decode artifacts found under data/staging/grib2_decode/.")
        notes.append("Run: make decode-grib2  (or use test fixtures)")
        return BuildProductionTilesResult(
            built=0,
            skipped=0,
            artifacts_found=0,
            catalog_marked=0,
            notes=notes,
        )

    for output_dir in artifact_dirs:
        artifact = load_decode_manifest(storage, output_dir)
        if artifact is None:
            skipped += 1
            continue

        geo_path = geo_metadata_path(storage, output_dir)
        if not storage.path_exists(geo_path):
            notes.append(f"Skipping {output_dir}: missing geo_metadata.json")
            skipped += 1
            continue

        metadata = load_geo_metadata(storage, output_dir)
        if metadata is None:
            skipped += 1
            continue

        validation = validate_geo_metadata(metadata)
        if not validation.valid:
            notes.append(f"Skipping {output_dir}: {'; '.join(validation.errors)}")
            skipped += 1
            continue

        timestamp = artifact.raw_path.rsplit("/", 1)[-1]
        frame: Optional[RadarFile] = None
        if session is not None:
            frame = _find_catalog_frame_for_artifact(session, artifact)
            if frame is not None:
                timestamp = frame.timestamp

        artifact_built = 0
        for z in z_levels:
            for x in range(xy_limit):
                for y in range(xy_limit):
                    path = build_production_tile_for_frame(
                        storage,
                        layer=layer,
                        timestamp=timestamp,
                        artifact=artifact,
                        metadata=metadata,
                        z=z,
                        x=x,
                        y=y,
                    )
                    if path is None:
                        skipped += 1
                    else:
                        built += 1
                        artifact_built += 1

        if mark_catalog and session is not None and frame is not None and artifact_built > 0:
            mark_frame_production_prototype(
                frame,
                artifact=artifact,
                metadata_path=geo_path,
            )
            catalog_marked += 1

    notes.append(f"Artifacts found: {len(artifact_dirs)}")
    notes.append("Production warping prototype — not verified real MRMS output.")
    if mark_catalog:
        notes.append(f"Catalog marked production_rendered (prototype): {catalog_marked} frame(s)")
    else:
        notes.append("Catalog not modified (use --mark-catalog to update matching frames).")

    if session is not None and mark_catalog and catalog_marked > 0:
        session.commit()

    return BuildProductionTilesResult(
        built=built,
        skipped=skipped,
        artifacts_found=len(artifact_dirs),
        catalog_marked=catalog_marked,
        notes=notes,
    )

