"""Tests for multi-zoom render queue benchmark (Phase 22)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.models.render_job import JOB_STATUS_SUCCEEDED
from backend.app.services.render_queue_benchmark import (
    DEFAULT_MAX_ZOOM,
    DEFAULT_MIN_ZOOM,
    DEFAULT_QUEUE_BENCHMARK_COUNT,
    MAX_QUEUE_BENCHMARK_COUNT,
    resolve_benchmark_count,
    resolve_benchmark_zoom,
    run_render_queue_benchmark,
)
from backend.app.services.validation_dashboard import build_validation_summary
from backend.app.services.validation_report_store import (
    load_latest_queue_benchmark_report,
    load_queue_benchmark_history,
)


def test_resolve_benchmark_count_defaults_and_cap():
    count, warnings = resolve_benchmark_count(0)
    assert count == DEFAULT_QUEUE_BENCHMARK_COUNT
    assert warnings

    count, warnings = resolve_benchmark_count(99)
    assert count == MAX_QUEUE_BENCHMARK_COUNT
    assert any("capping" in item for item in warnings)

    count, warnings = resolve_benchmark_count(5)
    assert count == 5
    assert not warnings


def test_resolve_benchmark_zoom_clamps():
    lo, hi, warnings = resolve_benchmark_zoom(0, 99)
    assert lo == 0
    assert hi <= 4
    assert warnings


def test_queue_benchmark_report_shape_dry_run(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    report = run_render_queue_benchmark(
        db_session,
        storage,
        count=2,
        min_zoom=DEFAULT_MIN_ZOOM,
        max_zoom=DEFAULT_MAX_ZOOM,
        dry_run=True,
        source_mode="stub",
    )

    body = report.to_dict()
    assert body["prototype"] is True
    assert body["verified_mrms"] is False
    assert body["dry_run"] is True
    assert body["jobs_enqueued"] == 0
    assert body["jobs_processed"] == 0
    assert len(body["job_summaries"]) >= 1
    assert body["job_summaries"][0]["status"] == "dry_run"
    assert body["min_zoom"] == DEFAULT_MIN_ZOOM
    assert body["max_zoom"] == DEFAULT_MAX_ZOOM


def test_queue_benchmark_persists_latest_and_history(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    run_render_queue_benchmark(
        db_session,
        storage,
        count=1,
        dry_run=True,
        source_mode="stub",
        persist=True,
    )

    latest = load_latest_queue_benchmark_report(storage)
    assert latest is not None
    assert latest["dry_run"] is True
    assert latest["verified_mrms"] is False

    history = load_queue_benchmark_history(storage)
    assert len(history) == 1
    assert history[0]["jobs_enqueued"] == 0


def test_queue_benchmark_with_mock_worker(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    def _fake_worker(session, storage, job):
        job.status = JOB_STATUS_SUCCEEDED
        job.tiles_written = 2
        job.tiles_skipped = 1
        job.output_bytes = 500
        job.progress_total = 3
        session.commit()
        return job

    report = run_render_queue_benchmark(
        db_session,
        storage,
        count=2,
        min_zoom=0,
        max_zoom=1,
        dry_run=False,
        source_mode="stub",
        worker_fn=_fake_worker,
    )

    assert report.jobs_enqueued == 2
    assert report.jobs_processed == 2
    assert report.jobs_succeeded == 2
    assert report.total_tiles_written == 4
    assert report.total_tiles_skipped == 2
    assert report.total_output_bytes == 1000
    assert len(report.job_summaries) == 2
    assert report.job_summaries[0].tiles_written == 2


def test_validation_summary_includes_queue_benchmark(client, db_session, storage, monkeypatch):
    from backend.app.services.validation_report_store import save_queue_benchmark_report

    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_queue_benchmark_report(
        storage,
        {
            "source_mode": "stub",
            "effective_count": 2,
            "min_zoom": 0,
            "max_zoom": 1,
            "jobs_enqueued": 2,
            "jobs_processed": 2,
            "jobs_succeeded": 2,
            "total_tiles_written": 4,
            "job_summaries": [
                {
                    "timestamp": "2026-06-25T18:00:00Z",
                    "job_id": 1,
                    "status": "succeeded",
                    "tiles_written": 2,
                }
            ],
            "verified_mrms": False,
            "prototype": True,
        },
    )

    response = client.get("/api/validation/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["queue_benchmark_available"] is True
    assert body["queue_benchmark"]["jobs_succeeded"] == 2
    assert body["queue_benchmark"]["job_summaries"][0]["job_id"] == 1
    assert "validation_history" in body

    summary = build_validation_summary(db_session, storage)
    assert summary["queue_benchmark_available"] is True


def test_validation_summary_missing_queue_benchmark(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["queue_benchmark_available"] is False
    assert body["queue_benchmark"] is None


def test_validation_benchmarks_endpoint(client, storage, monkeypatch):
    from backend.app.services.validation_report_store import save_queue_benchmark_report

    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_queue_benchmark_report(
        storage,
        {"source_mode": "stub", "jobs_enqueued": 1, "verified_mrms": False, "prototype": True},
    )

    response = client.get("/api/validation/benchmarks")
    assert response.status_code == 200
    body = response.json()
    assert body["prototype"] is True
    assert body["verified_mrms"] is False
    assert body["latest"] is not None
    assert body["count"] >= 1


def test_production_tile_serving_still_gated_phase22(client, db_session, storage, monkeypatch):
    from backend.app.models import RadarFile
    from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
    from backend.app.services.decoded_tile_cache import TILE_MODE_PLACEHOLDER

    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    timestamp = "2026-06-25T23:30:00Z"
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase22_gate.grib2.gz"),
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
