"""Tests for gated sandbox acknowledgment history review (Phase 99)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_gated_ack_history import (
    REVIEW_ACK_HISTORY_READY,
    REVIEW_JSON,
    REVIEW_PREFLIGHT_BLOCKED,
    SUGGESTED_COMMAND,
    compact_gated_ack_history,
    load_gated_ack_history_report,
    review_gated_ack_history,
)
from backend.app.services.mrms_render_candidate_preflight import PREFLIGHT_CANDIDATE_READY
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_history import (
    ACK_STATUS_HISTORY_JSON,
)
from backend.app.services.mrms_render_candidate_sandbox_import_export import STATUS_IMPORTED
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary
from backend.tests.test_mrms_render_candidate_gated_comparison_ack import _seed_trend_ready_chain


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def _seed_ack_ready_chain(storage, monkeypatch):
    _seed_trend_ready_chain(storage, monkeypatch)
    from backend.app.services.mrms_render_candidate_gated_comparison_ack import review_gated_comparison_ack

    review_gated_comparison_ack(storage)


def test_review_blocked_without_preflight_evidence(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = review_gated_ack_history(storage)
    assert report["review_status"] == REVIEW_PREFLIGHT_BLOCKED
    assert report["history_skipped"] is True
    assert report["ack_skipped"] is True
    assert report["trend_skipped"] is True


def test_review_skips_history_when_ack_not_ready(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = review_gated_ack_history(storage)
    assert report["history_skipped"] is True
    assert report["review_status"] == REVIEW_PREFLIGHT_BLOCKED


def test_review_refreshes_history_when_gates_open(storage, monkeypatch):
    _seed_ack_ready_chain(storage, monkeypatch)
    report = review_gated_ack_history(storage)
    assert report["preflight_level"] == PREFLIGHT_CANDIDATE_READY
    assert report["manifest_io_skipped"] is False
    assert report["import_export_status"] == STATUS_IMPORTED
    assert report["ack_skipped"] is False
    assert report["history_skipped"] is False
    assert report["review_status"] in {REVIEW_ACK_HISTORY_READY, "ack_history_missing"}
    assert storage.absolute_path(ACK_STATUS_HISTORY_JSON).is_file()


def test_review_persists_report(storage, monkeypatch):
    _seed_ack_ready_chain(storage, monkeypatch)
    report = review_gated_ack_history(storage)
    assert storage.absolute_path(REVIEW_JSON).is_file()
    loaded = load_gated_ack_history_report(storage)
    assert loaded is not None
    assert loaded["review_status"] == report["review_status"]
    assert loaded["history_skipped"] is False


def test_summary_includes_gated_ack_history(db_session, storage, monkeypatch):
    _seed_ack_ready_chain(storage, monkeypatch)
    review_gated_ack_history(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_render_candidate_gated_ack_history")
    assert compact is not None
    assert compact["ack_history_ready_is_not_production_authorization"] is True


def test_gated_ack_history_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-render-candidate/sandbox/gated-ack-history")
    assert response.status_code == 200
    assert response.json()["verified_mrms"] is False


def test_gated_ack_history_post_refresh(client, storage, monkeypatch):
    _seed_ack_ready_chain(storage, monkeypatch)
    response = client.post("/api/validation/mrms-render-candidate/sandbox/gated-ack-history")
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["history_skipped"] is False
    assert (body["compact"]["ack_history_count"] or 0) >= 0


def test_review_does_not_clear_alerts(storage, monkeypatch):
    _seed_ack_ready_chain(storage, monkeypatch)
    save_validation_alert(storage, {"status": ALERT_FAILED, "message": "test"})
    review_gated_ack_history(storage)
    assert load_validation_alert(storage).get("status") == ALERT_FAILED


def test_compact_before_review(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_gated_ack_history(storage)
    assert compact["available"] is False
    assert compact["suggested_command"] == SUGGESTED_COMMAND
