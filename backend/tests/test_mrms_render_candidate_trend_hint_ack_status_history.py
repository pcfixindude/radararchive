"""Tests for candidate trend-hint acknowledgment status history (Phase 83)."""

from __future__ import annotations

import json

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status import (
    ROLLUP_NEEDS_ACKNOWLEDGMENT,
    refresh_sandbox_comparison_acknowledgment_status,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_history import (
    COVERAGE_WORSENED,
    _save_ack_status_history,
    _safety_fields as history_safety_fields,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint import (
    refresh_ack_status_trend_hint,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint import (
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint,
)
from backend.app.services.mrms_render_candidate_trend_hint_ack_status import (
    ROLLUP_CURRENT,
    ROLLUP_NOT_NEEDED,
    refresh_trend_hint_ack_status,
)
from backend.app.services.mrms_render_candidate_trend_hint_ack_status_history import (
    COVERAGE_IMPROVED,
    COVERAGE_NO_BASELINE,
    COVERAGE_UNCHANGED,
    HISTORY_JSON,
    HISTORY_MD,
    MAX_HISTORY_ENTRIES,
    append_trend_hint_ack_status_history_entry,
    build_trend_hint_ack_status_history_entry,
    compact_trend_hint_ack_status_history,
    load_trend_hint_ack_status_history,
    refresh_trend_hint_ack_status_history_report,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_acknowledgment import (
    create_trend_hint_review_acknowledgment,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_history import (
    COMPARISON_CHANGED,
    COMPARISON_UNCHANGED,
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


def _seed_candidate_trend_hint_needs_review(storage, monkeypatch):
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
    _save_ack_status_history(
        storage,
        [
            {**base, "recorded_at": "2026-01-01T00:00:02Z"},
            {**base, "recorded_at": "2026-01-01T00:00:01Z"},
        ],
    )
    refresh_ack_status_trend_hint(storage)
    from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history import (
        _save_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history,
        _safety_fields as trend_review_history_safety_fields,
    )

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


def test_history_empty_when_no_refresh(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    history = load_trend_hint_ack_status_history(storage)
    compact = compact_trend_hint_ack_status_history(storage)
    assert history == []
    assert compact["available"] is False
    assert compact["history_count"] == 0


def test_status_refresh_appends_history_entry(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    history = load_trend_hint_ack_status_history(storage)
    assert len(history) == 1
    assert history[0]["rollup_status"] == ROLLUP_NEEDS_ACKNOWLEDGMENT
    assert history[0]["coverage_change"] == COVERAGE_NO_BASELINE
    assert history[0]["verified_mrms"] is False


def test_status_refresh_appends_multiple_entries(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    create_trend_hint_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Reviewed current candidate trend hint.",
        acknowledged_trend_review=True,
    )
    refresh_trend_hint_ack_status(storage)
    history = load_trend_hint_ack_status_history(storage)
    assert len(history) == 2
    assert history[0]["rollup_status"] == ROLLUP_CURRENT
    assert history[0]["coverage_change"] == COVERAGE_IMPROVED
    assert history[1]["rollup_status"] == ROLLUP_NEEDS_ACKNOWLEDGMENT


def test_coverage_change_unchanged_when_rollup_same(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status import (
        refresh_ack_status_trend_review_acknowledgment_status,
    )
    from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status import (
        ROLLUP_CURRENT as STATUS_ROLLUP_CURRENT,
    )
    from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history import (
        COVERAGE_UNCHANGED as TREND_REVIEW_COVERAGE_UNCHANGED,
        _save_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history,
        _safety_fields as trend_review_history_safety_fields,
    )

    entry = build_comparison_history_entry(
        comparison_type="current_vs_imported",
        comparison={"changed_sandbox_status": False},
        comparison_status=COMPARISON_UNCHANGED,
        source_paths={"import_json_path": "data/dev/test.json"},
    )
    append_comparison_history_entry(storage, entry)
    refresh_sandbox_comparison_trend_hint(storage)
    refresh_sandbox_comparison_acknowledgment_status(storage)
    refresh_ack_status_trend_hint(storage)
    refresh_ack_status_trend_review_acknowledgment_status(storage)
    trend_base = {
        "rollup_status": STATUS_ROLLUP_CURRENT,
        "acknowledgment_status": "current",
        "coverage_change": TREND_REVIEW_COVERAGE_UNCHANGED,
        "stale_acknowledgment": False,
        **trend_review_history_safety_fields(),
    }
    _save_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history(
        storage,
        [
            {**trend_base, "recorded_at": "2026-01-01T00:00:03Z"},
            {**trend_base, "recorded_at": "2026-01-01T00:00:02Z"},
            {**trend_base, "recorded_at": "2026-01-01T00:00:01Z"},
        ],
    )
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)
    refresh_trend_hint_ack_status(storage)
    refresh_trend_hint_ack_status(storage)
    history = load_trend_hint_ack_status_history(storage)
    assert history[0]["coverage_change"] == COVERAGE_UNCHANGED
    assert history[1]["coverage_change"] == COVERAGE_NO_BASELINE


def test_coverage_change_worsened(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    create_trend_hint_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Acknowledged earlier hint.",
        acknowledged_trend_review=True,
    )
    refresh_trend_hint_ack_status(storage)
    from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history import (
        _save_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history,
        _safety_fields as trend_review_history_safety_fields,
    )

    trend_base = {
        "rollup_status": ROLLUP_NEEDS_ACKNOWLEDGMENT,
        "acknowledgment_status": "none",
        "coverage_change": COVERAGE_WORSENED,
        "stale_acknowledgment": True,
        **trend_review_history_safety_fields(),
    }
    _save_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history(
        storage,
        [
            {**trend_base, "recorded_at": "2026-01-02T00:00:03Z"},
            {**trend_base, "recorded_at": "2026-01-02T00:00:02Z"},
            {**trend_base, "recorded_at": "2026-01-01T00:00:01Z"},
        ],
    )
    refresh_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint(storage)
    refresh_trend_hint_ack_status(storage)
    history = load_trend_hint_ack_status_history(storage)
    assert history[0]["coverage_change"] == COVERAGE_WORSENED


def test_history_bounded_to_max_entries(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    for index in range(MAX_HISTORY_ENTRIES + 5):
        status = {
            "generated_at": f"2026-06-27T12:{index:02d}:00Z",
            "rollup_status": ROLLUP_NOT_NEEDED,
            "acknowledgment_status": "not_needed",
            "schema_version": "1",
        }
        append_trend_hint_ack_status_history_entry(storage, status)
    history = load_trend_hint_ack_status_history(storage, limit=MAX_HISTORY_ENTRIES + 10)
    assert len(history) == MAX_HISTORY_ENTRIES


def test_history_json_and_markdown_persistence(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    assert storage.absolute_path(HISTORY_JSON).is_file()
    refresh_trend_hint_ack_status_history_report(storage)
    assert storage.absolute_path(HISTORY_MD).is_file()
    markdown = storage.absolute_path(HISTORY_MD).read_text(encoding="utf-8")
    assert "trend-hint acknowledgment status history" in markdown.lower()


def test_history_safety_invariants(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    compact = compact_trend_hint_ack_status_history(storage)
    entry = load_trend_hint_ack_status_history(storage)[0]
    for payload in (compact, entry):
        assert payload["verified_mrms"] is False
        assert payload["does_not_clear_alerts"] is True
        assert payload["does_not_authorize_production_use"] is True


def test_history_does_not_clear_alerts(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    save_validation_alert(storage, {"level": ALERT_FAILED, "reason": "test"})
    refresh_trend_hint_ack_status(storage)
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert["level"] == ALERT_FAILED


def test_summary_includes_history_compact(db_session, storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary["mrms_render_candidate_trend_hint_ack_status_history"]
    assert compact["verified_mrms"] is False
    assert compact["history_count"] == 1


def test_history_get_endpoint(client, storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    response = client.get("/api/validation/mrms-render-candidate/sandbox/trend-hint-ack-status/history")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["count"] == 1


def test_history_post_endpoint(client, storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    response = client.post("/api/validation/mrms-render-candidate/sandbox/trend-hint-ack-status/history")
    assert response.status_code == 200
    assert storage.absolute_path(HISTORY_MD).is_file()


def test_build_entry_includes_change_fields(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    previous = build_trend_hint_ack_status_history_entry(
        {"rollup_status": ROLLUP_NEEDS_ACKNOWLEDGMENT, "acknowledgment_status": "none"},
        previous_entry=None,
    )
    latest = build_trend_hint_ack_status_history_entry(
        {
            "rollup_status": ROLLUP_CURRENT,
            "acknowledgment_status": "current",
            "generated_at": "2026-06-27T12:00:00Z",
        },
        previous_entry=previous,
    )
    assert latest["rollup_status_change"]["baseline"] == ROLLUP_NEEDS_ACKNOWLEDGMENT
    assert latest["rollup_status_change"]["latest"] == ROLLUP_CURRENT
    assert latest["coverage_change"] == COVERAGE_IMPROVED
    serialized = json.dumps(latest)
    assert "rollup_status_change" in serialized
