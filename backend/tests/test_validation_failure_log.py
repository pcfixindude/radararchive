"""Tests for validation failure log and Phase 24 diagnostics."""

from __future__ import annotations

from unittest.mock import patch

from backend.app.config import settings
from backend.app.services.mrms_batch_validation import BatchValidationReport
from backend.app.services.render_queue_benchmark import RenderQueueBenchmarkReport
from backend.app.services.scheduled_validation import (
    STEP_FAILED,
    STEP_SUCCEEDED,
    run_real_mrms_smoke_test,
    run_scheduled_validation,
)
from backend.app.services.validation_failure_log import (
    MAX_FAILURE_ENTRIES,
    append_validation_failure,
    count_validation_failures,
    load_recent_validation_failures,
)
from backend.app.services.validation_dashboard import build_validation_summary


def test_append_validation_failure_and_bounded_log(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    for index in range(MAX_FAILURE_ENTRIES + 5):
        append_validation_failure(
            storage,
            phase="scheduled_validation",
            step="batch_validation",
            source_mode="stub",
            command_context="make test",
            error_message=f"error-{index}",
        )

    assert count_validation_failures(storage) == MAX_FAILURE_ENTRIES
    recent = load_recent_validation_failures(storage, limit=3)
    assert len(recent) == 3
    assert recent[0]["error_message"] == f"error-{MAX_FAILURE_ENTRIES + 4}"


def test_scheduled_step_detail_shape(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    report = run_scheduled_validation(
        db_session,
        storage,
        count=1,
        batch_fn=lambda *_a, **_k: BatchValidationReport(source_mode="stub", warnings=["stub warning"]),
        queue_benchmark_fn=lambda *_a, **_k: RenderQueueBenchmarkReport(source_mode="stub"),
        command_context="make test",
    )

    step = report.steps[0].to_dict()
    assert step["name"] == "catalog_status"
    assert step["status"] == STEP_SUCCEEDED
    assert step["started_at"] is not None
    assert step["finished_at"] is not None
    assert "summary" in step


def test_scheduled_validation_logs_failed_step(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    def _queue(*_args, **_kwargs):
        return RenderQueueBenchmarkReport(
            source_mode="stub",
            jobs_failed=1,
            errors=["job failed"],
        )

    report = run_scheduled_validation(
        db_session,
        storage,
        count=1,
        batch_fn=lambda *_a, **_k: BatchValidationReport(source_mode="stub"),
        queue_benchmark_fn=_queue,
        command_context="make test",
    )
    assert report.exit_code == 1
    failures = load_recent_validation_failures(storage, limit=5)
    assert len(failures) >= 1


def test_validation_summary_includes_failures_and_steps(client, db_session, storage, monkeypatch):
    from backend.app.services.validation_report_store import save_scheduled_validation_report

    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    append_validation_failure(
        storage,
        phase="scheduled_validation",
        step="queue_benchmark",
        source_mode="stub",
        error_message="test failure",
    )
    save_scheduled_validation_report(
        storage,
        {
            "source_mode": "stub",
            "success": True,
            "exit_code": 0,
            "steps": [
                {
                    "name": "catalog_status",
                    "status": "succeeded",
                    "started_at": "2026-06-28T10:00:00Z",
                    "finished_at": "2026-06-28T10:00:01Z",
                    "elapsed_seconds": 1.0,
                    "summary": {"total_frames": 5},
                    "warnings": [],
                    "errors": [],
                }
            ],
            "verified_mrms": False,
            "prototype": True,
        },
    )

    response = client.get("/api/validation/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["validation_failures_count"] >= 1
    assert len(body["validation_failures_recent"]) >= 1
    assert body["scheduled_validation"]["steps"][0]["name"] == "catalog_status"

    summary = build_validation_summary(db_session, storage)
    assert summary["validation_failures_count"] >= 1


def test_validation_failures_endpoint(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    append_validation_failure(
        storage,
        phase="test",
        step="batch_validation",
        error_message="endpoint failure",
    )

    response = client.get("/api/validation/failures?limit=5")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 1
    assert body["entries"][0]["error_message"] == "endpoint failure"


def test_validation_summary_missing_failures(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/summary")
    body = response.json()
    assert body["validation_failures_count"] == 0
    assert body["validation_failures_recent"] == []


def test_real_smoke_test_safety_limits(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    with patch(
        "backend.app.services.scheduled_validation.run_scheduled_validation",
    ) as mock_run:
        from backend.app.services.scheduled_validation import ScheduledValidationReport

        mock_run.return_value = ScheduledValidationReport(source_mode="real", real_requested=True)
        run_real_mrms_smoke_test(db_session, storage, persist=False)
        mock_run.assert_called_once()
        kwargs = mock_run.call_args.kwargs
        assert kwargs["count"] == 1
        assert kwargs["min_zoom"] == 0
        assert kwargs["max_zoom"] == 0
        assert kwargs["real_requested"] is True
        assert kwargs["command_context"] == "make real-mrms-smoke-test"


def test_production_tile_serving_still_gated_phase24(client, db_session, storage, monkeypatch):
    from backend.app.models import RadarFile
    from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
    from backend.app.services.decoded_tile_cache import TILE_MODE_PLACEHOLDER

    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    timestamp = "2026-06-28T00:00:00Z"
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase24_gate.grib2.gz"),
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
