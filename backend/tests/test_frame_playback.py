"""Tests for frame playback prefetch (Phase 109)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.demo.seed import seed_demo_catalog
from backend.app.services.frame_playback import prefetch_frames
from backend.app.services.selected_frame_decode import FRAME_STATUS_MATCHED, save_frame_cache
from backend.app.services.tile_service import generate_placeholder_tile_png


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)


def test_prefetch_frames_uses_cache(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    timestamp = "2026-06-28T13:26:38Z"
    cache_dir = storage.normalize_path("dev/mrms_frame_cache", "20260628T132638Z")
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
            "sync_message": "cached",
        },
    )
    result = prefetch_frames(db_session, storage, [timestamp, "2026-06-27T20:00:00Z"])
    assert result["prefetched"] == 2
    assert result["matched"] == 1
    assert result["frames"][0]["cached"] is True
    assert result["frames"][0]["frame_status"] == FRAME_STATUS_MATCHED


def test_prefetch_api(client, storage, db_session, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    seed_demo_catalog(db_session, storage=storage)
    response = client.get(
        "/api/dev/decoded-overlay/prefetch"
        "?timestamps=2026-06-27T20:00:00Z,2026-06-27T20:05:00Z"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["prefetched"] == 2
    assert body["verified_mrms"] is False
