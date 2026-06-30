"""Tests for MRMS candidate readiness milestone audit (Phase 100)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight import PREFLIGHT_CANDIDATE_READY
from backend.app.services.mrms_render_candidate_readiness_milestone_audit import (
    AUDIT_BLOCKED,
    AUDIT_JSON,
    CATEGORY_NONE,
    ROOT_GATE_PREFLIGHT,
    SUGGESTED_COMMAND,
    build_readiness_milestone_audit,
    compact_readiness_milestone_audit,
    load_readiness_milestone_audit,
    run_readiness_milestone_audit,
)
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary
from backend.tests.test_mrms_render_candidate_gated_ack_history import _seed_ack_ready_chain


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def test_audit_blocked_when_preflight_not_ready(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = build_readiness_milestone_audit(storage)
    assert report["audit_status"] == AUDIT_BLOCKED
    assert report["preflight_ready"] is False
    assert report["root_gate"] == ROOT_GATE_PREFLIGHT
    assert report["add_gated_wrapper_recommended"] is False
    assert report["stop_gated_wrapper_loop"] is True
    downstream = report["downstream_blocked_only_because_preflight"]
    assert "dry_run_plan" in downstream
    assert "ack_history" in downstream


def test_audit_refresh_persists_report(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = run_readiness_milestone_audit(storage, refresh_chain=True)
    assert storage.absolute_path(AUDIT_JSON).is_file()
    loaded = load_readiness_milestone_audit(storage)
    assert loaded is not None
    assert loaded["audit_status"] == report["audit_status"]
    assert loaded.get("refresh_steps")


def test_audit_when_preflight_ready(storage, monkeypatch):
    _seed_ack_ready_chain(storage, monkeypatch)
    report = run_readiness_milestone_audit(storage, refresh_chain=True)
    assert report["preflight_level"] == PREFLIGHT_CANDIDATE_READY
    assert report["blocker_category"] == CATEGORY_NONE
    assert report["add_gated_wrapper_recommended"] is False


def test_summary_includes_milestone_audit(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    run_readiness_milestone_audit(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_render_candidate_readiness_milestone_audit")
    assert compact is not None
    assert compact["milestone_audit_is_not_production_authorization"] is True


def test_milestone_audit_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-render-candidate/readiness-milestone-audit")
    assert response.status_code == 200
    assert response.json()["verified_mrms"] is False


def test_milestone_audit_post_refresh(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.post("/api/validation/mrms-render-candidate/readiness-milestone-audit")
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["stop_gated_wrapper_loop"] is True
    assert body["compact"]["suggested_command"] == SUGGESTED_COMMAND


def test_audit_does_not_clear_alerts(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(storage, {"status": ALERT_FAILED, "message": "test"})
    run_readiness_milestone_audit(storage, refresh_chain=True)
    assert load_validation_alert(storage).get("status") == ALERT_FAILED


def test_compact_before_run(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_readiness_milestone_audit(storage)
    assert compact["available"] is False
    assert compact["suggested_command"] == SUGGESTED_COMMAND
    assert compact["stop_gated_wrapper_loop"] is True
