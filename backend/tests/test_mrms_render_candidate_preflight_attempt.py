"""Tests for gated MRMS render candidate preflight attempt (Phase 88)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight import (
    PREFLIGHT_CANDIDATE_READY,
    PREFLIGHT_JSON,
)
from backend.app.services.mrms_render_candidate_preflight_attempt import (
    ATTEMPT_BLOCKED_BY_READINESS,
    ATTEMPT_JSON,
    ATTEMPT_RAN_BLOCKED,
    ATTEMPT_RAN_CANDIDATE_READY,
    attempt_gated_preflight,
    compact_preflight_attempt,
    load_preflight_attempt,
)
from backend.app.services.mrms_render_candidate_review_readiness import (
    CHAIN_READY,
    OVERALL_PREFLIGHT_CANDIDATE_READY,
    OVERALL_READY_FOR_PREFLIGHT,
    evaluate_candidate_review_readiness,
    gather_review_chain_evidence,
)
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary
from backend.tests.test_mrms_render_candidate_preflight import _seed_candidate_ready_chain


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def _ready_review_chain_evidence(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    evidence = gather_review_chain_evidence(storage)
    evidence["trend_hints"] = {**evidence["trend_hints"], "blockers": [], "warnings": [], "trend_review_recommended": False}
    evidence["ack_status_rollup"] = {**evidence["ack_status_rollup"], "rollup_status": "current"}
    evidence["review_digest"] = {
        **evidence["review_digest"],
        "available": True,
        "digest_status": "current",
        "stale_acknowledgment": False,
    }
    evidence["regeneration_hint"] = {"regeneration_recommended": False}
    evidence["review_acknowledgments"] = {
        **evidence["review_acknowledgments"],
        "available": True,
        "trend_review_still_recommended": False,
    }
    evidence["review_digest_diff"] = {**evidence["review_digest_diff"], "diff_status": "unchanged"}
    return evidence


def test_attempt_blocked_when_readiness_not_ready(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    attempt = attempt_gated_preflight(storage)
    assert attempt["attempt_status"] == ATTEMPT_BLOCKED_BY_READINESS
    assert attempt["preflight_not_run"] is True
    assert attempt["verified_mrms"] is False
    assert len(attempt.get("blocking_items") or []) > 0


def test_attempt_does_not_write_preflight_when_blocked(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    attempt_gated_preflight(storage)
    assert not storage.absolute_path(PREFLIGHT_JSON).is_file()
    assert storage.absolute_path(ATTEMPT_JSON).is_file()


def test_attempt_runs_preflight_when_chain_ready(storage, monkeypatch):
    _seed_candidate_ready_chain(storage, monkeypatch)
    evidence = _ready_review_chain_evidence(storage, monkeypatch)
    readiness = evaluate_candidate_review_readiness(evidence)
    assert readiness["chain_readiness_level"] == CHAIN_READY
    assert readiness["overall_readiness_level"] in {
        OVERALL_READY_FOR_PREFLIGHT,
        OVERALL_PREFLIGHT_CANDIDATE_READY,
    }

    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_preflight_attempt.gather_review_chain_evidence",
        lambda _storage: evidence,
    )
    attempt = attempt_gated_preflight(storage)
    assert attempt["preflight_not_run"] is False
    assert attempt["attempt_status"] in {ATTEMPT_RAN_CANDIDATE_READY, ATTEMPT_RAN_BLOCKED}
    assert storage.absolute_path(PREFLIGHT_JSON).is_file()


def test_attempt_ran_candidate_ready_when_evidence_complete(storage, monkeypatch):
    _seed_candidate_ready_chain(storage, monkeypatch)
    evidence = _ready_review_chain_evidence(storage, monkeypatch)
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_preflight_attempt.gather_review_chain_evidence",
        lambda _storage: evidence,
    )
    attempt = attempt_gated_preflight(storage)
    assert attempt["attempt_status"] == ATTEMPT_RAN_CANDIDATE_READY
    assert attempt["preflight_level"] == PREFLIGHT_CANDIDATE_READY


def test_compact_shows_gate_closed_on_empty_chain(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_preflight_attempt(storage)
    assert compact["gate_open"] is False
    assert compact["available"] is False


def test_summary_includes_preflight_attempt(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    attempt_gated_preflight(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_render_candidate_preflight_attempt")
    assert compact is not None
    assert compact["gated_preflight_ready_is_not_production_authorization"] is True


def test_preflight_attempt_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-render-candidate/sandbox/preflight-attempt")
    assert response.status_code == 200
    assert response.json()["verified_mrms"] is False


def test_preflight_attempt_post_blocked(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.post("/api/validation/mrms-render-candidate/sandbox/preflight-attempt")
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["attempt_status"] == ATTEMPT_BLOCKED_BY_READINESS


def test_attempt_does_not_clear_alerts(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(storage, {"status": ALERT_FAILED, "message": "test"})
    attempt_gated_preflight(storage)
    assert load_validation_alert(storage).get("status") == ALERT_FAILED


def test_attempt_blocked_when_production_enabled(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", True)
    attempt = attempt_gated_preflight(storage)
    assert attempt["attempt_status"] == ATTEMPT_BLOCKED_BY_READINESS


def test_load_preflight_attempt_after_save(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    attempt_gated_preflight(storage)
    loaded = load_preflight_attempt(storage)
    assert loaded is not None
    assert loaded["attempt_status"] == ATTEMPT_BLOCKED_BY_READINESS
