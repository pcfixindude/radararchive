"""Tests for gated render candidate dry-run plan review (Phase 92)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_dry_run_plan import (
    DRY_RUN_PLAN_JSON,
    DRY_RUN_PLAN_READY,
    load_render_candidate_dry_run_plan,
)
from backend.app.services.mrms_render_candidate_gated_dry_run_review import (
    REVIEW_JSON,
    REVIEW_PLAN_READY,
    REVIEW_PREFLIGHT_BLOCKED,
    SUGGESTED_COMMAND,
    compact_gated_dry_run_review,
    load_gated_dry_run_review_report,
    review_gated_dry_run_plan,
)
from backend.app.services.mrms_render_candidate_preflight import PREFLIGHT_CANDIDATE_READY
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary
from backend.tests.test_mrms_render_candidate_dry_run_plan import _seed_preflight_ready_chain


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def test_review_blocked_without_preflight_evidence(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = review_gated_dry_run_plan(storage)
    assert report["review_status"] == REVIEW_PREFLIGHT_BLOCKED
    assert report["dry_run_plan_skipped"] is True
    assert report["dry_run_plan_status"] is None
    assert len(report.get("next_commands") or []) > 0


def test_review_skips_dry_run_plan_when_preflight_not_ready(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = review_gated_dry_run_plan(storage)
    assert report["dry_run_plan_skipped"] is True
    assert load_render_candidate_dry_run_plan(storage) is None

def test_review_generates_plan_when_preflight_ready(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    report = review_gated_dry_run_plan(storage)
    assert report["preflight_level"] == PREFLIGHT_CANDIDATE_READY
    assert report["dry_run_plan_skipped"] is False
    assert report["review_status"] == REVIEW_PLAN_READY
    assert report["dry_run_plan_status"] == DRY_RUN_PLAN_READY
    assert storage.absolute_path(DRY_RUN_PLAN_JSON).is_file()


def test_review_persists_report(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    review_gated_dry_run_plan(storage)
    assert storage.absolute_path(REVIEW_JSON).is_file()
    loaded = load_gated_dry_run_review_report(storage)
    assert loaded is not None
    assert loaded["review_status"] == REVIEW_PLAN_READY


def test_summary_includes_gated_dry_run_review(db_session, storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    review_gated_dry_run_plan(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_render_candidate_gated_dry_run_review")
    assert compact is not None
    assert compact["dry_run_plan_ready_is_not_production_authorization"] is True


def test_gated_dry_run_review_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-render-candidate/sandbox/gated-dry-run-review")
    assert response.status_code == 200
    assert response.json()["verified_mrms"] is False


def test_gated_dry_run_review_post_refresh(client, storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    response = client.post("/api/validation/mrms-render-candidate/sandbox/gated-dry-run-review")
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["review_status"] == REVIEW_PLAN_READY
    assert body["compact"]["dry_run_plan_skipped"] is False


def test_review_does_not_clear_alerts(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    save_validation_alert(storage, {"status": ALERT_FAILED, "message": "test"})
    review_gated_dry_run_plan(storage)
    assert load_validation_alert(storage).get("status") == ALERT_FAILED


def test_compact_before_review(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_gated_dry_run_review(storage)
    assert compact["available"] is False
    assert compact["suggested_command"] == SUGGESTED_COMMAND
