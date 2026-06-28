"""Tests for MRMS proof history drill-down API (Phase 28)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.decoded_tile_cache import TILE_MODE_PLACEHOLDER
from backend.app.services.mrms_proof_history import (
    build_proof_history_payload,
    build_regression_history_payload,
    build_signoffs_list_payload,
    compact_proof_history_entry,
    compact_regression_history_entry,
    compact_signoff_item,
)
from backend.app.services.mrms_proof_regression import save_proof_regression_report
from backend.app.services.mrms_proof_report import save_mrms_proof_report
from backend.app.services.mrms_signoff import create_signoff_record


def test_compact_proof_history_item():
    item = compact_proof_history_entry(
        {
            "generated_at": "2026-06-28T10:00:00Z",
            "overall_status": "failed",
            "frame_count": 3,
            "criteria_counts": {"passed": 1, "failed": 2, "warning": 0, "skipped": 5},
        }
    )
    assert item["verified_mrms"] is False
    assert item["operator_review_required"] is True
    assert item["criteria_counts"]["failed"] == 2


def test_compact_regression_history_item():
    item = compact_regression_history_entry(
        {
            "checked_at": "2026-06-28T10:00:00Z",
            "regression_status": "detected",
            "regression_detected": True,
            "regression_count": 2,
        }
    )
    assert item["verified_mrms"] is False
    assert "detected" in item["summary"]


def test_compact_signoff_item_does_not_imply_verified():
    item = compact_signoff_item(
        {
            "signoff_id": "abc",
            "created_at": "2026-06-28T10:00:00Z",
            "operator_initials": "OP",
            "proof_report_timestamp": "2026-06-28T09:00:00Z",
            "accepted_limitations": "prototype only",
        }
    )
    assert item["verified_mrms"] is False
    assert item["does_not_set_verified_mrms"] is True
    assert item["local_signoff_only"] is True


def test_missing_history_returns_empty_lists(storage):
    proof = build_proof_history_payload(storage)
    regression = build_regression_history_payload(storage)
    signoffs = build_signoffs_list_payload(storage)
    assert proof["entries"] == []
    assert proof["count"] == 0
    assert regression["entries"] == []
    assert signoffs["entries"] == []
    assert signoffs["verified_mrms"] is False


def test_proof_history_endpoint(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_mrms_proof_report(
        storage,
        {
            "generated_at": "2026-06-28T10:00:00Z",
            "overall_status": "insufficient_evidence",
            "frame_count": 2,
            "criteria_counts": {"passed": 0, "failed": 3, "warning": 0, "skipped": 4},
            "verified_mrms": False,
        },
    )
    response = client.get("/api/validation/proof/history")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["count"] >= 1
    assert body["entries"][0]["verified_mrms"] is False


def test_proof_regression_history_endpoint(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_proof_regression_report(
        storage,
        {
            "checked_at": "2026-06-28T10:00:00Z",
            "regression_status": "detected",
            "regression_detected": True,
            "regression_count": 1,
            "verified_mrms": False,
        },
    )
    response = client.get("/api/validation/proof-regression/history")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["count"] >= 1


def test_signoffs_list_endpoint_shape(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_signoff_record(
        storage,
        operator_name="Reviewer",
        operator_notes="Reviewed proof history",
    )
    response = client.get("/api/validation/signoffs")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["does_not_set_verified_mrms"] is True
    assert body["count"] == 1
    assert body["entries"][0]["verified_mrms"] is False


def test_validation_summary_remains_stable(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert "mrms_proof" in body
    assert "mrms_signoff" in body


def test_production_tile_serving_still_gated_phase28(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    timestamp = "2026-06-28T05:00:00Z"
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase28_gate.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=True,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    response = client.get(f"/tiles/mrms_reflectivity/{timestamp}/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"
    assert response.headers.get("x-radararchive-tile") in (TILE_MODE_PLACEHOLDER, "placeholder_for_real_raw")
