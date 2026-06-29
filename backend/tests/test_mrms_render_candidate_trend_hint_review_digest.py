"""Tests for candidate trend-hint review chain digest (Phase 84)."""

from __future__ import annotations

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
    refresh_trend_hint_ack_status,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest import (
    DIGEST_BLOCKED,
    DIGEST_CURRENT,
    DIGEST_MISSING,
    DIGEST_NEEDS_ATTENTION,
    DIGEST_STABLE,
    DIGEST_JSON,
    DIGEST_MD,
    build_trend_hint_review_digest,
    build_trend_hint_review_digest_markdown,
    compact_trend_hint_review_digest,
    refresh_trend_hint_review_digest,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_acknowledgment import (
    create_trend_hint_review_acknowledgment,
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


def test_digest_missing_when_no_history(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    digest = build_trend_hint_review_digest(storage)
    assert digest["digest_status"] == DIGEST_MISSING
    assert digest["verified_mrms"] is False


def test_digest_needs_attention_when_review_needed(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    digest = build_trend_hint_review_digest(storage)
    assert digest["digest_status"] == DIGEST_NEEDS_ATTENTION
    assert digest["rollup_status"] == ROLLUP_NEEDS_ACKNOWLEDGMENT
    assert digest["history_count"] == 1


def test_digest_current_when_ack_matches(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    create_trend_hint_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Reviewed current candidate trend hint.",
        acknowledged_trend_review=True,
    )
    refresh_trend_hint_ack_status(storage)
    digest = build_trend_hint_review_digest(storage)
    assert digest["digest_status"] == DIGEST_CURRENT
    assert digest["rollup_status"] == ROLLUP_CURRENT


def test_digest_stable_when_not_needed(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status import (
        ROLLUP_CURRENT as STATUS_ROLLUP_CURRENT,
        ROLLUP_NOT_NEEDED,
    )
    from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history import (
        COVERAGE_UNCHANGED,
        _save_ack_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history,
        _safety_fields as trend_review_history_safety_fields,
    )

    trend_base = {
        "rollup_status": STATUS_ROLLUP_CURRENT,
        "acknowledgment_status": "current",
        "coverage_change": COVERAGE_UNCHANGED,
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
    digest = build_trend_hint_review_digest(storage)
    assert digest["digest_status"] == DIGEST_STABLE
    assert digest["rollup_status"] == ROLLUP_NOT_NEEDED


def test_digest_blocked_when_production_enabled(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", True)
    digest = build_trend_hint_review_digest(storage)
    assert digest["digest_status"] == DIGEST_BLOCKED


def test_digest_json_and_markdown_persistence(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    digest = refresh_trend_hint_review_digest(storage)
    assert storage.absolute_path(DIGEST_JSON).is_file()
    markdown = storage.absolute_path(DIGEST_MD).read_text(encoding="utf-8")
    assert "review chain digest" in markdown.lower()
    assert "Digest status" in build_trend_hint_review_digest_markdown(digest)


def test_digest_safety_invariants(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    digest = refresh_trend_hint_review_digest(storage)
    compact = compact_trend_hint_review_digest(storage)
    for payload in (digest, compact):
        assert payload["verified_mrms"] is False
        assert payload["does_not_clear_alerts"] is True
        assert payload["does_not_authorize_production_use"] is True


def test_digest_does_not_clear_alerts(storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    save_validation_alert(storage, {"level": ALERT_FAILED, "reason": "test"})
    refresh_trend_hint_review_digest(storage)
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert["level"] == ALERT_FAILED


def test_summary_includes_digest_compact(db_session, storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    refresh_trend_hint_review_digest(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary["mrms_render_candidate_trend_hint_review_digest"]
    assert compact["verified_mrms"] is False
    assert compact["digest_status"] == DIGEST_NEEDS_ATTENTION


def test_digest_get_endpoint(client, storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    response = client.get("/api/validation/mrms-render-candidate/sandbox/trend-hint-review-digest")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["compact"]["digest_status"] is not None


def test_digest_post_endpoint(client, storage, monkeypatch):
    _seed_candidate_trend_hint_needs_review(storage, monkeypatch)
    refresh_trend_hint_ack_status(storage)
    response = client.post("/api/validation/mrms-render-candidate/sandbox/trend-hint-review-digest")
    assert response.status_code == 200
    assert storage.absolute_path(DIGEST_JSON).is_file()
