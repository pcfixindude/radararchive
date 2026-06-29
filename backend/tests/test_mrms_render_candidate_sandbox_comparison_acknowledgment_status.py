"""Tests for MRMS render candidate sandbox comparison acknowledgment status (Phase 70)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox import generate_render_candidate_sandbox
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status import (
    ACK_STATUS_BLOCKED,
    ACK_STATUS_CURRENT,
    ACK_STATUS_MISSING,
    ACK_STATUS_NONE,
    ACK_STATUS_NOT_NEEDED,
    ACK_STATUS_STALE,
    ROLLUP_CURRENT,
    ROLLUP_NEEDS_ACKNOWLEDGMENT,
    ROLLUP_NOT_NEEDED,
    ROLLUP_STALE,
    STATUS_JSON,
    build_acknowledgment_status_markdown,
    build_sandbox_comparison_acknowledgment_status,
    compact_sandbox_comparison_acknowledgment_status,
    refresh_sandbox_comparison_acknowledgment_status,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_history import (
    COMPARISON_CHANGED,
    COMPARISON_UNCHANGED,
    append_comparison_history_entry,
    build_comparison_history_entry,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_review_acknowledgment import (
    create_sandbox_comparison_review_acknowledgment,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_trend_hint import (
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


def _seed_needs_review_hint(storage, monkeypatch):
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


def test_status_missing_when_no_trend_hint(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    status = build_sandbox_comparison_acknowledgment_status(storage)
    assert status["acknowledgment_status"] == ACK_STATUS_MISSING
    assert status["verified_mrms"] is False


def test_status_not_needed_when_stable_hint(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    entry = build_comparison_history_entry(
        comparison_type="current_vs_imported",
        comparison={"changed_sandbox_status": False},
        comparison_status=COMPARISON_UNCHANGED,
        source_paths={"import_json_path": "data/dev/test.json"},
    )
    append_comparison_history_entry(storage, entry)
    refresh_sandbox_comparison_trend_hint(storage)
    status = build_sandbox_comparison_acknowledgment_status(storage)
    assert status["acknowledgment_status"] == ACK_STATUS_NOT_NEEDED
    assert status["rollup_status"] == ROLLUP_NOT_NEEDED


def test_status_none_when_review_needed_without_ack(storage, monkeypatch):
    _seed_needs_review_hint(storage, monkeypatch)
    status = build_sandbox_comparison_acknowledgment_status(storage)
    assert status["acknowledgment_status"] == ACK_STATUS_NONE
    assert status["rollup_status"] == ROLLUP_NEEDS_ACKNOWLEDGMENT
    assert status["trend_review_recommended"] is True


def test_status_current_when_ack_matches_hint(storage, monkeypatch):
    _seed_needs_review_hint(storage, monkeypatch)
    create_sandbox_comparison_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Reviewed current trend hint.",
        acknowledged_trend_review=True,
    )
    status = build_sandbox_comparison_acknowledgment_status(storage)
    assert status["acknowledgment_status"] == ACK_STATUS_CURRENT
    assert status["rollup_status"] == ROLLUP_CURRENT
    assert status["stale_acknowledgment"] is False


def test_status_stale_after_hint_refresh(storage, monkeypatch):
    _seed_needs_review_hint(storage, monkeypatch)
    create_sandbox_comparison_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Reviewed earlier hint.",
    )
    entry = build_comparison_history_entry(
        comparison_type="current_vs_imported",
        comparison={"changed_sandbox_status": True, "changed_safety_gate_summary": True},
        comparison_status=COMPARISON_CHANGED,
        source_paths={"import_json_path": "data/dev/test2.json"},
    )
    append_comparison_history_entry(storage, entry)
    refresh_sandbox_comparison_trend_hint(storage)
    status = build_sandbox_comparison_acknowledgment_status(storage)
    assert status["acknowledgment_status"] == ACK_STATUS_STALE
    assert status["rollup_status"] == ROLLUP_STALE
    assert status["stale_acknowledgment"] is True


def test_status_blocked_when_production_enabled(storage, monkeypatch):
    _seed_needs_review_hint(storage, monkeypatch)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", True)
    status = build_sandbox_comparison_acknowledgment_status(storage)
    assert status["acknowledgment_status"] == ACK_STATUS_BLOCKED


def test_status_json_and_markdown_persistence(storage, monkeypatch):
    _seed_needs_review_hint(storage, monkeypatch)
    status = refresh_sandbox_comparison_acknowledgment_status(storage)
    assert storage.absolute_path(STATUS_JSON).is_file()
    markdown = storage.absolute_path(status["markdown_path"]).read_text(encoding="utf-8")
    assert "acknowledgment status rollup" in markdown.lower()
    assert "Rollup status" in build_acknowledgment_status_markdown(status)


def test_status_safety_invariants(storage, monkeypatch):
    _seed_needs_review_hint(storage, monkeypatch)
    status = refresh_sandbox_comparison_acknowledgment_status(storage)
    compact = compact_sandbox_comparison_acknowledgment_status(storage)
    for payload in (status, compact):
        assert payload["verified_mrms"] is False
        assert payload["does_not_clear_alerts"] is True
        assert payload["does_not_authorize_production_use"] is True


def test_status_does_not_clear_alerts(storage, monkeypatch):
    _seed_needs_review_hint(storage, monkeypatch)
    save_validation_alert(storage, {"level": ALERT_FAILED, "reason": "test"})
    refresh_sandbox_comparison_acknowledgment_status(storage)
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert["level"] == ALERT_FAILED


def test_summary_includes_status_compact(db_session, storage, monkeypatch):
    _seed_needs_review_hint(storage, monkeypatch)
    refresh_sandbox_comparison_acknowledgment_status(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary["mrms_render_candidate_sandbox_comparison_acknowledgment_status"]
    assert compact["verified_mrms"] is False
    assert compact["rollup_status"] == ROLLUP_NEEDS_ACKNOWLEDGMENT


def test_status_get_endpoint(client, storage, monkeypatch):
    _seed_needs_review_hint(storage, monkeypatch)
    response = client.get(
        "/api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["compact"]["rollup_status"] is not None


def test_status_post_endpoint(client, storage, monkeypatch):
    _seed_needs_review_hint(storage, monkeypatch)
    response = client.post(
        "/api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status"
    )
    assert response.status_code == 200
    assert storage.absolute_path(STATUS_JSON).is_file()


def test_status_from_import_export_workflow(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    refresh_sandbox_comparison_trend_hint(storage)
    status = build_sandbox_comparison_acknowledgment_status(storage)
    assert status["hint_status"] is not None
    assert status["rollup_status"] is not None
