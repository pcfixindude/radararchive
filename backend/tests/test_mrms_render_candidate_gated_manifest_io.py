"""Tests for gated sandbox manifest import/export (Phase 95)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_gated_manifest_io import (
    REVIEW_JSON,
    REVIEW_MANIFEST_IO_READY,
    REVIEW_PREFLIGHT_BLOCKED,
    REVIEW_SCAFFOLD_BLOCKED,
    SUGGESTED_COMMAND,
    compact_gated_manifest_io,
    load_gated_manifest_io_report,
    review_gated_manifest_io,
)
from backend.app.services.mrms_render_candidate_preflight import PREFLIGHT_CANDIDATE_READY
from backend.app.services.mrms_render_candidate_sandbox import SANDBOX_READY
from backend.app.services.mrms_render_candidate_sandbox_import_export import (
    STATUS_IMPORTED,
    STATUS_JSON,
)
from backend.app.services.mrms_render_candidate_scaffold import SCAFFOLD_READY
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary
from backend.tests.test_mrms_render_candidate_gated_sandbox_layout import _seed_scaffold_ready_chain


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def _seed_layout_ready_chain(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    from backend.app.services.mrms_render_candidate_sandbox import generate_render_candidate_sandbox

    generate_render_candidate_sandbox(storage)


def test_review_blocked_without_preflight_evidence(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = review_gated_manifest_io(storage)
    assert report["review_status"] == REVIEW_PREFLIGHT_BLOCKED
    assert report["manifest_io_skipped"] is True
    assert report["sandbox_skipped"] is True
    assert report["scaffold_skipped"] is True


def test_review_skips_manifest_io_when_scaffold_not_ready(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = review_gated_manifest_io(storage)
    assert report["review_status"] in {REVIEW_PREFLIGHT_BLOCKED, REVIEW_SCAFFOLD_BLOCKED}
    assert report["manifest_io_skipped"] is True


def test_review_runs_manifest_io_when_gates_open(storage, monkeypatch):
    _seed_layout_ready_chain(storage, monkeypatch)
    report = review_gated_manifest_io(storage)
    assert report["preflight_level"] == PREFLIGHT_CANDIDATE_READY
    assert report["scaffold_skipped"] is False
    assert report["scaffold_status"] == SCAFFOLD_READY
    assert report["sandbox_skipped"] is False
    assert report["sandbox_status"] == SANDBOX_READY
    assert report["manifest_io_skipped"] is False
    assert report["review_status"] == REVIEW_MANIFEST_IO_READY
    assert report["import_export_status"] == STATUS_IMPORTED
    assert storage.absolute_path(STATUS_JSON).is_file()


def test_review_persists_report(storage, monkeypatch):
    _seed_layout_ready_chain(storage, monkeypatch)
    review_gated_manifest_io(storage)
    assert storage.absolute_path(REVIEW_JSON).is_file()
    loaded = load_gated_manifest_io_report(storage)
    assert loaded is not None
    assert loaded["review_status"] == REVIEW_MANIFEST_IO_READY


def test_summary_includes_gated_manifest_io(db_session, storage, monkeypatch):
    _seed_layout_ready_chain(storage, monkeypatch)
    review_gated_manifest_io(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_render_candidate_gated_manifest_io")
    assert compact is not None
    assert compact["manifest_io_ready_is_not_production_authorization"] is True


def test_gated_manifest_io_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-render-candidate/sandbox/gated-manifest-io")
    assert response.status_code == 200
    assert response.json()["verified_mrms"] is False


def test_gated_manifest_io_post_refresh(client, storage, monkeypatch):
    _seed_layout_ready_chain(storage, monkeypatch)
    response = client.post("/api/validation/mrms-render-candidate/sandbox/gated-manifest-io")
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["review_status"] == REVIEW_MANIFEST_IO_READY
    assert body["compact"]["manifest_io_skipped"] is False


def test_review_does_not_clear_alerts(storage, monkeypatch):
    _seed_layout_ready_chain(storage, monkeypatch)
    save_validation_alert(storage, {"status": ALERT_FAILED, "message": "test"})
    review_gated_manifest_io(storage)
    assert load_validation_alert(storage).get("status") == ALERT_FAILED


def test_compact_before_review(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_gated_manifest_io(storage)
    assert compact["available"] is False
    assert compact["suggested_command"] == SUGGESTED_COMMAND
