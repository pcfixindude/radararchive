"""Tests for local-dev frame quality checks (Phase 115)."""

from __future__ import annotations

import json

from backend.app.services.frame_quality import (
    CHECK_ARTIFACTS,
    CHECK_DECODE_MANIFEST,
    CHECK_DIMENSIONS,
    CHECK_GEOREF_BOUNDS,
    CHECK_GRID_VALUES,
    QUALITY_ERROR,
    QUALITY_OK,
    QUALITY_UNAVAILABLE,
    QUALITY_WARNING,
    assess_frame_quality,
)
from backend.app.services.georef_overlay import GEOREF_QUALITY_PROTOTYPE, resolve_georef_overlay
from backend.app.services.render_metadata import GeoRenderMetadata, write_geo_metadata


def _write_decode_manifest(storage, decode_dir: str, *, width=10, height=8, vmin=0.0, vmax=1.0):
    storage.ensure_directories(decode_dir)
    raster_name = "normalized.raw"
    raster_path = storage.normalize_path(decode_dir, raster_name)
    storage.write_bytes(raster_path, b"\x00" * (width * height * 4))
    manifest = {
        "prototype": True,
        "production_rendering": False,
        "raw_path": "data/raw/mrms/reflectivity/test.grib2.gz",
        "width": width,
        "height": height,
        "value_min": vmin,
        "value_max": vmax,
        "raster_path": raster_name,
        "decoder": "test",
    }
    storage.absolute_path(storage.normalize_path(decode_dir, "decode_manifest.json")).write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    return raster_path


def test_assess_frame_quality_ok(storage):
    decode_dir = storage.normalize_path("staging", "grib2_decode", "quality_ok")
    _write_decode_manifest(storage, decode_dir)
    preview = storage.normalize_path("dev", "preview.png")
    storage.write_bytes(preview, b"png")
    geo = GeoRenderMetadata(
        product_name="MRMS",
        valid_timestamp="2026-06-28T13:26:38Z",
        source_crs="EPSG:4326",
        output_crs="EPSG:3857",
        bounds=[-100.0, 30.0, -90.0, 40.0],
        grid_width=10,
        grid_height=8,
        georef_quality="rasterio_wgs84_affine",
    )
    write_geo_metadata(storage, decode_dir, geo)
    georef = resolve_georef_overlay(storage, decode_dir)

    report = assess_frame_quality(
        storage,
        decode_output_dir=decode_dir,
        preview_path=preview,
        georef=georef,
        tile_preview={"built": 2, "tile_mode": "local_raster_tiles", "max_z": 1},
        overlay_visible=True,
    )

    assert report["status"] == QUALITY_OK
    assert report["diagnostic_only"] is True
    assert report["verified_mrms"] is False
    names = {item["name"] for item in report["checks"]}
    assert CHECK_ARTIFACTS in names
    assert CHECK_DECODE_MANIFEST in names


def test_assess_frame_quality_missing_preview_error(storage):
    decode_dir = storage.normalize_path("staging", "grib2_decode", "quality_missing_preview")
    _write_decode_manifest(storage, decode_dir)
    georef = resolve_georef_overlay(storage, decode_dir)

    report = assess_frame_quality(
        storage,
        decode_output_dir=decode_dir,
        preview_path=storage.normalize_path("dev", "missing.png"),
        georef=georef,
        overlay_visible=True,
    )

    assert report["status"] == QUALITY_ERROR
    artifacts = next(c for c in report["checks"] if c["name"] == CHECK_ARTIFACTS)
    assert artifacts["status"] == QUALITY_ERROR


def test_assess_frame_quality_flat_grid_warning(storage):
    decode_dir = storage.normalize_path("staging", "grib2_decode", "quality_flat")
    _write_decode_manifest(storage, decode_dir, vmin=0.5, vmax=0.5)
    georef = resolve_georef_overlay(storage, decode_dir)

    report = assess_frame_quality(
        storage,
        decode_output_dir=decode_dir,
        georef=georef,
        overlay_visible=False,
    )

    grid = next(c for c in report["checks"] if c["name"] == CHECK_GRID_VALUES)
    assert grid["status"] == QUALITY_WARNING
    assert report["status"] in {QUALITY_WARNING, QUALITY_ERROR}


