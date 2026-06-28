"""Tests for scheduled review session export step (Phase 44)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_batch_validation import BatchValidationReport
from backend.app.services.mrms_review_session import create_review_session_record
from backend.app.services.mrms_review_session_export import (
    EXPORT_JSON_PATH,
    EXPORT_MD_PATH,
    compact_scheduled_review_export,
)
from backend.app.services.render_queue_benchmark import RenderQueueBenchmarkReport
from backend.app.services.scheduled_validation import run_scheduled_validation
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _mock_runners():
    return (
        lambda *_a, **_k: BatchValidationReport(source_mode="stub", effective_frame_count=1),
        lambda *_a, **_k: RenderQueueBenchmarkReport(source_mode="stub", jobs_succeeded=1),
    )


def test_scheduled_review_export_report_shape_when_not_requested(db_session, storage, monkeypatch):
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
    assert body["review_export_requested"] is False
    assert body["review_export_generated"] is False
    assert body["verified_mrms"] is False
    step_names = [step.name for step in report.steps]
    assert "review_session_export" not in step_names


def test_review_export_step_runs_only_when_requested(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="scheduled export test",
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
    step_names = [step.name for step in report.steps]
    assert "review_session_export" in step_names
    assert report.review_export_requested is True


def test_skipped_no_review_session_behavior(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    report = run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        review_export_requested=True,
        persist=False,
    )
    body = report.to_dict()
    assert body["review_export_requested"] is True
    assert body["review_export_generated"] is False
    assert body["review_export_reason"] == "skipped_no_review_session"
    assert report.success is True
    export_step = next(step for step in report.steps if step.name == "review_session_export")
    assert export_step.status == "skipped"


def test_scheduled_review_export_succeeds_when_session_exists(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="export exists",
        accepted_limitations=True,
    )
    report = run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        proof_requested=True,
        bundle_requested=True,
        diff_bundle_requested=True,
        handoff_requested=True,
        digest_requested=True,
        review_export_requested=True,
        persist=False,
    )
    body = report.to_dict()
    assert body["review_export_requested"] is True
    assert body["review_export_generated"] is True
    assert body["review_export_reason"] == "generated"
    assert body["review_export_path"]
    assert body["review_export_metadata_path"]
    assert body["verified_mrms"] is False
    assert storage.absolute_path(EXPORT_MD_PATH).is_file()
    assert storage.absolute_path(EXPORT_JSON_PATH).is_file()


def test_scheduled_review_export_does_not_clear_alerts(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    from backend.app.services.mrms_proof_bundle_diff import DIFF_WORSENED
    from backend.app.services.proof_bundle_diff_alert_history import (
        record_proof_bundle_diff_alert_history,
    )

    record_proof_bundle_diff_alert_history(
        storage,
        {
            "overall_diff_status": DIFF_WORSENED,
            "checked_at": "2026-06-28T16:12:00Z",
            "evidence_changes_count": 1,
            "current_bundle": {"bundle_id": "b1"},
            "baseline_bundle": {"bundle_id": "base"},
            "verified_mrms": False,
            "operator_attention_needed": True,
        },
        skip_duplicate=False,
    )
    create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="alert test",
        accepted_limitations=True,
    )
    alert_before = load_validation_alert(storage)
    batch_fn, queue_fn = _mock_runners()
    run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        review_export_requested=True,
        persist=False,
    )
    alert_after = load_validation_alert(storage)
    if alert_before is not None:
        assert alert_after is not None
        assert alert_after.get("operator_attention_needed") == alert_before.get(
            "operator_attention_needed"
        )


def test_scheduled_review_export_does_not_mutate_production_gates(
    client, db_session, storage, monkeypatch
):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T11:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase44.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=False,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()
    create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="gate test",
        accepted_limitations=True,
    )
    batch_fn, queue_fn = _mock_runners()
    run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        review_export_requested=True,
        persist=False,
    )
    db_session.refresh(frame)
    assert frame.production_rendering is False

    response = client.get("/tiles/mrms_reflectivity/2026-06-28T11:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"


def test_scheduled_review_export_always_verified_mrms_false(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="verified false",
        accepted_limitations=True,
    )
    batch_fn, queue_fn = _mock_runners()
    report = run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        review_export_requested=True,
        persist=False,
    )
    assert report.verified_mrms is False
    assert report.to_dict()["verified_mrms"] is False


def test_summary_includes_scheduled_review_export(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="summary test",
        accepted_limitations=True,
    )
    batch_fn, queue_fn = _mock_runners()
    run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        review_export_requested=True,
        persist=True,
    )
    summary = build_validation_summary(db_session, storage)
    scheduled_export = summary.get("scheduled_review_export")
    export_compact = summary.get("mrms_review_session_export")
    hint = summary.get("review_export_regeneration_hint")
    assert scheduled_export is not None
    assert scheduled_export["review_export_requested"] is True
    assert scheduled_export["review_export_generated"] is True
    assert scheduled_export["local_export_only"] is True
    assert export_compact is not None
    assert export_compact["available"] is True
    assert hint is not None
    assert hint["verified_mrms"] is False


def test_compact_scheduled_review_export_from_report():
    scheduled = {
        "review_export_requested": True,
        "review_export_generated": False,
        "review_export_reason": "skipped_no_review_session",
    }
    compact = compact_scheduled_review_export(scheduled)
    assert compact is not None
    assert compact["review_export_requested"] is True
    assert compact["review_export_reason"] == "skipped_no_review_session"
    assert compact["verified_mrms"] is False


def test_runtime_export_artifacts_gitignored():
    gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
    text = gitignore.read_text(encoding="utf-8")
    assert "mrms_review_session_export_latest.md" in text
