"""Tests for playback clip manifest import (Phase 125)."""

from __future__ import annotations

import json

from backend.app.config import settings
from backend.app.services.clip_import import (
    IMPORT_STATUS_INVALID,
    IMPORT_STATUS_PARTIAL,
    IMPORT_STATUS_READY,
    build_clip_import_report,
    extract_apply_frame_timestamps,
    validate_clip_manifest,
)
from backend.app.services.playback_export import EXPORT_KIND, MAX_CLIP_FRAMES, build_playback_export
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


def _sample_export_manifest(ts_old: str, ts_new: str) -> dict:
    return {
        "clip_id": "clip_test",
        "export_kind": EXPORT_KIND,
        "layer_id": "mrms_reflectivity",
        "range_start": ts_old,
        "range_end": ts_new,
        "range_order_adjusted": False,
        "loop_suggested": True,
        "frame_count": 2,
        "cache_ready_count": 1,
        "decode_ready_count": 0,
        "missing_cache_count": 0,
        "cold_count": 1,
        "failed_count": 0,
        "frames": [
            {
                "timestamp": ts_old,
                "index": 0,
                "cache_state": "ready",
                "cache_ready": True,
                "decode_ready": False,
                "preview_paths": [],
                "preview_path_count": 0,
            },
            {
                "timestamp": ts_new,
                "index": 1,
                "cache_state": "cold_no_manifest",
                "cache_ready": False,
                "decode_ready": False,
                "preview_paths": [],
                "preview_path_count": 0,
            },
        ],
        "exported_at": "2026-06-28T14:00:00Z",
        "status": "ready",
        "verified_mrms": False,
        "local_dev_only": True,
        "prototype": True,
        "production_tile_serving": False,
    }


def test_validate_clip_manifest_rejects_non_object():
    normalized, errors, warnings = validate_clip_manifest([])
    assert normalized is None
    assert errors
    assert not warnings


def test_validate_clip_manifest_rejects_verified_mrms():
    manifest = _sample_export_manifest("2026-06-28T13:00:00Z", "2026-06-28T13:26:38Z")
    manifest["verified_mrms"] = True
    normalized, errors, _ = validate_clip_manifest(manifest)
    assert normalized is None
    assert any("verified_mrms" in error for error in errors)


def test_validate_clip_manifest_rejects_wrong_export_kind():
    manifest = _sample_export_manifest("2026-06-28T13:00:00Z", "2026-06-28T13:26:38Z")
    manifest["export_kind"] = "other_kind"
    normalized, errors, _ = validate_clip_manifest(manifest)
    assert normalized is None
    assert any("export_kind" in error for error in errors)


def test_validate_clip_manifest_normalizes_timestamps():
    manifest = _sample_export_manifest("2026-06-28T13:00:00Z", "2026-06-28T13:26:38Z")
    normalized, errors, warnings = validate_clip_manifest(manifest)
    assert not errors
    assert normalized is not None
    assert normalized["range_start"] == "2026-06-28T13:00:00Z"
    assert normalized["loop_suggested"] is True
    assert len(normalized["frames"]) == 2
    assert warnings


def test_extract_apply_frame_timestamps_returns_ordered_unique_list():
    manifest = _sample_export_manifest("2026-06-28T13:00:00Z", "2026-06-28T13:26:38Z")
    timestamps = extract_apply_frame_timestamps(manifest)
    assert timestamps == ["2026-06-28T13:00:00Z", "2026-06-28T13:26:38Z"]


def test_extract_apply_frame_timestamps_bounds_to_max_clip_frames():
    manifest = _sample_export_manifest("2026-06-28T13:00:00Z", "2026-06-28T13:26:38Z")
    manifest["frames"] = [
        {
            "timestamp": f"2026-06-28T{index // 60:02d}:{index % 60:02d}:00Z",
            "index": index,
            "cache_state": "ready",
            "cache_ready": True,
            "decode_ready": False,
            "preview_paths": [],
            "preview_path_count": 0,
        }
        for index in range(MAX_CLIP_FRAMES + 3)
    ]
    timestamps = extract_apply_frame_timestamps(manifest)
    assert len(timestamps) == MAX_CLIP_FRAMES


def test_extract_apply_frame_timestamps_returns_empty_without_frames():
    manifest = _sample_export_manifest("2026-06-28T13:00:00Z", "2026-06-28T13:26:38Z")
    manifest["frames"] = []
    assert extract_apply_frame_timestamps(manifest) == []


def test_build_clip_import_report_refreshes_readiness(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts_old = "2026-06-28T13:00:00Z"
    ts_new = "2026-06-28T13:26:38Z"
    for ts in (ts_old, ts_new):
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
        timestamps=[ts_old, ts_new],
        loop_suggested=True,
    )
    report = build_clip_import_report(db_session, storage, manifest)

    assert report["valid"] is True
    assert report["import_status"] in {IMPORT_STATUS_READY, IMPORT_STATUS_PARTIAL}
    assert report["manifest"]["range_start"] == ts_old
    assert report["manifest"]["loop_suggested"] is True
    assert report["readiness_summary"]["frame_count"] == 2
    assert report["verified_mrms"] is False
    assert report["does_not_run_decode"] is True


def test_clip_import_api(client, storage, db_session, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts_old = "2026-06-28T13:00:00Z"
    ts_new = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts_old)
    _register_real_frame(db_session, storage, ts_new)

    manifest = _sample_export_manifest(ts_old, ts_new)
    response = client.post("/api/dev/clip-import", json={"manifest": manifest})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["manifest"]["clip_id"] == "clip_test"
    assert body["manifest"]["loop_suggested"] is True
    assert body["verified_mrms"] is False


def test_clip_import_api_rejects_invalid_manifest(client):
    response = client.post(
        "/api/dev/clip-import",
        json={"manifest": {"export_kind": "wrong", "verified_mrms": True}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["import_status"] == IMPORT_STATUS_INVALID
    assert body["errors"]


def test_clip_import_cli_writes_report(db_session, storage, monkeypatch, tmp_path):
    _use_test_storage(monkeypatch, storage)
    ts_old = "2026-06-28T13:00:00Z"
    ts_new = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts_old)
    _register_real_frame(db_session, storage, ts_new)

    manifest = _sample_export_manifest(ts_old, ts_new)
    manifest_path = tmp_path / "clip.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    from scripts import clip_import as clip_import_script

    monkeypatch.setattr(
        "sys.argv",
        ["clip_import.py", "--file", str(manifest_path)],
    )
    clip_import_script.main()

    report_path = storage.absolute_path("dev/clip_import_latest.json")
    assert report_path.is_file()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["valid"] is True
