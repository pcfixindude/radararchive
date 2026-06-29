"""Tests for gated sandbox comparison trend hint review (Phase 97)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_gated_trend_review import (
    REVIEW_JSON,
    REVIEW_PREFLIGHT_BLOCKED,
    REVIEW_TREND_READY,
    SUGGESTED_COMMAND,
    compact_gated_trend_review,
    load_gated_trend_review_report,
    review_gated_trend_review,
)
from backend.app.services.mrms_render_candidate_preflight import PREFLIGHT_CANDIDATE_READY
from backend.app.services.mrms_render_candidate_sandbox_comparison_trend_hint import (
    HINT_JSON,
    HINT_READY,
)
from backend.app.services.mrms_render_candidate_sandbox_import_export import STATUS_IMPORTED
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary
from backend.tests.test_mrms_render_candidate_gated_manifest_io import _seed_layout_ready_chain


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def _seed_comparison_history_ready_chain(storage, monkeypatch):
    _seed_layout_ready_chain(storage, monkeypatch)
    from backend.app.services.mrms_render_candidate_sandbox_import_export import run_import_export_workflow

    run_import_export_workflow(storage, export=True, import_after_export=True)
    from backend.app.services.mrms_render_candidate_gated_comparison_history import (
        review_gated_comparison_history,
    )

    review_gated_comparison_history(storage)


def test_review_blocked_without_preflight_evidence(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = review_gated_trend_review(storage)
    assert report["review_status"] == REVIEW_PREFLIGHT_BLOCKED
    assert report["trend_skipped"] is True
    assert report["comparison_skipped"] is True
    assert report["manifest_io_skipped"] is True


def test_review_skips_trend_when_comparison_not_ready(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = review_gated_trend_review(storage)
    assert report["trend_skipped"] is True
    assert report["review_status"] == REVIEW_PREFLIGHT_BLOCKED


def test_review_refreshes_trend_when_gates_open(storage, monkeypatch):
    _seed_comparison_history_ready_chain(storage, monkeypatch)
    report = review_gated_trend_review(storage)
    assert report["preflight_level"] == PREFLIGHT_CANDIDATE_READY
    assert report["manifest_io_skipped"] is False
    assert report["import_export_status"] == STATUS_IMPORTED
    assert report["comparison_skipped"] is False
    assert report["trend_skipped"] is False
    assert report["review_status"] in {REVIEW_TREND_READY, "trend_hint_needs_review", "trend_hint_blocked"}
    assert storage.absolute_path(HINT_JSON).is_file()


def test_review_persists_report(storage, monkeypatch):
    _seed_comparison_history_ready_chain(storage, monkeypatch)
    report = review_gated_trend_review(storage)
    assert storage.absolute_path(REVIEW_JSON).is_file()
    loaded = load_gated_trend_review_report(storage)
    assert loaded is not None
    assert loaded["review_status"] == report["review_status"]
    assert loaded["trend_skipped"] is False


def test_summary_includes_gated_trend_review(db_session, storage, monkeypatch):
    _seed_comparison_history_ready_chain(storage, monkeypatch)
    review_gated_trend_review(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_render_candidate_gated_trend_review")
    assert compact is not None
    assert compact["trend_hint_ready_is_not_production_authorization"] is True


def test_gated_trend_review_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-render-candidate/sandbox/gated-trend-review")
    assert response.status_code == 200
    assert response.json()["verified_mrms"] is False


def test_gated_trend_review_post_refresh(client, storage, monkeypatch):
    _seed_comparison_history_ready_chain(storage, monkeypatch)
    response = client.post("/api/validation/mrms-render-candidate/sandbox/gated-trend-review")
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["trend_skipped"] is False
    assert body["compact"]["hint_status"] in {HINT_READY, "needs_review", "blocked", "missing"}


def test_review_does_not_clear_alerts(storage, monkeypatch):
    _seed_comparison_history_ready_chain(storage, monkeypatch)
    save_validation_alert(storage, {"status": ALERT_FAILED, "message": "test"})
    review_gated_trend_review(storage)
    assert load_validation_alert(storage).get("status") == ALERT_FAILED


def test_compact_before_review(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_gated_trend_review(storage)
    assert compact["available"] is False
    assert compact["suggested_command"] == SUGGESTED_COMMAND
