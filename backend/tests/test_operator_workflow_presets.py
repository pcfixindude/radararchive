"""Tests for operator workflow presets (Phase 52)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.operator_review_status import (
    EVIDENCE_MIXED,
    EVIDENCE_WORSENING,
    STATUS_OK,
    STATUS_WATCH,
    build_operator_review_status,
)
from backend.app.services.operator_workflow_presets import (
    EXPECTED_PRESET_IDS,
    PRESET_CREATE_REVIEW_SESSION_AND_EXPORT,
    PRESET_FULL_LOCAL_PROOF_REVIEW,
    PRESET_QUICK_STATUS_CHECK,
    PRESET_REGENERATE_DIGEST_CHECKLIST_EXPORT,
    build_operator_workflow_presets,
    build_operator_workflow_presets_payload,
    compact_operator_workflow_presets,
)
from backend.app.services.validation_dashboard import build_validation_summary


def _preset_by_id(presets: list[dict], preset_id: str) -> dict:
    for preset in presets:
        if preset.get("preset_id") == preset_id:
            return preset
    raise AssertionError(f"preset {preset_id} not found")


def test_all_expected_preset_ids_exist(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    presets = build_operator_workflow_presets(storage)
    assert {preset["preset_id"] for preset in presets} == set(EXPECTED_PRESET_IDS)


def test_preset_shape(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    preset = _preset_by_id(build_operator_workflow_presets(storage), PRESET_QUICK_STATUS_CHECK)
    for key in (
        "preset_id",
        "title",
        "description",
        "when_to_use",
        "command",
        "expected_outputs",
        "safety_notes",
        "recommended",
        "recommendation_reason",
        "verified_mrms",
        "local_workflow_only",
        "does_not_clear_alerts",
        "does_not_enable_production",
    ):
        assert key in preset
    assert preset["verified_mrms"] is False
    assert preset["does_not_clear_alerts"] is True
    assert preset["does_not_enable_production"] is True


def test_quick_status_check_preset(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    preset = _preset_by_id(build_operator_workflow_presets(storage), PRESET_QUICK_STATUS_CHECK)
    assert preset["command"] == "make operator-review-status"
    assert preset["title"] == "Quick status check"


def test_full_local_proof_review_preset(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    preset = _preset_by_id(build_operator_workflow_presets(storage), PRESET_FULL_LOCAL_PROOF_REVIEW)
    assert preset["command"] == "make scheduled-proof-bundle"


def test_create_review_session_and_export_preset(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    preset = _preset_by_id(
        build_operator_workflow_presets(storage),
        PRESET_CREATE_REVIEW_SESSION_AND_EXPORT,
    )
    assert "make mrms-review-session" in preset["command"]
    assert "--export-after-create" in preset["command"]


def test_regenerate_digest_preset(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    preset = _preset_by_id(
        build_operator_workflow_presets(storage),
        PRESET_REGENERATE_DIGEST_CHECKLIST_EXPORT,
    )
    assert preset["command"] == "make scheduled-proof-bundle-review-export"


def test_recommendation_quick_status_when_ok_or_watch(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    status = build_operator_review_status(storage)
    status["status_level"] = STATUS_OK
    presets = build_operator_workflow_presets(storage, status=status)
    quick = _preset_by_id(presets, PRESET_QUICK_STATUS_CHECK)
    assert quick["recommended"] is True
    assert quick["recommendation_reason"] == "operator_review_status_ok_or_watch"


def test_recommendation_digest_stale(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    status = build_operator_review_status(storage)
    status["digest_regeneration_recommended"] = True
    presets = build_operator_workflow_presets(storage, status=status)
    regen = _preset_by_id(presets, PRESET_REGENERATE_DIGEST_CHECKLIST_EXPORT)
    assert regen["recommended"] is True
    assert regen["recommendation_reason"] == "digest_or_checklist_stale"


def test_recommendation_no_review_session(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    status = build_operator_review_status(storage)
    status["latest_review_session_at"] = None
    status["review_session_recommended"] = True
    presets = build_operator_workflow_presets(storage, status=status)
    session = _preset_by_id(presets, PRESET_CREATE_REVIEW_SESSION_AND_EXPORT)
    assert session["recommended"] is True
    assert session["recommendation_reason"] == "no_review_session"


def test_recommendation_worsening_mixed_trend(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    for trend in (EVIDENCE_WORSENING, EVIDENCE_MIXED):
        status = build_operator_review_status(storage)
        status["latest_review_session_at"] = "2026-01-01T00:00:00Z"
        status["evidence_trend"] = trend
        presets = build_operator_workflow_presets(storage, status=status)
        session = _preset_by_id(presets, PRESET_CREATE_REVIEW_SESSION_AND_EXPORT)
        assert session["recommended"] is True
        assert session["recommendation_reason"] == "export_diff_trend_worsening_or_mixed"


def test_recommended_presets_sorted_first(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    status = build_operator_review_status(storage)
    status["status_level"] = STATUS_WATCH
    presets = build_operator_workflow_presets(storage, status=status)
    recommended = [preset for preset in presets if preset["recommended"]]
    assert presets[: len(recommended)] == recommended


def test_summary_includes_operator_workflow_presets(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("operator_workflow_presets")
    assert compact is not None
    assert compact["available"] is True
    assert len(compact.get("presets") or []) == len(EXPECTED_PRESET_IDS)
    assert compact["verified_mrms"] is False


def test_endpoint_returns_safe_preset_list_when_files_missing(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    response = client.get("/api/validation/operator-workflow-presets")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["does_not_clear_alerts"] is True
    assert len(body.get("presets") or []) == len(EXPECTED_PRESET_IDS)
    for preset in body["presets"]:
        assert preset["verified_mrms"] is False
        assert preset["does_not_clear_alerts"] is True


def test_presets_do_not_mutate_production_gates(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    before = settings.enable_production_radar_tiles
    compact_operator_workflow_presets(storage)
    build_operator_workflow_presets_payload(storage)
    assert settings.enable_production_radar_tiles == before


def test_payload_recommended_presets_subset(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", storage.storage_root)
    payload = build_operator_workflow_presets_payload(storage)
    recommended = payload.get("recommended_presets") or []
    assert all(item.get("recommended") for item in recommended)
    assert payload["recommended_count"] == len(recommended)
