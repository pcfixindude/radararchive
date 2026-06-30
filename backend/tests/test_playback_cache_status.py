"""Tests for playback cache status (Phase 112)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.frame_cache_warmer import save_cache_warm_report
from backend.app.services.playback_cache_status import (
    CACHE_STATE_COLD,
    CACHE_STATE_FAILED,
    CACHE_STATE_MISSING_RAW,
    CACHE_STATE_READY,
    CACHE_STATE_STUB,
    build_playback_cache_status,
    resolve_frame_cache_state,
)
from backend.app.services.selected_frame_decode import (
    FRAME_STATUS_MATCHED,
    save_frame_cache,
)
from backend.app.services.tile_service import generate_placeholder_tile_png


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)


def test_resolve_frame_cache_state_ready(storage, db_session, monkeypatch):
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
    assert resolve_frame_cache_state(db_session, storage, ts) == CACHE_STATE_READY


def test_build_playback_cache_status_counts(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts_ready = "2026-06-28T13:26:38Z"
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
    save_cache_warm_report(
        storage,
        {
            "warm_status": "partial",
            "ran_at": "2026-06-28T15:00:00Z",
            "frames_matched": 1,
            "failed_frames": [{"timestamp": "2026-06-27T20:00:00Z", "message": "fail"}],
        },
    )

    status = build_playback_cache_status(
        db_session,
        storage,
        [ts_ready, "2026-06-27T20:00:00Z", "2099-01-01T00:00:00Z"],
    )

    assert status["warmed_count"] == 1
    assert status["failed_count"] >= 1
    assert status["missing_count"] >= 1
    assert status["cache_warm_ran_at"] == "2026-06-28T15:00:00Z"
    assert len(status["frames"]) == 3


def test_cache_status_api(client, storage, db_session, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get(
        "/api/dev/decoded-overlay/cache-status"
        "?timestamps=2026-06-27T20:00:00Z,2026-06-27T20:05:00Z"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["frame_count"] == 2
    assert body["verified_mrms"] is False
    assert all("cache_state" in frame for frame in body["frames"])
