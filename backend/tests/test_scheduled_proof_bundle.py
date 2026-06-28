"""Tests for scheduled proof bundle export/diff and alert hooks (Phase 32)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_batch_validation import BatchValidationReport
from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_MIXED,
    DIFF_WORSENED,
    build_proof_bundle_diff_report,
)
from backend.app.services.render_queue_benchmark import RenderQueueBenchmarkReport
from backend.app.services.scheduled_validation import run_scheduled_validation
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import (
    CAUSE_PROOF_BUNDLE_DIFF_WORSENED,
    build_validation_alert,
)
from backend.app.services.validation_dashboard import build_validation_summary


def _write_bundle_manifest(storage: LocalStorage, archive_name: str, manifest: dict) -> str:
    bundle_dir = storage.absolute_path(f"dev/proof_bundles/{archive_name}")
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return f"data/dev/proof_bundles/{archive_name}"


def _write_bundle_evidence(storage: LocalStorage, archive_name: str, filename: str, payload: dict) -> None:
    path = storage.absolute_path(f"dev/proof_bundles/{archive_name}/evidence/{filename}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _mock_runners():
    return (
        lambda *_a, **_k: BatchValidationReport(source_mode="stub", effective_frame_count=1),
        lambda *_a, **_k: RenderQueueBenchmarkReport(source_mode="stub", jobs_succeeded=1),
    )


def test_scheduled_validation_proof_bundle_report_shape(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()

    report = run_scheduled_validation(
        db_session,
        storage,
        count=1,
        proof_requested=True,
        bundle_requested=True,
        persist=False,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )

    body = report.to_dict()
    step_names = [step["name"] for step in body["steps"]]
    assert "proof_report" in step_names
    assert "proof_regression" in step_names
    assert "proof_bundle_export" in step_names
    assert body["mrms_proof_bundle"] is not None
    assert body["mrms_proof_bundle"]["verified_mrms"] is False
    assert body["verified_mrms"] is False


def test_scheduled_validation_proof_bundle_diff_report_shape(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()

    _write_bundle_manifest(
        storage,
        "mrms_proof_bundle_sched_base",
        {
            "bundle_id": "base",
            "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_sched_base",
            "archive_name": "mrms_proof_bundle_sched_base",
            "files_included": ["evidence/mrms_proof_latest.json"],
            "files_missing": [],
        },
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_sched_base",
        "mrms_proof_latest.json",
        {"overall_status": "ready_for_operator_review", "criteria_counts": {"passed": 2, "failed": 0}},
    )

    report = run_scheduled_validation(
        db_session,
        storage,
        count=1,
        proof_requested=True,
        bundle_requested=True,
        diff_bundle_requested=True,
        persist=False,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )

    body = report.to_dict()
    assert "proof_bundle_diff" in [step["name"] for step in body["steps"]]
    assert body["mrms_proof_bundle_diff"] is not None
    assert body["diff_bundle_requested"] is True


def test_alert_includes_proof_bundle_diff_worsened(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    baseline_folder = _write_bundle_manifest(
        storage,
        "mrms_proof_bundle_alert_base",
        {
            "bundle_id": "good",
            "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_alert_base",
            "archive_name": "mrms_proof_bundle_alert_base",
            "files_included": ["evidence/mrms_proof_latest.json"],
            "files_missing": [],
        },
    )
    current_folder = _write_bundle_manifest(
        storage,
        "mrms_proof_bundle_alert_cur",
        {
            "bundle_id": "bad",
            "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_alert_cur",
            "archive_name": "mrms_proof_bundle_alert_cur",
            "files_included": ["evidence/mrms_proof_latest.json"],
            "files_missing": [],
        },
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_alert_base",
        "mrms_proof_latest.json",
        {
            "overall_status": "ready_for_operator_review",
            "criteria_counts": {"passed": 2, "failed": 0, "warning": 0, "skipped": 0},
        },
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_alert_cur",
        "mrms_proof_latest.json",
        {
            "overall_status": "failed",
            "criteria_counts": {"passed": 0, "failed": 3, "warning": 0, "skipped": 0},
        },
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_alert_base",
        "mrms_proof_regression_latest.json",
        {"regression_detected": False, "regression_status": "none"},
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_alert_cur",
        "mrms_proof_regression_latest.json",
        {"regression_detected": True, "regression_status": "regression_detected"},
    )

    diff_report = build_proof_bundle_diff_report(
        storage,
        current_bundle_folder=current_folder,
        baseline_bundle_folder=baseline_folder,
    )
    assert diff_report["overall_diff_status"] == DIFF_WORSENED

    alert = build_validation_alert(
        storage,
        scheduled={
            "ran_at": "2026-06-28T12:00:00Z",
            "success": True,
            "exit_code": 0,
            "mrms_proof_bundle_diff": diff_report,
            "verified_mrms": False,
        },
    )
    assert alert["proof_bundle_diff_attention"] is True
    assert alert["operator_attention_needed"] is True
    assert alert["verified_mrms"] is False
    causes = [item.get("cause") for item in alert.get("grouped_failure_causes", [])]
    assert CAUSE_PROOF_BUNDLE_DIFF_WORSENED in causes


def test_proof_bundle_diff_mixed_sets_operator_attention(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    diff_report = {
        "overall_diff_status": DIFF_MIXED,
        "evidence_changes_count": 2,
        "checked_at": "2026-06-28T12:00:00Z",
        "verified_mrms": False,
    }
    alert = build_validation_alert(
        storage,
        scheduled={"success": True, "exit_code": 0, "mrms_proof_bundle_diff": diff_report},
    )
    assert alert["operator_attention_needed"] is True
    assert alert["proof_bundle_diff_status"] == DIFF_MIXED


def test_scheduled_summary_includes_proof_bundle_status(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()

    run_scheduled_validation(
        db_session,
        storage,
        count=1,
        bundle_requested=True,
        diff_bundle_requested=True,
        persist=True,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )

    summary = build_validation_summary(db_session, storage)
    spb = summary.get("scheduled_proof_bundle")
    assert spb is not None
    assert spb["bundle_exported"] is True
    assert spb["verified_mrms"] is False


def test_bundle_export_diff_does_not_mutate_gates(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    batch_fn, queue_fn = _mock_runners()

    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T07:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase32.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=False,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    report = run_scheduled_validation(
        db_session,
        storage,
        bundle_requested=True,
        diff_bundle_requested=True,
        persist=False,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )
    assert report.to_dict()["verified_mrms"] is False

    db_session.refresh(frame)
    assert frame.production_rendering is False

    response = client.get("/tiles/mrms_reflectivity/2026-06-28T07:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"


def test_gitignore_covers_scheduled_bundle_artifacts():
    gitignore = Path("/Users/irds/Projects/radararchive/.gitignore").read_text(encoding="utf-8")
    assert "data/dev/proof_bundles/" in gitignore
    assert "data/dev/mrms_proof_bundle_diff_latest.json" in gitignore
