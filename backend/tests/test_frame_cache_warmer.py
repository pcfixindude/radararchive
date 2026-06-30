"""Tests for frame cache warming (Phase 111)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.frame_cache_warmer import (
    load_cache_warm_report,
    run_cache_warm,
    select_cache_window,
    save_cache_warm_report,
)
from backend.app.services.mrms_bulk_ingest import save_bulk_ingest_report
from backend.app.services.selected_frame_decode import (
    FRAME_STATUS_MATCHED,
    save_frame_cache,
)
from backend.app.services.tile_service import generate_placeholder_tile_png


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)


def test_select_cache_window_from_bulk_ingest_report(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_bulk_ingest_report(
        storage,
        {
            "registered_timestamps": [
                "2026-06-28T13:20:00Z",
                "2026-06-28T13:25:00Z",
                "2026-06-28T13:26:38Z",
            ],
            "downloaded_timestamps": [
                "2026-06-28T13:20:00Z",
                "2026-06-28T13:25:00Z",
                "2026-06-28T13:26:38Z",
            ],
        },
    )
    raw_path = storage.normalize_path(
        "raw/mrms/reflectivity",
        "20260628T132638Z_MRMS_ReflectivityAtLowestAltitude_00.50_20260628-132638.grib2.gz",
    )
    storage.ensure_directories(raw_path.rsplit("/", 1)[0])
    storage.write_bytes(raw_path, b"\x1f\x8b\x08\x00")

    timestamps, source = select_cache_window(
        db_session,
        storage,
        limit=2,
        real_only=False,
    )
    assert source == "bulk_ingest_report"
    assert len(timestamps) == 2
    assert timestamps[-1] == "2026-06-28T13:26:38Z"


def test_run_cache_warm_skips_cached_frames(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts1 = "2026-06-28T13:26:38Z"
    ts2 = "2026-06-28T13:27:00Z"
    save_bulk_ingest_report(
        storage,
        {"registered_timestamps": [ts1, ts2], "downloaded_timestamps": [ts1, ts2]},
    )
    cache_dir = storage.normalize_path("dev/mrms_frame_cache", "20260628T132638Z")
    preview_path = storage.normalize_path(cache_dir, "preview_z0_x0_y0.png")
    storage.ensure_directories(cache_dir)
    storage.write_bytes(preview_path, generate_placeholder_tile_png())
    save_frame_cache(
        storage,
        ts1,
        {
            "frame_status": FRAME_STATUS_MATCHED,
            "selected_timestamp": ts1,
            "preview_paths": [preview_path],
        },
    )

    calls: list[str] = []

    def _resolve(session, storage, timestamp, **kwargs):
        calls.append(timestamp)
        return {
            "frame_status": FRAME_STATUS_MATCHED,
            "selected_timestamp": timestamp,
            "cache_dir": f"dev/mrms_frame_cache/{timestamp}",
        }

    report = run_cache_warm(
        db_session,
        storage,
        limit=2,
        real_only=False,
        resolve_fn=_resolve,
    )

    assert report["frames_already_cached"] == 1
    assert report["frames_decoded"] == 1
    assert calls == [ts2]
    assert load_cache_warm_report(storage) is not None


def test_run_cache_warm_force_refresh(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts = "2026-06-28T13:26:38Z"
    save_bulk_ingest_report(storage, {"registered_timestamps": [ts], "downloaded_timestamps": [ts]})
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

    calls: list[str] = []

    def _resolve(session, storage, timestamp, **kwargs):
        calls.append(timestamp)
        return {"frame_status": FRAME_STATUS_MATCHED, "selected_timestamp": timestamp}

    report = run_cache_warm(
        db_session,
        storage,
        limit=1,
        force=True,
        real_only=False,
        resolve_fn=_resolve,
    )

    assert report["frames_already_cached"] == 0
    assert report["frames_decoded"] == 1
    assert calls == [ts]


def test_run_cache_warm_partial_failure(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts1 = "2026-06-28T13:26:38Z"
    ts2 = "2026-06-28T13:27:00Z"
    save_bulk_ingest_report(
        storage,
        {"registered_timestamps": [ts1, ts2], "downloaded_timestamps": [ts1, ts2]},
    )

    def _resolve(session, storage, timestamp, **kwargs):
        if timestamp == ts1:
            return {"frame_status": FRAME_STATUS_MATCHED, "selected_timestamp": timestamp}
        return {
            "frame_status": "decode_failed",
            "selected_timestamp": timestamp,
            "sync_message": "decode failed",
        }

    report = run_cache_warm(
        db_session,
        storage,
        limit=2,
        real_only=False,
        resolve_fn=_resolve,
    )

    assert report["warm_status"] == "partial"
    assert report["frames_decoded"] == 1
    assert report["frames_failed"] == 1
    assert report["json_path"]
    assert save_cache_warm_report(storage, report)["markdown_path"]
