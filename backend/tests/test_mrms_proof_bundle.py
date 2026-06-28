"""Tests for MRMS proof bundle export (Phase 30)."""

from __future__ import annotations

import json
import zipfile

import pytest

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.decoded_tile_cache import TILE_MODE_PLACEHOLDER
from backend.app.services.mrms_proof_bundle import (
    BUNDLE_README,
    export_mrms_proof_bundle,
    load_latest_proof_bundle_manifest,
)
from backend.app.services.mrms_proof_report import save_mrms_proof_report
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_dashboard import build_validation_summary


def _minimal_proof() -> dict:
    return {
        "generated_at": "2026-06-28T10:00:00Z",
        "overall_status": "insufficient_evidence",
        "frame_count": 1,
        "criteria_counts": {"passed": 0, "failed": 1, "warning": 0, "skipped": 0, "unknown": 0},
        "frames": [],
        "verified_mrms": False,
        "proof_only": True,
    }


def test_proof_bundle_manifest_shape(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_mrms_proof_report(storage, _minimal_proof())

    manifest = export_mrms_proof_bundle(db_session, storage, include_history=False)

    assert manifest["verified_mrms"] is False
    assert manifest["proof_only"] is True
    assert manifest["local_bundle_only"] is True
    assert manifest["does_not_enable_production"] is True
    assert manifest["bundle_id"]
    assert manifest["created_at"]
    assert manifest["file_count"] > 0
    assert isinstance(manifest["files_included"], list)
    assert isinstance(manifest["files_missing"], list)
    assert "manifest.json" in manifest["files_included"]


def test_missing_evidence_lists_files_missing_not_failure(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    manifest = export_mrms_proof_bundle(db_session, storage, include_history=False)

    assert manifest["verified_mrms"] is False
    assert len(manifest["files_missing"]) > 0
    assert manifest["file_count"] > 0


def test_bundle_readme_warnings(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    manifest = export_mrms_proof_bundle(db_session, storage, include_history=False)

    readme_path = storage.absolute_path(f"dev/proof_bundles/{manifest['archive_name']}/README.md")
    readme = readme_path.read_text(encoding="utf-8")
    assert "NOT** verify MRMS" in readme or "NOT verify MRMS" in readme
    assert "NOT** enable production rendering" in readme or "NOT enable production rendering" in readme
    assert BUNDLE_README[:40] in readme


def test_zip_export_works(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    manifest = export_mrms_proof_bundle(db_session, storage, include_history=False)

    zip_path = storage.absolute_path(manifest["zip_path"])
    assert zip_path.is_file()
    with zipfile.ZipFile(zip_path, "r") as archive:
        names = archive.namelist()
        assert any(name.endswith("manifest.json") for name in names)
        assert any(name.endswith("README.md") for name in names)


def test_validation_summary_includes_proof_bundle_status(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    export_mrms_proof_bundle(db_session, storage, include_history=False)

    summary = build_validation_summary(db_session, storage)
    bundle = summary["mrms_proof_bundle"]
    assert bundle["available"] is True
    assert bundle["verified_mrms"] is False
    assert bundle["file_count"] > 0
    assert len(summary["runbook_references"]) >= 4


def test_proof_bundles_endpoint(client, storage, monkeypatch, db_session):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    export_mrms_proof_bundle(db_session, storage, include_history=False)

    response = client.get("/api/validation/proof-bundles")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["count"] >= 1
    assert body["latest"]["available"] is True


def test_bundle_does_not_mutate_catalog_gates(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T05:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase30.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=False,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    manifest = export_mrms_proof_bundle(db_session, storage, include_history=False)
    assert manifest["verified_mrms"] is False

    db_session.refresh(frame)
    assert frame.production_rendering is False

    response = client.get("/tiles/mrms_reflectivity/2026-06-28T05:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"
    assert response.headers.get("x-radararchive-tile") in (
        TILE_MODE_PLACEHOLDER,
        "placeholder_for_real_raw",
    )


def test_latest_manifest_persisted(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    manifest = export_mrms_proof_bundle(db_session, storage, include_history=False)
    loaded = load_latest_proof_bundle_manifest(storage)
    assert loaded is not None
    assert loaded["bundle_id"] == manifest["bundle_id"]
