"""Tests for gated candidate artifact sandbox layout (Phase 94)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_gated_sandbox_layout import (
    REVIEW_JSON,
    REVIEW_LAYOUT_READY,
    REVIEW_PREFLIGHT_BLOCKED,
    REVIEW_SCAFFOLD_BLOCKED,
    SUGGESTED_COMMAND,
    compact_gated_sandbox_layout,
    load_gated_sandbox_layout_report,
    review_gated_sandbox_layout,
)
from backend.app.services.mrms_render_candidate_preflight import PREFLIGHT_CANDIDATE_READY
from backend.app.services.mrms_render_candidate_sandbox import (
    MANIFEST_JSON,
    SANDBOX_READY,
    load_sandbox_manifest,
)
from backend.app.services.mrms_render_candidate_scaffold import SCAFFOLD_READY
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary
from backend.tests.test_mrms_render_candidate_scaffold import _seed_preflight_ready_chain


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def _seed_scaffold_ready_chain(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    from backend.app.services.mrms_render_candidate_dry_run_plan import generate_render_candidate_dry_run_plan
    from backend.app.services.mrms_render_candidate_scaffold import generate_render_candidate_scaffold

    generate_render_candidate_dry_run_plan(storage)
    generate_render_candidate_scaffold(storage)


def test_review_blocked_without_preflight_evidence(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = review_gated_sandbox_layout(storage)
    assert report["review_status"] == REVIEW_PREFLIGHT_BLOCKED
    assert report["sandbox_skipped"] is True
    assert report["scaffold_skipped"] is True
    assert report["dry_run_plan_skipped"] is True
    assert load_sandbox_manifest(storage) is None


def test_review_skips_sandbox_when_scaffold_not_ready(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = review_gated_sandbox_layout(storage)
    assert report["review_status"] in {REVIEW_PREFLIGHT_BLOCKED, REVIEW_SCAFFOLD_BLOCKED}
    assert report["sandbox_skipped"] is True


def test_review_generates_sandbox_when_gates_open(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    report = review_gated_sandbox_layout(storage)
    assert report["preflight_level"] == PREFLIGHT_CANDIDATE_READY
    assert report["scaffold_skipped"] is False
    assert report["scaffold_status"] == SCAFFOLD_READY
    assert report["sandbox_skipped"] is False
    assert report["review_status"] == REVIEW_LAYOUT_READY
    assert report["sandbox_status"] == SANDBOX_READY
    assert report["delete_performed"] is False
    assert storage.absolute_path(MANIFEST_JSON).is_file()


def test_review_does_not_delete_sandbox_files(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    report = review_gated_sandbox_layout(storage)
    assert report["delete_performed"] is False
    loaded = load_sandbox_manifest(storage)
    assert loaded is not None
    assert loaded.get("delete_performed") is False


def test_review_persists_report(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    review_gated_sandbox_layout(storage)
    assert storage.absolute_path(REVIEW_JSON).is_file()
    loaded = load_gated_sandbox_layout_report(storage)
    assert loaded is not None
    assert loaded["review_status"] == REVIEW_LAYOUT_READY


def test_summary_includes_gated_sandbox_layout(db_session, storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    review_gated_sandbox_layout(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_render_candidate_gated_sandbox_layout")
    assert compact is not None
    assert compact["sandbox_layout_ready_is_not_production_authorization"] is True


def test_gated_sandbox_layout_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-render-candidate/sandbox/gated-layout-review")
    assert response.status_code == 200
    assert response.json()["verified_mrms"] is False


def test_gated_sandbox_layout_post_refresh(client, storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    response = client.post("/api/validation/mrms-render-candidate/sandbox/gated-layout-review")
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["review_status"] == REVIEW_LAYOUT_READY
    assert body["compact"]["sandbox_skipped"] is False


def test_review_does_not_clear_alerts(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    save_validation_alert(storage, {"status": ALERT_FAILED, "message": "test"})
    review_gated_sandbox_layout(storage)
    assert load_validation_alert(storage).get("status") == ALERT_FAILED


def test_compact_before_review(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_gated_sandbox_layout(storage)
    assert compact["available"] is False
    assert compact["suggested_command"] == SUGGESTED_COMMAND
