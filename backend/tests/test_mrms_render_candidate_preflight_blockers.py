"""Tests for preflight blocker resolution (Phase 89)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight_attempt import ATTEMPT_BLOCKED_BY_READINESS
from backend.app.services.mrms_render_candidate_preflight_blockers import (
    BLOCKERS_JSON,
    RESOLUTION_BLOCKED,
    RESOLUTION_PREFLIGHT_CANDIDATE_READY,
    _commands_for_blocker_text,
    compact_preflight_blockers,
    load_preflight_blockers_report,
    resolve_preflight_blockers,
)
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary
from backend.tests.test_mrms_render_candidate_preflight import _seed_candidate_ready_chain
from backend.tests.test_mrms_render_candidate_preflight_attempt import _ready_review_chain_evidence


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def test_commands_for_ack_rollup_missing():
    cmds = _commands_for_blocker_text("acknowledgment status rollup is missing")
    assert "make mrms-render-candidate-sandbox-comparison-trend-hint --refresh" in cmds
    assert "make mrms-render-candidate-trend-hint-ack-status --refresh" in cmds


def test_commands_for_visual_no_sample_set():
    from backend.app.services.mrms_render_candidate_preflight_blockers import _commands_for_visual_blocker

    cmds = _commands_for_visual_blocker("no_sample_set")
    assert "make mrms-visual-review-sample-set" in cmds


def test_resolve_blocked_does_not_force_preflight(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = resolve_preflight_blockers(storage)
    assert report["resolution_status"] == RESOLUTION_BLOCKED
    assert report["preflight_not_run"] is True
    assert report["preflight_attempt_status"] == ATTEMPT_BLOCKED_BY_READINESS
    assert len(report.get("remaining_blockers") or []) > 0
    assert len(report.get("next_commands") or []) > 0


def test_resolve_persists_report(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    resolve_preflight_blockers(storage)
    assert storage.absolute_path(BLOCKERS_JSON).is_file()
    loaded = load_preflight_blockers_report(storage)
    assert loaded is not None
    assert loaded["resolution_status"] == RESOLUTION_BLOCKED


def test_resolve_includes_visual_blocker(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = resolve_preflight_blockers(storage)
    visual_blockers = report.get("visual_blockers") or []
    assert any("visual sample readiness" in item for item in visual_blockers)


def test_resolve_candidate_ready_when_chain_and_visual_ready(storage, monkeypatch):
    _seed_candidate_ready_chain(storage, monkeypatch)
    evidence = _ready_review_chain_evidence(storage, monkeypatch)
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_review_readiness.gather_review_chain_evidence",
        lambda _storage: evidence,
    )
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_preflight_attempt.gather_review_chain_evidence",
        lambda _storage: evidence,
    )
    report = resolve_preflight_blockers(storage)
    assert report["resolution_status"] == RESOLUTION_PREFLIGHT_CANDIDATE_READY
    assert report["preflight_not_run"] is False
    assert "dry-run-plan" in " ".join(report.get("next_commands") or [])


def test_summary_includes_preflight_blockers(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    resolve_preflight_blockers(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_render_candidate_preflight_blockers")
    assert compact is not None
    assert compact["gated_preflight_ready_is_not_production_authorization"] is True


def test_preflight_blockers_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-render-candidate/sandbox/preflight-blockers")
    assert response.status_code == 200
    assert response.json()["verified_mrms"] is False


def test_preflight_blockers_post_resolve(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.post("/api/validation/mrms-render-candidate/sandbox/preflight-blockers")
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["resolution_status"] == RESOLUTION_BLOCKED
    assert body["compact"]["preflight_not_run"] is True


def test_resolve_does_not_clear_alerts(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(storage, {"status": ALERT_FAILED, "message": "test"})
    resolve_preflight_blockers(storage)
    assert load_validation_alert(storage).get("status") == ALERT_FAILED


def test_compact_before_resolve(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_preflight_blockers(storage)
    assert compact["available"] is False
    assert compact["resolution_status"] == RESOLUTION_BLOCKED
