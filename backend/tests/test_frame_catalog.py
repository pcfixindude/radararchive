"""Tests for frame catalog browser (Phase 122)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.frame_catalog import (
    build_frame_catalog,
    resolve_frame_decode_state,
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


def test_resolve_frame_decode_state_ready(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts = "2026-06-28T13:26:38Z"
    cache_dir = storage.normalize_path("dev/mrms_frame_cache", "20260628T132638Z")
    preview_path = storage.normalize_path(cache_dir, "preview_z0_x0_y0.png")
    storage.ensure_directories(cache_dir)
    storage.write_bytes(preview_path, generate_placeholder_tile_png())
    save_frame_cache(
        storage,
        ts,
        {
            "frame_status": FRAME_STATUS_MATCHED,
            "selected_timestamp": ts,
            "preview_paths": [preview_path],
        },
    )
    ready, status = resolve_frame_decode_state(storage, ts)
    assert ready is True
    assert status == FRAME_STATUS_MATCHED


def test_build_frame_catalog_newest_first(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts_old = "2026-06-28T13:00:00Z"
    ts_new = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts_old)
    _register_real_frame(db_session, storage, ts_new)

    catalog = build_frame_catalog(
        db_session,
        storage,
        timestamps=[ts_old, ts_new],
    )

    assert catalog["frame_count"] == 2
    assert catalog["frames"][0]["timestamp"] == ts_new
    assert catalog["frames"][1]["timestamp"] == ts_old
    assert catalog["verified_mrms"] is False


def test_build_frame_catalog_cache_and_decode_counts(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts)
    cache_dir = storage.normalize_path("dev/mrms_frame_cache", "20260628T132638Z")
    preview_path = storage.normalize_path(cache_dir, "preview_z0_x0_y0.png")
    storage.ensure_directories(cache_dir)
    storage.write_bytes(preview_path, generate_placeholder_tile_png())
    save_frame_cache(
        storage,
        ts,
        {
            "frame_status": FRAME_STATUS_MATCHED,
            "selected_timestamp": ts,
            "preview_paths": [preview_path],
        },
    )

    catalog = build_frame_catalog(db_session, storage, timestamps=[ts])

    assert catalog["cache_ready_count"] == 1
    assert catalog["decode_ready_count"] == 1
    frame = catalog["frames"][0]
    assert frame["cache_state"] == CACHE_STATE_READY
    assert frame["cache_ready"] is True
    assert frame["decode_ready"] is True


def test_frame_catalog_api(client, storage, db_session, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts)

    response = client.get(
        "/api/dev/frame-catalog",
        params={"timestamps": ts, "limit": 8},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["frame_count"] == 1
    assert body["verified_mrms"] is False
    assert body["frames"][0]["timestamp"] == ts
    assert "cache_state" in body["frames"][0]
    assert "decode_ready" in body["frames"][0]
