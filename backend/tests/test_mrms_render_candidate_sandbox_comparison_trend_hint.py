"""Tests for MRMS render candidate sandbox comparison trend hints (Phase 68)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox import generate_render_candidate_sandbox
from backend.app.services.mrms_render_candidate_sandbox_comparison_history import (
    COMPARISON_CHANGED,
    COMPARISON_UNCHANGED,
    append_comparison_history_entry,
    build_comparison_history_entry,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_trend_hint import (
    HINT_BLOCKED,
    HINT_JSON,
    HINT_MD,
    HINT_MISSING,
    HINT_NEEDS_REVIEW,
    HINT_READY,
    TREND_CHANGING,
    TREND_NO_DATA,
    TREND_STABLE,
    build_sandbox_comparison_trend_hint,
    build_trend_hint_markdown,
    compact_sandbox_comparison_trend_hint,
    refresh_sandbox_comparison_trend_hint,
)
from backend.app.services.mrms_render_candidate_sandbox_import_export import (
    export_candidate_sandbox_manifest,
    import_candidate_sandbox_manifest,
)
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def _seed_sandbox(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)


def test_trend_hint_no_data_when_history_empty(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    hint = build_sandbox_comparison_trend_hint(storage)
    assert hint["trend"] == TREND_NO_DATA
    assert hint["hint_status"] == HINT_MISSING
    assert hint["verified_mrms"] is False


def test_trend_hint_stable_when_unchanged_history(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    for _ in range(3):
        entry = build_comparison_history_entry(
            comparison_type="current_vs_imported",
            comparison={"changed_sandbox_status": False},
            comparison_status=COMPARISON_UNCHANGED,
            source_paths={"import_json_path": "data/dev/test.json"},
        )
        append_comparison_history_entry(storage, entry)
    hint = build_sandbox_comparison_trend_hint(storage)
    assert hint["trend"] == TREND_STABLE
    assert hint["hint_status"] == HINT_READY
    assert hint["trend_review_recommended"] is False


def test_trend_hint_needs_review_on_changed_streak(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    for _ in range(2):
        entry = build_comparison_history_entry(
            comparison_type="current_vs_imported",
            comparison={"changed_sandbox_status": True, "changed_safety_gate_summary": True},
            comparison_status=COMPARISON_CHANGED,
            source_paths={"import_json_path": "data/dev/test.json"},
        )
        append_comparison_history_entry(storage, entry)
    hint = build_sandbox_comparison_trend_hint(storage)
    assert hint["trend"] == TREND_CHANGING
    assert hint["hint_status"] == HINT_NEEDS_REVIEW
    assert hint["trend_review_recommended"] is True
    assert hint["current_changed_streak"] >= 2


def test_trend_hint_from_import_export_workflow(storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    hint = build_sandbox_comparison_trend_hint(storage)
    assert hint["history_count"] >= 1
    assert hint["hint_status"] in {HINT_READY, HINT_NEEDS_REVIEW}


def test_trend_hint_json_and_markdown_persistence(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    entry = build_comparison_history_entry(
        comparison_type="current_vs_imported",
        comparison={"changed_sandbox_status": False},
        comparison_status=COMPARISON_UNCHANGED,
        source_paths={"import_json_path": "data/dev/test.json"},
    )
    append_comparison_history_entry(storage, entry)
    hint = refresh_sandbox_comparison_trend_hint(storage)
    assert storage.absolute_path(HINT_JSON).is_file()
    assert storage.absolute_path(HINT_MD).is_file()
    markdown = storage.absolute_path(HINT_MD).read_text(encoding="utf-8")
    assert "trend hints only" in markdown.lower()
    assert hint["json_path"] == storage.normalize_path(HINT_JSON)


def test_trend_hint_markdown_contains_sections(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    hint = build_sandbox_comparison_trend_hint(storage)
    markdown = build_trend_hint_markdown(hint)
    assert "Trend summary" in markdown
    assert "Recurring signals" in markdown


def test_trend_hint_blocked_when_production_enabled(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    entry = build_comparison_history_entry(
        comparison_type="current_vs_imported",
        comparison={"changed_sandbox_status": False},
        comparison_status=COMPARISON_UNCHANGED,
        source_paths={"import_json_path": "data/dev/test.json"},
    )
    append_comparison_history_entry(storage, entry)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", True)
    hint = build_sandbox_comparison_trend_hint(storage)
    assert hint["hint_status"] == HINT_BLOCKED


def test_trend_hint_safety_invariants(storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    hint = refresh_sandbox_comparison_trend_hint(storage)
    compact = compact_sandbox_comparison_trend_hint(storage)
    for payload in (hint, compact):
        assert payload["verified_mrms"] is False
        assert payload["does_not_enable_production"] is True
        assert payload["does_not_clear_alerts"] is True
        assert payload["does_not_authorize_production_use"] is True


def test_trend_hint_does_not_clear_alerts(storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    save_validation_alert(storage, {"level": ALERT_FAILED, "reason": "test"})
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    refresh_sandbox_comparison_trend_hint(storage)
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert["level"] == ALERT_FAILED


def test_summary_includes_trend_hint_compact(db_session, storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    refresh_sandbox_comparison_trend_hint(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary["mrms_render_candidate_sandbox_comparison_trend_hint"]
    assert compact["verified_mrms"] is False
    assert compact["trend"] is not None


def test_trend_hint_get_endpoint(client, storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    response = client.get(
        "/api/validation/mrms-render-candidate/sandbox/import-export/comparison-trend-hint"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["compact"]["trend"] is not None


def test_trend_hint_post_endpoint(client, storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    response = client.post(
        "/api/validation/mrms-render-candidate/sandbox/import-export/comparison-trend-hint"
    )
    assert response.status_code == 200
    assert storage.absolute_path(HINT_JSON).is_file()
