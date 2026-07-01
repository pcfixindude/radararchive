"""Tests for frame quality drill-down (Phase 124)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.frame_quality_report import (
    READINESS_COLD,
    READINESS_MISSING,
    READINESS_PARTIAL,
    READINESS_READY,
    build_frame_quality_detail,
    build_frame_quality_report,
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


def test_build_frame_quality_detail_ready(db_session, storage, monkeypatch):
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
            "sync_message": "Cached for playback.",
        },
    )

    detail = build_frame_quality_detail(db_session, storage, ts)

    assert detail["valid"] is True
    assert detail["readiness_summary"] in {READINESS_READY, READINESS_PARTIAL}
    assert detail["decode_ready"] is True
    assert detail["path_hints"]["preview_available"] is True
    assert detail["path_hints"]["manifest_present"] is True
    assert detail["frame_quality"]["verified_mrms"] is False
    assert detail["suggested_commands"]
    assert detail["does_not_run_decode"] is True


def test_build_frame_quality_detail_cold(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts = "2026-06-28T13:00:00Z"
    _register_real_frame(db_session, storage, ts)

    detail = build_frame_quality_detail(db_session, storage, ts)

    assert detail["valid"] is True
    assert detail["readiness_summary"] == READINESS_COLD
    assert detail["cache_state"] != CACHE_STATE_READY
    assert "make mrms-warm-frame-cache" in detail["suggested_commands"][0]
    assert detail["path_hints"]["raw_path"] is not None


def test_build_frame_quality_detail_missing(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts = "2026-06-28T12:00:00Z"

    detail = build_frame_quality_detail(db_session, storage, ts)

    assert detail["valid"] is True
    assert detail["readiness_summary"] == READINESS_MISSING
    assert detail["path_hints"]["preview_available"] is False


def test_build_frame_quality_report_multiple(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts_ready = "2026-06-28T13:26:38Z"
    ts_cold = "2026-06-28T13:00:00Z"
    _register_real_frame(db_session, storage, ts_ready)
    _register_real_frame(db_session, storage, ts_cold)
    cache_dir = storage.normalize_path("dev/mrms_frame_cache", "20260628T132638Z")
    preview_path = storage.normalize_path(cache_dir, "preview_z0_x0_y0.png")
    storage.ensure_directories(cache_dir)
    storage.write_bytes(preview_path, generate_placeholder_tile_png())
    save_frame_cache(
        storage,
        ts_ready,
        {
            "frame_status": FRAME_STATUS_MATCHED,
            "selected_timestamp": ts_ready,
            "preview_paths": [preview_path],
        },
    )

    report = build_frame_quality_report(
        db_session,
        storage,
        timestamps=[ts_ready, ts_cold, "not-a-timestamp"],
    )

    assert report["frame_count"] == 2
    assert report["cold_count"] == 1
    assert report["ready_count"] + report["partial_count"] == 1
    assert report["verified_mrms"] is False
    assert report["status_only"] is True


def test_frame_quality_api(client, storage, db_session, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts)

    response = client.get(
        "/api/dev/frame-quality",
        params={"timestamps": ts},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["frame_count"] == 1
    assert body["verified_mrms"] is False
    assert body["does_not_run_decode"] is True
    frame = body["frames"][0]
    assert frame["timestamp"] == ts
    assert "path_hints" in frame
    assert "suggested_commands" in frame
    assert "frame_quality" in frame


def test_frame_quality_api_requires_timestamps(client):
    response = client.get("/api/dev/frame-quality")
    assert response.status_code == 422
