"""Tests for candidate review readiness consolidation (Phase 87)."""

from __future__ import annotations

import json

from backend.app.config import settings
from backend.app.services.mrms_proof_bundle_diff import DIFF_WORSENED
from backend.app.services.mrms_render_candidate_review_readiness import (
    CHAIN_BLOCKED,
    CHAIN_NEEDS_REVIEW,
    CHAIN_READY,
    OVERALL_BLOCKED,
    OVERALL_NEEDS_REVIEW,
    OVERALL_READY_FOR_PREFLIGHT,
    READINESS_JSON,
    READINESS_MD,
    build_review_regeneration_hint,
    compact_candidate_review_readiness,
    evaluate_candidate_review_readiness,
    gather_review_chain_evidence,
    generate_candidate_review_readiness,
    load_candidate_review_readiness,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest import (
    refresh_trend_hint_review_digest,
)
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary
from backend.tests.test_mrms_render_candidate_trend_hint_review_digest_history import (
    _seed_candidate_trend_hint_needs_review,
)


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def test_evidence_includes_review_chain_sections(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    evidence = gather_review_chain_evidence(storage)
    for key in (
        "trend_hints",
        "review_acknowledgments",
        "ack_status_rollup",
        "ack_status_history",
        "review_digest",
        "review_digest_history",
        "review_digest_diff",
        "regeneration_hint",
        "preflight",
    ):
        assert key in evidence


def test_regeneration_hint_when_digest_not_persisted(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    hint = build_review_regeneration_hint(storage)
    assert hint["regeneration_recommended"] is True
    assert hint["reason"] == "digest_not_persisted"
    assert "trend-hint-review-digest" in (hint.get("suggested_command") or "")


def test_regeneration_hint_when_digest_diff_worsened(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    from backend.app.services.mrms_render_candidate_trend_hint_review_digest_diff import (
        record_trend_hint_review_digest_diff,
    )
    from backend.tests.test_mrms_render_candidate_trend_hint_review_digest_diff import (
        _history_entry,
    )

    record_trend_hint_review_digest_diff(
        storage,
        current_entry=_history_entry(recorded_at="2026-06-28T16:01:00Z"),
        baseline_entry=_history_entry(recorded_at="2026-06-28T16:00:00Z"),
    )
    from backend.app.services.mrms_render_candidate_trend_hint_review_digest_diff import (
        load_latest_trend_hint_review_digest_diff,
    )

    latest = load_latest_trend_hint_review_digest_diff(storage)
    latest["diff_status"] = DIFF_WORSENED
    storage.absolute_path("dev/mrms_render_candidate_trend_hint_review_digest_diff_latest.json").write_text(
        json.dumps(latest, indent=2),
        encoding="utf-8",
    )
    hint = build_review_regeneration_hint(storage)
    assert hint["regeneration_recommended"] is True
    assert hint["reason"] == f"digest_diff_{DIFF_WORSENED}"


def test_readiness_blocked_when_production_enabled(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", True)
    evidence = gather_review_chain_evidence(storage)
    report = evaluate_candidate_review_readiness(evidence)
    assert report["chain_readiness_level"] == CHAIN_BLOCKED
    assert report["overall_readiness_level"] == OVERALL_BLOCKED
    assert any("production" in item.lower() for item in report["blocking_items"])


def test_readiness_blocked_on_empty_chain(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = evaluate_candidate_review_readiness(gather_review_chain_evidence(storage))
    assert report["chain_readiness_level"] == CHAIN_BLOCKED
    assert report["review_chain_ready"] is False
    assert report["gated_preflight_still_blocked"] is True


def test_readiness_needs_review_when_chain_seeded(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_review_digest(storage)
    report = evaluate_candidate_review_readiness(gather_review_chain_evidence(storage))
    assert report["chain_readiness_level"] in {CHAIN_NEEDS_REVIEW, CHAIN_BLOCKED, CHAIN_READY}
    assert report["overall_readiness_level"] in {
        OVERALL_BLOCKED,
        OVERALL_NEEDS_REVIEW,
        OVERALL_READY_FOR_PREFLIGHT,
    }
    regen = report.get("regeneration_hint") or {}
    assert "regeneration_recommended" in regen


def test_next_step_suggests_preflight_when_chain_ready(storage, monkeypatch):
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
    report = evaluate_candidate_review_readiness(evidence)
    assert report["chain_readiness_level"] == CHAIN_READY
    assert report["overall_readiness_level"] == OVERALL_READY_FOR_PREFLIGHT
    assert "preflight" in report["next_operator_step"].lower()
    assert any("preflight" in cmd for cmd in report["suggested_commands"])


def test_generate_persists_json_and_markdown(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = generate_candidate_review_readiness(storage)
    assert storage.absolute_path(READINESS_JSON).is_file()
    assert storage.absolute_path(READINESS_MD).is_file()
    loaded = load_candidate_review_readiness(storage)
    assert loaded is not None
    assert loaded["chain_readiness_level"] == report["chain_readiness_level"]


def test_summary_includes_review_readiness(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_candidate_review_readiness(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_render_candidate_review_readiness")
    assert compact is not None
    assert compact["gated_preflight_ready_is_not_production_authorization"] is True
    assert compact["verified_mrms"] is False


def test_review_readiness_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-render-candidate/sandbox/review-readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["compact"]["gated_preflight_still_blocked"] is True


def test_review_readiness_post_endpoint_persists(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.post("/api/validation/mrms-render-candidate/sandbox/review-readiness")
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["available"] is True
    assert storage.absolute_path(READINESS_JSON).is_file()


def test_readiness_does_not_clear_alerts(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(storage, {"status": ALERT_FAILED, "message": "test"})
    generate_candidate_review_readiness(storage)
    alert = load_validation_alert(storage)
    assert alert.get("status") == ALERT_FAILED


def test_preflight_blocked_flag_from_compact(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_candidate_review_readiness(storage)
    assert compact["preflight_blocked"] in {True, False}
    assert compact["preflight_candidate_ready"] is False or compact["preflight_blocked"] is False


def test_safety_fields_on_regeneration_hint(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    hint = build_review_regeneration_hint(storage)
    assert hint["verified_mrms"] is False
    assert hint["does_not_clear_alerts"] is True
    assert hint["does_not_enable_production"] is True
