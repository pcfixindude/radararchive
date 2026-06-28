"""Feature-flagged tile cache from Phase 12 decode artifacts (prototype only)."""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field
from typing import Optional

from backend.app.models.radar_file import (
    RENDER_STATUS_DECODED_PROTOTYPE,
    RENDER_STATUS_PLACEHOLDER,
    RENDER_STATUS_PRODUCTION_RENDERED,
    RadarFile,
)
from backend.app.services.grib2_decoder import (
    DECODE_OUTPUT_ROOT,
    MANIFEST_NAME,
    RASTER_RAW_NAME,
    RASTER_TIF_NAME,
    build_decode_output_dir,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.tile_service import (
    generate_decoded_prototype_tile_png,
    generate_placeholder_tile_png,
)

TILE_CACHE_ROOT = "data/tiles/decoded_prototype"
TILE_MODE_PLACEHOLDER = "placeholder"
TILE_MODE_PLACEHOLDER_FOR_REAL_RAW = "placeholder_for_real_raw"
TILE_MODE_DECODED_PROTOTYPE = "decoded-prototype"


@dataclass
class DecodeArtifact:
    output_dir: str
    manifest_path: str
    raster_path: str
    width: int
    height: int
    raw_path: str
    decoder: Optional[str] = None
    prototype: bool = True
    production_rendering: bool = False


@dataclass
class TileServeResult:
    png_bytes: bytes
    tile_mode: str
    render_status: str
    production_rendering: bool
    from_cache: bool
    fallback: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass
class BuildTileCacheResult:
    built: int
    skipped: int
    artifacts_found: int
    notes: list[str] = field(default_factory=list)


def _timestamp_token(timestamp: str) -> str:
    return timestamp.replace(":", "").replace("-", "")


def load_decode_manifest(storage: LocalStorage, output_dir: str) -> Optional[DecodeArtifact]:
    manifest_repo_path = storage.normalize_path(output_dir, MANIFEST_NAME)
    if not storage.path_exists(manifest_repo_path):
        return None

    try:
        payload = json.loads(storage.absolute_path(manifest_repo_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if not payload.get("prototype", False):
        return None
    if payload.get("production_rendering", True):
        return None

    raw_path = payload.get("raw_path")
    raster_name = payload.get("raster_path")
    width = payload.get("width")
    height = payload.get("height")
    if not raw_path or not raster_name or width is None or height is None:
        return None

    raster_repo_path = storage.normalize_path(output_dir, str(raster_name))
    if not storage.path_exists(raster_repo_path):
        return None

    return DecodeArtifact(
        output_dir=output_dir,
        manifest_path=manifest_repo_path,
        raster_path=raster_repo_path,
        width=int(width),
        height=int(height),
        raw_path=str(raw_path),
        decoder=payload.get("decoder"),
        prototype=True,
        production_rendering=False,
    )


def find_decode_artifact_for_frame(storage: LocalStorage, frame: RadarFile) -> Optional[DecodeArtifact]:
    if not frame.raw_path:
        return None
    if not frame.raw_path.startswith("data/raw/mrms/"):
        return None
    output_dir = build_decode_output_dir(storage, frame.raw_path)
    return load_decode_manifest(storage, output_dir)


def _read_normalized_grid(storage: LocalStorage, artifact: DecodeArtifact) -> Optional[list[list[float]]]:
    if artifact.raster_path.endswith(".raw"):
        return _read_normalized_raw_grid(storage, artifact)
    if artifact.raster_path.endswith(".tif"):
        return _read_normalized_tif_grid(storage, artifact)
    return None


def _read_normalized_raw_grid(storage: LocalStorage, artifact: DecodeArtifact) -> Optional[list[list[float]]]:
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
        # wgrib2 1xN prototype: reshape as 1 row
        if height == 1 and width == count:
            return [list(values)]
        return None

    grid: list[list[float]] = []
    idx = 0
    for _ in range(height):
        grid.append(list(values[idx : idx + width]))
        idx += width
    return grid


def _read_normalized_tif_grid(storage: LocalStorage, artifact: DecodeArtifact) -> Optional[list[list[float]]]:
    try:
        import rasterio
        import numpy as np
    except ImportError:
        return None

    try:
        with rasterio.open(storage.absolute_path(artifact.raster_path)) as dataset:
            data = dataset.read(1).astype("float32")
    except OSError:
        return None

    height, width = data.shape
    return np.nan_to_num(data, nan=0.0).tolist()


def _tile_cache_path(
    storage: LocalStorage,
    timestamp: str,
    z: int,
    x: int,
    y: int,
) -> str:
    token = _timestamp_token(timestamp)
    return storage.normalize_path(TILE_CACHE_ROOT, token, str(z), str(x), f"{y}.png")


def render_decoded_prototype_tile(
    storage: LocalStorage,
    artifact: DecodeArtifact,
    *,
    z: int,
    x: int,
    y: int,
    tile_size: int = 256,
) -> Optional[bytes]:
    grid = _read_normalized_grid(storage, artifact)
    if grid is None:
        return None
    return generate_decoded_prototype_tile_png(
        grid,
        z=z,
        x=x,
        y=y,
        width=tile_size,
        height=tile_size,
    )


def get_or_build_cached_tile(
    storage: LocalStorage,
    timestamp: str,
    artifact: DecodeArtifact,
    *,
    z: int,
    x: int,
    y: int,
) -> Optional[bytes]:
    cache_path = _tile_cache_path(storage, timestamp, z, x, y)
    if storage.path_exists(cache_path):
        try:
            return storage.absolute_path(cache_path).read_bytes()
        except OSError:
            pass

    png_bytes = render_decoded_prototype_tile(storage, artifact, z=z, x=x, y=y)
    if png_bytes is None:
        return None

    storage.write_bytes(cache_path, png_bytes, overwrite=True)
    return png_bytes


def try_serve_production_tile(
    storage: LocalStorage,
    frame: RadarFile,
    timestamp: str,
    *,
    enable_production_radar_tiles: bool,
    z: int,
    x: int,
    y: int,
) -> Optional[TileServeResult]:
    """Serve geo-accurate production tiles when fully enabled (not implemented in Phase 14)."""
    if not enable_production_radar_tiles:
        return None
    if not frame.production_rendering:
        return None
    if frame.render_status != RENDER_STATUS_PRODUCTION_RENDERED:
        return None
    if not frame.render_artifact_path or not storage.path_exists(frame.render_artifact_path):
        return None

    # Production tile pyramid rendering is future work — gate only, no renderer yet.
    return None


def try_serve_decoded_prototype_tile(
    storage: LocalStorage,
    frame: RadarFile,
    timestamp: str,
    *,
    z: int,
    x: int,
    y: int,
) -> Optional[TileServeResult]:
    artifact = find_decode_artifact_for_frame(storage, frame)
    if artifact is None:
        return None

    cache_path = _tile_cache_path(storage, timestamp, z, x, y)
    from_cache = storage.path_exists(cache_path)
    png_bytes = get_or_build_cached_tile(storage, timestamp, artifact, z=z, x=x, y=y)
    if png_bytes is None:
        return None

    return TileServeResult(
        png_bytes=png_bytes,
        tile_mode=TILE_MODE_DECODED_PROTOTYPE,
        render_status=RENDER_STATUS_DECODED_PROTOTYPE,
        production_rendering=False,
        from_cache=from_cache,
        notes=["Prototype decode tile — not production radar rendering."],
    )


def serve_tile_with_optional_decode(
    storage: LocalStorage,
    frame: RadarFile,
    timestamp: str,
    *,
    enable_decoded_tiles: bool,
    enable_production_radar_tiles: bool = False,
    z: int,
    x: int,
    y: int,
) -> TileServeResult:
    """Return production, decoded prototype, or placeholder tile based on flags and catalog."""
    production = try_serve_production_tile(
        storage,
        frame,
        timestamp,
        enable_production_radar_tiles=enable_production_radar_tiles,
        z=z,
        x=x,
        y=y,
    )
    if production is not None:
        return production

    placeholder_kind = TILE_MODE_PLACEHOLDER
    if frame.processed_status == "placeholder_for_real_raw":
        placeholder_kind = TILE_MODE_PLACEHOLDER_FOR_REAL_RAW

    if enable_decoded_tiles:
        decoded = try_serve_decoded_prototype_tile(
            storage,
            frame,
            timestamp,
            z=z,
            x=x,
            y=y,
        )
        if decoded is not None:
            return decoded

    return TileServeResult(
        png_bytes=generate_placeholder_tile_png(z=z, x=x, y=y),
        tile_mode=placeholder_kind,
        render_status=RENDER_STATUS_PLACEHOLDER,
        production_rendering=False,
        from_cache=False,
        fallback=enable_decoded_tiles or enable_production_radar_tiles,
        notes=["Placeholder tile (default or render fallback)."]
        if (enable_decoded_tiles or enable_production_radar_tiles)
        else [],
    )


def list_decode_artifact_dirs(storage: LocalStorage) -> list[str]:
    root = storage.absolute_path(DECODE_OUTPUT_ROOT)
    if not root.exists():
        return []
    dirs: list[str] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        repo_path = storage.normalize_path(DECODE_OUTPUT_ROOT, child.name)
        if load_decode_manifest(storage, repo_path) is not None:
            dirs.append(repo_path)
    return dirs


def build_tile_cache(
    storage: LocalStorage,
    *,
    timestamps: Optional[list[str]] = None,
    z_levels: Optional[list[int]] = None,
    xy_limit: int = 1,
) -> BuildTileCacheResult:
    """Pre-build prototype tile cache for decoded artifacts."""
    storage.ensure_directories(TILE_CACHE_ROOT)
    z_levels = z_levels or [0]
    built = 0
    skipped = 0
    notes: list[str] = []
    artifact_dirs = list_decode_artifact_dirs(storage)

    if not artifact_dirs:
        notes.append("No decode artifacts found under data/staging/grib2_decode/.")
        notes.append("Run: make decode-grib2  (after downloading a real MRMS .grib2.gz file)")
        return BuildTileCacheResult(built=0, skipped=0, artifacts_found=0, notes=notes)

    for output_dir in artifact_dirs:
        artifact = load_decode_manifest(storage, output_dir)
        if artifact is None:
            skipped += 1
            continue

        token = output_dir.rsplit("/", 1)[-1]
        timestamp = timestamps[0] if timestamps else token

        for z in z_levels:
            for x in range(xy_limit):
                for y in range(xy_limit):
                    png = get_or_build_cached_tile(storage, timestamp, artifact, z=z, x=x, y=y)
                    if png is None:
                        skipped += 1
                    else:
                        built += 1

    notes.append(f"Artifacts found: {len(artifact_dirs)}")
    return BuildTileCacheResult(
        built=built,
        skipped=skipped,
        artifacts_found=len(artifact_dirs),
        notes=notes,
    )
