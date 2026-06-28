"""Tests for proof bundle diff alert escalation hints (Phase 36)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_proof_bundle_diff import DIFF_MIXED, DIFF_UNCHANGED, DIFF_WORSENED
from backend.app.services.proof_bundle_diff_acknowledgment import (
    ACKNOWLEDGMENTS_PATH,
    create_diff_acknowledgment,
)
from backend.app.services.proof_bundle_diff_alert_history import record_proof_bundle_diff_alert_history
from backend.app.services.proof_bundle_diff_escalation import (
    ACK_CURRENT,
    ACK_NONE,
    ACK_NOT_NEEDED,
    ACK_STALE,
    ESCALATION_ATTENTION,
    ESCALATION_NONE,
    ESCALATION_URGENT,
    ESCALATION_WATCH,
    build_proof_bundle_diff_escalation,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import build_validation_alert, load_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _fake_diff_report(*, status: str, bundle_id: str, checked_at: str, changes: int = 1) -> dict:
    return {
        "overall_diff_status": status,
        "checked_at": checked_at,
        "evidence_changes_count": changes,
        "current_bundle": {"bundle_id": bundle_id},
        "baseline_bundle": {"bundle_id": "base"},
        "verified_mrms": False,
    }


def _seed_history(storage: LocalStorage, entries: list[tuple[str, str]]) -> None:
    """Seed history where entries[0] is the latest (newest) (status, checked_at)."""
    for index, (status, checked_at) in enumerate(reversed(entries)):
        record_proof_bundle_diff_alert_history(
            storage,
            _fake_diff_report(status=status, bundle_id=f"b{index}", checked_at=checked_at),
            skip_duplicate=False,
        )


def _write_ack(storage: LocalStorage, *, created_at: str, operator: str = "OP") -> None:
    repo_path = storage.normalize_path(ACKNOWLEDGMENTS_PATH)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    record = {
        "acknowledgment_id": "ack-test",
        "created_at": created_at,
        "operator": operator,
        "operator_initials": operator,
        "note": "test acknowledgment",
        "verified_mrms": False,
        "local_acknowledgment_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }
    storage.absolute_path(repo_path).write_text(json.dumps([record], indent=2), encoding="utf-8")


def test_escalation_no_data(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    escalation = build_proof_bundle_diff_escalation(storage)
    assert escalation["escalation_level"] == ESCALATION_NONE
    assert escalation["verified_mrms"] is False
    assert escalation["local_escalation_only"] is True
    assert escalation["does_not_clear_alerts"] is True
    assert escalation["does_not_enable_production"] is True


def test_escalation_none_when_stable(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(
        storage,
        [(DIFF_UNCHANGED, "2026-06-28T16:10:00Z"), (DIFF_UNCHANGED, "2026-06-28T16:09:00Z")],
    )
    escalation = build_proof_bundle_diff_escalation(storage)
    assert escalation["escalation_level"] == ESCALATION_NONE
    assert escalation["acknowledgment_status"] == ACK_NOT_NEEDED


def test_escalation_watch_single_worsened(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(
        storage,
        [(DIFF_WORSENED, "2026-06-28T16:10:00Z"), (DIFF_UNCHANGED, "2026-06-28T16:09:00Z")],
    )
    escalation = build_proof_bundle_diff_escalation(storage)
    assert escalation["escalation_level"] == ESCALATION_WATCH
    assert escalation["current_attention_streak"] == 1
    assert escalation["acknowledgment_status"] == ACK_NONE


def test_escalation_attention_two_streak(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(
        storage,
        [
            (DIFF_WORSENED, "2026-06-28T16:12:00Z"),
            (DIFF_MIXED, "2026-06-28T16:11:00Z"),
            (DIFF_UNCHANGED, "2026-06-28T16:10:00Z"),
        ],
    )
    escalation = build_proof_bundle_diff_escalation(storage)
    assert escalation["escalation_level"] == ESCALATION_ATTENTION
    assert escalation["current_attention_streak"] >= 2


def test_escalation_urgent_three_streak_no_current_ack(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(
        storage,
        [
            (DIFF_WORSENED, "2026-06-28T16:14:00Z"),
            (DIFF_WORSENED, "2026-06-28T16:13:00Z"),
            (DIFF_MIXED, "2026-06-28T16:12:00Z"),
            (DIFF_UNCHANGED, "2026-06-28T16:11:00Z"),
        ],
    )
    escalation = build_proof_bundle_diff_escalation(storage)
    assert escalation["escalation_level"] == ESCALATION_URGENT
    assert escalation["current_attention_streak"] >= 3
    assert escalation["acknowledgment_status"] in (ACK_NONE, ACK_STALE)


def test_stale_acknowledgment_before_latest_attention(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(
        storage,
        [
            (DIFF_WORSENED, "2026-06-28T16:12:00Z"),
            (DIFF_UNCHANGED, "2026-06-28T16:11:00Z"),
        ],
    )
    _write_ack(storage, created_at="2026-06-28T16:11:30Z")
    escalation = build_proof_bundle_diff_escalation(storage)
    assert escalation["stale_acknowledgment"] is True
    assert escalation["acknowledgment_status"] == ACK_STALE


def test_current_acknowledgment_after_latest_attention(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(storage, [(DIFF_WORSENED, "2026-06-28T16:10:00Z")])
    _write_ack(storage, created_at="2026-06-28T16:11:00Z")
    escalation = build_proof_bundle_diff_escalation(storage)
    assert escalation["acknowledgment_status"] == ACK_CURRENT
    assert escalation["stale_acknowledgment"] is False
    assert escalation["escalation_level"] == ESCALATION_WATCH


def test_escalation_does_not_clear_alerts(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(storage, [(DIFF_WORSENED, "2026-06-28T16:10:00Z")])
    _write_ack(storage, created_at="2026-06-28T16:11:00Z")
    build_proof_bundle_diff_escalation(storage)
    alert = build_validation_alert(
        storage,
        scheduled={
            "success": True,
            "exit_code": 0,
            "mrms_proof_bundle_diff": {"overall_diff_status": DIFF_WORSENED},
        },
    )
    assert alert["operator_attention_needed"] is True
    assert alert["proof_bundle_diff_attention"] is True


def test_summary_includes_escalation(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(storage, [(DIFF_WORSENED, "2026-06-28T16:10:00Z")])
    summary = build_validation_summary(db_session, storage)
    escalation = summary.get("proof_bundle_diff_escalation")
    assert escalation is not None
    assert escalation.get("escalation_level") == ESCALATION_WATCH
    assert escalation.get("verified_mrms") is False
    assert escalation.get("does_not_clear_alerts") is True


def test_alert_includes_escalation_fields(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(
        storage,
        [
            (DIFF_WORSENED, "2026-06-28T16:12:00Z"),
            (DIFF_WORSENED, "2026-06-28T16:11:00Z"),
        ],
    )
    alert = build_validation_alert(storage)
    assert alert.get("proof_bundle_diff_escalation_level") == ESCALATION_ATTENTION
    assert "proof_bundle_diff_escalation_reason" in alert
    assert alert.get("verified_mrms") is False


def test_escalation_endpoint_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/proof-bundle-diff-escalation")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["does_not_clear_alerts"] is True
    assert body["escalation"]["escalation_level"] == ESCALATION_NONE


def test_escalation_does_not_mutate_gates(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    _seed_history(storage, [(DIFF_WORSENED, "2026-06-28T16:10:00Z")])
    build_proof_bundle_diff_escalation(storage)

    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T10:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase36.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=False,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()
    db_session.refresh(frame)
    assert frame.production_rendering is False

    response = client.get("/tiles/mrms_reflectivity/2026-06-28T10:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"


def test_gitignore_covers_escalation_runtime_artifacts():
    gitignore = Path("/Users/irds/Projects/radararchive/.gitignore").read_text(encoding="utf-8")
    assert "proof_bundle_diff_alert_history.json" in gitignore
    assert "proof_bundle_diff_acknowledgments.json" in gitignore


def test_acknowledgment_create_still_does_not_clear_alerts(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(storage, [(DIFF_WORSENED, "2026-06-28T16:10:00Z")])
    create_diff_acknowledgment(storage, operator_initials="OP", note="local review")
    escalation = build_proof_bundle_diff_escalation(storage)
    assert escalation["does_not_clear_alerts"] is True
    alert = build_validation_alert(
        storage,
        scheduled={
            "success": True,
            "exit_code": 0,
            "mrms_proof_bundle_diff": {"overall_diff_status": DIFF_WORSENED},
        },
    )
    assert alert["operator_attention_needed"] is True
