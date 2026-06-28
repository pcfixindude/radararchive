"""Tests for dev-only MRMS sign-off API (Phase 29)."""

from __future__ import annotations

import json

import pytest

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.decoded_tile_cache import TILE_MODE_PLACEHOLDER
from backend.app.services.mrms_proof_regression import save_proof_regression_report
from backend.app.services.mrms_proof_report import save_mrms_proof_report
from backend.app.services.mrms_signoff import load_signoffs
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_report_store import save_scheduled_validation_report


def _proof_report() -> dict:
    return {
        "generated_at": "2026-06-28T10:00:00Z",
        "overall_status": "insufficient_evidence",
        "frame_count": 2,
        "criteria_counts": {"passed": 1, "failed": 1, "warning": 0, "skipped": 0, "unknown": 0},
        "frames": [],
        "verified_mrms": False,
        "proof_only": True,
    }


def _regression_report(*, detected: bool = True) -> dict:
    return {
        "checked_at": "2026-06-28T11:00:00Z",
        "regression_detected": detected,
        "regression_status": "regression_detected" if detected else "no_regression",
        "regression_count": 1 if detected else 0,
        "findings": [{"kind": "overall_status", "message": "status worsened"}] if detected else [],
        "verified_mrms": False,
        "prototype": True,
    }


def test_post_signoff_success(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_mrms_proof_report(storage, _proof_report())

    response = client.post(
        "/api/validation/signoffs",
        json={
            "operator_initials": "AB",
            "operator_notes": "Reviewed draft proof locally.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["local_signoff_only"] is True
    assert body["does_not_enable_production"] is True
    assert body["signoff"]["verified_mrms"] is False
    assert body["signoff"]["does_not_enable_production"] is True
    assert body["alert"]["latest_signoff_at"] == body["signoff"]["created_at"]


def test_post_signoff_requires_operator(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.post(
        "/api/validation/signoffs",
        json={"operator_notes": "notes only"},
    )
    assert response.status_code == 422


def test_post_signoff_requires_notes_or_limitations(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.post(
        "/api/validation/signoffs",
        json={"operator_initials": "AB"},
    )
    assert response.status_code == 422


def test_post_signoff_does_not_mutate_catalog_or_flags(
    client, db_session, storage, monkeypatch
):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T04:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase29.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=False,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    response = client.post(
        "/api/validation/signoffs",
        json={
            "operator_name": "Pat",
            "accepted_limitations": "Prototype only",
        },
    )
    assert response.status_code == 200
    assert response.json()["production_enabled"] is False

    db_session.refresh(frame)
    assert frame.production_rendering is False
    assert frame.render_status == RENDER_STATUS_PRODUCTION_RENDERED

    tile_response = client.get("/tiles/mrms_reflectivity/2026-06-28T04:00:00Z/0/0/0.png")
    assert tile_response.status_code == 200
    assert tile_response.headers.get("x-radararchive-production-rendering") == "false"
    assert tile_response.headers.get("x-radararchive-tile") in (
        TILE_MODE_PLACEHOLDER,
        "placeholder_for_real_raw",
    )


def test_post_signoff_preserves_regression_alert(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_proof_regression_report(storage, _regression_report(detected=True))

    response = client.post(
        "/api/validation/signoffs",
        json={
            "operator_initials": "OP",
            "operator_notes": "Reviewed regression findings",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["proof_regression_still_active"] is True
    assert body["alert"]["proof_regression_still_active"] is True
    assert body["alert"]["proof_regression_detected"] is True
    assert body["signoff"]["proof_regression_still_active_after_signoff"] is True

    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert["proof_regression_detected"] is True
    assert alert["latest_signoff_at"] is not None


def test_summary_includes_scheduled_proof_step_compact(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    scheduled = {
        "ran_at": "2026-06-28T12:00:00Z",
        "success": True,
        "exit_code": 0,
        "proof_requested": True,
        "steps": [
            {
                "name": "mrms_proof_report",
                "status": "succeeded",
                "elapsed_seconds": 1.25,
            }
        ],
        "mrms_proof_regression": _regression_report(detected=False),
        "verified_mrms": False,
        "prototype": True,
    }
    save_scheduled_validation_report(storage, scheduled)

    response = client.get("/api/validation/summary")
    assert response.status_code == 200
    body = response.json()
    proof_step = body["scheduled_validation"]["proof_step"]
    assert proof_step["ran"] is True
    assert proof_step["proof_requested"] is True
    assert proof_step["status"] == "succeeded"
    assert proof_step["elapsed_seconds"] == 1.25
    assert proof_step["proof_regression_detected"] is False
    assert body["verified_mrms"] is False


def test_validation_summary_stable_after_signoff(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    before = client.get("/api/validation/summary").json()
    client.post(
        "/api/validation/signoffs",
        json={"operator_initials": "ZZ", "operator_notes": "ok"},
    )
    after = client.get("/api/validation/summary").json()
    assert after["verified_mrms"] is False
    assert after["placeholder_default"] == before["placeholder_default"]
    assert after["production_rendering_enabled"] == before["production_rendering_enabled"]
    assert after["mrms_signoff"]["signoff_count"] == before["mrms_signoff"]["signoff_count"] + 1


def test_signoff_persists_to_json_file(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    client.post(
        "/api/validation/signoffs",
        json={"operator_name": "Sam", "accepted_limitations": "stub tiles"},
    )
    entries = load_signoffs(storage)
    assert len(entries) == 1
    assert entries[0]["verified_mrms"] is False
    assert entries[0]["does_not_enable_production"] is True
