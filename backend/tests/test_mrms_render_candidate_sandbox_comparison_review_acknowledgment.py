"""Tests for MRMS render candidate sandbox comparison review acknowledgments (Phase 69)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox import generate_render_candidate_sandbox
from backend.app.services.mrms_render_candidate_sandbox_comparison_history import (
    COMPARISON_CHANGED,
    append_comparison_history_entry,
    build_comparison_history_entry,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_review_acknowledgment import (
    ACKNOWLEDGMENTS_PATH,
    SandboxComparisonReviewAcknowledgmentValidationError,
    build_sandbox_comparison_review_acknowledgments_payload,
    compact_sandbox_comparison_review_acknowledgment_summary,
    create_sandbox_comparison_review_acknowledgment,
    load_sandbox_comparison_review_acknowledgments,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_trend_hint import (
    HINT_NEEDS_REVIEW,
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


def _seed_trend_hint_needs_review(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)
    for _ in range(2):
        entry = build_comparison_history_entry(
            comparison_type="current_vs_imported",
            comparison={"changed_sandbox_status": True},
            comparison_status=COMPARISON_CHANGED,
            source_paths={"import_json_path": "data/dev/test.json"},
        )
        append_comparison_history_entry(storage, entry)
    refresh_sandbox_comparison_trend_hint(storage)


def test_acknowledgment_requires_operator_and_note(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    try:
        create_sandbox_comparison_review_acknowledgment(storage, note="reviewed")
    except SandboxComparisonReviewAcknowledgmentValidationError as exc:
        assert "operator" in str(exc).lower()
    else:
        raise AssertionError("expected validation error")


def test_acknowledgment_captures_related_trend_hint(storage, monkeypatch):
    _seed_trend_hint_needs_review(storage, monkeypatch)
    record = create_sandbox_comparison_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Reviewed sandbox comparison trend hints locally.",
        acknowledged_trend_review=True,
    )
    assert record["related_hint_status"] == HINT_NEEDS_REVIEW
    assert record["related_trend"] is not None
    assert record["acknowledged_trend_review"] is True
    assert record["verified_mrms"] is False


def test_acknowledgment_persists_to_json(storage, monkeypatch):
    _seed_trend_hint_needs_review(storage, monkeypatch)
    create_sandbox_comparison_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Local review only.",
    )
    entries = load_sandbox_comparison_review_acknowledgments(storage)
    assert len(entries) == 1
    assert storage.absolute_path(ACKNOWLEDGMENTS_PATH).is_file()


def test_acknowledgment_from_import_export_workflow(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    refresh_sandbox_comparison_trend_hint(storage)
    record = create_sandbox_comparison_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Acknowledged after import/export comparison review.",
    )
    assert record["related_trend"] is not None


def test_acknowledgment_safety_invariants(storage, monkeypatch):
    _seed_trend_hint_needs_review(storage, monkeypatch)
    create_sandbox_comparison_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Safety check.",
    )
    compact = compact_sandbox_comparison_review_acknowledgment_summary(storage)
    assert compact["verified_mrms"] is False
    assert compact["does_not_clear_alerts"] is True
    assert compact["does_not_enable_production"] is True
    assert compact["does_not_authorize_production_use"] is True


def test_acknowledgment_does_not_clear_alerts(storage, monkeypatch):
    _seed_trend_hint_needs_review(storage, monkeypatch)
    save_validation_alert(storage, {"level": ALERT_FAILED, "reason": "test"})
    create_sandbox_comparison_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Does not clear alerts.",
    )
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert["level"] == ALERT_FAILED


def test_summary_includes_acknowledgment_compact(db_session, storage, monkeypatch):
    _seed_trend_hint_needs_review(storage, monkeypatch)
    create_sandbox_comparison_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="Summary test.",
    )
    summary = build_validation_summary(db_session, storage)
    compact = summary["mrms_render_candidate_sandbox_comparison_review_acknowledgment"]
    assert compact["available"] is True
    assert compact["verified_mrms"] is False
    assert compact["count"] == 1


def test_acknowledgment_get_endpoint(client, storage, monkeypatch):
    _seed_trend_hint_needs_review(storage, monkeypatch)
    create_sandbox_comparison_review_acknowledgment(
        storage,
        operator_initials="OP",
        note="API GET test.",
    )
    response = client.get(
        "/api/validation/mrms-render-candidate/sandbox/import-export/comparison-review-acknowledgments"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["count"] == 1


def test_acknowledgment_post_endpoint(client, storage, monkeypatch):
    _seed_trend_hint_needs_review(storage, monkeypatch)
    response = client.post(
        "/api/validation/mrms-render-candidate/sandbox/import-export/comparison-review-acknowledgments",
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
        "/api/validation/mrms-render-candidate/sandbox/import-export/comparison-review-acknowledgments",
        json={"note": "missing operator"},
    )
    assert response.status_code == 422


def test_acknowledgments_payload_lists_entries(storage, monkeypatch):
    _seed_trend_hint_needs_review(storage, monkeypatch)
    create_sandbox_comparison_review_acknowledgment(
        storage,
        operator_initials="A",
        note="First.",
    )
    create_sandbox_comparison_review_acknowledgment(
        storage,
        operator_initials="B",
        note="Second.",
    )
    payload = build_sandbox_comparison_review_acknowledgments_payload(storage, limit=10)
    assert payload["count"] == 2
    assert len(payload["entries"]) == 2
