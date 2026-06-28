"""Tests for scheduled handoff auto-generation and operator guidance (Phase 33)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_batch_validation import BatchValidationReport
from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_MIXED,
    DIFF_UNCHANGED,
    DIFF_WORSENED,
    build_proof_bundle_diff_report,
)
from backend.app.services.operator_guidance import (
    GUIDANCE_BY_CAUSE,
    build_operator_guidance,
)
from backend.app.services.render_queue_benchmark import RenderQueueBenchmarkReport
from backend.app.services.scheduled_validation import run_scheduled_validation
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import (
    CAUSE_DECODER_UNAVAILABLE,
    CAUSE_PROOF_BUNDLE_DIFF_WORSENED,
    CAUSE_ZERO_TILES_WRITTEN,
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


def _worsened_bundle_pair(storage: LocalStorage) -> tuple[str, str]:
    baseline_folder = _write_bundle_manifest(
        storage,
        "mrms_proof_bundle_handoff_base",
        {
            "bundle_id": "good",
            "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_handoff_base",
            "archive_name": "mrms_proof_bundle_handoff_base",
            "files_included": ["evidence/mrms_proof_latest.json"],
            "files_missing": [],
        },
    )
    current_folder = _write_bundle_manifest(
        storage,
        "mrms_proof_bundle_handoff_cur",
        {
            "bundle_id": "bad",
            "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_handoff_cur",
            "archive_name": "mrms_proof_bundle_handoff_cur",
            "files_included": ["evidence/mrms_proof_latest.json"],
            "files_missing": [],
        },
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_handoff_base",
        "mrms_proof_latest.json",
        {
            "overall_status": "ready_for_operator_review",
            "criteria_counts": {"passed": 2, "failed": 0, "warning": 0, "skipped": 0},
        },
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_handoff_cur",
        "mrms_proof_latest.json",
        {
            "overall_status": "failed",
            "criteria_counts": {"passed": 0, "failed": 3, "warning": 0, "skipped": 0},
        },
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_handoff_base",
        "mrms_proof_regression_latest.json",
        {"regression_detected": False, "regression_status": "none"},
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_handoff_cur",
        "mrms_proof_regression_latest.json",
        {"regression_detected": True, "regression_status": "regression_detected"},
    )
    return baseline_folder, current_folder


def test_scheduled_validation_handoff_report_shape(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()

    report = run_scheduled_validation(
        db_session,
        storage,
        count=1,
        handoff_requested=True,
        persist=False,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )
    body = report.to_dict()
    assert body["handoff_requested"] is True
    assert body["handoff_generated"] is False
    assert body["handoff_reason"] == "skipped_diff_not_requested"
    assert "operator_handoff" in [step["name"] for step in body["steps"]]
    assert body["verified_mrms"] is False


def _seed_bundle_index(storage: LocalStorage, baseline_folder: str, current_folder: str) -> None:
    baseline_id = "good"
    current_id = "bad"
    index = [
        {
            "bundle_id": current_id,
            "bundle_folder": current_folder,
            "created_at": "2026-06-28T12:01:00Z",
            "archive_name": current_folder.split("/")[-1],
        },
        {
            "bundle_id": baseline_id,
            "bundle_folder": baseline_folder,
            "created_at": "2026-06-28T12:00:00Z",
            "archive_name": baseline_folder.split("/")[-1],
        },
    ]
    storage.absolute_path("dev/proof_bundles_index.json").write_text(
        json.dumps(index, indent=2),
        encoding="utf-8",
    )
    storage.absolute_path("dev/proof_bundles_latest.json").write_text(
        json.dumps(index[0], indent=2),
        encoding="utf-8",
    )


def test_worsened_diff_triggers_handoff_when_enabled(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    baseline_folder, current_folder = _worsened_bundle_pair(storage)
    _seed_bundle_index(storage, baseline_folder, current_folder)

    diff_report = build_proof_bundle_diff_report(storage)
    assert diff_report["overall_diff_status"] == DIFF_WORSENED

    report = run_scheduled_validation(
        db_session,
        storage,
        count=1,
        diff_bundle_requested=True,
        handoff_requested=True,
        persist=False,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )
    body = report.to_dict()
    assert body["handoff_requested"] is True
    assert body["handoff_generated"] is True
    assert body["handoff_reason"] == "proof_bundle_diff_worsened"
    assert body["diff_status_that_triggered_handoff"] == DIFF_WORSENED
    assert body["handoff_path"]
    assert body["verified_mrms"] is False

    handoff_json = storage.absolute_path("dev/mrms_operator_handoff_latest.json")
    assert handoff_json.is_file()
    record = json.loads(handoff_json.read_text(encoding="utf-8"))
    assert record["auto_generated"] is True
    assert record["verified_mrms"] is False


def test_mixed_diff_triggers_handoff_when_enabled(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()

    report = run_scheduled_validation(
        db_session,
        storage,
        count=1,
        diff_bundle_requested=True,
        handoff_requested=True,
        persist=False,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )
    body = report.to_dict()
    diff_status = (body.get("mrms_proof_bundle_diff") or {}).get("overall_diff_status")
    if diff_status == DIFF_MIXED:
        assert body["handoff_generated"] is True
        assert body["handoff_reason"] == "proof_bundle_diff_mixed"
    else:
        alert = build_validation_alert(
            storage,
            scheduled={
                "success": True,
                "exit_code": 0,
                "mrms_proof_bundle_diff": {
                    "overall_diff_status": DIFF_MIXED,
                    "evidence_changes_count": 2,
                    "checked_at": "2026-06-28T12:00:00Z",
                },
            },
        )
        guidance = build_operator_guidance(alert)
        assert any(item["cause"] == "proof_bundle_diff_mixed" for item in guidance)


def test_unchanged_diff_skips_handoff_with_reason(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    archive = "mrms_proof_bundle_handoff_same"
    folder = _write_bundle_manifest(
        storage,
        archive,
        {
            "bundle_id": "same",
            "bundle_folder": f"data/dev/proof_bundles/{archive}",
            "archive_name": archive,
            "files_included": ["evidence/mrms_proof_latest.json"],
            "files_missing": [],
        },
    )
    payload = {
        "overall_status": "ready_for_operator_review",
        "criteria_counts": {"passed": 2, "failed": 0, "warning": 0, "skipped": 0},
    }
    _write_bundle_evidence(storage, archive, "mrms_proof_latest.json", payload)

    diff_report = build_proof_bundle_diff_report(
        storage,
        current_bundle_folder=folder,
        baseline_bundle_folder=folder,
    )
    assert diff_report["overall_diff_status"] in (DIFF_UNCHANGED, "no_baseline")

    report = run_scheduled_validation(
        db_session,
        storage,
        count=1,
        bundle_requested=True,
        diff_bundle_requested=True,
        handoff_requested=True,
        persist=False,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )
    body = report.to_dict()
    assert body["handoff_requested"] is True
    assert body["handoff_generated"] is False
    assert str(body["handoff_reason"]).startswith("skipped_diff_status_")


def test_guidance_mapping_proof_bundle_diff_worsened():
    alert = build_validation_alert(
        LocalStorage(settings.local_storage_root),
        scheduled={
            "success": True,
            "exit_code": 0,
            "mrms_proof_bundle_diff": {
                "overall_diff_status": DIFF_WORSENED,
                "evidence_changes_count": 1,
            },
        },
    )
    guidance = build_operator_guidance(alert)
    assert len(guidance) >= 1
    titles = [item["title"] for item in guidance]
    assert any("worsened" in title.lower() or "diff" in title.lower() for title in titles)
    assert GUIDANCE_BY_CAUSE["proof_bundle_diff_worsened"]["path"].endswith("RUNBOOK_REAL_MRMS_VALIDATION.md")


def test_guidance_mapping_decoder_and_zero_tiles():
    alert = {
        "operator_attention_needed": True,
        "proof_bundle_diff_attention": False,
        "grouped_failure_causes": [
            {"cause": CAUSE_DECODER_UNAVAILABLE, "step": "decode", "count": 1},
            {"cause": CAUSE_ZERO_TILES_WRITTEN, "step": "tiles", "count": 1},
        ],
    }
    guidance = build_operator_guidance(alert)
    causes = {item["cause"] for item in guidance}
    assert CAUSE_DECODER_UNAVAILABLE in causes
    assert CAUSE_ZERO_TILES_WRITTEN in causes


def test_validation_summary_includes_guidance_and_handoff(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    _worsened_bundle_pair(storage)
    _seed_bundle_index(
        storage,
        "data/dev/proof_bundles/mrms_proof_bundle_handoff_base",
        "data/dev/proof_bundles/mrms_proof_bundle_handoff_cur",
    )

    run_scheduled_validation(
        db_session,
        storage,
        count=1,
        diff_bundle_requested=True,
        handoff_requested=True,
        persist=True,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )

    summary = build_validation_summary(db_session, storage)
    assert summary["verified_mrms"] is False
    spb = summary.get("scheduled_proof_bundle")
    assert spb is not None
    assert spb.get("handoff_requested") is True
    handoff = summary.get("operator_handoff")
    assert handoff is not None
    if spb.get("handoff_generated"):
        assert handoff.get("handoff_generated") is True
    alert = summary.get("validation_alert")
    if alert and alert.get("operator_attention_needed"):
        assert isinstance(summary.get("operator_guidance"), list)


def test_handoff_does_not_mutate_gates_or_verify(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    batch_fn, queue_fn = _mock_runners()
    _worsened_bundle_pair(storage)
    _seed_bundle_index(
        storage,
        "data/dev/proof_bundles/mrms_proof_bundle_handoff_base",
        "data/dev/proof_bundles/mrms_proof_bundle_handoff_cur",
    )

    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T08:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase33.grib2.gz"),
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
        diff_bundle_requested=True,
        handoff_requested=True,
        persist=False,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )
    assert report.to_dict()["verified_mrms"] is False
    db_session.refresh(frame)
    assert frame.production_rendering is False

    response = client.get("/tiles/mrms_reflectivity/2026-06-28T08:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"


def test_alert_includes_operator_guidance_when_attention_needed(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    alert = build_validation_alert(
        storage,
        scheduled={
            "success": True,
            "exit_code": 0,
            "mrms_proof_bundle_diff": {
                "overall_diff_status": DIFF_WORSENED,
                "evidence_changes_count": 1,
            },
        },
    )
    assert alert["operator_attention_needed"] is True
    assert len(alert.get("operator_guidance", [])) >= 1
    assert alert["operator_guidance"][0]["path"].startswith("docs/")


def test_gitignore_covers_handoff_artifacts():
    gitignore = Path("/Users/irds/Projects/radararchive/.gitignore").read_text(encoding="utf-8")
    assert "mrms_operator_handoff_latest.md" in gitignore
    assert "mrms_operator_handoff_latest.json" in gitignore
