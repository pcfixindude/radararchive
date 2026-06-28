"""Tests for consolidated operator review status (Phase 49)."""

from __future__ import annotations

import json

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_IMPROVED,
    DIFF_MIXED,
    DIFF_UNCHANGED,
    DIFF_WORSENED,
)
from backend.app.services.mrms_review_session import create_review_session_record
from backend.app.services.mrms_review_session_export import (
    SUGGESTED_EXPORT_COMMAND,
    export_latest_review_session,
)
from backend.app.services.mrms_review_session_export_diff import (
    EXPORT_DIFF_HISTORY_PATH,
    EXPORT_DIFF_LATEST_PATH,
    record_export_diff_metadata,
)
from backend.app.services.operator_review_status import (
    SUGGESTED_ATTENTION_SESSION_COMMAND,
    SUGGESTED_INITIAL_SESSION_COMMAND,
    SUGGESTED_SCHEDULED_REVIEW_EXPORT_COMMAND,
    STATUS_ATTENTION,
    STATUS_OK,
    STATUS_UNKNOWN,
    STATUS_URGENT,
    STATUS_WATCH,
    build_operator_review_status,
    compact_operator_review_status,
)
from backend.app.services.proof_bundle_diff_alert_history import record_proof_bundle_diff_alert_history
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import (
    ALERT_FAILED,
    load_validation_alert,
    save_validation_alert,
)
from backend.app.services.validation_dashboard import build_validation_summary


