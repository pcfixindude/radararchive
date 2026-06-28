"""Tests for MRMS proof bundle diff and operator handoff (Phase 31)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.decoded_tile_cache import TILE_MODE_PLACEHOLDER
from backend.app.services.mrms_operator_handoff import (
    HANDOFF_MD_PATH,
    generate_operator_handoff,
    load_latest_operator_handoff,
)
from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_IMPROVED,
    DIFF_MIXED,
    DIFF_NO_BASELINE,
    DIFF_UNCHANGED,
    DIFF_UNKNOWN,
    DIFF_WORSENED,
    build_proof_bundle_diff_report,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_dashboard import build_validation_summary


def _write_bundle_manifest(storage: LocalStorage, archive_name: str, manifest: dict) -> str:
    bundle_dir = storage.absolute_path(f"dev/proof_bundles/{archive_name}")
    bundle_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir = bundle_dir / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    (bundle_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return f"data/dev/proof_bundles/{archive_name}"


def _write_bundle_evidence(storage: LocalStorage, archive_name: str, filename: str, payload: dict) -> None:
    path = storage.absolute_path(f"dev/proof_bundles/{archive_name}/evidence/{filename}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_proof_bundle_diff_report_shape(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    baseline_folder = _write_bundle_manifest(
        storage,
        "mrms_proof_bundle_baseline",
        {
            "bundle_id": "baseline-id",
            "created_at": "2026-06-28T10:00:00Z",
            "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_baseline",
            "archive_name": "mrms_proof_bundle_baseline",
            "files_included": ["evidence/mrms_proof_latest.json"],
            "files_missing": [],
        },
    )
    current_folder = _write_bundle_manifest(
        storage,
        "mrms_proof_bundle_current",
        {
            "bundle_id": "current-id",
            "created_at": "2026-06-28T11:00:00Z",
            "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_current",
            "archive_name": "mrms_proof_bundle_current",
            "files_included": ["evidence/mrms_proof_latest.json"],
            "files_missing": [],
        },
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_baseline",
        "mrms_proof_latest.json",
        {"overall_status": "failed", "criteria_counts": {"passed": 0, "failed": 2, "warning": 0, "skipped": 0}},
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_current",
        "mrms_proof_latest.json",
        {"overall_status": "insufficient_evidence", "criteria_counts": {"passed": 1, "failed": 1, "warning": 0, "skipped": 0}},
    )

    report = build_proof_bundle_diff_report(
        storage,
        current_bundle_folder=current_folder,
        baseline_bundle_folder=baseline_folder,
    )

    assert report["verified_mrms"] is False
    assert report["local_diff_only"] is True
    assert report["does_not_enable_production"] is True
    assert report["overall_diff_status"] in (DIFF_IMPROVED, DIFF_MIXED, DIFF_UNCHANGED)
    assert "proof_status_change" in report
    assert report["current_bundle"]["bundle_id"] == "current-id"
    assert report["baseline_bundle"]["bundle_id"] == "baseline-id"


def test_no_baseline_behavior(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    current_folder = _write_bundle_manifest(
        storage,
        "mrms_proof_bundle_only",
        {
            "bundle_id": "only-id",
            "created_at": "2026-06-28T10:00:00Z",
            "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_only",
            "archive_name": "mrms_proof_bundle_only",
            "files_included": [],
            "files_missing": ["evidence/mrms_proof_latest.json"],
        },
    )

    report = build_proof_bundle_diff_report(
        storage,
        current_bundle_folder=current_folder,
        baseline_bundle_folder=None,
    )
    assert report["overall_diff_status"] == DIFF_NO_BASELINE
    assert report["verified_mrms"] is False
    assert any("baseline" in warning.lower() for warning in report.get("warnings", []))


def test_unchanged_bundle_comparison(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    payload = {
        "overall_status": "failed",
        "criteria_counts": {"passed": 0, "failed": 2, "warning": 0, "skipped": 0},
    }
    for name in ("mrms_proof_bundle_a", "mrms_proof_bundle_b"):
        folder = _write_bundle_manifest(
            storage,
            name,
            {
                "bundle_id": f"{name}-id",
                "created_at": "2026-06-28T10:00:00Z",
                "bundle_folder": f"data/dev/proof_bundles/{name}",
                "archive_name": name,
                "files_included": ["evidence/mrms_proof_latest.json"],
                "files_missing": [],
            },
        )
        _write_bundle_evidence(storage, name, "mrms_proof_latest.json", payload)

    report = build_proof_bundle_diff_report(
        storage,
        current_bundle_folder="data/dev/proof_bundles/mrms_proof_bundle_b",
        baseline_bundle_folder="data/dev/proof_bundles/mrms_proof_bundle_a",
    )
    assert report["overall_diff_status"] == DIFF_UNCHANGED
    assert report["evidence_changes_count"] == 0


def test_worsened_diff_classification(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _write_bundle_manifest(
        storage,
        "mrms_proof_bundle_good",
        {
            "bundle_id": "good",
            "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_good",
            "archive_name": "mrms_proof_bundle_good",
            "files_included": ["evidence/mrms_proof_latest.json", "evidence/mrms_proof_regression_latest.json"],
            "files_missing": [],
        },
    )
    _write_bundle_manifest(
        storage,
        "mrms_proof_bundle_bad",
        {
            "bundle_id": "bad",
            "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_bad",
            "archive_name": "mrms_proof_bundle_bad",
            "files_included": ["evidence/mrms_proof_latest.json", "evidence/mrms_proof_regression_latest.json"],
            "files_missing": [],
        },
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_good",
        "mrms_proof_latest.json",
        {"overall_status": "ready_for_operator_review", "criteria_counts": {"passed": 2, "failed": 0, "warning": 0, "skipped": 0}},
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_bad",
        "mrms_proof_latest.json",
        {"overall_status": "failed", "criteria_counts": {"passed": 0, "failed": 3, "warning": 0, "skipped": 0}},
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_good",
        "mrms_proof_regression_latest.json",
        {"regression_detected": False, "regression_status": "none"},
    )
    _write_bundle_evidence(
        storage,
        "mrms_proof_bundle_bad",
        "mrms_proof_regression_latest.json",
        {"regression_detected": True, "regression_status": "regression_detected"},
    )

    report = build_proof_bundle_diff_report(
        storage,
        current_bundle_folder="data/dev/proof_bundles/mrms_proof_bundle_bad",
        baseline_bundle_folder="data/dev/proof_bundles/mrms_proof_bundle_good",
    )
    assert report["overall_diff_status"] == DIFF_WORSENED


def test_missing_files_reported_not_fatal(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    report = build_proof_bundle_diff_report(
        storage,
        current_bundle_folder=_write_bundle_manifest(
            storage,
            "mrms_proof_bundle_missing",
            {
                "bundle_id": "cur",
                "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_missing",
                "archive_name": "mrms_proof_bundle_missing",
                "files_included": [],
                "files_missing": ["evidence/mrms_proof_latest.json"],
            },
        ),
        baseline_bundle_folder=_write_bundle_manifest(
            storage,
            "mrms_proof_bundle_missing_base",
            {
                "bundle_id": "base",
                "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_missing_base",
                "archive_name": "mrms_proof_bundle_missing_base",
                "files_included": [],
                "files_missing": ["evidence/mrms_proof_latest.json"],
            },
        ),
    )
    assert report["verified_mrms"] is False
    assert report["overall_diff_status"] in (DIFF_UNKNOWN, DIFF_UNCHANGED, DIFF_NO_BASELINE)


def test_handoff_checklist_warnings(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record = generate_operator_handoff(db_session, storage)
    md_path = storage.absolute_path(HANDOFF_MD_PATH)
    content = md_path.read_text(encoding="utf-8")
    assert "does **NOT** verify MRMS" in content
    assert "verified_mrms` remains **false**" in content
    assert record["verified_mrms"] is False
    assert record["does_not_enable_production"] is True
    assert load_latest_operator_handoff(storage) is not None


def test_validation_summary_includes_diff_and_handoff(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    generate_operator_handoff(db_session, storage)
    build_proof_bundle_diff_report(
        storage,
        current_bundle_folder=_write_bundle_manifest(
            storage,
            "mrms_proof_bundle_summary",
            {
                "bundle_id": "s",
                "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_summary",
                "archive_name": "mrms_proof_bundle_summary",
                "files_included": [],
                "files_missing": [],
            },
        ),
        baseline_bundle_folder=None,
    )
    summary = build_validation_summary(db_session, storage)
    assert summary["mrms_proof_bundle_diff"]["verified_mrms"] is False
    assert summary["operator_handoff"]["verified_mrms"] is False
    assert summary["operator_handoff"]["available"] is True


def test_gitignore_covers_proof_bundle_artifacts():
    gitignore = Path("/Users/irds/Projects/radararchive/.gitignore").read_text(encoding="utf-8")
    assert "data/dev/proof_bundles/" in gitignore
    assert "data/dev/mrms_proof_bundle_diff_latest.json" in gitignore
    assert "data/dev/mrms_operator_handoff_latest.md" in gitignore


def test_handoff_does_not_mutate_catalog_gates(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T06:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase31.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=False,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    generate_operator_handoff(db_session, storage)
    build_proof_bundle_diff_report(
        storage,
        current_bundle_folder=_write_bundle_manifest(
            storage,
            "mrms_proof_bundle_gate",
            {
                "bundle_id": "g",
                "bundle_folder": "data/dev/proof_bundles/mrms_proof_bundle_gate",
                "archive_name": "mrms_proof_bundle_gate",
                "files_included": [],
                "files_missing": [],
            },
        ),
        baseline_bundle_folder=None,
    )

    db_session.refresh(frame)
    assert frame.production_rendering is False

    response = client.get("/tiles/mrms_reflectivity/2026-06-28T06:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"
    assert response.headers.get("x-radararchive-tile") in (
        TILE_MODE_PLACEHOLDER,
        "placeholder_for_real_raw",
    )


def test_proof_bundle_diff_endpoint(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/proof-bundle-diff?refresh=true")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["report"]["verified_mrms"] is False


def test_operator_handoff_endpoint(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    generate_operator_handoff(db_session, storage)
    response = client.get("/api/validation/operator-handoff")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["handoff"]["verified_mrms"] is False
