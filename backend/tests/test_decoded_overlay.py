"""Tests for local dev decoded map overlay (Phase 105)."""

from __future__ import annotations

import json

from backend.app.config import settings
from backend.app.services.decoded_overlay import (
    OVERLAY_STATUS_DECODED_PROTOTYPE,
    OVERLAY_STATUS_MISSING,
    PREVIEW_API_PATH,
    build_decoded_overlay,
)
from backend.app.services.mrms_local_render_pipeline import (
    PIPELINE_JSON,
    PREVIEW_DIR,
    save_local_render_pipeline_report,
)
from backend.app.services.selected_frame_decode import FRAME_STATUS_MATCHED, save_frame_cache
from backend.app.services.render_metadata import GeoRenderMetadata, write_geo_metadata
from backend.app.services.tile_service import generate_placeholder_tile_png


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)


def _seed_frame_cache(storage, timestamp: str, preview_path: str, **extra) -> None:
    save_frame_cache(
        storage,
        timestamp,
        {
            "frame_status": FRAME_STATUS_MATCHED,
            "selected_timestamp": timestamp,
            "candidate_timestamp": timestamp,
            "preview_paths": [preview_path],
            "tile_mode": extra.get("tile_mode", "single_image"),
            "tile_preview": extra.get("tile_preview"),
            "tile_root": extra.get("tile_root"),
            "color_scale_mode": extra.get("color_scale_mode"),
            "render_mode": "decoded_prototype",
            "pipeline_status": "preview_ok",
            "sync_message": "test cache",
            **{k: v for k, v in extra.items() if k not in {"tile_mode", "tile_preview", "tile_root", "color_scale_mode"}},
        },
    )


def test_build_decoded_overlay_missing(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    overlay = build_decoded_overlay(storage)
    assert overlay["available"] is False
    assert overlay["overlay_status"] == OVERLAY_STATUS_MISSING
    assert overlay["verified_mrms"] is False
    assert overlay["production_tile_serving"] is False


def test_build_decoded_overlay_with_preview(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    preview_path = storage.normalize_path(PREVIEW_DIR, "preview_z0_x0_y0.png")
    storage.ensure_directories(PREVIEW_DIR)
    storage.write_bytes(preview_path, generate_placeholder_tile_png())

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
        geo_accurate=False,
        georef_quality="rasterio_wgs84_bounds",
        notes=["georef_bounds: dataset.bounds in WGS84"],
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
    assert overlay["artifact_available"] is True
    assert overlay["available"] is False
    assert overlay["overlay_visible"] is False
    assert overlay["sync_status"] == "no_selection"
    assert overlay["preview_url"] is None
    assert overlay["bounds"] == [-100.0, 30.0, -90.0, 40.0]
    assert overlay["georef_quality"] == "rasterio_wgs84_bounds"
    assert overlay["bounds_source"] == "rasterio_transform_wgs84"
    assert overlay["geo_accurate"] is False
    assert "NOT verified MRMS" in overlay["labels"][1]


def test_build_decoded_overlay_sync_matched(storage, db_session, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    preview_path = storage.normalize_path(PREVIEW_DIR, "preview_z0_x0_y0.png")
    storage.ensure_directories(PREVIEW_DIR)
    storage.write_bytes(preview_path, generate_placeholder_tile_png())
    _seed_frame_cache(storage, "2026-06-28T13:26:38Z", preview_path)
    overlay = build_decoded_overlay(
        storage,
        selected_timestamp="2026-06-28T13:26:38Z",
        session=db_session,
    )
    assert overlay["sync_status"] == "matched"
    assert overlay["overlay_visible"] is True
    assert overlay["available"] is True


def test_build_decoded_overlay_with_tiles(storage, db_session, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    preview_path = storage.normalize_path(PREVIEW_DIR, "preview_z0_x0_y0.png")
    storage.ensure_directories(PREVIEW_DIR)
    storage.write_bytes(preview_path, generate_placeholder_tile_png())
    tile_root = storage.normalize_path("dev/mrms_frame_cache", "20260628T132638Z", "tiles")
    _seed_frame_cache(
        storage,
        "2026-06-28T13:26:38Z",
        preview_path,
        tile_mode="local_raster_tiles",
        tile_root=tile_root,
        tile_preview={"built": 5, "max_z": 1, "tile_mode": "local_raster_tiles"},
        color_scale_mode="reflectivity_dbz",
    )
    overlay = build_decoded_overlay(
        storage,
        selected_timestamp="2026-06-28T13:26:38Z",
        session=db_session,
    )
    assert overlay["tile_mode"] == "local_raster_tiles"
    assert overlay["tile_url_template"] == "/api/dev/decoded-overlay/tiles/{z}/{x}/{y}.png"
    assert overlay["tile_count"] == 5


def test_decoded_overlay_api_json(client, storage, db_session, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    preview_path = storage.normalize_path(PREVIEW_DIR, "preview_z0_x0_y0.png")
    storage.ensure_directories(PREVIEW_DIR)
    storage.write_bytes(preview_path, generate_placeholder_tile_png())
    _seed_frame_cache(storage, "2026-06-28T13:26:38Z", preview_path)
    response = client.get("/api/dev/decoded-overlay?timestamp=2026-06-28T13:26:38Z")
    assert response.status_code == 200
    body = response.json()
    assert body["sync_status"] == "matched"
    assert body["overlay_visible"] is True
    assert body["verified_mrms"] is False


def test_decoded_overlay_preview_png(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    preview_path = storage.normalize_path(PREVIEW_DIR, "preview_z0_x0_y0.png")
    storage.ensure_directories(PREVIEW_DIR)
    png = generate_placeholder_tile_png()
    storage.write_bytes(preview_path, png)
    pipeline_json = storage.normalize_path(PIPELINE_JSON)
    storage.ensure_directories(pipeline_json.rsplit("/", 1)[0])
    storage.absolute_path(pipeline_json).write_text(
        json.dumps({"preview_paths": [preview_path]}),
        encoding="utf-8",
    )

    response = client.get("/api/dev/decoded-overlay/preview.png")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("image/png")
    assert response.headers.get("x-radararchive-verified-mrms") == "false"
    assert response.content == png


def test_decoded_overlay_preview_missing_404(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/dev/decoded-overlay/preview.png")
    assert response.status_code == 404


def test_decoded_overlay_tile_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    tile_path = storage.normalize_path("dev/mrms_local_render_tiles", "0", "0", "0.png")
    storage.ensure_directories(tile_path.rsplit("/", 1)[0])
    png = generate_placeholder_tile_png()
    storage.write_bytes(tile_path, png)
    response = client.get("/api/dev/decoded-overlay/tiles/0/0/0.png")
    assert response.status_code == 200
    assert response.content == png
