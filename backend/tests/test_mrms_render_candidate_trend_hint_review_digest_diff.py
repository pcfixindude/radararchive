"""Tests for candidate trend-hint review digest diff (Phase 86)."""

from __future__ import annotations

import json

from backend.app.config import settings
from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_IMPROVED,
    DIFF_MIXED,
    DIFF_NO_BASELINE,
    DIFF_UNCHANGED,
    DIFF_WORSENED,
)
from backend.app.services.mrms_render_candidate_trend_hint_ack_status import (
    ROLLUP_CURRENT,
    ROLLUP_NEEDS_ACKNOWLEDGMENT,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest import (
    DIGEST_BLOCKED,
    DIGEST_CURRENT,
    DIGEST_NEEDS_ATTENTION,
    refresh_trend_hint_review_digest,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest_diff import (
    DIFF_HISTORY_JSON,
    DIFF_LATEST_JSON,
    MAX_DIFF_HISTORY,
    compare_trend_hint_review_digest_entries,
    compact_trend_hint_review_digest_diff,
    load_latest_trend_hint_review_digest_diff,
    record_trend_hint_review_digest_diff,
    refresh_trend_hint_review_digest_diff,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_acknowledgment import (
    create_trend_hint_review_acknowledgment,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest_history import (
    COVERAGE_IMPROVED,
    COVERAGE_UNCHANGED,
    COVERAGE_WORSENED,
    build_trend_hint_review_digest_history_entry,
)
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary
from backend.tests.test_mrms_render_candidate_trend_hint_review_digest_history import (
    _seed_candidate_trend_hint_needs_review,
)


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def _history_entry(
    *,
    recorded_at: str,
    digest_status: str = DIGEST_CURRENT,
    rollup_status: str = ROLLUP_CURRENT,
    coverage_change: str = COVERAGE_UNCHANGED,
) -> dict:
    digest = {
        "digest_status": digest_status,
        "rollup_status": rollup_status,
        "acknowledgment_status": "current",
        "history_count": 1,
    }
    return build_trend_hint_review_digest_history_entry(digest, previous_entry=None) | {
        "recorded_at": recorded_at,
        "digest_status": digest_status,
        "rollup_status": rollup_status,
        "coverage_change": coverage_change,
    }


def test_diff_no_baseline(storage):
    current = _history_entry(recorded_at="2026-06-28T16:00:00Z")
    diff = compare_trend_hint_review_digest_entries(None, current)
    assert diff["diff_status"] == DIFF_NO_BASELINE
    assert diff["verified_mrms"] is False
    assert diff["does_not_clear_alerts"] is True


def test_diff_unchanged(storage):
    baseline = _history_entry(recorded_at="2026-06-28T16:00:00Z")
    current = _history_entry(recorded_at="2026-06-28T16:01:00Z")
    diff = compare_trend_hint_review_digest_entries(baseline, current)
    assert diff["diff_status"] == DIFF_UNCHANGED


def test_diff_worsened_digest_status(storage):
    baseline = _history_entry(recorded_at="2026-06-28T16:00:00Z", digest_status=DIGEST_CURRENT)
    current = _history_entry(recorded_at="2026-06-28T16:01:00Z", digest_status=DIGEST_BLOCKED)
    diff = compare_trend_hint_review_digest_entries(baseline, current)
    assert diff["diff_status"] == DIFF_WORSENED


def test_diff_improved_digest_status(storage):
    baseline = _history_entry(recorded_at="2026-06-28T16:00:00Z", digest_status=DIGEST_BLOCKED)
    current = _history_entry(recorded_at="2026-06-28T16:01:00Z", digest_status=DIGEST_CURRENT)
    diff = compare_trend_hint_review_digest_entries(baseline, current)
    assert diff["diff_status"] == DIFF_IMPROVED


def test_diff_mixed_signals(storage):
    baseline = _history_entry(
        recorded_at="2026-06-28T16:00:00Z",
        digest_status=DIGEST_BLOCKED,
        rollup_status=ROLLUP_CURRENT,
    )
    current = _history_entry(
        recorded_at="2026-06-28T16:01:00Z",
        digest_status=DIGEST_CURRENT,
        rollup_status=ROLLUP_NEEDS_ACKNOWLEDGMENT,
    )
    diff = compare_trend_hint_review_digest_entries(baseline, current)
    assert diff["diff_status"] == DIFF_MIXED


def test_record_on_digest_refresh(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_review_digest(storage)
    first = load_latest_trend_hint_review_digest_diff(storage)
    assert first is not None
    assert first["diff_status"] == DIFF_NO_BASELINE

    create_trend_hint_review_acknowledgment(
        storage,
        operator_name="test",
        operator_initials="TT",
        note="ack",
    )
    refresh_trend_hint_review_digest(storage)
    second = load_latest_trend_hint_review_digest_diff(storage)
    assert second is not None
    assert second["diff_status"] in {DIFF_UNCHANGED, DIFF_IMPROVED, DIFF_WORSENED, DIFF_MIXED}


def test_bounded_diff_history(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    baseline = _history_entry(recorded_at="2026-06-28T16:00:00Z")
    for index in range(MAX_DIFF_HISTORY + 5):
        current = _history_entry(recorded_at=f"2026-06-28T16:{index:02d}:01Z")
        record_trend_hint_review_digest_diff(
            storage,
            current_entry=current,
            baseline_entry=baseline,
        )
    history_path = storage.absolute_path(DIFF_HISTORY_JSON)
    history = json.loads(history_path.read_text(encoding="utf-8"))
    assert len(history) == MAX_DIFF_HISTORY


def test_compact_unavailable_when_empty(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_trend_hint_review_digest_diff(storage)
    assert compact["available"] is False
    assert compact["diff_status"] is None


def test_summary_includes_digest_diff(storage, db_session, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_review_digest(storage)
    summary = build_validation_summary(db_session, storage)
    diff = summary.get("mrms_render_candidate_trend_hint_review_digest_diff")
    assert diff is not None
    assert diff["available"] is True
    assert diff["diff_status"] == DIFF_NO_BASELINE


def test_diff_endpoint(storage, client, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_review_digest(storage)
    response = client.get(
        "/api/validation/mrms-render-candidate/sandbox/trend-hint-review-digest/diff"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["compact"]["diff_status"] == DIFF_NO_BASELINE


def test_refresh_recomputes_from_history(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_review_digest(storage)
    refresh_trend_hint_review_digest(storage)
    refreshed = refresh_trend_hint_review_digest_diff(storage)
    assert refreshed is not None
    assert refreshed["diff_status"] in {DIFF_UNCHANGED, DIFF_IMPROVED, DIFF_WORSENED, DIFF_MIXED}
    latest_path = storage.absolute_path(DIFF_LATEST_JSON)
    assert latest_path.is_file()


def test_diff_does_not_clear_alerts(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    from backend.app.services.validation_alerts import ALERT_FAILED, save_validation_alert

    save_validation_alert(storage, {"status": ALERT_FAILED, "message": "test"})
    refresh_trend_hint_review_digest(storage)
    record_trend_hint_review_digest_diff(
        storage,
        current_entry=_history_entry(recorded_at="2026-06-28T16:00:00Z", digest_status=DIGEST_NEEDS_ATTENTION),
        baseline_entry=_history_entry(recorded_at="2026-06-28T15:00:00Z"),
    )
    alert = load_validation_alert(storage)
    assert alert.get("status") == ALERT_FAILED


def test_rollup_status_change_worsened(storage):
    baseline = _history_entry(
        recorded_at="2026-06-28T16:00:00Z",
        rollup_status=ROLLUP_CURRENT,
    )
    current = _history_entry(
        recorded_at="2026-06-28T16:01:00Z",
        rollup_status=ROLLUP_NEEDS_ACKNOWLEDGMENT,
    )
    diff = compare_trend_hint_review_digest_entries(baseline, current)
    assert diff["diff_status"] == DIFF_WORSENED
