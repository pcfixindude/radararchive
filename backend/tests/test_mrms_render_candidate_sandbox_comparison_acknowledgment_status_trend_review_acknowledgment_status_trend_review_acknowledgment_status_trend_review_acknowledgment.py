"""Tests for trend review acknowledgment status trend review acknowledgment status trend hint review acknowledgments (Phase 81)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status import (
    ROLLUP_NEEDS_ACKNOWLEDGMENT,
    refresh_sandbox_comparison_acknowledgment_status,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_history import (
    COVERAGE_WORSENED,
    _safety_fields as history_safety_fields,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint import (
    refresh_ack_status_trend_hint,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history import (
    _save_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history,
    _safety_fields as trend_review_history_safety_fields,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint import (
    HINT_NEEDS_REVIEW,
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment import (
    ACKNOWLEDGMENTS_PATH,
    AckStatusTrendReviewAckStatusTrendReviewAckStatusTrendReviewAcknowledgmentValidationError,
    build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgments_payload,
    compact_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_summary,
    create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment,
    load_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgments,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_history import (
    COMPARISON_CHANGED,
    append_comparison_history_entry,
    build_comparison_history_entry,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_trend_hint import (
    refresh_sandbox_comparison_trend_hint,
)
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def _seed_status_trend_review_ack_status_trend_review_ack_status_trend_hint_needs_review(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    for _ in range(2):
        entry = build_comparison_history_entry(
            comparison_type="current_vs_imported",
            comparison={"changed_sandbox_status": True},
            comparison_status=COMPARISON_CHANGED,
            source_paths={"import_json_path": "data/dev/test.json"},
        )
        append_comparison_history_entry(storage, entry)
    refresh_sandbox_comparison_trend_hint(storage)
    refresh_sandbox_comparison_acknowledgment_status(storage)
    from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_history import (
        _save_ack_status_history,
    )

    base = {
        "rollup_status": ROLLUP_NEEDS_ACKNOWLEDGMENT,
        "acknowledgment_status": "none",
        "coverage_change": COVERAGE_WORSENED,
        "stale_acknowledgment": False,
        **history_safety_fields(),
    }
    _save_ack_status_history(
        storage,
        [
            {**base, "recorded_at": "2026-01-01T00:00:02Z"},
            {**base, "recorded_at": "2026-01-01T00:00:01Z"},
        ],
    )
    refresh_ack_status_trend_hint(storage)
    trend_base = {
        "rollup_status": ROLLUP_NEEDS_ACKNOWLEDGMENT,
        "acknowledgment_status": "none",
        "coverage_change": COVERAGE_WORSENED,
        "stale_acknowledgment": False,
        **trend_review_history_safety_fields(),
    }
    _save_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history(
        storage,
        [
            {**trend_base, "recorded_at": "2026-01-01T00:00:02Z"},
            {**trend_base, "recorded_at": "2026-01-01T00:00:01Z"},
        ],
    )
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)


def test_acknowledgment_requires_operator_and_note(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    try:
        create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
            storage,
            note="reviewed",
        )
    except AckStatusTrendReviewAckStatusTrendReviewAckStatusTrendReviewAcknowledgmentValidationError as exc:
        assert "operator" in str(exc).lower()
    else:
        raise AssertionError("expected validation error")


def test_acknowledgment_captures_related_status_trend_hint(storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_trend_hint_needs_review(storage, monkeypatch)
    record = create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Reviewed status trend hints locally.",
        acknowledged_trend_review=True,
    )
    assert record["related_hint_status"] == HINT_NEEDS_REVIEW
    assert record["related_trend"] is not None
    assert record["acknowledged_trend_review"] is True
    assert record["verified_mrms"] is False


def test_acknowledgment_persists_to_json(storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_trend_hint_needs_review(storage, monkeypatch)
    create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Local review only.",
    )
    entries = load_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgments(
        storage
    )
    assert len(entries) == 1
    assert storage.absolute_path(ACKNOWLEDGMENTS_PATH).is_file()


def test_acknowledgment_safety_invariants(storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_trend_hint_needs_review(storage, monkeypatch)
    create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Safety check.",
    )
    compact = compact_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_summary(
        storage
    )
    assert compact["verified_mrms"] is False
    assert compact["does_not_clear_alerts"] is True
    assert compact["does_not_authorize_production_use"] is True


def test_acknowledgment_does_not_clear_alerts(storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_trend_hint_needs_review(storage, monkeypatch)
    save_validation_alert(storage, {"level": ALERT_FAILED, "reason": "test"})
    create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Does not clear alerts.",
    )
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert["level"] == ALERT_FAILED


def test_summary_includes_acknowledgment_compact(db_session, storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_trend_hint_needs_review(storage, monkeypatch)
    create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Summary test.",
    )
    summary = build_validation_summary(db_session, storage)
    compact = summary[
        "mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment"
    ]
    assert compact["available"] is True
    assert compact["verified_mrms"] is False
    assert compact["count"] == 1


def test_acknowledgment_get_endpoint(client, storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_trend_hint_needs_review(storage, monkeypatch)
    create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="API GET test.",
    )
    response = client.get(
        "/api/validation/mrms-render-candidate/sandbox/import-export/"
        "comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgments"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["count"] == 1


def test_acknowledgment_post_endpoint(client, storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_trend_hint_needs_review(storage, monkeypatch)
    response = client.post(
        "/api/validation/mrms-render-candidate/sandbox/import-export/"
        "comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgments",
        json={
            "operator_initials": "OP",
            "note": "API POST test.",
            "acknowledged_trend_review": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["does_not_clear_alerts"] is True
    assert body["acknowledgment"]["operator_initials"] == "OP"


def test_acknowledgment_post_validation_error(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.post(
        "/api/validation/mrms-render-candidate/sandbox/import-export/"
        "comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgments",
        json={"note": "missing operator"},
    )
    assert response.status_code == 422


def test_acknowledgments_payload_lists_entries(storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_trend_hint_needs_review(storage, monkeypatch)
    create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
        storage,
        operator_initials="A",
        note="First.",
    )
    create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
        storage,
        operator_initials="B",
        note="Second.",
    )
    payload = build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgments_payload(
        storage,
        limit=10,
    )
    assert payload["count"] == 2
    assert len(payload["entries"]) == 2