def test_assess_frame_quality_dimension_mismatch_warning(storage):
    decode_dir = storage.normalize_path("staging", "grib2_decode", "quality_dims")
    _write_decode_manifest(storage, decode_dir, width=10, height=8)
    geo = GeoRenderMetadata(
        product_name="MRMS",
        valid_timestamp=None,
        source_crs="EPSG:4326",
        output_crs="EPSG:3857",
        bounds=[-100.0, 30.0, -90.0, 40.0],
        grid_width=99,
        grid_height=8,
    )
    write_geo_metadata(storage, decode_dir, geo)
    georef = resolve_georef_overlay(storage, decode_dir)

    report = assess_frame_quality(storage, decode_output_dir=decode_dir, georef=georef)
    dims = next(c for c in report["checks"] if c["name"] == CHECK_DIMENSIONS)
    assert dims["status"] == QUALITY_WARNING


def test_assess_frame_quality_prototype_georef_warning(storage):
    georef = {
        "bounds": [-125.0, 24.0, -66.0, 50.0],
        "georef_quality": GEOREF_QUALITY_PROTOTYPE,
        "bounds_source": "prototype_fallback",
    }
    report = assess_frame_quality(storage, georef=georef)
    georef_check = next(c for c in report["checks"] if c["name"] == CHECK_GEOREF_BOUNDS)
    assert georef_check["status"] == QUALITY_WARNING


def test_assess_frame_quality_unavailable_without_context(storage):
    report = assess_frame_quality(storage)
    assert report["status"] == QUALITY_UNAVAILABLE
    manifest = next(c for c in report["checks"] if c["name"] == CHECK_DECODE_MANIFEST)
    assert manifest["status"] == QUALITY_UNAVAILABLE


def test_decoded_overlay_includes_frame_quality(storage, monkeypatch):
    from backend.app.config import settings
    from backend.app.services.decoded_overlay import build_decoded_overlay
    from backend.app.services.mrms_local_render_pipeline import PREVIEW_DIR, save_local_render_pipeline_report
    from backend.app.services.tile_service import generate_placeholder_tile_png

    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    decode_dir = storage.normalize_path("staging", "grib2_decode", "overlay_quality")
    _write_decode_manifest(storage, decode_dir)
    preview_path = storage.normalize_path(PREVIEW_DIR, "preview_z0_x0_y0.png")
    storage.ensure_directories(PREVIEW_DIR)
    storage.write_bytes(preview_path, generate_placeholder_tile_png())
    geo = GeoRenderMetadata(
        product_name="MRMS",
        valid_timestamp="2026-06-28T13:26:38Z",
        source_crs="EPSG:4326",
        output_crs="EPSG:3857",
        bounds=[-100.0, 30.0, -90.0, 40.0],
        grid_width=10,
        grid_height=8,
        georef_quality="rasterio_wgs84_affine",
    )
    write_geo_metadata(storage, decode_dir, geo)

    save_local_render_pipeline_report(
        storage,
        {
            "ran_at": "2026-06-28T14:00:00Z",
            "pipeline_status": "preview_ok",
            "render_mode": "decoded_prototype",
            "produced_local_artifact": True,
            "preview_paths": [preview_path],
            "decode_output_dir": decode_dir,
            "candidate": {"raw_path": "data/raw/mrms/reflectivity/test.grib2.gz"},
        },
    )

    overlay = build_decoded_overlay(storage)
    assert "frame_quality" in overlay
    assert overlay["frame_quality"]["status"] in {QUALITY_OK, QUALITY_WARNING, QUALITY_UNAVAILABLE}
    assert overlay["frame_quality"]["verified_mrms"] is False
