"""WGS84 overlay bounds from rasterio CRS/affine (local prototype only)."""

from __future__ import annotations

from typing import Any, Optional

from backend.app.services.render_metadata import DEFAULT_MRMS_BOUNDS

WGS84_EPSG = "EPSG:4326"

GEOREF_METHOD_PROTOTYPE = "prototype_bounds"
GEOREF_METHOD_RASTERIO_WGS84_AFFINE = "rasterio_wgs84_affine"
GEOREF_METHOD_RASTERIO_WGS84_BOUNDS = "rasterio_wgs84_bounds"
GEOREF_METHOD_RASTERIO_NATIVE = "rasterio_native_bounds"

ENRICHMENT_NOTE_PREFIX = "georef_bounds:"


def is_wgs84_crs(crs: Optional[str]) -> bool:
    if not crs:
        return False
    upper = str(crs).upper()
    return upper in {"EPSG:4326", "WGS84", "OGC:CRS84"} or "4326" in upper


def normalize_wgs84_bounds(west: float, south: float, east: float, north: float) -> list[float]:
    return [float(west), float(south), float(east), float(north)]


def bounds_from_affine_corners(
    transform: Any,
    width: int,
    height: int,
) -> tuple[float, float, float, float]:
    """Axis-aligned bbox from raster affine + dimensions in the dataset CRS."""
    from rasterio.transform import array_bounds

    west, south, east, north = array_bounds(height, width, transform)
    return float(west), float(south), float(east), float(north)


def transform_bounds_to_wgs84(
    west: float,
    south: float,
    east: float,
    north: float,
    src_crs: str,
) -> list[float]:
    from rasterio.warp import transform_bounds

    transformed = transform_bounds(src_crs, WGS84_EPSG, west, south, east, north, densify_pts=21)
    return normalize_wgs84_bounds(*transformed)


def extract_wgs84_bounds_from_dataset(dataset: Any) -> dict[str, Any]:
    """Derive WGS84 [west, south, east, north] from an open rasterio dataset."""
    notes: list[str] = []
    source_crs = str(dataset.crs) if getattr(dataset, "crs", None) else None
    transform = getattr(dataset, "transform", None)
    width = int(getattr(dataset, "width", 0) or 0)
    height = int(getattr(dataset, "height", 0) or 0)

    if transform is not None and not transform.is_identity and width > 0 and height > 0:
        west, south, east, north = bounds_from_affine_corners(transform, width, height)
        method = GEOREF_METHOD_RASTERIO_WGS84_AFFINE
        notes.append(f"{ENRICHMENT_NOTE_PREFIX} corner affine in source CRS")
        if source_crs and not is_wgs84_crs(source_crs):
            bounds = transform_bounds_to_wgs84(west, south, east, north, source_crs)
            method = GEOREF_METHOD_RASTERIO_WGS84_BOUNDS
            notes.append(f"{ENRICHMENT_NOTE_PREFIX} affine corners reprojected to WGS84")
        else:
            bounds = normalize_wgs84_bounds(west, south, east, north)
            notes.append(f"{ENRICHMENT_NOTE_PREFIX} WGS84 affine corners")
    elif getattr(dataset, "bounds", None) and source_crs:
        raw = dataset.bounds
        west, south, east, north = float(raw.left), float(raw.bottom), float(raw.right), float(raw.top)
        if is_wgs84_crs(source_crs):
            bounds = normalize_wgs84_bounds(west, south, east, north)
            method = GEOREF_METHOD_RASTERIO_WGS84_BOUNDS
            notes.append(f"{ENRICHMENT_NOTE_PREFIX} dataset.bounds in WGS84")
        else:
            bounds = transform_bounds_to_wgs84(west, south, east, north, source_crs)
            method = GEOREF_METHOD_RASTERIO_WGS84_BOUNDS
            notes.append(f"{ENRICHMENT_NOTE_PREFIX} dataset.bounds reprojected to WGS84")
    else:
        bounds = list(DEFAULT_MRMS_BOUNDS)
        method = GEOREF_METHOD_PROTOTYPE
        notes.append(f"{ENRICHMENT_NOTE_PREFIX} missing CRS/transform — prototype CONUS bounds")

    notes.append("Improved prototype placement — geo_accurate remains false (not verified MRMS).")
    return {
        "bounds": bounds,
        "georef_quality": method,
        "source_crs": source_crs,
        "transform": list(transform)[:6] if transform is not None else None,
        "pixel_size_x": float(dataset.res[0]) if getattr(dataset, "res", None) else None,
        "pixel_size_y": float(dataset.res[1]) if getattr(dataset, "res", None) else None,
        "notes": notes,
    }


def extract_wgs84_bounds_from_raster_path(raster_abs_path: str) -> Optional[dict[str, Any]]:
    """Open raster path with rasterio and return WGS84 bounds metadata."""
    try:
        import rasterio
    except ImportError:
        return None

    try:
        with rasterio.open(raster_abs_path) as dataset:
            return extract_wgs84_bounds_from_dataset(dataset)
    except OSError:
        return None
