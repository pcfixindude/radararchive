"""Local dev color preview tiles from decoded artifacts (prototype only)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from backend.app.services.color_scale import COLOR_SCALE_MODE, encode_dbz_grid_png
from backend.app.services.decoded_tile_cache import DecodeArtifact, load_decode_manifest
from backend.app.services.storage import LocalStorage

LOCAL_TILE_ROOT = "dev/mrms_local_render_tiles"
TILE_MODE_SINGLE_IMAGE = "single_image"
TILE_MODE_LOCAL_RASTER = "local_raster_tiles"
TILE_SIZE = 256


def _sample_dbz_grid_to_tile(
    grid: list[list[float]],
    *,
    z: int,
    x: int,
    y: int,
    width: int,
    height: int,
) -> list[list[float]]:
    grid_h = len(grid)
    grid_w = len(grid[0]) if grid_h else 0
    if grid_w == 0 or grid_h == 0:
        return [[-999.0 for _ in range(width)] for _ in range(height)]

    num_tiles = max(1, 2**z)
    region_w = max(1, grid_w // num_tiles)
    region_h = max(1, grid_h // num_tiles)
    start_x = min(grid_w - 1, x * region_w)
    start_y = min(grid_h - 1, y * region_h)

    tile: list[list[float]] = []
    for row in range(height):
        gy = min(grid_h - 1, start_y + (row * region_h // max(1, height)))
        row_values: list[float] = []
        for col in range(width):
            gx = min(grid_w - 1, start_x + (col * region_w // max(1, width)))
            row_values.append(float(grid[gy][gx]))
        tile.append(row_values)
    return tile
TILE_MODE_SINGLE_IMAGE = "single_image"
TILE_MODE_LOCAL_RASTER = "local_raster_tiles"
TILE_SIZE = 256


@dataclass
class LocalTilePreviewResult:
    built: int = 0
    skipped: int = 0
    max_z: int = 0
    tile_mode: str = TILE_MODE_SINGLE_IMAGE
    color_scale_mode: str = COLOR_SCALE_MODE
    tile_paths: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _manifest_dbz_range(storage: LocalStorage, output_dir: str) -> tuple[Optional[float], Optional[float]]:
    manifest_path = storage.normalize_path(output_dir, "decode_manifest.json")
    if not storage.path_exists(manifest_path):
        return None, None
    try:
        payload = json.loads(storage.absolute_path(manifest_path).read_text(encoding="utf-8"))
        vmin = payload.get("value_min")
        vmax = payload.get("value_max")
        return (
            float(vmin) if vmin is not None else None,
            float(vmax) if vmax is not None else None,
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None, None


def normalized_to_dbz(value: float, *, vmin: float, vmax: float) -> float:
    if vmax == vmin:
        return vmin
    return float(value) * (vmax - vmin) + vmin


def read_artifact_dbz_grid(storage: LocalStorage, artifact: DecodeArtifact) -> Optional[list[list[float]]]:
    """Read decode artifact grid and convert normalized raster values to dBZ."""
    from backend.app.services.decoded_tile_cache import _read_normalized_grid

    grid = _read_normalized_grid(storage, artifact)
    if grid is None:
        return None

    vmin, vmax = _manifest_dbz_range(storage, artifact.output_dir)
    if vmin is None or vmax is None:
        return grid

    return [
        [normalized_to_dbz(value, vmin=vmin, vmax=vmax) for value in row]
        for row in grid
    ]


def render_color_preview_tile(
    dbz_grid: list[list[float]],
    *,
    z: int = 0,
    x: int = 0,
    y: int = 0,
    width: int = TILE_SIZE,
    height: int = TILE_SIZE,
) -> bytes:
    sampled = _sample_dbz_grid_to_tile(dbz_grid, z=z, x=x, y=y, width=width, height=height)
    return encode_dbz_grid_png(sampled, width=width, height=height)


def render_color_preview_from_artifact(
    storage: LocalStorage,
    artifact: DecodeArtifact,
    *,
    z: int = 0,
    x: int = 0,
    y: int = 0,
) -> Optional[bytes]:
    dbz_grid = read_artifact_dbz_grid(storage, artifact)
    if dbz_grid is None:
        return None
    return render_color_preview_tile(dbz_grid, z=z, x=x, y=y)


def _local_tile_path(storage: LocalStorage, *, z: int, x: int, y: int) -> str:
    return storage.normalize_path(LOCAL_TILE_ROOT, str(z), str(x), f"{y}.png")


def build_local_tile_preview(
    storage: LocalStorage,
    artifact: DecodeArtifact,
    *,
    z_levels: Optional[list[int]] = None,
    xy_limit: int = 2,
) -> LocalTilePreviewResult:
    """Build a small local color tile pyramid under data/dev/."""
    z_levels = z_levels or [0, 1]
    result = LocalTilePreviewResult(max_z=max(z_levels) if z_levels else 0)
    dbz_grid = read_artifact_dbz_grid(storage, artifact)
    if dbz_grid is None:
        result.notes.append("Could not read dBZ grid for local tile preview.")
        return result

    storage.ensure_directories(LOCAL_TILE_ROOT)
    for z in z_levels:
        for x in range(xy_limit):
            for y in range(xy_limit):
                png = render_color_preview_tile(dbz_grid, z=z, x=x, y=y)
                tile_path = _local_tile_path(storage, z=z, x=x, y=y)
                storage.ensure_directories(tile_path.rsplit("/", 1)[0])
                storage.write_bytes(tile_path, png, overwrite=True)
                result.built += 1
                result.tile_paths.append(tile_path)

    if result.built > 0:
        result.tile_mode = TILE_MODE_LOCAL_RASTER
        result.notes.append(f"Built {result.built} local color tiles under {LOCAL_TILE_ROOT}/")
    return result


def load_local_tile_png(storage: LocalStorage, *, z: int, x: int, y: int) -> Optional[bytes]:
    tile_path = _local_tile_path(storage, z=z, x=x, y=y)
    if not storage.path_exists(tile_path):
        return None
    try:
        return storage.absolute_path(tile_path).read_bytes()
    except OSError:
        return None


def compact_tile_preview(result: LocalTilePreviewResult) -> dict[str, Any]:
    return {
        "built": result.built,
        "skipped": result.skipped,
        "max_z": result.max_z,
        "tile_mode": result.tile_mode,
        "color_scale_mode": result.color_scale_mode,
        "tile_paths": result.tile_paths[:8],
        "notes": result.notes,
    }
