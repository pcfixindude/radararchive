"""Tests for scheduled MRMS visual review step (Phase 59)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_batch_validation import BatchValidationReport
from backend.app.services.mrms_visual_review import (
    VISUAL_REVIEW_LATEST_JSON,
    VISUAL_REVIEW_LATEST_MD,
    compact_scheduled_visual_review,
)
from backend.app.services.operator_workflow_presets import (
    EXPECTED_PRESET_IDS,
    PRESET_FULL_SCHEDULED_PROOF_REVIEW_WITH_VISUAL_REVIEW,
    PRESET_REGENERATE_VISUAL_REVIEW,
    build_operator_workflow_presets,
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


def test_scheduled_visual_review_report_shape_when_not_requested(db_session, storage, monkeypatch):
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
    assert body["visual_review_requested"] is False
    assert body["visual_review_generated"] is False
    assert body["verified_mrms"] is False
    step_names = [step.name for step in report.steps]
    assert "mrms_visual_review" not in step_names


def test_visual_review_step_runs_only_when_requested(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    report = run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        visual_review_requested=True,
        persist=False,
    )
    step_names = [step.name for step in report.steps]
    assert "mrms_visual_review" in step_names
    assert report.visual_review_requested is True


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
    assert report.visual_review_requested is False
    assert report.operator_status_requested is False
    assert report.review_export_requested is False


def test_scheduled_visual_review_succeeds_when_requested(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
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
        operator_status_requested=True,
        visual_review_requested=True,
        persist=False,
    )
    body = report.to_dict()
    assert body["visual_review_requested"] is True
    assert body["visual_review_generated"] is True
    assert body["visual_review_reason"] == "generated"
    assert body["visual_review_path"]
    assert body["visual_review_markdown_path"]
    assert body["verified_mrms"] is False
    assert storage.absolute_path(VISUAL_REVIEW_LATEST_JSON).is_file()
    assert storage.absolute_path(VISUAL_REVIEW_LATEST_MD).is_file()
    assert report.success is True


def test_visual_review_failure_does_not_fail_scheduled_run(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()

    def _boom(*_args, **_kwargs):
        raise RuntimeError("visual review boom")

    monkeypatch.setattr(
        "backend.app.services.mrms_visual_review.generate_mrms_visual_review",
        _boom,
    )
    report = run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        visual_review_requested=True,
        persist=False,
    )
    body = report.to_dict()
    assert body["visual_review_generated"] is False
    assert body["visual_review_reason"] == "generation_failed"
    assert "visual review boom" in (body["visual_review_error"] or "")
    assert report.success is True
    visual_step = next(step for step in report.steps if step.name == "mrms_visual_review")
    assert visual_step.status in ("warning", "succeeded")


def test_summary_includes_scheduled_visual_review(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        visual_review_requested=True,
        persist=True,
    )
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("scheduled_visual_review")
    assert compact is not None
    assert compact["visual_review_requested"] is True
    assert compact["verified_mrms"] is False
    assert compact["local_visual_review_only"] is True


def test_operator_review_status_includes_scheduled_visual_review(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    from backend.app.services.operator_review_status import compact_operator_review_status

    status = compact_operator_review_status(storage)
    assert "scheduled_visual_review" in status


def test_workflow_presets_mention_visual_review_commands(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    presets = build_operator_workflow_presets(storage)
    standalone = next(
        preset for preset in presets if preset["preset_id"] == PRESET_REGENERATE_VISUAL_REVIEW
    )
    scheduled = next(
        preset
        for preset in presets
        if preset["preset_id"] == PRESET_FULL_SCHEDULED_PROOF_REVIEW_WITH_VISUAL_REVIEW
    )
    assert standalone["command"] == "make mrms-visual-review"
    assert scheduled["command"] == "make scheduled-proof-bundle-visual-review"
    assert "standalone" in standalone["description"].lower() or "standalone" in standalone["when_to_use"].lower()


def test_visual_review_preset_recommended_when_hint_recommends(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    from backend.app.services.operator_review_status import build_operator_review_status

    status = build_operator_review_status(storage)
    status["visual_review_regeneration_recommended"] = True
    presets = build_operator_workflow_presets(storage, status=status)
    standalone = next(
        preset for preset in presets if preset["preset_id"] == PRESET_REGENERATE_VISUAL_REVIEW
    )
    scheduled = next(
        preset
        for preset in presets
        if preset["preset_id"] == PRESET_FULL_SCHEDULED_PROOF_REVIEW_WITH_VISUAL_REVIEW
    )
    assert standalone["recommended"] is True
    assert scheduled["recommended"] is True


def test_scheduled_visual_review_target_exists_in_presets(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    assert PRESET_FULL_SCHEDULED_PROOF_REVIEW_WITH_VISUAL_REVIEW in EXPECTED_PRESET_IDS


def test_scheduled_visual_review_does_not_clear_alerts(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    before = load_validation_alert(storage)
    run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        visual_review_requested=True,
        persist=True,
    )
    after = load_validation_alert(storage)
    if before is not None and after is not None:
        assert after.get("status") == before.get("status")


def test_scheduled_visual_review_does_not_mutate_production_gates(
    db_session, storage, monkeypatch
):
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
        visual_review_requested=True,
        persist=False,
    )
    assert settings.enable_production_radar_tiles is False


def test_scheduled_visual_review_always_verified_mrms_false(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    report = run_scheduled_validation(
        db_session,
        storage,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
        visual_review_requested=True,
        persist=False,
    )
    assert report.verified_mrms is False
    compact = compact_scheduled_visual_review(report.to_dict())
    assert compact["verified_mrms"] is False


def test_production_tile_serving_still_gated_phase59(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    response = client.get("/api/tiles/mrms/2026-06-28T12:00:00Z/0/0/0.png")
    assert response.status_code in (404, 503)
