"""Tests for selected-frame decode (Phase 108)."""

from __future__ import annotations

import json

from backend.app.config import settings
from backend.app.demo.seed import seed_demo_catalog
from backend.app.services.selected_frame_decode import (
    FRAME_STATUS_MATCHED,
    FRAME_STATUS_NO_LOCAL_CANDIDATE,
    FRAME_STATUS_STUB_INPUT,
    frame_cache_dir,
    find_local_mrms_candidate,
    resolve_selected_frame,
    save_frame_cache,
)
from backend.app.services.tile_service import generate_placeholder_tile_png


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)


def test_find_local_mrms_candidate_demo_stub(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    seed_demo_catalog(db_session, storage=storage)
    candidate = find_local_mrms_candidate(db_session, storage, "2026-06-27T20:00:00Z")
    assert candidate is not None
    assert candidate["is_placeholder"] is True


def test_resolve_selected_frame_no_local_candidate(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    seed_demo_catalog(db_session, storage=storage)
    report = resolve_selected_frame(db_session, storage, "2026-06-27T20:00:00Z")
    assert report["frame_status"] == FRAME_STATUS_STUB_INPUT


def test_resolve_selected_frame_no_catalog_match(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    seed_demo_catalog(db_session, storage=storage)
    report = resolve_selected_frame(db_session, storage, "2099-01-01T00:00:00Z")
    assert report["frame_status"] == FRAME_STATUS_NO_LOCAL_CANDIDATE
    assert report.get("nearest_raw_timestamp") is None or isinstance(report["nearest_raw_timestamp"], str)


def test_resolve_selected_frame_from_cache(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    timestamp = "2026-06-28T13:26:38Z"
    cache_dir = frame_cache_dir(storage, timestamp)
    preview_path = storage.normalize_path(cache_dir, "preview_z0_x0_y0.png")
    storage.ensure_directories(cache_dir)
    storage.write_bytes(preview_path, generate_placeholder_tile_png())
    save_frame_cache(
        storage,
        timestamp,
        {
            "frame_status": FRAME_STATUS_MATCHED,
            "selected_timestamp": timestamp,
            "candidate_timestamp": timestamp,
            "preview_paths": [preview_path],
            "tile_mode": "single_image",
            "render_mode": "decoded_prototype",
            "pipeline_status": "preview_ok",
            "sync_message": "cached",
        },
    )
    report = resolve_selected_frame(db_session, storage, timestamp)
    assert report["frame_status"] == FRAME_STATUS_MATCHED
    assert report["preview_paths"][0] == preview_path


def test_resolve_selected_frame_matched_via_mock_decode(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    timestamp = "2026-06-28T13:26:38Z"
    raw_path = storage.normalize_path(
        "raw/mrms/reflectivity",
        "20260628T132638Z_MRMS_ReflectivityAtLowestAltitude_00.50_20260628-132638.grib2.gz",
    )
    storage.ensure_directories(raw_path.rsplit("/", 1)[0])
    storage.write_bytes(raw_path, b"\x1f\x8b\x08\x00" + b"0" * 20)

    from backend.app.models import RadarFile
    from backend.app.models.radar_file import PROCESSED_STATUS_PENDING
    from backend.app.sources.mrms import MRMS_CATALOG_SOURCE

    db_session.add(
        RadarFile(
            product_id="mrms_reflectivity",
            timestamp=timestamp,
            raw_path=raw_path,
            processed_path="data/processed/mrms/reflectivity/x.png",
            processed_status=PROCESSED_STATUS_PENDING,
            source=MRMS_CATALOG_SOURCE,
            raw_kind="mrms_real_grib2",
        )
    )
    db_session.commit()

    decode_dir = storage.normalize_path("staging/grib2_decode", "fixture_frame")
    storage.ensure_directories(decode_dir)
    storage.absolute_path(storage.normalize_path(decode_dir, "decode_manifest.json")).write_text(
        json.dumps(
            {
                "prototype": True,
                "production_rendering": False,
                "raw_path": raw_path,
                "raster_path": "normalized.raw",
                "width": 4,
                "height": 4,
                "value_min": 0,
                "value_max": 1,
            }
        ),
        encoding="utf-8",
    )
    import struct

    grid = struct.pack("16f", *([0.5] * 16))
    storage.write_bytes(storage.normalize_path(decode_dir, "normalized.raw"), grid)

    def _mock_decode(storage, raw_path, **kwargs):
        from backend.app.services.grib2_decoder import Grib2DecodeResult

        return Grib2DecodeResult(
            raw_path=raw_path,
            raw_kind="mrms_real_grib2",
            success=True,
            decoder_used="mock",
            output_dir=decode_dir,
            manifest_path=storage.normalize_path(decode_dir, "decode_manifest.json"),
            raster_path=storage.normalize_path(decode_dir, "normalized.raw"),
            width=4,
            height=4,
        )

    monkeypatch.setattr(
        "backend.app.services.selected_frame_decode.decode_grib2_file",
        _mock_decode,
    )
    monkeypatch.setattr(
        "backend.app.services.selected_frame_decode.build_decode_output_dir",
        lambda storage, raw_path: decode_dir,
    )
    monkeypatch.setattr(
        "backend.app.services.selected_frame_decode.detect_decoder_availability",
        lambda: type("D", (), {"any_decoder": True, "summary_message": lambda self: "ok"})(),
    )

    report = resolve_selected_frame(db_session, storage, timestamp)
    assert report["frame_status"] == FRAME_STATUS_MATCHED
    assert report["preview_paths"]
