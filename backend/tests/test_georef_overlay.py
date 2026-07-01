"""Tests for georef overlay resolution (Phase 107+)."""

from backend.app.services.georef_bounds import ENRICHMENT_NOTE_PREFIX, GEOREF_METHOD_RASTERIO_WGS84_AFFINE
from backend.app.services.georef_overlay import (
    GEOREF_QUALITY_RASTERIO_WGS84,
    resolve_georef_overlay,
)
from backend.app.services.render_metadata import GeoRenderMetadata, write_geo_metadata


def test_resolve_georef_overlay_prototype_without_geo(storage):
    result = resolve_georef_overlay(storage, None)
    assert result["geo_accurate"] is False
    assert result["georef_quality"] == "prototype_bounds"


def test_resolve_georef_overlay_rasterio_wgs84(storage):
    decode_dir = storage.normalize_path("staging", "grib2_decode", "fixture")
    storage.ensure_directories(decode_dir)
    geo = GeoRenderMetadata(
        product_name="MRMS",
        valid_timestamp="2026-06-28T13:26:38Z",
        source_crs="EPSG:4326",
        output_crs="EPSG:3857",
        bounds=[-100.0, 30.0, -90.0, 40.0],
        grid_width=100,
        grid_height=50,
        pixel_size_x=0.01,
        pixel_size_y=0.01,
        transform=[0.01, 0.0, -100.0, 0.0, -0.01, 40.0],
        geo_accurate=False,
        georef_quality=GEOREF_METHOD_RASTERIO_WGS84_AFFINE,
        notes=[f"{ENRICHMENT_NOTE_PREFIX} WGS84 affine corners"],
    )
    write_geo_metadata(storage, decode_dir, geo)
    result = resolve_georef_overlay(storage, decode_dir)
    assert result["geo_accurate"] is False
    assert result["georef_quality"] == GEOREF_QUALITY_RASTERIO_WGS84
    assert result["bounds"] == [-100.0, 30.0, -90.0, 40.0]
    assert any("WGS84 bounds" in note for note in result["georef_notes"])
