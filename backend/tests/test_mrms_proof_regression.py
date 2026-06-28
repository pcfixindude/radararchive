"""Tests for MRMS proof regression and operator sign-off (Phase 27)."""

from __future__ import annotations

import json

import pytest

from backend.app.config import settings
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.models import RadarFile
from backend.app.services.decoded_tile_cache import TILE_MODE_PLACEHOLDER
from backend.app.services.mrms_proof_regression import (
    REGRESSION_DETECTED,
    build_proof_regression_report,
    compact_proof_regression,
    detect_proof_regressions,
    load_proof_regression_report,
    run_proof_regression_check,
    save_proof_regression_report,
)
from backend.app.services.mrms_proof_report import save_mrms_proof_report
from backend.app.services.mrms_signoff import (
    SignoffValidationError,
    compact_signoff_summary,
    create_signoff_record,
    load_signoffs,
)
from backend.app.services.scheduled_validation import run_scheduled_validation
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import (
    CAUSE_PROOF_REGRESSION,
    build_validation_alert,
    refresh_validation_alert,
)


def _proof_report(
    *,
    overall_status: str = "insufficient_evidence",
    passed: int = 1,
    failed: int = 2,
    warning: int = 0,
    frame_count: int = 3,
    tile_frames: int = 0,
    decode_frames: int = 0,
) -> dict:
    frames = []
    for i in range(frame_count):
        frames.append(
            {
                "timestamp": f"2026-06-28T0{i}:00:00Z",
                "evidence": {
                    "tiles_written": 1 if i < tile_frames else 0,
                    "decode_artifact_path": f"data/staging/decode/{i}" if i < decode_frames else None,
                    "decoder_used": "mock" if i < decode_frames else None,
                    "geo_sanity": {
                        "tile_output_nonempty": i < tile_frames,
                        "bounds_valid": i < decode_frames,
                        "grid_positive": i < decode_frames,
                    },
                },
            }
        )
    return {
        "generated_at": "2026-06-28T10:00:00Z",
        "overall_status": overall_status,
        "requested_frame_count": frame_count,
        "frame_count": frame_count,
        "criteria_counts": {
            "passed": passed,
            "failed": failed,
            "warning": warning,
            "skipped": 0,
            "unknown": 0,
        },
        "frames": frames,
        "verified_mrms": False,
        "proof_only": True,
    }


def test_proof_regression_report_shape(storage):
    current = _proof_report()
    previous = _proof_report(passed=3)
    findings = detect_proof_regressions(current, previous)
    report = build_proof_regression_report(storage)
    assert "regression_status" in report
    assert report["verified_mrms"] is False


def test_status_worsened_detection():
    current = _proof_report(overall_status="failed", passed=0)
    previous = _proof_report(overall_status="ready_for_operator_review", passed=5)
    findings = detect_proof_regressions(current, previous)
    kinds = {f["kind"] for f in findings}
    assert "overall_status_worsened" in kinds
    assert "passed_criteria_decreased" in kinds


def test_tile_evidence_disappeared_detection():
    current = _proof_report(tile_frames=0)
    previous = _proof_report(tile_frames=2)
    findings = detect_proof_regressions(current, previous)
    assert any(f["kind"] == "tile_evidence_disappeared" for f in findings)


def test_regression_persistence_and_alert_integration(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_mrms_proof_report(storage, _proof_report(passed=3, tile_frames=2))
    save_mrms_proof_report(storage, _proof_report(passed=1, tile_frames=0, overall_status="failed"))

    report = run_proof_regression_check(storage)
    assert report["regression_detected"] is True
    assert report["regression_count"] >= 1
    saved = load_proof_regression_report(storage)
    assert saved is not None

    alert = refresh_validation_alert(storage)
    assert alert["proof_regression_detected"] is True
    assert alert["operator_attention_needed"] is True
    causes = alert.get("grouped_failure_causes") or []
    assert any(c.get("cause") == CAUSE_PROOF_REGRESSION for c in causes)


def test_signoff_record_shape(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record = create_signoff_record(
        storage,
        operator_initials="OP",
        operator_notes="Reviewed draft proof report",
        accepted_limitations="Prototype only",
    )
    assert record["verified_mrms"] is False
    assert record["does_not_set_verified_mrms"] is True
    assert record["no_automatic_promotion"] is True
    assert record["signoff_id"]


def test_signoff_requires_identity_and_notes(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    with pytest.raises(SignoffValidationError):
        create_signoff_record(storage, operator_notes="notes only")
    with pytest.raises(SignoffValidationError):
        create_signoff_record(storage, operator_name="Alice")


def test_signoff_does_not_set_verified_mrms(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record = create_signoff_record(
        storage,
        operator_name="Alice",
        accepted_limitations="Not verified MRMS",
    )
    entries = load_signoffs(storage)
    assert entries[0]["verified_mrms"] is False


def test_summary_includes_regression_and_signoff(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_proof_regression_report(
        storage,
        {
            "checked_at": "2026-06-28T10:00:00Z",
            "regression_status": REGRESSION_DETECTED,
            "regression_detected": True,
            "regression_count": 2,
            "verified_mrms": False,
        },
    )
    create_signoff_record(
        storage,
        operator_name="Bob",
        operator_notes="Reviewed",
    )

    response = client.get("/api/validation/summary")
    body = response.json()
    assert body["mrms_proof_regression"]["regression_detected"] is True
    assert body["mrms_signoff"]["signoff_count"] == 1
    assert body["mrms_signoff"]["verified_mrms"] is False


def test_scheduled_validation_proof_flag(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    report = run_scheduled_validation(
        db_session,
        storage,
        count=1,
        min_zoom=0,
        max_zoom=0,
        real_requested=False,
        proof_requested=True,
        persist=False,
        batch_fn=lambda *args, **kwargs: type(
            "Batch",
            (),
            {
                "to_dict": lambda self: {"decoded_count": 0, "discovered_count": 0},
                "warnings": [],
                "errors": [],
            },
        )(),
        queue_benchmark_fn=lambda *args, **kwargs: type(
            "Queue",
            (),
            {
                "to_dict": lambda self: {
                    "jobs_succeeded": 0,
                    "jobs_failed": 0,
                    "total_tiles_written": 0,
                },
                "warnings": [],
                "errors": [],
            },
        )(),
    )
    step_names = [step.name for step in report.steps]
    assert "mrms_proof_report" in step_names
    assert report.mrms_proof is not None
    assert report.mrms_proof_regression is not None
    assert report.mrms_proof["verified_mrms"] is False


def test_proof_regression_endpoint(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/proof-regression?refresh=true")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False


def test_signoffs_endpoint(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_signoff_record(storage, operator_name="Carol", operator_notes="ok")
    response = client.get("/api/validation/signoffs")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["count"] == 1


def test_compact_proof_regression_defaults():
    compact = compact_proof_regression(None)
    assert compact["regression_detected"] is False
    assert compact["verified_mrms"] is False


def test_production_tile_serving_still_gated_phase27(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    timestamp = "2026-06-28T04:00:00Z"
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase27_gate.grib2.gz"),
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
