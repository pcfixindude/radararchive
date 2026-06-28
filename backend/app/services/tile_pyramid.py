"""Geo-accurate tile warping prototype — stdlib math only, no GDAL/rasterio."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from backend.app.services.render_metadata import GeoRenderMetadata
from backend.app.services.storage import LocalStorage

TILE_SIZE = 256
WEB_MERCATOR_HALF_EXTENT = 20037508.342789244
EARTH_RADIUS = 6378137.0

SUPPORTED_OUTPUT_CRS = frozenset({"EPSG:3857"})
SUPPORTED_SOURCE_CRS = frozenset({"EPSG:4326", "WGS84", None})


@dataclass
class GeoMetadataValidation:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_geo_metadata(metadata: GeoRenderMetadata) -> GeoMetadataValidation:
    """Validate geo metadata for the warping prototype."""
    errors: list[str] = []
    warnings: list[str] = []

    if metadata.grid_width <= 0 or metadata.grid_height <= 0:
        errors.append("grid_width and grid_height must be positive")

    if len(metadata.bounds) != 4:
        errors.append("bounds must contain [west, south, east, north]")
    else:
        west, south, east, north = metadata.bounds
        if west >= east:
            errors.append("bounds west must be less than east")
        if south >= north:
            errors.append("bounds south must be less than north")

    output_crs = (metadata.output_crs or "").upper()
    if output_crs not in SUPPORTED_OUTPUT_CRS:
        errors.append(f"unsupported output_crs: {metadata.output_crs} (prototype supports EPSG:3857 only)")

    source_crs = metadata.source_crs
    if source_crs is None:
        warnings.append("source_crs missing — assuming bounds are WGS84 (EPSG:4326)")
    elif source_crs not in SUPPORTED_SOURCE_CRS:
        errors.append(f"unsupported source_crs: {source_crs} (prototype supports EPSG:4326 only)")

    if not metadata.geo_accurate:
        warnings.append("geo_accurate is false — warping prototype only, not verified production output")

    return GeoMetadataValidation(valid=len(errors) == 0, errors=errors, warnings=warnings)


def production_tile_cache_path(layer: str, timestamp: str, z: int, x: int, y: int) -> tuple[str, ...]:
    """Return path parts for data/tiles/production/{layer}/{token}/{z}/{x}/{y}.png."""
    token = timestamp.replace(":", "").replace("-", "")
    return ("tiles", "production", layer, token, str(z), str(x), f"{y}.png")


def build_production_tile_repo_path(
    storage: LocalStorage,
    layer: str,
    timestamp: str,
    z: int,
    x: int,
    y: int,
) -> str:
    parts = production_tile_cache_path(layer, timestamp, z, x, y)
    return storage.normalize_path(*parts)


def load_production_tile_bytes(
    storage: LocalStorage,
    *,
    layer: str,
    timestamp: str,
    z: int,
    x: int,
    y: int,
) -> Optional[bytes]:
    cache_path = build_production_tile_repo_path(storage, layer, timestamp, z, x, y)
    if not storage.path_exists(cache_path):
        return None
    try:
        return storage.absolute_path(cache_path).read_bytes()
    except OSError:
        return None


def tile_bounds_epsg3857(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    """XYZ tile bounds as (min_x, min_y, max_x, max_y) in EPSG:3857."""
    n = 2**z
    tile_span = (2 * WEB_MERCATOR_HALF_EXTENT) / n
    min_x = -WEB_MERCATOR_HALF_EXTENT + x * tile_span
    max_x = min_x + tile_span
    max_y = WEB_MERCATOR_HALF_EXTENT - y * tile_span
    min_y = max_y - tile_span
    return min_x, min_y, max_x, max_y


def web_mercator_to_lon_lat(x: float, y: float) -> tuple[float, float]:
    lon = math.degrees(x / EARTH_RADIUS)
    lat = math.degrees(2 * math.atan(math.exp(y / EARTH_RADIUS)) - math.pi / 2)
    return lon, lat


def lon_lat_to_web_mercator(lon: float, lat: float) -> tuple[float, float]:
    lat = max(min(lat, 85.05112878), -85.05112878)
    x = EARTH_RADIUS * math.radians(lon)
    y = EARTH_RADIUS * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y


def _geo_to_grid_fraction(
    lon: float,
    lat: float,
    bounds: list[float],
) -> tuple[float, float]:
    """Map WGS84 lon/lat to fractional grid coordinates (col, row)."""
    west, south, east, north = bounds
    if east == west or north == south:
        return 0.0, 0.0
    col_frac = (lon - west) / (east - west)
    row_frac = (north - lat) / (north - south)
    return col_frac, row_frac


def _sample_bilinear(grid: list[list[float]], col_frac: float, row_frac: float) -> float:
    height = len(grid)
    width = len(grid[0]) if height else 0
    if width == 0 or height == 0:
        return 0.0

    max_col = max(width - 1, 0)
    max_row = max(height - 1, 0)
    gx = max(0.0, min(max_col, col_frac * max_col))
    gy = max(0.0, min(max_row, row_frac * max_row))

    x0 = int(math.floor(gx))
    y0 = int(math.floor(gy))
    x1 = min(x0 + 1, max_col)
    y1 = min(y0 + 1, max_row)
    tx = gx - x0
    ty = gy - y0

    v00 = float(grid[y0][x0])
    v10 = float(grid[y0][x1])
    v01 = float(grid[y1][x0])
    v11 = float(grid[y1][x1])
    top = v00 * (1 - tx) + v10 * tx
    bottom = v01 * (1 - tx) + v11 * tx
    return max(0.0, min(1.0, top * (1 - ty) + bottom * ty))


def warp_grid_to_tile_values(
    grid: list[list[float]],
    metadata: GeoRenderMetadata,
    *,
    z: int,
    x: int,
    y: int,
    tile_size: int = TILE_SIZE,
) -> Optional[list[list[float]]]:
    """Sample normalized grid into EPSG:3857 tile pixel values using geographic bounds."""
    validation = validate_geo_metadata(metadata)
    if not validation.valid:
        return None

    min_x, min_y, max_x, max_y = tile_bounds_epsg3857(z, x, y)
    bounds = metadata.bounds
    tile: list[list[float]] = []

    for row in range(tile_size):
        py = max_y - (row + 0.5) * (max_y - min_y) / tile_size
        row_values: list[float] = []
        for col in range(tile_size):
            px = min_x + (col + 0.5) * (max_x - min_x) / tile_size
            lon, lat = web_mercator_to_lon_lat(px, py)
            col_frac, row_frac = _geo_to_grid_fraction(lon, lat, bounds)
            row_values.append(_sample_bilinear(grid, col_frac, row_frac))
        tile.append(row_values)
    return tile
