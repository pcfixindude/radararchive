"""Tests for one-shot local replay setup (Phase 121)."""

from __future__ import annotations

import json
import subprocess
import sys

from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import app
from backend.app.services.decode_retry import RETRY_JSON
from backend.app.services.frame_cache_warmer import save_cache_warm_report
from backend.app.services.local_replay_ready import (
    STEP_FRAME_CACHE,
    STEP_LOCAL_FRAMES,
    build_local_replay_ready_plan,
    run_local_replay_ready,
)
from backend.app.services.raw_file_classifier import RAW_KIND_MRMS_REAL_GRIB2
from backend.app.services.selected_frame_decode import FRAME_STATUS_MATCHED, save_frame_cache
from backend.app.services.tile_service import generate_placeholder_tile_png
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)


def _register_real_frame(db_session, storage, ts: str):
    from backend.app.models import Layer, Product, RadarFile

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
        source=MRMS_CATALOG_SOURCE,
        raw_path=raw_path,
        raw_kind=RAW_KIND_MRMS_REAL_GRIB2,
        download_status="downloaded",
    )
    db_session.add(row)
    db_session.commit()


def _write_decode_report(storage, payload: dict):
    storage.write_text(storage.normalize_path(RETRY_JSON), json.dumps(payload))


def test_no_local_frames_plan(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    plan = build_local_replay_ready_plan(db_session, storage)
    assert plan["ready"] is False
    assert plan["frame_count"] == 0
    assert plan["checklist"][0]["id"] == STEP_LOCAL_FRAMES
    assert "mrms-ingest-window" in (plan["next_command"] or "")


def test_frames_found_cache_missing(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts)
    plan = build_local_replay_ready_plan(db_session, storage, limit=8)
    assert plan["frame_count"] == 1
    assert plan["ready"] is False
    cache_step = next(item for item in plan["checklist"] if item["id"] == STEP_FRAME_CACHE)
    assert cache_step["status"] in {"missing", "warning"}


def test_ready_state_with_cache_and_decode(db_session, storage, monkeypatch):
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
    save_cache_warm_report(
        storage,
        {
            "warm_status": "ok",
            "ran_at": "2026-06-28T15:00:00Z",
            "frames_matched": 1,
            "frames_considered": 1,
            "decoded_timestamps": [ts],
        },
    )
    _write_decode_report(
        storage,
        {
            "decode_retry_status": "preview_ok",
            "produced_decoded_preview": True,
            "ran_at": "2026-06-28T15:00:00Z",
        },
    )
    plan = build_local_replay_ready_plan(db_session, storage, limit=8)
    assert plan["ready"] is True
    assert plan["next_command"] == "make backend && make frontend"


def test_dry_run_does_not_execute_warm(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts)

    called = {"warm": 0, "decode": 0}

    def _fake_warm(*args, **kwargs):
        called["warm"] += 1
        return {"warm_status": "ok", "frames_matched": 1}

    def _fake_decode(*args, **kwargs):
        called["decode"] += 1
        return {"decode_retry_status": "preview_ok", "produced_decoded_preview": True}

    monkeypatch.setattr("backend.app.services.local_replay_ready.run_cache_warm", _fake_warm)
    monkeypatch.setattr("backend.app.services.local_replay_ready.run_decode_retry", _fake_decode)

    plan = build_local_replay_ready_plan(db_session, storage, limit=8)
    assert called["warm"] == 0
    assert called["decode"] == 0
    assert plan["dry_run"] is True


def test_run_mode_executes_bounded_local_steps(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts)

    calls: list[str] = []

    def _fake_warm(*args, **kwargs):
        calls.append("warm")
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
        save_cache_warm_report(
            storage,
            {
                "warm_status": "ok",
                "ran_at": "2026-06-28T15:00:00Z",
                "frames_matched": 1,
                "frames_considered": 1,
                "decoded_timestamps": [ts],
            },
        )
        return {"warm_status": "ok", "frames_matched": 1, "frames_decoded": 1}

    def _fake_decode(*args, **kwargs):
        calls.append("decode")
        _write_decode_report(
            storage,
            {
                "decode_retry_status": "preview_ok",
                "produced_decoded_preview": True,
                "ran_at": "2026-06-28T15:00:00Z",
            },
        )
        return {"decode_retry_status": "preview_ok", "produced_decoded_preview": True}

    monkeypatch.setattr("backend.app.services.local_replay_ready.run_cache_warm", _fake_warm)
    monkeypatch.setattr("backend.app.services.local_replay_ready.run_decode_retry", _fake_decode)

    report = run_local_replay_ready(db_session, storage, limit=8, run=True)
    assert "warm" in calls
    assert report["dry_run"] is False
    assert report["ready"] is True


def test_local_replay_ready_api():
    client = TestClient(app)
    response = client.get("/api/dev/local-replay-ready", params={"limit": 8})
    assert response.status_code == 200
    payload = response.json()
    assert "checklist" in payload
    assert payload["does_not_run_real_ingest"] is True
    assert payload["verified_mrms"] is False


def test_cli_dry_run_by_default():
    result = subprocess.run(
        [sys.executable, "scripts/local_replay_ready.py", "--json"],
        capture_output=True,
        text=True,
        cwd=".",
        env={**dict(__import__("os").environ), "PYTHONPATH": "."},
    )
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True
    assert payload["does_not_run_real_ingest"] is True
    if payload["frame_count"] == 0:
        assert result.returncode == 2
