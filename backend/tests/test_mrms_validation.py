"""Tests for MRMS validation pipeline and worker hardening (Phase 19)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from backend.app.config import settings
from backend.app.models.render_job import (
    JOB_STATUS_FAILED,
    JOB_STATUS_QUEUED,
    JOB_STATUS_RUNNING,
    JOB_STATUS_SUCCEEDED,
)
from backend.app.services.grib2_decoder import Grib2DecodeResult
from backend.app.services.grib2_inspector import Grib2InspectResult
from backend.app.services.mrms_downloader import DownloadBatchResult, DownloadResult
from backend.app.services.mrms_validation import (
    MrmsValidationReport,
    resolve_validation_source_mode,
    run_mrms_validation,
)
from backend.app.services.render_queue import enqueue_render_job, recover_stale_running_jobs
from backend.app.sources.mrms import MrmsDiscoveredFile
from backend.app.workers.render_worker import run_worker_loop


def _discovery(product: str, *, limit=None, mode=None):
    return [
        MrmsDiscoveredFile(
            product="MRMS_ReflectivityAtLowestAltitude",
            catalog_product_id="mrms_reflectivity",
            timestamp="2026-06-25T18:00:00Z",
            file_name="MRMS_ReflectivityAtLowestAltitude_00.00_20260625-180000.grib2.gz",
            object_key="CONUS/MRMS_ReflectivityAtLowestAltitude_00.00_20260625-180000.grib2.gz",
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
                raw_path="raw/mrms/reflectivity/20260625T180000Z_MRMS.grib2.gz",
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
        manifest_path="data/staging/grib2_decode/test/decode_manifest.json",
    )


def test_validation_report_shape_with_mocked_steps(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    with patch(
        "backend.app.services.mrms_validation.detect_decoder_availability",
        return_value=MagicMock(any_decoder=True),
    ), patch(
        "backend.app.services.mrms_validation.find_real_mrms_inspect_candidates",
        return_value=[
            MagicMock(
                radar_file_id=1,
                timestamp="2026-06-25T18:00:00Z",
                raw_path="raw/mrms/reflectivity/test.grib2.gz",
            )
        ],
    ):
        report = run_mrms_validation(
            db_session,
            storage,
            source_mode="stub",
            discover_fn=_discovery,
            download_fn=_download_batch,
            inspect_fn=_inspect_ok,
            decode_fn=_decode_ok,
        )

    body = report.to_dict()
    assert body["source_mode"] == "stub"
    assert body["discovered_count"] == 1
    assert body["downloaded_count"] == 1
    assert body["inspected_count"] == 1
    assert body["decoded_count"] == 1
    assert body["render_jobs_enqueued"] == 1
    assert body["production_rendering_enabled"] is False
    assert body["verified_mrms"] is False
    assert body["prototype"] is True
    assert "tile_cache" in body
    assert isinstance(body["warnings"], list)


def test_validation_stub_mode_no_decoder_friendly(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    with patch(
        "backend.app.services.mrms_validation.detect_decoder_availability",
        return_value=MagicMock(any_decoder=False),
    ), patch(
        "backend.app.services.mrms_validation.find_real_mrms_inspect_candidates",
        return_value=[],
    ):
        report = run_mrms_validation(
            db_session,
            storage,
            source_mode="stub",
            discover_fn=_discovery,
            download_fn=_download_batch,
        )

    assert report.discovered_count == 1
    assert report.decoded_count == 0
    assert report.render_jobs_enqueued == 0
    assert any("stub" in w.lower() or "offline" in w.lower() for w in report.warnings)
    assert report.production_rendering_enabled is False
    assert report.verified_mrms is False


def test_validation_with_worker_mock(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    fake_job = MagicMock()
    fake_job.id = 99
    fake_job.status = JOB_STATUS_SUCCEEDED
    fake_job.tiles_written = 2
    fake_job.tiles_skipped = 0
    fake_job.output_bytes = 512

    with patch(
        "backend.app.services.mrms_validation.detect_decoder_availability",
        return_value=MagicMock(any_decoder=True),
    ), patch(
        "backend.app.services.mrms_validation.find_real_mrms_inspect_candidates",
        return_value=[MagicMock(raw_path="raw/mrms/reflectivity/test.grib2.gz")],
    ):
        report = run_mrms_validation(
            db_session,
            storage,
            source_mode="stub",
            discover_fn=_discovery,
            download_fn=_download_batch,
            inspect_fn=_inspect_ok,
            decode_fn=_decode_ok,
            run_worker=True,
            worker_fn=lambda _s, _st: fake_job,
        )

    assert report.worker_jobs_processed == 1
    assert report.tile_cache.tiles_written == 2
    assert report.tile_cache.job_status == JOB_STATUS_SUCCEEDED


def test_resolve_validation_source_mode_defaults_stub(monkeypatch):
    monkeypatch.setattr(settings, "mrms_source_mode", "stub")
    assert resolve_validation_source_mode(real_requested=False) == "stub"


def test_resolve_validation_source_mode_real_flag(monkeypatch):
    monkeypatch.setattr(settings, "mrms_source_mode", "stub")
    assert resolve_validation_source_mode(real_requested=True) == "real"


def test_stale_running_job_recovery_requeues(db_session):
    job = enqueue_render_job(db_session, max_attempts=3)
    job.status = JOB_STATUS_RUNNING
    job.attempt_count = 1
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    job.started_at = stale_time
    db_session.commit()

    recovered = recover_stale_running_jobs(db_session, stale_seconds=3600)
    db_session.refresh(job)

    assert recovered == 1
    assert job.status == JOB_STATUS_QUEUED
    assert "stale running" in (job.error_message or "").lower()


def test_stale_running_job_recovery_fails_when_exhausted(db_session):
    job = enqueue_render_job(db_session, max_attempts=2)
    job.status = JOB_STATUS_RUNNING
    job.attempt_count = 2
    stale_time = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    job.started_at = stale_time
    db_session.commit()

    recovered = recover_stale_running_jobs(db_session, stale_seconds=3600)
    db_session.refresh(job)

    assert recovered == 1
    assert job.status == JOB_STATUS_FAILED


def test_stale_running_job_ignores_recent(db_session):
    job = enqueue_render_job(db_session)
    job.status = JOB_STATUS_RUNNING
    job.attempt_count = 1
    job.started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    db_session.commit()

    recovered = recover_stale_running_jobs(db_session, stale_seconds=3600)
    db_session.refresh(job)

    assert recovered == 0
    assert job.status == JOB_STATUS_RUNNING


def test_worker_loop_stops_when_requested(db_session, storage):
    enqueue_render_job(db_session)
    processed = run_worker_loop(
        db_session,
        storage,
        max_jobs=10,
        sleep_seconds=0,
        should_stop=lambda: True,
    )
    assert processed == 0


def test_validation_does_not_enable_production_rendering(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    with patch(
        "backend.app.services.mrms_validation.detect_decoder_availability",
        return_value=MagicMock(any_decoder=True),
    ), patch(
        "backend.app.services.mrms_validation.find_real_mrms_inspect_candidates",
        return_value=[MagicMock(raw_path="raw/mrms/reflectivity/test.grib2.gz")],
    ):
        report = run_mrms_validation(
            db_session,
            storage,
            source_mode="stub",
            discover_fn=_discovery,
            download_fn=_download_batch,
            inspect_fn=_inspect_ok,
            decode_fn=_decode_ok,
        )

    assert settings.enable_production_radar_tiles is False
    assert report.production_rendering_enabled is False


def test_production_tile_serving_still_gated_after_validation(client, db_session, storage, monkeypatch):
    from backend.app.models import RadarFile
    from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
    from backend.app.services.decoded_tile_cache import TILE_MODE_PLACEHOLDER

    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    timestamp = "2026-06-25T22:00:00Z"
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "validate_gate.grib2.gz"),
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
