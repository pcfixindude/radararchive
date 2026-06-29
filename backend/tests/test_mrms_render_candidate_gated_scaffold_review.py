"""Tests for gated render candidate scaffold review (Phase 93)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_dry_run_plan import (
    DRY_RUN_PLAN_JSON,
    DRY_RUN_PLAN_READY,
    load_render_candidate_dry_run_plan,
)
from backend.app.services.mrms_render_candidate_gated_scaffold_review import (
    REVIEW_DRY_RUN_BLOCKED,
    REVIEW_JSON,
    REVIEW_PREFLIGHT_BLOCKED,
    REVIEW_SCAFFOLD_READY,
    SUGGESTED_COMMAND,
    compact_gated_scaffold_review,
    load_gated_scaffold_review_report,
    review_gated_scaffold,
)
from backend.app.services.mrms_render_candidate_preflight import PREFLIGHT_CANDIDATE_READY
from backend.app.services.mrms_render_candidate_scaffold import (
    SCAFFOLD_JSON,
    SCAFFOLD_READY,
    load_render_candidate_scaffold,
)
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary
from backend.tests.test_mrms_render_candidate_scaffold import _seed_preflight_ready_chain


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def test_review_blocked_without_preflight_evidence(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = review_gated_scaffold(storage)
    assert report["review_status"] == REVIEW_PREFLIGHT_BLOCKED
    assert report["scaffold_skipped"] is True
    assert report["dry_run_plan_skipped"] is True
    assert load_render_candidate_scaffold(storage) is None


def test_review_skips_scaffold_when_dry_run_not_ready(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = review_gated_scaffold(storage)
    assert report["review_status"] in {REVIEW_PREFLIGHT_BLOCKED, REVIEW_DRY_RUN_BLOCKED}
    assert report["scaffold_skipped"] is True


def test_review_generates_scaffold_when_gates_open(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    from backend.app.services.mrms_render_candidate_dry_run_plan import generate_render_candidate_dry_run_plan

    generate_render_candidate_dry_run_plan(storage)
    report = review_gated_scaffold(storage)
    assert report["preflight_level"] == PREFLIGHT_CANDIDATE_READY
    assert report["dry_run_plan_skipped"] is False
    assert report["dry_run_plan_status"] == DRY_RUN_PLAN_READY
    assert report["scaffold_skipped"] is False
    assert report["review_status"] == REVIEW_SCAFFOLD_READY
    assert report["scaffold_status"] == SCAFFOLD_READY
    assert report["execute_performed"] is False
    assert storage.absolute_path(SCAFFOLD_JSON).is_file()


def test_review_does_not_execute_scaffold(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    from backend.app.services.mrms_render_candidate_dry_run_plan import generate_render_candidate_dry_run_plan

    generate_render_candidate_dry_run_plan(storage)
    report = review_gated_scaffold(storage)
    assert report["execute_performed"] is False
    loaded = load_render_candidate_scaffold(storage)
    assert loaded is not None
    assert loaded["execute_performed"] is False


def test_review_persists_report(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    from backend.app.services.mrms_render_candidate_dry_run_plan import generate_render_candidate_dry_run_plan

    generate_render_candidate_dry_run_plan(storage)
    review_gated_scaffold(storage)
    assert storage.absolute_path(REVIEW_JSON).is_file()
    loaded = load_gated_scaffold_review_report(storage)
    assert loaded is not None
    assert loaded["review_status"] == REVIEW_SCAFFOLD_READY


def test_summary_includes_gated_scaffold_review(db_session, storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    from backend.app.services.mrms_render_candidate_dry_run_plan import generate_render_candidate_dry_run_plan

    generate_render_candidate_dry_run_plan(storage)
    review_gated_scaffold(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_render_candidate_gated_scaffold_review")
    assert compact is not None
    assert compact["scaffold_ready_is_not_production_authorization"] is True


def test_gated_scaffold_review_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-render-candidate/sandbox/gated-scaffold-review")
    assert response.status_code == 200
    assert response.json()["verified_mrms"] is False


def test_gated_scaffold_review_post_refresh(client, storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    from backend.app.services.mrms_render_candidate_dry_run_plan import generate_render_candidate_dry_run_plan

    generate_render_candidate_dry_run_plan(storage)
    response = client.post("/api/validation/mrms-render-candidate/sandbox/gated-scaffold-review")
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["review_status"] == REVIEW_SCAFFOLD_READY
    assert body["compact"]["scaffold_skipped"] is False


def test_review_does_not_clear_alerts(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    save_validation_alert(storage, {"status": ALERT_FAILED, "message": "test"})
    from backend.app.services.mrms_render_candidate_dry_run_plan import generate_render_candidate_dry_run_plan

    generate_render_candidate_dry_run_plan(storage)
    review_gated_scaffold(storage)
    assert load_validation_alert(storage).get("status") == ALERT_FAILED


def test_compact_before_review(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_gated_scaffold_review(storage)
    assert compact["available"] is False
    assert compact["suggested_command"] == SUGGESTED_COMMAND


def test_dry_run_plan_created_when_preflight_ready_in_review(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    report = review_gated_scaffold(storage)
    assert report["dry_run_plan_status"] == DRY_RUN_PLAN_READY
    assert storage.absolute_path(DRY_RUN_PLAN_JSON).is_file()
