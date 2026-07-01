"""Tests for playback clip export (Phase 123)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.playback_export import (
    build_clip_id,
    build_playback_export,
    resolve_clip_timestamps,
)
from backend.app.services.playback_cache_status import CACHE_STATE_READY
from backend.app.services.selected_frame_decode import FRAME_STATUS_MATCHED, save_frame_cache
from backend.app.services.tile_service import generate_placeholder_tile_png


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)


def _register_real_frame(db_session, storage, ts: str):
    from backend.app.models import Layer, Product, RadarFile
    from backend.app.services.raw_file_classifier import RAW_KIND_MRMS_REAL_GRIB2
    from backend.app.sources.mrms import MRMS_CATALOG_SOURCE

    layer = db_session.get(Layer, "mrms_reflectivity")
    if layer is None:
        layer = Layer(id="mrms_reflectivity", name="MRMS Reflectivity", type="raster", available=True)
        db_session.add(layer)
    product = db_session.get(Product, "mrms_reflectivity")
    if product is None:
        product = Product(id="mrms_reflectivity", layer_id="mrms_reflectivity", name="MRMS Reflectivity")
        db_session.add(product)
    raw_path = storage.normalize_path(
        "raw/mrms/reflectivity",
        f"MRMS_ReflectivityAtLowestAltitude.{ts.replace(':', '').replace('-', '')}.grib2.gz",
    )
    storage.ensure_directories(storage.normalize_path("raw/mrms/reflectivity"))
    storage.write_bytes(raw_path, b"fake-grib2")
    row = RadarFile(
        timestamp=ts,
        product_id="mrms_reflectivity",
        raw_path=raw_path,
        raw_kind=RAW_KIND_MRMS_REAL_GRIB2,
        source=MRMS_CATALOG_SOURCE,
    )
    db_session.add(row)
    db_session.commit()


def test_resolve_clip_timestamps_from_playback_list():
    times = [
        "2026-06-28T13:00:00Z",
        "2026-06-28T13:13:00Z",
        "2026-06-28T13:26:38Z",
    ]
    clip, adjusted = resolve_clip_timestamps(
        "2026-06-28T13:26:38Z",
        "2026-06-28T13:00:00Z",
        timestamps=times,
    )
    assert adjusted is True
    assert clip == times


def test_build_clip_id():
    clip_id = build_clip_id("2026-06-28T13:00:00Z", "2026-06-28T13:26:38Z")
    assert clip_id == "clip_20260628T130000Z_20260628T132638Z"


def test_build_playback_export_manifest(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts_old = "2026-06-28T13:00:00Z"
    ts_mid = "2026-06-28T13:13:00Z"
    ts_new = "2026-06-28T13:26:38Z"
    for ts in (ts_old, ts_mid, ts_new):
        _register_real_frame(db_session, storage, ts)

    cache_dir = storage.normalize_path("dev/mrms_frame_cache", "20260628T132638Z")
    preview_path = storage.normalize_path(cache_dir, "preview_z0_x0_y0.png")
    storage.ensure_directories(cache_dir)
    storage.write_bytes(preview_path, generate_placeholder_tile_png())
    save_frame_cache(
        storage,
        ts_new,
        {
            "frame_status": FRAME_STATUS_MATCHED,
            "selected_timestamp": ts_new,
            "preview_paths": [preview_path],
        },
    )

    manifest = build_playback_export(
        db_session,
        storage,
        range_start=ts_old,
        range_end=ts_new,
        timestamps=[ts_old, ts_mid, ts_new],
        loop_suggested=True,
    )

    assert manifest["status"] == "ready"
    assert manifest["frame_count"] == 3
    assert manifest["loop_suggested"] is True
    assert manifest["verified_mrms"] is False
    assert manifest["frames"][0]["timestamp"] == ts_old
    assert manifest["frames"][-1]["timestamp"] == ts_new
    assert manifest["frames"][-1]["preview_path_count"] == 1
    assert manifest["frames"][-1]["preview_paths"] == [preview_path]
    assert manifest["decode_ready_count"] == 1
    assert manifest["cache_ready_count"] >= 1


def test_playback_export_api(client, storage, db_session, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts_old = "2026-06-28T13:00:00Z"
    ts_new = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts_old)
    _register_real_frame(db_session, storage, ts_new)

    response = client.get(
        "/api/dev/playback-export",
        params={
            "range_start": ts_old,
            "range_end": ts_new,
            "timestamps": f"{ts_old},{ts_new}",
            "loop": "true",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["export_kind"] == "playback_clip_manifest"
    assert body["frame_count"] == 2
    assert body["loop_suggested"] is True
    assert body["verified_mrms"] is False
    assert body["frames"][0]["cache_state"] == CACHE_STATE_READY or body["frames"][0]["cache_state"]


def test_playback_export_api_requires_range(client):
    response = client.get(
        "/api/dev/playback-export",
        params={"range_start": "", "range_end": "2026-06-28T13:26:38Z"},
    )
    assert response.status_code == 422 or response.status_code == 400
