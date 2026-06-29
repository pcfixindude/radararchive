"""Tests for gated sandbox comparison acknowledgment review (Phase 98)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_gated_comparison_ack import (
    REVIEW_ACK_NEEDS_ACK,
    REVIEW_ACK_READY,
    REVIEW_JSON,
    REVIEW_PREFLIGHT_BLOCKED,
    SUGGESTED_COMMAND,
    compact_gated_comparison_ack,
    load_gated_comparison_ack_report,
    review_gated_comparison_ack,
)
from backend.app.services.mrms_render_candidate_preflight import PREFLIGHT_CANDIDATE_READY
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status import (
    STATUS_JSON,
)
from backend.app.services.mrms_render_candidate_sandbox_import_export import STATUS_IMPORTED
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary
from backend.tests.test_mrms_render_candidate_gated_trend_review import _seed_comparison_history_ready_chain


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def _seed_trend_ready_chain(storage, monkeypatch):
    _seed_comparison_history_ready_chain(storage, monkeypatch)
    from backend.app.services.mrms_render_candidate_gated_trend_review import review_gated_trend_review

    review_gated_trend_review(storage)


def test_review_blocked_without_preflight_evidence(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = review_gated_comparison_ack(storage)
    assert report["review_status"] == REVIEW_PREFLIGHT_BLOCKED
    assert report["ack_skipped"] is True
    assert report["trend_skipped"] is True
    assert report["comparison_skipped"] is True


def test_review_skips_ack_when_trend_not_ready(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = review_gated_comparison_ack(storage)
    assert report["ack_skipped"] is True
    assert report["review_status"] == REVIEW_PREFLIGHT_BLOCKED


def test_review_refreshes_ack_when_gates_open(storage, monkeypatch):
    _seed_trend_ready_chain(storage, monkeypatch)
    report = review_gated_comparison_ack(storage)
    assert report["preflight_level"] == PREFLIGHT_CANDIDATE_READY
    assert report["manifest_io_skipped"] is False
    assert report["import_export_status"] == STATUS_IMPORTED
    assert report["trend_skipped"] is False
    assert report["ack_skipped"] is False
    assert report["review_status"] in {
        REVIEW_ACK_READY,
        REVIEW_ACK_NEEDS_ACK,
        "comparison_ack_stale",
        "comparison_ack_blocked",
    }
    assert storage.absolute_path(STATUS_JSON).is_file()


def test_review_persists_report(storage, monkeypatch):
    _seed_trend_ready_chain(storage, monkeypatch)
    report = review_gated_comparison_ack(storage)
    assert storage.absolute_path(REVIEW_JSON).is_file()
    loaded = load_gated_comparison_ack_report(storage)
    assert loaded is not None
    assert loaded["review_status"] == report["review_status"]
    assert loaded["ack_skipped"] is False


def test_summary_includes_gated_comparison_ack(db_session, storage, monkeypatch):
    _seed_trend_ready_chain(storage, monkeypatch)
    review_gated_comparison_ack(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_render_candidate_gated_comparison_ack")
    assert compact is not None
    assert compact["comparison_ack_ready_is_not_production_authorization"] is True


def test_gated_comparison_ack_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-render-candidate/sandbox/gated-ack-review")
    assert response.status_code == 200
    assert response.json()["verified_mrms"] is False


def test_gated_comparison_ack_post_refresh(client, storage, monkeypatch):
    _seed_trend_ready_chain(storage, monkeypatch)
    response = client.post("/api/validation/mrms-render-candidate/sandbox/gated-ack-review")
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["ack_skipped"] is False
    assert body["compact"]["rollup_status"] is not None


def test_review_does_not_clear_alerts(storage, monkeypatch):
    _seed_trend_ready_chain(storage, monkeypatch)
    save_validation_alert(storage, {"status": ALERT_FAILED, "message": "test"})
    review_gated_comparison_ack(storage)
    assert load_validation_alert(storage).get("status") == ALERT_FAILED


def test_compact_before_review(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_gated_comparison_ack(storage)
    assert compact["available"] is False
    assert compact["suggested_command"] == SUGGESTED_COMMAND
