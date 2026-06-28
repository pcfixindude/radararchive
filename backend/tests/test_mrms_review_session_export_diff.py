"""Tests for review session export diff and auto-export-after-create (Phase 45)."""

from __future__ import annotations

import json

import pytest

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_IMPROVED,
    DIFF_MIXED,
    DIFF_NO_BASELINE,
    DIFF_UNCHANGED,
    DIFF_WORSENED,
)
from backend.app.services.mrms_review_session import create_review_session_record
from backend.app.services.mrms_review_session_export import (
    build_export_history_entry,
    export_latest_review_session,
    try_export_after_review_session_create,
)
from backend.app.services.mrms_review_session_export_diff import (
    EXPORT_DIFF_HISTORY_PATH,
    EXPORT_DIFF_LATEST_PATH,
    MAX_EXPORT_DIFF_HISTORY,
    build_review_session_export_diff_payload,
    compare_export_metadata,
    record_export_diff_metadata,
)
from backend.app.services.proof_bundle_diff_escalation import (
    ESCALATION_ATTENTION,
    ESCALATION_NONE,
    ESCALATION_URGENT,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _export_metadata(
    *,
    created_at: str,
    session_id: str = "sess-1",
    open_attention_count: int = 0,
    comparison_status: str = DIFF_UNCHANGED,
    escalation_level: str = ESCALATION_NONE,
    digest_regeneration_recommended: bool = False,
    proof_bundle_diff_status: str = DIFF_UNCHANGED,
    acknowledgment_id: str | None = None,
    export_path: str = "data/dev/mrms_review_session_export_latest.md",
) -> dict:
    return {
        "created_at": created_at,
        "export_path": export_path,
        "metadata_path": "data/dev/mrms_review_session_export_latest.json",
        "session_id": session_id,
        "operator": "OP",
        "comparison_status": comparison_status,
        "open_attention_count": open_attention_count,
        "escalation_level": escalation_level,
        "digest_regeneration_recommended": digest_regeneration_recommended,
        "proof_bundle_diff_status": proof_bundle_diff_status,
        "acknowledgment_id": acknowledgment_id,
        "verified_mrms": False,
        "local_export_only": True,
    }


def test_export_diff_metadata_shape(storage):
    entry = build_export_history_entry(_export_metadata(created_at="2026-06-28T16:00:00Z"))
    diff = compare_export_metadata(entry, entry)
    assert diff["latest_export_created_at"] == "2026-06-28T16:00:00Z"
    assert diff["overall_export_diff_status"] == DIFF_UNCHANGED
    assert diff["verified_mrms"] is False
    assert diff["local_export_diff_only"] is True
    assert diff["does_not_clear_alerts"] is True
    assert diff["does_not_enable_production"] is True
    assert "improvements" in diff
    assert "regressions" in diff
    assert "unchanged_items" in diff


def test_export_diff_no_baseline(storage):
    current = build_export_history_entry(_export_metadata(created_at="2026-06-28T16:00:00Z"))
    diff = compare_export_metadata(None, current)
    assert diff["overall_export_diff_status"] == DIFF_NO_BASELINE
    assert diff["baseline_export_created_at"] is None
    assert diff["verified_mrms"] is False


def test_export_diff_unchanged(storage):
    baseline = build_export_history_entry(_export_metadata(created_at="2026-06-28T16:00:00Z"))
    current = build_export_history_entry(
        _export_metadata(created_at="2026-06-28T16:01:00Z", session_id="sess-1")
    )
    diff = compare_export_metadata(baseline, current)
    assert diff["overall_export_diff_status"] == DIFF_UNCHANGED
    assert diff["session_changed"] is False


def test_export_diff_improved(storage):
    baseline = build_export_history_entry(
        _export_metadata(created_at="2026-06-28T16:00:00Z", open_attention_count=5)
    )
    current = build_export_history_entry(
        _export_metadata(created_at="2026-06-28T16:01:00Z", open_attention_count=1)
    )
    diff = compare_export_metadata(baseline, current)
    assert diff["overall_export_diff_status"] == DIFF_IMPROVED
    assert "open_attention_count" in diff["improvements"]


def test_export_diff_worsened(storage):
    baseline = build_export_history_entry(
        _export_metadata(
            created_at="2026-06-28T16:00:00Z",
            escalation_level=ESCALATION_NONE,
            open_attention_count=0,
        )
    )
    current = build_export_history_entry(
        _export_metadata(
            created_at="2026-06-28T16:01:00Z",
            escalation_level=ESCALATION_URGENT,
            open_attention_count=3,
        )
    )
    diff = compare_export_metadata(baseline, current)
    assert diff["overall_export_diff_status"] == DIFF_WORSENED


def test_export_diff_mixed(storage):
    baseline = build_export_history_entry(
        _export_metadata(
            created_at="2026-06-28T16:00:00Z",
            open_attention_count=5,
            escalation_level=ESCALATION_NONE,
        )
    )
    current = build_export_history_entry(
        _export_metadata(
            created_at="2026-06-28T16:01:00Z",
            open_attention_count=1,
            escalation_level=ESCALATION_URGENT,
        )
    )
    diff = compare_export_metadata(baseline, current)
    assert diff["overall_export_diff_status"] == DIFF_MIXED


def test_export_diff_history_bounded(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    for index in range(MAX_EXPORT_DIFF_HISTORY + 5):
        record_export_diff_metadata(
            storage,
            build_export_history_entry(
                _export_metadata(created_at=f"2026-06-28T16:{index:02d}:00Z", session_id=f"s{index}")
            ),
            baseline_history_entry=build_export_history_entry(
                _export_metadata(
                    created_at=f"2026-06-28T15:{index:02d}:00Z",
                    session_id=f"b{index}",
                )
            ),
        )
    payload = build_review_session_export_diff_payload(storage)
    assert len(payload["entries"]) == MAX_EXPORT_DIFF_HISTORY


def test_summary_includes_export_diff(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="D1",
        session_notes="diff summary",
        accepted_limitations=True,
    )
    export_latest_review_session(storage)
    create_review_session_record(
        storage,
        operator_initials="D2",
        session_notes="diff summary 2",
        accepted_limitations=True,
    )
    export_latest_review_session(storage)
    summary = build_validation_summary(db_session, storage)
    export_diff = summary.get("mrms_review_session_export_diff")
    assert export_diff is not None
    assert export_diff["available"] is True
    assert export_diff["verified_mrms"] is False
    assert export_diff["local_export_diff_only"] is True


def test_export_diff_endpoints_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/review-sessions/export/diff")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["local_export_diff_only"] is True
    assert body["compact"]["available"] is False

    history_response = client.get("/api/validation/review-sessions/export/diff/history")
    assert history_response.status_code == 200
    assert history_response.json()["count"] == 0


def test_auto_export_after_create_creates_session_and_export(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record = create_review_session_record(
        storage,
        operator_initials="AE",
        session_notes="auto export",
        accepted_limitations=True,
    )
    status = try_export_after_review_session_create(storage, record)
    assert status["export_after_create_requested"] is True
    assert status["export_generated"] is True
    assert status["export_path"]
    assert status["export_error"] is None
    diff_path = storage.absolute_path(storage.normalize_path(EXPORT_DIFF_LATEST_PATH))
    assert diff_path.is_file()


def test_auto_export_failure_does_not_roll_back_session(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record = create_review_session_record(
        storage,
        operator_initials="FAIL",
        session_notes="export fail",
        accepted_limitations=True,
    )
    session_id = record["session_id"]

    def _raise_export(*_args, **_kwargs):
        raise RuntimeError("simulated export failure")

    monkeypatch.setattr(
        "backend.app.services.mrms_review_session_export.export_latest_review_session",
        _raise_export,
    )
    status = try_export_after_review_session_create(storage, record)
    assert status["export_generated"] is False
    assert "simulated export failure" in (status.get("export_error") or "")
    from backend.app.services.mrms_review_session import load_review_sessions

    sessions = load_review_sessions(storage)
    assert sessions[0]["session_id"] == session_id


def test_auto_export_after_create_api(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.post(
        "/api/validation/review-sessions",
        json={
            "operator_initials": "API",
            "session_notes": "api auto export",
            "accepted_limitations": True,
            "export_after_create": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["export_after_create_requested"] is True
    assert body["export_generated"] is True
    assert body["export_path"]


def test_auto_export_does_not_clear_alerts(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    from backend.app.services.proof_bundle_diff_alert_history import (
        record_proof_bundle_diff_alert_history,
    )

    record_proof_bundle_diff_alert_history(
        storage,
        {
            "overall_diff_status": DIFF_WORSENED,
            "checked_at": "2026-06-28T16:12:00Z",
            "evidence_changes_count": 1,
            "current_bundle": {"bundle_id": "b1"},
            "baseline_bundle": {"bundle_id": "base"},
            "verified_mrms": False,
            "operator_attention_needed": True,
        },
        skip_duplicate=False,
    )
    alert_before = load_validation_alert(storage)
    record = create_review_session_record(
        storage,
        operator_initials="AL",
        session_notes="alert preserved",
        accepted_limitations=True,
    )
    try_export_after_review_session_create(storage, record)
    alert_after = load_validation_alert(storage)
    if alert_before is not None:
        assert alert_after is not None
        assert alert_after.get("operator_attention_needed") == alert_before.get(
            "operator_attention_needed"
        )


def test_export_diff_always_verified_mrms_false(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record_export_diff_metadata(
        storage,
        build_export_history_entry(_export_metadata(created_at="2026-06-28T16:00:00Z")),
    )
    latest_path = storage.absolute_path(storage.normalize_path(EXPORT_DIFF_LATEST_PATH))
    data = json.loads(latest_path.read_text(encoding="utf-8"))
    assert data["verified_mrms"] is False


def test_export_diff_does_not_mutate_production_gates(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    radar = RadarFile(
        product_id="mrms",
        timestamp="2026-06-28T12:00:00Z",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
    )
    db_session.add(radar)
    db_session.commit()
    create_review_session_record(
        storage,
        operator_initials="GATE",
        session_notes="gates",
        accepted_limitations=True,
    )
    export_latest_review_session(storage)
    record_export_diff_metadata(
        storage,
        build_export_history_entry(_export_metadata(created_at="2026-06-28T16:01:00Z")),
        baseline_history_entry=build_export_history_entry(
            _export_metadata(created_at="2026-06-28T16:00:00Z")
        ),
    )
    assert settings.enable_production_radar_tiles is False
    summary = build_validation_summary(db_session, storage)
    assert summary["verified_mrms"] is False
    assert summary["catalog"]["verified_mrms"] is False


def test_export_records_diff_on_generate(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="R1",
        session_notes="record diff",
        accepted_limitations=True,
    )
    export_latest_review_session(storage)
    assert storage.absolute_path(storage.normalize_path(EXPORT_DIFF_LATEST_PATH)).is_file()
    create_review_session_record(
        storage,
        operator_initials="R2",
        session_notes="record diff 2",
        accepted_limitations=True,
    )
    export_latest_review_session(storage)
    history_path = storage.absolute_path(storage.normalize_path(EXPORT_DIFF_HISTORY_PATH))
    history = json.loads(history_path.read_text(encoding="utf-8"))
    assert len(history) >= 2
    assert history[0]["overall_export_diff_status"] != DIFF_NO_BASELINE
