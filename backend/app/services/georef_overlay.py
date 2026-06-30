"""Georef resolution for local decoded overlay (prototype, not production)."""

from __future__ import annotations

from typing import Any, Optional

from backend.app.services.render_metadata import DEFAULT_MRMS_BOUNDS, GeoRenderMetadata, load_geo_metadata
from backend.app.services.storage import LocalStorage

GEOREF_QUALITY_PROTOTYPE = "prototype_bounds"
GEOREF_QUALITY_RASTERIO_BOUNDS = "rasterio_bounds"
GEOREF_QUALITY_RASTERIO_WGS84 = "rasterio_wgs84_affine"


def resolve_georef_overlay(
    storage: LocalStorage,
    decode_output_dir: Optional[str],
) -> dict[str, Any]:
    """Return bounds and georef metadata; geo_accurate stays false unless production-validated."""
    if not decode_output_dir:
        return {
            "bounds": list(DEFAULT_MRMS_BOUNDS),
            "georef_mode": GEOREF_QUALITY_PROTOTYPE,
            "georef_quality": GEOREF_QUALITY_PROTOTYPE,
            "geo_accurate": False,
            "georef_notes": [
                "No decode output dir — using DEFAULT_MRMS_BOUNDS prototype placement.",
                "Missing: decode artifact, geo_metadata.json, rasterio enrichment.",
            ],
        }

    geo = load_geo_metadata(storage, decode_output_dir)
    if geo is None or len(geo.bounds) != 4:
        return {
            "bounds": list(DEFAULT_MRMS_BOUNDS),
            "georef_mode": GEOREF_QUALITY_PROTOTYPE,
            "georef_quality": GEOREF_QUALITY_PROTOTYPE,
            "geo_accurate": False,
            "georef_notes": [
                "geo_metadata.json missing or incomplete — prototype CONUS bounds used.",
            ],
        }

    bounds = [float(v) for v in geo.bounds]
    notes: list[str] = list(geo.notes or [])
    rasterio_enriched = any("Enriched from rasterio" in note for note in notes)
    crs = (geo.source_crs or "").upper()
    has_wgs84 = crs in {"EPSG:4326", "WGS84"} or "4326" in crs
    has_transform = geo.transform is not None and len(geo.transform or []) >= 6
    has_pixel_size = geo.pixel_size_x is not None and geo.pixel_size_y is not None

    georef_quality = GEOREF_QUALITY_PROTOTYPE
    georef_mode = GEOREF_QUALITY_PROTOTYPE
    if rasterio_enriched:
        georef_mode = GEOREF_QUALITY_RASTERIO_BOUNDS
        georef_quality = GEOREF_QUALITY_RASTERIO_BOUNDS
        notes.append("Rasterio bounds used for map overlay (prototype local dev).")
    if rasterio_enriched and has_wgs84 and has_transform:
        georef_quality = GEOREF_QUALITY_RASTERIO_WGS84
        georef_mode = GEOREF_QUALITY_RASTERIO_WGS84
        notes.append("WGS84 affine available from rasterio — still not production geo-accurate.")
    if not has_wgs84:
        notes.append("CRS not confirmed as WGS84/EPSG:4326 — bounds may not align with map.")
    if not has_transform:
        notes.append("Missing raster affine transform — tile warping not validated.")
    if not has_pixel_size:
        notes.append("Missing pixel size metadata.")

    return {
        "bounds": bounds,
        "georef_mode": georef_mode,
        "georef_quality": georef_quality,
        "geo_accurate": False,
        "georef_notes": notes,
        "source_crs": geo.source_crs,
        "has_transform": has_transform,
        "has_pixel_size": has_pixel_size,
    }
