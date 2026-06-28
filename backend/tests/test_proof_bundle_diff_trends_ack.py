"""Tests for proof bundle diff alert trends and acknowledgments (Phase 35)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_proof_bundle_diff import DIFF_IMPROVED, DIFF_MIXED, DIFF_UNCHANGED, DIFF_WORSENED
from backend.app.services.proof_bundle_diff_acknowledgment import (
    ACKNOWLEDGMENTS_PATH,
    DiffAcknowledgmentValidationError,
    create_diff_acknowledgment,
    load_diff_acknowledgments,
)
from backend.app.services.proof_bundle_diff_alert_history import record_proof_bundle_diff_alert_history
from backend.app.services.proof_bundle_diff_alert_trends import (
    TREND_IMPROVING,
    TREND_MIXED,
    TREND_NO_DATA,
    TREND_STABLE,
    TREND_WORSENING,
    build_proof_bundle_diff_alert_trend,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import build_validation_alert, load_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _fake_diff_report(*, status: str, bundle_id: str, changes: int = 1) -> dict:
    return {
        "overall_diff_status": status,
        "checked_at": f"2026-06-28T16:{bundle_id[-2:]}:00Z",
        "evidence_changes_count": changes,
        "current_bundle": {"bundle_id": bundle_id},
        "baseline_bundle": {"bundle_id": "base"},
        "verified_mrms": False,
    }


def _seed_history(storage: LocalStorage, statuses: list[str]) -> None:
    """Seed history where statuses[0] is the latest (newest) entry."""
    total = len(statuses)
    for index, status in enumerate(reversed(statuses)):
        position = total - 1 - index
        record_proof_bundle_diff_alert_history(
            storage,
            _fake_diff_report(status=status, bundle_id=f"b{position}", changes=position),
            skip_duplicate=False,
        )


def test_trend_summary_shape(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(storage, [DIFF_WORSENED, DIFF_UNCHANGED])
    trend = build_proof_bundle_diff_alert_trend(storage)
    assert trend["latest_status"] == DIFF_WORSENED
    assert trend["trend"] in (TREND_WORSENING, TREND_STABLE)
    assert "current_attention_streak" in trend
    assert trend["verified_mrms"] is False
    assert trend["local_trend_only"] is True


def test_no_data_trend(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    trend = build_proof_bundle_diff_alert_trend(storage)
    assert trend["trend"] == TREND_NO_DATA
    assert trend["history_count"] == 0


def test_worsening_trend_detection(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(storage, [DIFF_WORSENED, DIFF_WORSENED, DIFF_UNCHANGED])
    trend = build_proof_bundle_diff_alert_trend(storage)
    assert trend["trend"] == TREND_WORSENING
    assert trend["recent_worsened_count"] >= 2
    assert trend["current_attention_streak"] >= 1
    assert trend["last_worsened_at"] is not None


def test_improving_trend_detection(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(storage, [DIFF_IMPROVED, DIFF_IMPROVED, DIFF_WORSENED])
    trend = build_proof_bundle_diff_alert_trend(storage)
    assert trend["trend"] == TREND_IMPROVING
    assert trend["recent_improved_count"] >= 2
    assert trend["last_improved_at"] is not None


def test_mixed_trend_detection(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(storage, [DIFF_MIXED, DIFF_MIXED, DIFF_UNCHANGED])
    trend = build_proof_bundle_diff_alert_trend(storage)
    assert trend["trend"] == TREND_MIXED
    assert trend["recent_mixed_count"] >= 2
    assert trend["last_mixed_at"] is not None


def test_streak_counts(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(storage, [DIFF_UNCHANGED, DIFF_UNCHANGED, DIFF_WORSENED])
    trend = build_proof_bundle_diff_alert_trend(storage)
    assert trend["current_non_attention_streak"] >= 2
    assert trend["recent_unchanged_count"] >= 2


def test_acknowledgment_record_shape(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record = create_diff_acknowledgment(
        storage,
        operator_initials="OP",
        note="Reviewed worsened diff locally",
    )
    assert record["acknowledgment_id"]
    assert record["operator"] == "OP"
    assert record["verified_mrms"] is False
    assert record["local_acknowledgment_only"] is True
    assert record["does_not_clear_alerts"] is True
    assert record["does_not_enable_production"] is True


def test_acknowledgment_requires_operator(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    try:
        create_diff_acknowledgment(storage, note="missing operator")
    except DiffAcknowledgmentValidationError as exc:
        assert "operator" in str(exc).lower()
    else:
        raise AssertionError("expected validation error")


def test_acknowledgment_requires_note(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    try:
        create_diff_acknowledgment(storage, operator_initials="OP", note="   ")
    except DiffAcknowledgmentValidationError as exc:
        assert "note" in str(exc).lower()
    else:
        raise AssertionError("expected validation error")


def test_acknowledgment_does_not_clear_alerts(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record_proof_bundle_diff_alert_history(
        storage,
        _fake_diff_report(status=DIFF_WORSENED, bundle_id="bad"),
        skip_duplicate=False,
    )
    alert_before = build_validation_alert(
        storage,
        scheduled={
            "success": True,
            "exit_code": 0,
            "mrms_proof_bundle_diff": {"overall_diff_status": DIFF_WORSENED},
        },
    )
    create_diff_acknowledgment(storage, operator_initials="OP", note="acknowledged review")
    alert_after = build_validation_alert(
        storage,
        scheduled={
            "success": True,
            "exit_code": 0,
            "mrms_proof_bundle_diff": {"overall_diff_status": DIFF_WORSENED},
        },
    )
    assert alert_before["operator_attention_needed"] is True
    assert alert_after["operator_attention_needed"] is True
    assert alert_after["diff_acknowledgment_count"] == 1
    assert alert_after.get("latest_diff_acknowledgment_operator") == "OP"


def test_summary_includes_trend_and_ack(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(storage, [DIFF_WORSENED])
    create_diff_acknowledgment(storage, operator_initials="OP", note="local ack")
    summary = build_validation_summary(db_session, storage)
    trend = summary.get("proof_bundle_diff_alert_trend")
    ack = summary.get("proof_bundle_diff_acknowledgment")
    assert trend is not None
    assert trend.get("trend") == TREND_WORSENING
    assert ack is not None
    assert ack.get("available") is True
    assert ack.get("count") == 1


def test_trend_endpoint_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/proof-bundle-diff-alert-trend")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["trend"]["trend"] == TREND_NO_DATA


def test_acknowledgments_endpoint_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    ack_path = storage.absolute_path(ACKNOWLEDGMENTS_PATH)
    if ack_path.is_file():
        ack_path.unlink()
    response = client.get("/api/validation/proof-bundle-diff-acknowledgments")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 0
    assert body["entries"] == []


def test_acknowledgment_post_endpoint(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.post(
        "/api/validation/proof-bundle-diff-acknowledgments",
        json={"operator_initials": "OP", "note": "local test acknowledgment only"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["does_not_clear_alerts"] is True
    assert body["acknowledgment"]["note"] == "local test acknowledgment only"


def test_history_does_not_mutate_gates(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    create_diff_acknowledgment(storage, operator_initials="OP", note="gate test")

    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T10:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase35.grib2.gz"),
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


def test_gitignore_covers_acknowledgments():
    gitignore = Path("/Users/irds/Projects/radararchive/.gitignore").read_text(encoding="utf-8")
    assert "proof_bundle_diff_acknowledgments.json" in gitignore
