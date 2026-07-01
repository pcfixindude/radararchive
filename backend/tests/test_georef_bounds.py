"""Tests for WGS84 georef bounds extraction (Phase 114)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from backend.app.services.georef_bounds import (
    ENRICHMENT_NOTE_PREFIX,
    GEOREF_METHOD_PROTOTYPE,
    GEOREF_METHOD_RASTERIO_WGS84_AFFINE,
    GEOREF_METHOD_RASTERIO_WGS84_BOUNDS,
    bounds_from_affine_corners,
    extract_wgs84_bounds_from_dataset,
    is_wgs84_crs,
    normalize_wgs84_bounds,
    transform_bounds_to_wgs84,
)
from backend.app.services.georef_overlay import (
    GEOREF_QUALITY_PROTOTYPE,
    GEOREF_QUALITY_RASTERIO_WGS84,
    resolve_georef_overlay,
)
from backend.app.services.render_metadata import GeoRenderMetadata, write_geo_metadata


def test_is_wgs84_crs():
    assert is_wgs84_crs("EPSG:4326")
    assert is_wgs84_crs("OGC:CRS84")
    assert not is_wgs84_crs("EPSG:3857")


def test_normalize_wgs84_bounds():
    assert normalize_wgs84_bounds(-100, 30, -90, 40) == [-100.0, 30.0, -90.0, 40.0]


def test_bounds_from_affine_corners_wgs84():
    from rasterio.transform import from_bounds

    transform = from_bounds(-100.0, 30.0, -90.0, 40.0, 100, 50)
    west, south, east, north = bounds_from_affine_corners(transform, 100, 50)
    assert west == -100.0
    assert south == 30.0
    assert east == -90.0
    assert north == 40.0


@patch("rasterio.warp.transform_bounds")
def test_transform_bounds_to_wgs84(mock_transform_bounds):
    mock_transform_bounds.return_value = (-98.0, 31.0, -88.0, 41.0)
    bounds = transform_bounds_to_wgs84(-100, 30, -90, 40, "EPSG:3857")
    assert bounds == [-98.0, 31.0, -88.0, 41.0]
    mock_transform_bounds.assert_called_once()


def test_extract_wgs84_bounds_from_dataset_wgs84_affine():
    from rasterio.transform import from_bounds

    transform = from_bounds(-100.0, 30.0, -90.0, 40.0, 100, 50)
    dataset = SimpleNamespace(
        crs="EPSG:4326",
        transform=transform,
        width=100,
        height=50,
        bounds=SimpleNamespace(left=-100, bottom=30, right=-90, top=40),
        res=(0.1, 0.2),
    )
    result = extract_wgs84_bounds_from_dataset(dataset)
    assert result["georef_quality"] == GEOREF_METHOD_RASTERIO_WGS84_AFFINE
    assert result["bounds"] == [-100.0, 30.0, -90.0, 40.0]
    assert any(ENRICHMENT_NOTE_PREFIX in note for note in result["notes"])


@patch("backend.app.services.georef_bounds.transform_bounds_to_wgs84")
def test_extract_wgs84_bounds_from_dataset_reprojects(mock_reproject):
    from rasterio.transform import from_bounds

    mock_reproject.return_value = [-98.0, 31.0, -88.0, 41.0]
    transform = from_bounds(0, 0, 1000, 1000, 100, 50)
    dataset = SimpleNamespace(
        crs="EPSG:3857",
        transform=transform,
        width=100,
        height=50,
        bounds=SimpleNamespace(left=0, bottom=0, right=1000, top=1000),
        res=(10.0, 20.0),
    )
    result = extract_wgs84_bounds_from_dataset(dataset)
    assert result["georef_quality"] == GEOREF_METHOD_RASTERIO_WGS84_BOUNDS
    assert result["bounds"] == [-98.0, 31.0, -88.0, 41.0]
    mock_reproject.assert_called_once()


def test_extract_wgs84_bounds_missing_crs_fallback():
    dataset = SimpleNamespace(
        crs=None,
        transform=None,
        width=0,
        height=0,
        bounds=None,
        res=None,
    )
    result = extract_wgs84_bounds_from_dataset(dataset)
    assert result["georef_quality"] == GEOREF_METHOD_PROTOTYPE


def test_resolve_georef_overlay_prototype_without_geo(storage):
    result = resolve_georef_overlay(storage, None)
    assert result["geo_accurate"] is False
    assert result["georef_quality"] == GEOREF_QUALITY_PROTOTYPE
    assert result["bounds_source"] == "prototype_fallback"


def test_resolve_georef_overlay_rasterio_wgs84_affine(storage):
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
    assert result["bounds_source"] == "rasterio_affine_wgs84"
    assert any("not verified MRMS" in note for note in result["georef_notes"])


def test_enrich_geo_metadata_from_rasterio_uses_wgs84_bounds(storage, monkeypatch):
    from backend.app.services.render_metadata import enrich_geo_metadata_from_rasterio

    raster_path = storage.normalize_path("staging", "grib2_decode", "fixture", "normalized.tif")
    storage.ensure_directories(raster_path.rsplit("/", 1)[0])
    storage.write_bytes(raster_path, b"not-a-real-tiff")

    enriched_payload = {
        "bounds": [-101.0, 29.0, -89.0, 41.0],
        "georef_quality": GEOREF_METHOD_RASTERIO_WGS84_BOUNDS,
        "source_crs": "EPSG:4326",
        "transform": [0.01, 0.0, -101.0, 0.0, -0.01, 41.0],
        "pixel_size_x": 0.01,
        "pixel_size_y": 0.01,
        "notes": [f"{ENRICHMENT_NOTE_PREFIX} dataset.bounds in WGS84"],
    }
    monkeypatch.setattr(
        "backend.app.services.georef_bounds.extract_wgs84_bounds_from_raster_path",
        lambda _path: enriched_payload,
    )

    geo = GeoRenderMetadata(
        product_name="MRMS",
        valid_timestamp="2026-06-28T13:26:38Z",
        source_crs=None,
        output_crs="EPSG:3857",
        bounds=[-125.0, 24.0, -66.0, 50.0],
        grid_width=100,
        grid_height=50,
    )
    result = enrich_geo_metadata_from_rasterio(storage, raster_path, geo)
    assert result.bounds == [-101.0, 29.0, -89.0, 41.0]
    assert result.georef_quality == GEOREF_METHOD_RASTERIO_WGS84_BOUNDS
    assert result.geo_accurate is False
