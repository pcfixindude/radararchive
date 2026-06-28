"""Tests for local MRMS proof review sessions (Phase 41)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_operator_handoff import REVIEW_CHECKLIST_ITEMS
from backend.app.services.mrms_proof_bundle_diff import DIFF_WORSENED
from backend.app.services.mrms_review_session import (
    MAX_REVIEW_SESSIONS,
    ReviewSessionValidationError,
    build_review_sessions_payload,
    create_review_session_record,
    load_review_sessions,
    validate_review_session_input,
)
from backend.app.services.proof_bundle_diff_alert_history import record_proof_bundle_diff_alert_history
from backend.app.services.proof_bundle_diff_escalation_digest import (
    export_proof_bundle_diff_escalation_digest,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _fake_diff_report(*, status: str, bundle_id: str, checked_at: str) -> dict:
    return {
        "overall_diff_status": status,
        "checked_at": checked_at,
        "evidence_changes_count": 1,
        "current_bundle": {"bundle_id": bundle_id},
        "baseline_bundle": {"bundle_id": "base"},
        "verified_mrms": False,
        "operator_attention_needed": status in (DIFF_WORSENED,),
    }


def test_review_session_requires_operator(storage):
    with pytest.raises(ReviewSessionValidationError):
        validate_review_session_input(
            session_notes="notes",
            accepted_limitations=True,
        )


def test_review_session_requires_notes_or_checklist(storage):
    with pytest.raises(ReviewSessionValidationError):
        validate_review_session_input(
            operator_initials="OP",
            accepted_limitations=True,
        )


def test_review_session_requires_accepted_limitations(storage):
    with pytest.raises(ReviewSessionValidationError):
        validate_review_session_input(
            operator_initials="OP",
            session_notes="reviewed digest",
        )


def test_review_session_record_shape(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record = create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="Reviewed local digest and handoff checklist",
        accepted_limitations=True,
    )
    assert record["session_id"]
    assert record["created_at"]
    assert record["operator_initials"] == "OP"
    assert record["verified_mrms"] is False
    assert record["local_review_only"] is True
    assert record["does_not_clear_alerts"] is True
    assert record["does_not_enable_production"] is True
    assert isinstance(record["open_attention_items"], list)
    assert isinstance(record["checklist_items_not_reviewed"], list)
    assert len(record["checklist_items_not_reviewed"]) == len(REVIEW_CHECKLIST_ITEMS)


def test_review_session_links_evidence_when_available(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    export_proof_bundle_diff_escalation_digest(storage)
    handoff_json = storage.absolute_path("dev/mrms_operator_handoff_latest.json")
    handoff_json.parent.mkdir(parents=True, exist_ok=True)
    handoff_json.write_text(
        json.dumps({"markdown_path": "data/dev/mrms_operator_handoff_latest.md"}, indent=2),
        encoding="utf-8",
    )
    record = create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="linked evidence test",
        accepted_limitations=True,
    )
    assert record["latest_digest_path"]
    assert record["latest_operator_handoff_path"]


def test_bounded_review_session_history(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    for index in range(MAX_REVIEW_SESSIONS + 3):
        create_review_session_record(
            storage,
            operator_initials=f"O{index}",
            session_notes=f"session {index}",
            accepted_limitations=True,
        )
    entries = load_review_sessions(storage)
    assert len(entries) == MAX_REVIEW_SESSIONS


def test_get_review_sessions_endpoint_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/review-sessions")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["count"] == 0


def test_post_review_session_endpoint(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.post(
        "/api/validation/review-sessions",
        json={
            "operator_initials": "API",
            "session_notes": "API review session test",
            "accepted_limitations": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["local_review_only"] is True
    assert body["review_session"]["operator_initials"] == "API"


def test_summary_includes_latest_review_session(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="SUM",
        session_notes="summary test",
        accepted_limitations=True,
    )
    summary = build_validation_summary(db_session, storage)
    session = summary.get("mrms_review_session")
    assert session is not None
    assert session["available"] is True
    assert session["latest_operator"] == "SUM"
    assert session["verified_mrms"] is False


def test_review_session_does_not_clear_alerts(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    for index, checked_at in enumerate(
        ["2026-06-28T16:12:00Z", "2026-06-28T16:13:00Z", "2026-06-28T16:14:00Z"]
    ):
        record_proof_bundle_diff_alert_history(
            storage,
            _fake_diff_report(status=DIFF_WORSENED, bundle_id=f"b{index}", checked_at=checked_at),
            skip_duplicate=False,
        )
    alert_before = load_validation_alert(storage)
    create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="should not clear alerts",
        accepted_limitations=True,
    )
    alert_after = load_validation_alert(storage)
    if alert_before is not None:
        assert alert_after is not None
        assert alert_after.get("operator_attention_needed") == alert_before.get(
            "operator_attention_needed"
        )


def test_review_session_does_not_mutate_production_gates(
    client, db_session, storage, monkeypatch
):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T11:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase41.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=False,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="gate test",
        accepted_limitations=True,
    )
    db_session.refresh(frame)
    assert frame.production_rendering is False

    response = client.get("/tiles/mrms_reflectivity/2026-06-28T11:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"


def test_review_session_checklist_acknowledgement(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    reviewed = [REVIEW_CHECKLIST_ITEMS[0]]
    record = create_review_session_record(
        storage,
        operator_initials="OP",
        checklist_items_reviewed=reviewed,
        accepted_limitations=True,
    )
    assert record["checklist_items_reviewed"] == reviewed
    assert REVIEW_CHECKLIST_ITEMS[0] not in record["checklist_items_not_reviewed"]


def test_runtime_review_sessions_gitignored():
    gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
    assert "mrms_review_sessions.json" in gitignore.read_text(encoding="utf-8")


def test_build_review_sessions_payload_safe_empty(storage):
    payload = build_review_sessions_payload(storage)
    assert payload["verified_mrms"] is False
    assert payload["count"] == 0
