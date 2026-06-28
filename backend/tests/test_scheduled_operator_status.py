"""Tests for scheduled operator review status tie-in (Phase 50)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_batch_validation import BatchValidationReport
from backend.app.services.mrms_review_session import create_review_session_record
from backend.app.services.operator_review_status import compact_scheduled_operator_status
from backend.app.services.render_queue_benchmark import RenderQueueBenchmarkReport
from backend.app.services.scheduled_validation import run_scheduled_validation
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _mock_runners():
    return (
        lambda *_a, **_k: BatchValidationReport(source_mode="stub", effective_frame_count=1),
        lambda *_a, **_k: RenderQueueBenchmarkReport(source_mode="stub", jobs_succeeded=1),
    )


def test_default_scheduled_validation_unchanged(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    report = run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        persist=False,
    )
    body = report.to_dict()
    assert body["operator_status_requested"] is False
    assert body["operator_status_generated"] is False
    step_names = [step.name for step in report.steps]
    assert "operator_review_status" not in step_names


def test_scheduled_validation_includes_operator_status_when_requested(
    db_session, storage, monkeypatch
):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    report = run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        operator_status_requested=True,
        persist=False,
    )
    body = report.to_dict()
    assert body["operator_status_requested"] is True
    assert body["operator_status_generated"] is True
    assert body["operator_status_level"] in (
        "ok",
        "watch",
        "attention",
        "urgent",
        "unknown",
    )
    assert body["verified_mrms"] is False
    step_names = [step.name for step in report.steps]
    assert "operator_review_status" in step_names


def test_review_export_auto_includes_operator_status(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="auto status",
        accepted_limitations=True,
    )
    report = run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        review_export_requested=True,
        persist=False,
    )
    body = report.to_dict()
    assert body["operator_status_requested"] is True
    assert body["operator_status_generated"] is True
    assert "operator_review_status" in [step.name for step in report.steps]


def test_scheduled_operator_status_failure_does_not_fail_run(
    db_session, storage, monkeypatch
):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()

    def _boom(_storage):
        raise RuntimeError("operator status build failed")

    monkeypatch.setattr(
        "backend.app.services.operator_review_status.compact_operator_review_status",
        _boom,
    )
    report = run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        operator_status_requested=True,
        persist=False,
    )
    body = report.to_dict()
    assert body["operator_status_generated"] is False
    assert body["operator_status_error"]
    assert body["operator_status_reason"] == "generation_failed"
    assert report.success is True


def test_summary_includes_scheduled_operator_status(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        operator_status_requested=True,
        persist=True,
    )
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("scheduled_operator_status")
    assert compact is not None
    assert compact["operator_status_requested"] is True
    assert compact["verified_mrms"] is False


def test_compact_scheduled_operator_status_from_report():
    scheduled = {
        "operator_status_requested": True,
        "operator_status_generated": True,
        "operator_status_level": "watch",
        "operator_status_reason": "export_diff_trend_monitoring",
        "operator_status_top_suggested_command": "make operator-review-status",
        "operator_status_evidence_trend": "stable",
        "operator_status_elapsed_seconds": 0.01,
    }
    compact = compact_scheduled_operator_status(scheduled)
    assert compact is not None
    assert compact["operator_status_level"] == "watch"
    assert compact["verified_mrms"] is False


def test_operator_status_does_not_clear_alerts(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    from backend.app.services.validation_alerts import save_validation_alert

    save_validation_alert(
        storage,
        {
            "status": "failed",
            "updated_at": "2026-06-28T16:00:00Z",
            "latest_run_at": "2026-06-28T16:00:00Z",
            "failure_count": 1,
            "warning_count": 0,
            "operator_attention_needed": True,
            "verified_mrms": False,
        },
    )
    before = load_validation_alert(storage)
    run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        operator_status_requested=True,
        persist=False,
    )
    after = load_validation_alert(storage)
    assert after.get("status") == before.get("status")


def test_operator_status_does_not_mutate_production_gates(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    batch_fn, queue_fn = _mock_runners()
    radar = RadarFile(
        product_id="mrms",
        timestamp="2026-06-28T12:00:00Z",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
    )
    db_session.add(radar)
    db_session.commit()
    run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        operator_status_requested=True,
        persist=False,
    )
    assert settings.enable_production_radar_tiles is False
    summary = build_validation_summary(db_session, storage)
    assert summary["verified_mrms"] is False


def test_production_tile_serving_still_gated_phase50(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    radar = RadarFile(
        product_id="mrms",
        timestamp="2026-06-28T12:00:00Z",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
    )
    db_session.add(radar)
    db_session.commit()
    response = client.get("/api/tiles/mrms/2026-06-28T12:00:00Z/0/0/0.png")
    assert response.status_code in (404, 503)
