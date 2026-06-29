"""Tests for trend review acknowledgment status trend review acknowledgment status trend hints (Phase 80)."""

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
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment import (
    create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status import (
    ROLLUP_CURRENT,
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history import (
    COVERAGE_UNCHANGED,
    _save_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history,
    _safety_fields as trend_review_history_safety_fields,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint import (
    HINT_BLOCKED,
    HINT_JSON,
    HINT_MISSING,
    HINT_NEEDS_REVIEW,
    HINT_READY,
    TREND_CHANGING,
    TREND_NO_DATA,
    TREND_STABLE,
    build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint,
    build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint_markdown,
    compact_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint,
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint,
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


def _seed_status_trend_review_ack_status_trend_review_ack_status_history(storage, monkeypatch, *, count: int = 1):
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
    base = {
        "rollup_status": ROLLUP_NEEDS_ACKNOWLEDGMENT,
        "acknowledgment_status": "none",
        "coverage_change": COVERAGE_WORSENED,
        "stale_acknowledgment": False,
        **history_safety_fields(),
    }
    from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_history import (
        _save_ack_status_history,
    )

    _save_ack_status_history(
        storage,
        [
            {**base, "recorded_at": "2026-01-01T00:00:02Z"},
            {**base, "recorded_at": "2026-01-01T00:00:01Z"},
        ],
    )
    refresh_ack_status_trend_hint(storage)
    for _ in range(count):
        refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status(storage)


def test_trend_hint_no_data_when_history_empty(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    hint = build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)
    assert hint["trend"] == TREND_NO_DATA
    assert hint["hint_status"] == HINT_MISSING
    assert hint["verified_mrms"] is False


def test_trend_hint_stable_when_unchanged_history(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    base = {
        "rollup_status": ROLLUP_CURRENT,
        "acknowledgment_status": "current",
        "coverage_change": COVERAGE_UNCHANGED,
        "stale_acknowledgment": False,
        **trend_review_history_safety_fields(),
    }
    _save_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history(
        storage,
        [
            {**base, "recorded_at": "2026-01-01T00:00:03Z"},
            {**base, "recorded_at": "2026-01-01T00:00:02Z"},
            {**base, "recorded_at": "2026-01-01T00:00:01Z"},
        ],
    )
    hint = build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)
    assert hint["trend"] == TREND_STABLE
    assert hint["hint_status"] == HINT_READY
    assert hint["trend_review_recommended"] is False


def test_trend_hint_needs_review_on_worsened_streak(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    base = {
        "rollup_status": ROLLUP_NEEDS_ACKNOWLEDGMENT,
        "acknowledgment_status": "none",
        "coverage_change": COVERAGE_WORSENED,
        "stale_acknowledgment": False,
        **trend_review_history_safety_fields(),
    }
    _save_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history(
        storage,
        [
            {**base, "recorded_at": "2026-01-01T00:00:02Z"},
            {**base, "recorded_at": "2026-01-01T00:00:01Z"},
        ],
    )
    hint = build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)
    assert hint["trend"] == TREND_CHANGING
    assert hint["hint_status"] == HINT_NEEDS_REVIEW
    assert hint["trend_review_recommended"] is True


def test_trend_hint_from_status_refresh_workflow(storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_history(storage, monkeypatch, count=1)
    hint = build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)
    assert hint["history_count"] >= 1
    assert hint["hint_status"] in {HINT_READY, HINT_NEEDS_REVIEW}


def test_trend_hint_json_and_markdown_persistence(storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_history(storage, monkeypatch, count=1)
    hint = refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)
    assert storage.absolute_path(HINT_JSON).is_file()
    markdown = storage.absolute_path(hint["markdown_path"]).read_text(encoding="utf-8")
    assert "trend review acknowledgment status trend review acknowledgment status trend hints only" in markdown.lower()
    assert "Trend summary" in build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint_markdown(hint)


def test_trend_hint_blocked_when_production_enabled(storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_history(storage, monkeypatch, count=1)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", True)
    hint = build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)
    assert hint["hint_status"] == HINT_BLOCKED


def test_trend_hint_safety_invariants(storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_history(storage, monkeypatch, count=1)
    hint = refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)
    compact = compact_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)
    for payload in (hint, compact):
        assert payload["verified_mrms"] is False
        assert payload["does_not_clear_alerts"] is True
        assert payload["does_not_authorize_production_use"] is True


def test_trend_hint_does_not_clear_alerts(storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_history(storage, monkeypatch, count=1)
    save_validation_alert(storage, {"level": ALERT_FAILED, "reason": "test"})
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert["level"] == ALERT_FAILED


def test_summary_includes_trend_hint_compact(db_session, storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_history(storage, monkeypatch, count=1)
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary[
        "mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint"
    ]
    assert compact["verified_mrms"] is False
    assert compact["trend"] is not None


def test_trend_hint_get_endpoint(client, storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_history(storage, monkeypatch, count=1)
    response = client.get(
        "/api/validation/mrms-render-candidate/sandbox/import-export/"
        "comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status/trend-hint"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["compact"]["trend"] is not None


def test_trend_hint_post_endpoint(client, storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_history(storage, monkeypatch, count=1)
    response = client.post(
        "/api/validation/mrms-render-candidate/sandbox/import-export/"
        "comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status/trend-hint"
    )
    assert response.status_code == 200
    assert storage.absolute_path(HINT_JSON).is_file()


def test_trend_hint_after_acknowledgment_improves(storage, monkeypatch):
    _seed_status_trend_review_ack_status_trend_review_ack_status_history(storage, monkeypatch, count=1)
    create_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Reviewed.",
    )
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status(storage)
    hint = build_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)
    assert hint["history_count"] >= 2
