"""Tests for scheduled local validation (Phase 23)."""

from __future__ import annotations

from backend.app.config import MRMS_SOURCE_MODE_REAL, MRMS_SOURCE_MODE_STUB, settings
from backend.app.services.mrms_batch_validation import BatchValidationReport, FrameValidationSummary
from backend.app.services.render_queue_benchmark import RenderQueueBenchmarkReport
from backend.app.services.scheduled_validation import (
    DEFAULT_SCHEDULED_MAX_ZOOM,
    DEFAULT_SCHEDULED_MIN_ZOOM,
    resolve_scheduled_source_mode,
    run_scheduled_validation,
)
from backend.app.services.validation_dashboard import build_validation_summary
from backend.app.services.validation_report_store import (
    load_latest_scheduled_validation_report,
    load_scheduled_validation_history,
)


def test_resolve_scheduled_source_mode_defaults_stub(monkeypatch):
    monkeypatch.setattr(settings, "mrms_source_mode", MRMS_SOURCE_MODE_STUB)
    assert resolve_scheduled_source_mode(real_requested=False) == MRMS_SOURCE_MODE_STUB


def test_resolve_scheduled_source_mode_requires_explicit_real(monkeypatch):
    monkeypatch.setattr(settings, "mrms_source_mode", MRMS_SOURCE_MODE_STUB)
    assert resolve_scheduled_source_mode(real_requested=True) == MRMS_SOURCE_MODE_REAL


def test_scheduled_validation_report_shape_with_mocks(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    def _batch(*_args, **_kwargs):
        return BatchValidationReport(
            source_mode="stub",
            effective_frame_count=2,
            discovered_count=2,
            frame_summaries=[
                FrameValidationSummary(
                    timestamp="2026-06-25T18:00:00Z",
                    radar_file_id=1,
                    decode_status="downloaded",
                    tiles_planned=0,
                )
            ],
        )

    def _queue(*_args, **_kwargs):
        return RenderQueueBenchmarkReport(
            source_mode="stub",
            jobs_enqueued=2,
            jobs_processed=2,
            jobs_succeeded=2,
        )

    report = run_scheduled_validation(
        db_session,
        storage,
        count=2,
        min_zoom=DEFAULT_SCHEDULED_MIN_ZOOM,
        max_zoom=DEFAULT_SCHEDULED_MAX_ZOOM,
        real_requested=False,
        batch_fn=_batch,
        queue_benchmark_fn=_queue,
    )

    body = report.to_dict()
    assert body["prototype"] is True
    assert body["verified_mrms"] is False
    assert body["requested_count"] == 2
    assert body["min_zoom"] == DEFAULT_SCHEDULED_MIN_ZOOM
    assert body["max_zoom"] == DEFAULT_SCHEDULED_MAX_ZOOM
    assert len(body["steps"]) == 5
    assert body["steps"][0]["name"] == "catalog_status"
    assert body["batch_validation"] is not None
    assert body["queue_benchmark"] is not None
    assert body["render_queue"] is not None
    assert body["validation_summary"] is not None
    assert report.exit_code == 0
    assert report.success is True


def test_scheduled_validation_persists_latest_and_history(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    run_scheduled_validation(
        db_session,
        storage,
        count=1,
        batch_fn=lambda *_a, **_k: BatchValidationReport(source_mode="stub"),
        queue_benchmark_fn=lambda *_a, **_k: RenderQueueBenchmarkReport(source_mode="stub"),
    )

    latest = load_latest_scheduled_validation_report(storage)
    assert latest is not None
    assert latest["verified_mrms"] is False
    history = load_scheduled_validation_history(storage)
    assert len(history) == 1


def test_per_frame_tile_metrics_shape():
    frame = FrameValidationSummary(
        timestamp="2026-06-25T18:00:00Z",
        radar_file_id=42,
        decode_status="decoded",
        render_job_id=7,
        min_zoom=0,
        max_zoom=1,
        tiles_planned=3,
        tiles_written=2,
        tiles_skipped=1,
        output_bytes=400,
        elapsed_seconds=0.5,
    )
    body = frame.to_dict()
    assert body["radar_file_id"] == 42
    assert body["decode_status"] == "decoded"
    assert body["render_job_id"] == 7
    assert body["tiles_planned"] == 3
    assert body["tiles_written"] == 2


def test_validation_summary_includes_scheduled_validation(client, db_session, storage, monkeypatch):
    from backend.app.services.validation_report_store import save_scheduled_validation_report

    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_scheduled_validation_report(
        storage,
        {
            "source_mode": "stub",
            "success": True,
            "exit_code": 0,
            "effective_count": 3,
            "min_zoom": 0,
            "max_zoom": 1,
            "steps": [{"name": "catalog_status", "status": "ok"}],
            "batch_validation": {"decoded_count": 0},
            "queue_benchmark": {"jobs_succeeded": 3, "jobs_failed": 0},
            "verified_mrms": False,
            "prototype": True,
        },
    )

    response = client.get("/api/validation/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["scheduled_validation_available"] is True
    assert body["scheduled_validation"]["success"] is True
    assert body["scheduled_validation"]["queue_jobs_succeeded"] == 3
    assert "frame_summaries" in body

    summary = build_validation_summary(db_session, storage)
    assert summary["scheduled_validation_available"] is True


def test_validation_summary_missing_scheduled_report(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["scheduled_validation_available"] is False
    assert body["scheduled_validation"] is None
    assert body["frame_summaries"] == []


def test_validation_scheduled_endpoint(client, storage, monkeypatch):
    from backend.app.services.validation_report_store import save_scheduled_validation_report

    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_scheduled_validation_report(
        storage,
        {"source_mode": "stub", "success": True, "exit_code": 0, "verified_mrms": False, "prototype": True},
    )

    response = client.get("/api/validation/scheduled")
    assert response.status_code == 200
    body = response.json()
    assert body["latest"] is not None
    assert body["count"] >= 1


def test_scheduled_validation_exit_code_on_queue_failure(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    report = run_scheduled_validation(
        db_session,
        storage,
        batch_fn=lambda *_a, **_k: BatchValidationReport(source_mode="stub"),
        queue_benchmark_fn=lambda *_a, **_k: RenderQueueBenchmarkReport(
            source_mode="stub",
            jobs_failed=1,
            errors=["job failed"],
        ),
    )
    assert report.exit_code == 1
    assert report.success is False


def test_production_tile_serving_still_gated_phase23(client, db_session, storage, monkeypatch):
    from backend.app.models import RadarFile
    from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
    from backend.app.services.decoded_tile_cache import TILE_MODE_PLACEHOLDER

    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    timestamp = "2026-06-25T23:45:00Z"
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase23_gate.grib2.gz"),
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
