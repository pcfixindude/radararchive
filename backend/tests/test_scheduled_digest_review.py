"""Tests for scheduled escalation digest and operator review checklist (Phase 39)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_batch_validation import BatchValidationReport
from backend.app.services.mrms_operator_handoff import (
    REVIEW_CHECKLIST_ITEMS,
    generate_operator_handoff,
)
from backend.app.services.mrms_proof_bundle_diff import DIFF_WORSENED
from backend.app.services.proof_bundle_diff_escalation_digest import (
    DIGEST_JSON_PATH,
    DIGEST_MD_PATH,
    compact_scheduled_digest,
)
from backend.app.services.render_queue_benchmark import RenderQueueBenchmarkReport
from backend.app.services.scheduled_validation import run_scheduled_validation
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _mock_runners():
    return (
        lambda *_a, **_k: BatchValidationReport(source_mode="stub", effective_frame_count=1),
        lambda *_a, **_k: RenderQueueBenchmarkReport(source_mode="stub", jobs_succeeded=1),
    )


def _write_bundle_manifest(storage: LocalStorage, archive_name: str, manifest: dict) -> str:
    bundle_dir = storage.absolute_path(f"dev/proof_bundles/{archive_name}")
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return f"data/dev/proof_bundles/{archive_name}"


def _write_bundle_evidence(storage: LocalStorage, archive_name: str, filename: str, payload: dict) -> None:
    path = storage.absolute_path(f"dev/proof_bundles/{archive_name}/evidence/{filename}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _worsened_bundle_pair(storage: LocalStorage) -> tuple[str, str]:
    baseline_folder = _write_bundle_manifest(
        storage,
        "mrms_proof_bundle_digest_base",
        {
            "bundle_id": "good",
            "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_digest_base",
            "archive_name": "mrms_proof_bundle_digest_base",
            "files_included": ["evidence/mrms_proof_latest.json"],
            "files_missing": [],
        },
    )
    current_folder = _write_bundle_manifest(
        storage,
        "mrms_proof_bundle_digest_cur",
        {
            "bundle_id": "bad",
            "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_digest_cur",
            "archive_name": "mrms_proof_bundle_digest_cur",
            "files_included": ["evidence/mrms_proof_latest.json"],
            "files_missing": [],
        },
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_digest_base",
        "mrms_proof_latest.json",
        {
            "overall_status": "ready_for_operator_review",
            "criteria_counts": {"passed": 2, "failed": 0, "warning": 0, "skipped": 0},
        },
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_digest_cur",
        "mrms_proof_latest.json",
        {
            "overall_status": "failed",
            "criteria_counts": {"passed": 0, "failed": 3, "warning": 0, "skipped": 0},
        },
    )
    return baseline_folder, current_folder


def _seed_bundle_index(storage: LocalStorage, baseline_folder: str, current_folder: str) -> None:
    index = [
        {
            "bundle_id": "bad",
            "bundle_folder": current_folder,
            "created_at": "2026-06-28T12:01:00Z",
            "archive_name": current_folder.split("/")[-1],
        },
        {
            "bundle_id": "good",
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


def test_scheduled_digest_report_shape_when_not_requested(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    report = run_scheduled_validation(
        db_session,
        storage,
        count=1,
        persist=False,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )
    body = report.to_dict()
    assert body["digest_requested"] is False
    assert body["digest_generated"] is False
    assert body["digest_reason"] is None
    assert "escalation_digest" not in [step["name"] for step in body["steps"]]


def test_scheduled_digest_skipped_without_diff(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    report = run_scheduled_validation(
        db_session,
        storage,
        count=1,
        digest_requested=True,
        persist=False,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )
    body = report.to_dict()
    assert body["digest_requested"] is True
    assert body["digest_generated"] is False
    assert body["digest_reason"] == "skipped_diff_not_requested"
    digest_steps = [step for step in body["steps"] if step["name"] == "escalation_digest"]
    assert len(digest_steps) == 1
    assert digest_steps[0]["status"] == "skipped"


def test_scheduled_digest_runs_when_requested_with_diff(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    baseline_folder, current_folder = _worsened_bundle_pair(storage)
    _seed_bundle_index(storage, baseline_folder, current_folder)

    report = run_scheduled_validation(
        db_session,
        storage,
        count=1,
        diff_bundle_requested=True,
        handoff_requested=True,
        digest_requested=True,
        persist=True,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )
    body = report.to_dict()
    assert body["digest_requested"] is True
    assert body["digest_generated"] is True
    assert body["digest_reason"] == "generated"
    assert body["digest_path"]
    assert body["digest_metadata_path"]
    assert body["digest_elapsed_seconds"] is not None
    assert body["verified_mrms"] is False

    digest_md = storage.absolute_path(DIGEST_MD_PATH)
    digest_json = storage.absolute_path(DIGEST_JSON_PATH)
    assert digest_md.is_file()
    assert digest_json.is_file()


def test_scheduled_digest_does_not_clear_alerts(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    baseline_folder, current_folder = _worsened_bundle_pair(storage)
    _seed_bundle_index(storage, baseline_folder, current_folder)

    run_scheduled_validation(
        db_session,
        storage,
        count=1,
        diff_bundle_requested=True,
        digest_requested=True,
        persist=True,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert.get("operator_attention_needed") is True


def test_scheduled_digest_does_not_mutate_production_gates(
    client, db_session, storage, monkeypatch
):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    batch_fn, queue_fn = _mock_runners()
    baseline_folder, current_folder = _worsened_bundle_pair(storage)
    _seed_bundle_index(storage, baseline_folder, current_folder)

    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T09:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase39.grib2.gz"),
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
        digest_requested=True,
        persist=False,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )
    assert report.to_dict()["verified_mrms"] is False
    db_session.refresh(frame)
    assert frame.production_rendering is False

    response = client.get("/tiles/mrms_reflectivity/2026-06-28T09:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"


def test_scheduled_digest_does_not_trigger_stdout_without_notify_flag(
    db_session, storage, monkeypatch
):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    baseline_folder, current_folder = _worsened_bundle_pair(storage)
    _seed_bundle_index(storage, baseline_folder, current_folder)

    report = run_scheduled_validation(
        db_session,
        storage,
        diff_bundle_requested=True,
        digest_requested=True,
        notify_stdout=False,
        persist=False,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )
    body = report.to_dict()
    assert body["digest_generated"] is True
    assert body["notify_stdout_requested"] is False
    assert body["urgent_stdout_notice_triggered"] is False


def test_operator_checklist_includes_review_items(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    baseline_folder, current_folder = _worsened_bundle_pair(storage)
    _seed_bundle_index(storage, baseline_folder, current_folder)

    record = generate_operator_handoff(
        db_session,
        storage,
        include_escalation_review=True,
        auto_generated=True,
        trigger_reason="test",
    )
    markdown = storage.absolute_path("dev/mrms_operator_handoff_latest.md").read_text(encoding="utf-8")
    for item in REVIEW_CHECKLIST_ITEMS:
        assert item in markdown
    assert "Operator review checklist (Phase 39)" in markdown
    assert record["include_escalation_review"] is True
    assert record["review_checklist_count"] == len(REVIEW_CHECKLIST_ITEMS)
    assert record["verified_mrms"] is False


def test_validation_summary_includes_scheduled_digest_and_checklist(
    db_session, storage, monkeypatch
):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    batch_fn, queue_fn = _mock_runners()
    baseline_folder, current_folder = _worsened_bundle_pair(storage)
    _seed_bundle_index(storage, baseline_folder, current_folder)

    run_scheduled_validation(
        db_session,
        storage,
        diff_bundle_requested=True,
        handoff_requested=True,
        digest_requested=True,
        persist=True,
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_fn,
    )

    summary = build_validation_summary(db_session, storage)
    assert summary["verified_mrms"] is False
    scheduled_digest = summary.get("scheduled_digest")
    assert scheduled_digest is not None
    assert scheduled_digest["digest_requested"] is True
    assert scheduled_digest["digest_generated"] is True
    assert scheduled_digest["local_digest_only"] is True
    assert scheduled_digest["no_external_notifications"] is True

    handoff = summary.get("operator_handoff")
    assert handoff is not None
    assert handoff.get("include_escalation_review") is True
    assert handoff.get("review_checklist_count", 0) >= len(REVIEW_CHECKLIST_ITEMS)

    latest_digest = summary.get("proof_bundle_diff_escalation_digest")
    assert latest_digest is not None
    assert latest_digest.get("available") is True


def test_compact_scheduled_digest_from_report():
    scheduled = {
        "digest_requested": True,
        "digest_generated": True,
        "digest_path": "data/dev/proof_bundle_diff_escalation_digest_latest.md",
        "digest_metadata_path": "data/dev/proof_bundle_diff_escalation_digest_latest.json",
        "digest_reason": "generated",
        "digest_elapsed_seconds": 0.12,
    }
    compact = compact_scheduled_digest(scheduled)
    assert compact is not None
    assert compact["digest_generated"] is True
    assert compact["verified_mrms"] is False


def test_runtime_digest_artifacts_gitignored():
    gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
    text = gitignore.read_text(encoding="utf-8")
    assert "proof_bundle_diff_escalation_digest_latest.md" in text
    assert "mrms_operator_handoff_latest.md" in text