def _diff_entry(*, compared_at: str, status: str) -> dict:
    return {
        "compared_at": compared_at,
        "latest_export_created_at": compared_at,
        "baseline_export_created_at": "2026-06-28T15:00:00Z",
        "overall_export_diff_status": status,
        "session_changed": status != DIFF_UNCHANGED,
        "verified_mrms": False,
        "local_export_diff_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def _seed_diff_history(storage: LocalStorage, statuses: list[str]) -> None:
    total = len(statuses)
    entries = [
        _diff_entry(
            compared_at=f"2026-06-28T16:{total - 1 - index:02d}:00Z",
            status=status,
        )
        for index, status in enumerate(statuses)
    ]
    repo_path = storage.normalize_path(EXPORT_DIFF_HISTORY_PATH)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(json.dumps(entries, indent=2), encoding="utf-8")
    if entries:
        latest_repo = storage.normalize_path(EXPORT_DIFF_LATEST_PATH)
        storage.absolute_path(latest_repo).write_text(json.dumps(entries[0], indent=2), encoding="utf-8")


def _fake_diff_report(*, status: str, bundle_id: str, checked_at: str) -> dict:
    return {
        "overall_diff_status": status,
        "checked_at": checked_at,
        "evidence_changes_count": 1,
        "current_bundle": {"bundle_id": bundle_id},
        "baseline_bundle": {"bundle_id": "base"},
        "verified_mrms": False,
    }


def test_operator_review_status_shape(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    status = build_operator_review_status(storage)
    for key in (
        "created_at",
        "status_level",
        "status_reason",
        "top_recommended_action",
        "top_suggested_command",
        "review_session_recommended",
        "review_export_recommended",
        "digest_regeneration_recommended",
        "evidence_trend",
        "active_guidance_count",
        "verified_mrms",
        "local_status_only",
        "does_not_clear_alerts",
        "does_not_enable_production",
    ):
        assert key in status
    assert status["verified_mrms"] is False
    assert status["local_status_only"] is True
    assert status["does_not_clear_alerts"] is True
    assert status["does_not_enable_production"] is True


def test_no_data_unknown_behavior(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    status = build_operator_review_status(storage)
    assert status["status_level"] == STATUS_UNKNOWN
    assert status["evidence_trend"] in ("no_data", "unknown")
    assert status["review_session_recommended"] is True
    assert status["top_suggested_command"] == SUGGESTED_INITIAL_SESSION_COMMAND


def test_ok_behavior(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record = create_review_session_record(
        storage,
        operator_initials="OK",
        session_notes="stable review",
        accepted_limitations=True,
    )
    export_latest_review_session(storage, session=record)
    _seed_diff_history(storage, [DIFF_IMPROVED, DIFF_UNCHANGED])
    record_export_diff_metadata(
        storage,
        _diff_entry(compared_at="2026-06-28T16:10:00Z", status=DIFF_IMPROVED),
        baseline_history_entry=_diff_entry(
            compared_at="2026-06-28T16:09:00Z", status=DIFF_UNCHANGED
        ),
    )
    status = build_operator_review_status(storage)
    assert status["status_level"] == STATUS_OK
    assert status["evidence_trend"] == "improving"
    assert status["review_session_recommended"] is False
    assert status["review_export_recommended"] is False
    assert status["digest_regeneration_recommended"] is False


def test_watch_behavior(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record = create_review_session_record(
        storage,
        operator_initials="WT",
        session_notes="watch",
        accepted_limitations=True,
    )
    export_latest_review_session(storage, session=record)
    record_proof_bundle_diff_alert_history(
        storage,
        _fake_diff_report(
            status=DIFF_WORSENED,
            bundle_id="b1",
            checked_at="2026-06-28T16:10:00Z",
        ),
        skip_duplicate=False,
    )
    record_proof_bundle_diff_alert_history(
        storage,
        _fake_diff_report(
            status=DIFF_UNCHANGED,
            bundle_id="b0",
            checked_at="2026-06-28T16:09:00Z",
        ),
        skip_duplicate=False,
    )
    _seed_diff_history(storage, [DIFF_UNCHANGED, DIFF_UNCHANGED])
    status = build_operator_review_status(storage)
    assert status["status_level"] == STATUS_WATCH


def test_attention_behavior(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record = create_review_session_record(
        storage,
        operator_initials="AT",
        session_notes="attention",
        accepted_limitations=True,
    )
    export_latest_review_session(storage, session=record)
    _seed_diff_history(storage, [DIFF_UNCHANGED, DIFF_UNCHANGED])
    latest_repo = storage.normalize_path(EXPORT_DIFF_LATEST_PATH)
    latest = json.loads(storage.absolute_path(latest_repo).read_text(encoding="utf-8"))
    latest["overall_export_diff_status"] = DIFF_MIXED
    storage.absolute_path(latest_repo).write_text(json.dumps(latest, indent=2), encoding="utf-8")
    status = build_operator_review_status(storage)
    assert status["status_level"] == STATUS_ATTENTION
    assert status["status_reason"] == "latest_export_diff_mixed"


def test_urgent_behavior(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_validation_alert(
        storage,
        {
            "status": ALERT_FAILED,
            "updated_at": "2026-06-28T16:00:00Z",
            "latest_run_at": "2026-06-28T16:00:00Z",
            "failure_count": 2,
            "warning_count": 0,
            "operator_attention_needed": True,
            "verified_mrms": False,
        },
    )
    status = build_operator_review_status(storage)
    assert status["status_level"] == STATUS_URGENT
    assert status["status_reason"] == "validation_alert_failed"


def test_urgent_worsening_streak(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_WORSENED, DIFF_WORSENED, DIFF_UNCHANGED])
    status = build_operator_review_status(storage)
    assert status["status_level"] == STATUS_URGENT
    assert status["status_reason"] == "export_diff_trend_worsening_streak"


def test_digest_regeneration_maps_to_scheduled_command(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="DG",
        session_notes="digest test",
        accepted_limitations=True,
    )

    def _digest_hint(_storage):
        return {
            "digest_regeneration_recommended": True,
            "reason": "test_digest_stale",
            "latest_digest_at": None,
            "verified_mrms": False,
        }

    monkeypatch.setattr(
        "backend.app.services.operator_review_status.build_digest_regeneration_hint",
        _digest_hint,
    )
    status = build_operator_review_status(storage)
    assert status["digest_regeneration_recommended"] is True
    assert status["top_suggested_command"] == SUGGESTED_SCHEDULED_REVIEW_EXPORT_COMMAND


def test_stale_export_maps_to_export_command(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_UNCHANGED, DIFF_UNCHANGED])
    first = create_review_session_record(
        storage,
        operator_initials="OLD",
        session_notes="older",
        accepted_limitations=True,
    )
    export_latest_review_session(storage, session=first)
    create_review_session_record(
        storage,
        operator_initials="NEW",
        session_notes="newer",
        accepted_limitations=True,
    )
    status = build_operator_review_status(storage)
    assert status["review_export_recommended"] is True
    assert status["top_suggested_command"] == SUGGESTED_EXPORT_COMMAND


def test_no_review_session_maps_to_create_session_command(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_WORSENED, DIFF_WORSENED])
    status = build_operator_review_status(storage)
    assert status["review_session_recommended"] is True
    assert status["top_suggested_command"] == SUGGESTED_INITIAL_SESSION_COMMAND


def test_trend_session_recommendation_maps_to_attention_session_command(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record = create_review_session_record(
        storage,
        operator_initials="TR",
        session_notes="trend",
        accepted_limitations=True,
    )
    export_latest_review_session(storage, session=record)
    _seed_diff_history(storage, [DIFF_WORSENED, DIFF_WORSENED, DIFF_UNCHANGED])
    status = build_operator_review_status(storage)
    assert status["review_session_recommended"] is True
    assert status["top_suggested_command"] == SUGGESTED_ATTENTION_SESSION_COMMAND


def test_summary_includes_operator_review_status(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("operator_review_status")
    assert compact is not None
    assert compact["verified_mrms"] is False
    assert compact["local_status_only"] is True


def test_endpoint_returns_safe_status_when_files_missing(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/operator-review-status")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["local_status_only"] is True
    assert body["does_not_clear_alerts"] is True
    assert body["does_not_enable_production"] is True
    assert body["status"]["status_level"] == STATUS_UNKNOWN


def test_status_does_not_clear_alerts(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_validation_alert(
        storage,
        {
            "status": ALERT_FAILED,
            "updated_at": "2026-06-28T16:00:00Z",
            "latest_run_at": "2026-06-28T16:00:00Z",
            "failure_count": 1,
            "warning_count": 0,
            "operator_attention_needed": True,
            "verified_mrms": False,
        },
    )
    before = load_validation_alert(storage)
    compact_operator_review_status(storage)
    after = load_validation_alert(storage)
    assert after is not None
    assert after.get("status") == before.get("status")
    assert after.get("operator_attention_needed") == before.get("operator_attention_needed")


def test_status_does_not_mutate_production_gates(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    radar = RadarFile(
        product_id="mrms",
        timestamp="2026-06-28T12:00:00Z",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
    )
    db_session.add(radar)
    db_session.commit()
    compact_operator_review_status(storage)
    assert settings.enable_production_radar_tiles is False
    summary = build_validation_summary(db_session, storage)
    assert summary["verified_mrms"] is False
    assert summary["catalog"]["verified_mrms"] is False


def test_production_tile_serving_still_gated_phase49(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    radar = RadarFile(
        product_id="mrms",
        timestamp="2026-06-28T12:00:00Z",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
    )
    db_session.add(radar)
    db_session.commit()
    response = client.get("/api/tiles/mrms/2026-06-28T12:00:00Z/0/0/0.png")
    assert response.status_code in (404, 503)
    status_response = client.get("/api/validation/operator-review-status")
    assert status_response.status_code == 200
    assert status_response.json()["does_not_enable_production"] is True
