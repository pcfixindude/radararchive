"""Georef resolution for local decoded overlay (prototype, not production)."""

from __future__ import annotations

from typing import Any, Optional

from backend.app.services.georef_bounds import (
    ENRICHMENT_NOTE_PREFIX,
    GEOREF_METHOD_PROTOTYPE,
    GEOREF_METHOD_RASTERIO_WGS84_AFFINE,
    GEOREF_METHOD_RASTERIO_WGS84_BOUNDS,
    is_wgs84_crs,
)
from backend.app.services.render_metadata import DEFAULT_MRMS_BOUNDS, GeoRenderMetadata, load_geo_metadata
from backend.app.services.storage import LocalStorage

GEOREF_QUALITY_PROTOTYPE = GEOREF_METHOD_PROTOTYPE
GEOREF_QUALITY_RASTERIO_BOUNDS = "rasterio_bounds"
GEOREF_QUALITY_RASTERIO_WGS84 = GEOREF_METHOD_RASTERIO_WGS84_AFFINE
GEOREF_QUALITY_RASTERIO_WGS84_BOUNDS = GEOREF_METHOD_RASTERIO_WGS84_BOUNDS


def resolve_georef_overlay(
    storage: LocalStorage,
    decode_output_dir: Optional[str],
) -> dict[str, Any]:
    """Return bounds and georef metadata; geo_accurate stays false unless production-validated."""
    if not decode_output_dir:
        return _prototype_result(
            notes=[
                "No decode output dir — using DEFAULT_MRMS_BOUNDS prototype placement.",
                "Missing: decode artifact, geo_metadata.json, rasterio enrichment.",
            ],
        )

    geo = load_geo_metadata(storage, decode_output_dir)
    if geo is None or len(geo.bounds) != 4:
        return _prototype_result(
            notes=["geo_metadata.json missing or incomplete — prototype CONUS bounds used."],
        )

    return _resolve_from_geo(geo)


def _prototype_result(*, notes: list[str]) -> dict[str, Any]:
    return {
        "bounds": list(DEFAULT_MRMS_BOUNDS),
        "georef_mode": GEOREF_QUALITY_PROTOTYPE,
        "georef_quality": GEOREF_QUALITY_PROTOTYPE,
        "geo_accurate": False,
        "georef_notes": notes,
        "bounds_source": "prototype_fallback",
    }


def _resolve_from_geo(geo: GeoRenderMetadata) -> dict[str, Any]:
    bounds = [float(v) for v in geo.bounds]
    notes: list[str] = list(geo.notes or [])
    crs = geo.source_crs or ""
    has_transform = geo.transform is not None and len(geo.transform or []) >= 6
    has_pixel_size = geo.pixel_size_x is not None and geo.pixel_size_y is not None
    has_wgs84 = is_wgs84_crs(crs)
    georef_enriched = any(ENRICHMENT_NOTE_PREFIX in note for note in notes) or bool(geo.georef_quality)

    georef_quality = geo.georef_quality or GEOREF_QUALITY_PROTOTYPE
    georef_mode = georef_quality
    bounds_source = "geo_metadata"

    if georef_quality == GEOREF_METHOD_PROTOTYPE or not georef_enriched:
        georef_quality = GEOREF_QUALITY_PROTOTYPE
        georef_mode = GEOREF_QUALITY_PROTOTYPE
        bounds_source = "prototype_fallback"
        if not georef_enriched:
            notes.append("No rasterio WGS84 enrichment — prototype CONUS bounds may misalign.")
    elif georef_quality == GEOREF_METHOD_RASTERIO_WGS84_AFFINE:
        georef_mode = GEOREF_QUALITY_RASTERIO_WGS84
        bounds_source = "rasterio_affine_wgs84"
        notes.append("WGS84 bounds from raster affine — prototype local dev only.")
    elif georef_quality == GEOREF_METHOD_RASTERIO_WGS84_BOUNDS:
        georef_mode = GEOREF_QUALITY_RASTERIO_WGS84_BOUNDS
        bounds_source = "rasterio_transform_wgs84"
        notes.append("WGS84 bounds from rasterio reprojection — prototype local dev only.")
    else:
        georef_mode = GEOREF_QUALITY_RASTERIO_BOUNDS
        bounds_source = "rasterio_native"

    if georef_enriched and not has_wgs84 and crs:
        notes.append(f"Source CRS {crs} reprojected to WGS84 for map overlay.")
    if not has_transform:
        notes.append("Missing raster affine transform — image corners use axis-aligned bounds.")
    if not has_pixel_size:
        notes.append("Missing pixel size metadata.")

    notes.append("geo_accurate=false — not verified MRMS production georef.")

    return {
        "bounds": bounds,
        "georef_mode": georef_mode,
        "georef_quality": georef_quality,
        "geo_accurate": False,
        "georef_notes": notes,
        "source_crs": geo.source_crs,
        "bounds_source": bounds_source,
        "has_transform": has_transform,
        "has_pixel_size": has_pixel_size,
    }
