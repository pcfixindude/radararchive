"""Tests for trend-hint chain bootstrap (Phase 90)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight_attempt import ATTEMPT_BLOCKED_BY_READINESS
from backend.app.services.mrms_render_candidate_review_readiness import CHAIN_READY
from backend.app.services.mrms_render_candidate_trend_hint_ack_status import ROLLUP_MISSING
from backend.app.services.mrms_render_candidate_trend_hint_chain_bootstrap import (
    BOOTSTRAP_CHAIN_READY_VISUAL_BLOCKED,
    BOOTSTRAP_JSON,
    BOOTSTRAP_STILL_BLOCKED,
    SUGGESTED_COMMAND,
    bootstrap_trend_hint_chain,
    compact_trend_hint_chain_bootstrap,
    load_trend_hint_chain_bootstrap_report,
    seed_sandbox_comparison_history_if_needed,
)
from backend.app.services.mrms_render_candidate_trend_hint_ack_status import ROLLUP_NOT_NEEDED
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def test_seed_comparison_history_when_empty(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    result = seed_sandbox_comparison_history_if_needed(storage)
    assert result["seeded"] is True
    assert result["entries_added"] == 2
    again = seed_sandbox_comparison_history_if_needed(storage)
    assert again["seeded"] is False


def test_bootstrap_unblocks_trend_hint_chain(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = bootstrap_trend_hint_chain(storage)
    assert report["rollup_status"] != ROLLUP_MISSING
    assert report["trend_hint_chain_ready"] is True
    assert report["bootstrap_status"] in {
        BOOTSTRAP_CHAIN_READY_VISUAL_BLOCKED,
        BOOTSTRAP_STILL_BLOCKED,
    }
    assert not report["trend_hint_blockers"]


def test_bootstrap_visual_still_blocked(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = bootstrap_trend_hint_chain(storage)
    assert report["bootstrap_status"] == BOOTSTRAP_CHAIN_READY_VISUAL_BLOCKED
    assert any("visual sample readiness" in item for item in report["visual_blockers"])
    assert "make mrms-visual-review-sample-set" in (report.get("next_commands") or [])


def test_bootstrap_does_not_force_preflight(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = bootstrap_trend_hint_chain(storage)
    assert report["preflight_not_run"] is True
    assert report.get("preflight_attempt_status") == ATTEMPT_BLOCKED_BY_READINESS


def test_bootstrap_persists_report(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    bootstrap_trend_hint_chain(storage)
    assert storage.absolute_path(BOOTSTRAP_JSON).is_file()
    loaded = load_trend_hint_chain_bootstrap_report(storage)
    assert loaded is not None
    assert loaded["rollup_status"] in {ROLLUP_NOT_NEEDED, "current", "not_needed"}


def test_summary_includes_chain_bootstrap(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    bootstrap_trend_hint_chain(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_render_candidate_trend_hint_chain_bootstrap")
    assert compact is not None
    assert compact["gated_preflight_ready_is_not_production_authorization"] is True


def test_chain_bootstrap_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get(
        "/api/validation/mrms-render-candidate/sandbox/trend-hint-chain-bootstrap"
    )
    assert response.status_code == 200
    assert response.json()["verified_mrms"] is False


def test_chain_bootstrap_post_refresh(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.post(
        "/api/validation/mrms-render-candidate/sandbox/trend-hint-chain-bootstrap"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["bootstrap_status"] == BOOTSTRAP_CHAIN_READY_VISUAL_BLOCKED
    assert body["compact"]["trend_hint_chain_ready"] is True


def test_bootstrap_does_not_clear_alerts(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(storage, {"status": ALERT_FAILED, "message": "test"})
    bootstrap_trend_hint_chain(storage)
    assert load_validation_alert(storage).get("status") == ALERT_FAILED


def test_compact_before_bootstrap(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_trend_hint_chain_bootstrap(storage)
    assert compact["available"] is False
    assert compact["suggested_command"] == SUGGESTED_COMMAND


def test_bootstrap_chain_readiness_ready(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = bootstrap_trend_hint_chain(storage)
    assert report["chain_readiness_level"] == CHAIN_READY
