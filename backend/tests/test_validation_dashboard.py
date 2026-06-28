"""Tests for validation dashboard API and benchmark reporting (Phase 20)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from backend.app.config import settings
from backend.app.models.render_job import JOB_STATUS_RUNNING
from backend.app.services.grib2_decoder import Grib2DecodeResult
from backend.app.services.grib2_inspector import Grib2InspectResult
from backend.app.services.mrms_benchmark import run_mrms_benchmark
from backend.app.services.mrms_downloader import DownloadBatchResult, DownloadResult
from backend.app.services.mrms_validation import run_mrms_validation
from backend.app.services.render_queue import enqueue_render_job, recover_stale_running_jobs
from backend.app.services.validation_dashboard import build_validation_summary
from backend.app.services.validation_report_store import (
    load_latest_benchmark_report,
    load_latest_validation_report,
    save_latest_benchmark_report,
    save_latest_validation_report,
)
from backend.app.sources.mrms import MrmsDiscoveredFile


def _discovery(product: str, *, limit=None, mode=None):
    return [
        MrmsDiscoveredFile(
            product="MRMS_ReflectivityAtLowestAltitude",
            catalog_product_id="mrms_reflectivity",
            timestamp="2026-06-25T18:00:00Z",
            file_name="MRMS.grib2.gz",
            object_key="CONUS/MRMS.grib2.gz",
            source_url="https://example.test/mrms.grib2.gz",
            source_provider="noaa-aws-stub",
            size_bytes=12345,
        )
    ][: limit or 1]


def _download_batch(session, storage, limit, mode):
    return DownloadBatchResult(
        downloaded=[
            DownloadResult(
                radar_file_id=1,
                timestamp="2026-06-25T18:00:00Z",
                raw_path="raw/mrms/reflectivity/test.grib2.gz",
                sha256="abc",
                file_size_bytes=100,
                downloaded_at="2026-06-25T18:05:00Z",
                created=True,
                stub=False,
            )
        ],
        skipped=0,
        failed=[],
    )


def _inspect_ok(storage, raw_path):
    return Grib2InspectResult(
        raw_path=raw_path,
        raw_kind="mrms_real_grib2",
        file_exists=True,
        inspectable=True,
    )


def _decode_ok(storage, raw_path):
    return Grib2DecodeResult(
        raw_path=raw_path,
        raw_kind="mrms_real_grib2",
        success=True,
        output_dir="data/staging/grib2_decode/test",
    )


def test_validation_summary_endpoint_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["prototype"] is True
    assert body["verified_mrms"] is False
    assert body["production_rendering_enabled"] is False
    assert body["placeholder_default"] is True
    assert body["validation_available"] is False
    assert body["benchmark_available"] is False
    assert body["queue_benchmark_available"] is False
    assert body["scheduled_validation_available"] is False
    assert body["validation_failures_count"] == 0
    assert "render_queue" in body
    assert "catalog" in body


def test_validation_latest_endpoint_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/latest")
    assert response.status_code == 200
    body = response.json()
    assert body["prototype"] is True
    assert body["verified_mrms"] is False
    assert body["validation"] is None
    assert body["benchmark"] is None


def test_validation_summary_with_persisted_report(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_latest_validation_report(
        storage,
        {
            "source_mode": "stub",
            "discovered_count": 1,
            "downloaded_count": 0,
            "decoded_count": 0,
            "verified_mrms": False,
            "prototype": True,
        },
    )
    save_latest_benchmark_report(
        storage,
        {
            "source_mode": "stub",
            "tiles_planned": 2,
            "tiles_written": 1,
            "tile_build_elapsed_seconds": 0.5,
            "verified_mrms": False,
            "prototype": True,
        },
    )

    response = client.get("/api/validation/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["validation_available"] is True
    assert body["benchmark_available"] is True
    assert body["validation"]["discovered_count"] == 1
    assert body["benchmark"]["tiles_written"] == 1

    summary = build_validation_summary(db_session, storage)
    assert summary["validation_available"] is True


def test_validation_persist_on_run(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    with patch(
        "backend.app.services.mrms_validation.detect_decoder_availability",
        return_value=MagicMock(any_decoder=False),
    ), patch(
        "backend.app.services.mrms_validation.find_real_mrms_inspect_candidates",
        return_value=[],
    ):
        run_mrms_validation(
            db_session,
            storage,
            source_mode="stub",
            discover_fn=_discovery,
            download_fn=_download_batch,
        )

    saved = load_latest_validation_report(storage)
    assert saved is not None
    assert saved["source_mode"] == "stub"
    assert saved["verified_mrms"] is False
    assert saved.get("validated_at")


def test_benchmark_report_shape_with_mocks(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    with patch(
        "backend.app.services.mrms_validation.detect_decoder_availability",
        return_value=MagicMock(any_decoder=True),
    ), patch(
        "backend.app.services.mrms_validation.find_real_mrms_inspect_candidates",
        return_value=[MagicMock(raw_path="raw/mrms/reflectivity/test.grib2.gz")],
    ), patch(
        "backend.app.services.mrms_benchmark.build_production_tiles",
        return_value=MagicMock(
            tiles_planned=3,
            tiles_written=2,
            tiles_skipped_existing=1,
            output_bytes=900,
            errors=[],
        ),
    ):
        report = run_mrms_benchmark(
            db_session,
            storage,
            source_mode="stub",
            discover_fn=_discovery,
            download_fn=_download_batch,
            inspect_fn=_inspect_ok,
            decode_fn=_decode_ok,
            persist=True,
        )

    body = report.to_dict()
    assert body["prototype"] is True
    assert body["verified_mrms"] is False
    assert any(item["stage"] == "validation_pipeline" for item in body["stage_timings"])
    assert body["tiles_planned"] == 3
    assert body["tiles_written"] == 2
    saved = load_latest_benchmark_report(storage)
    assert saved is not None
    assert saved["tiles_written"] == 2


def test_configurable_stale_threshold(db_session, monkeypatch):
    monkeypatch.setattr(settings, "stale_running_job_seconds", 120)

    job = enqueue_render_job(db_session, max_attempts=3)
    job.status = JOB_STATUS_RUNNING
    job.attempt_count = 1
    stale_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    job.started_at = stale_time
    db_session.commit()

    recovered = recover_stale_running_jobs(db_session)
    assert recovered == 1


def test_production_tile_serving_still_gated_phase20(client, db_session, storage, monkeypatch):
    from backend.app.models import RadarFile
    from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
    from backend.app.services.decoded_tile_cache import TILE_MODE_PLACEHOLDER

    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    timestamp = "2026-06-25T23:00:00Z"
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase20_gate.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=True,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    response = client.get(f"/tiles/mrms_reflectivity/{timestamp}/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"
    assert response.headers.get("x-radararchive-tile") in (TILE_MODE_PLACEHOLDER, "placeholder_for_real_raw")
