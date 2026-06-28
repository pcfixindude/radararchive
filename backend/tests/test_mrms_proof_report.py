"""Tests for draft MRMS proof report automation (Phase 26)."""

from __future__ import annotations

import gzip
import json
import struct

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.decoded_tile_cache import TILE_MODE_PLACEHOLDER
from backend.app.services.grib2_decoder import MANIFEST_NAME, RASTER_RAW_NAME, build_decode_output_dir
from backend.app.services.mrms_proof_report import (
    OVERALL_INSUFFICIENT,
    OVERALL_NOT_STARTED,
    STATUS_FAILED,
    STATUS_PASSED,
    bounds_inside_conus_mrms,
    compact_mrms_proof_report,
    evaluate_frame_criteria,
    evaluate_geo_sanity,
    generate_mrms_proof_report,
    load_mrms_proof_report,
    resolve_overall_proof_status,
    save_mrms_proof_report,
)
from backend.app.services.render_metadata import GeoRenderMetadata, build_geo_metadata_for_decode, write_geo_metadata
from backend.app.services.storage import LocalStorage
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE


def _write_decode_fixture(storage: LocalStorage, raw_path: str, *, timestamp: str = "2026-06-28T02:00:00Z") -> str:
    output_dir = build_decode_output_dir(storage, raw_path)
    storage.ensure_directories(output_dir)
    grid_values = [i / 15.0 for i in range(16)]
    raster_path = storage.normalize_path(output_dir, RASTER_RAW_NAME)
    storage.write_bytes(raster_path, struct.pack(f"{len(grid_values)}f", *grid_values))
    manifest = {
        "prototype": True,
        "production_rendering": False,
        "raw_path": raw_path,
        "decoder": "mock",
        "width": 4,
        "height": 4,
        "raster_path": RASTER_RAW_NAME,
        "valid_timestamp": timestamp,
    }
    manifest_path = storage.normalize_path(output_dir, MANIFEST_NAME)
    storage.absolute_path(manifest_path).write_text(json.dumps(manifest), encoding="utf-8")
    geo = build_geo_metadata_for_decode(grid_width=4, grid_height=4)
    geo.valid_timestamp = timestamp
    write_geo_metadata(storage, output_dir, geo)
    return output_dir


def test_bounds_inside_conus_mrms():
    assert bounds_inside_conus_mrms([-125.0, 24.0, -66.0, 50.0]) is True
    assert bounds_inside_conus_mrms([0.0, 0.0, 1.0, 1.0]) is False


def test_geo_sanity_helper_behavior(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "geo_proof.grib2.gz")
    output_dir = _write_decode_fixture(storage, raw_path)
    geo = build_geo_metadata_for_decode(grid_width=4, grid_height=4)
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T02:00:00Z",
        raw_path=raw_path,
    )
    result = evaluate_geo_sanity(storage, frame=frame, geo_metadata=geo)
    assert result.crs_present is True
    assert result.bounds_valid is True
    assert result.grid_positive is True
    assert result.bounds_in_conus is True
    assert result.transform_ok is True
    assert output_dir


def test_criterion_evaluation_stub_fails_real_source(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    evidence = {
        "raw_path": "data/raw/demo/foo.stub",
        "raw_kind": "demo_seeded_stub",
        "layer": "mrms_reflectivity",
        "timestamp": "2026-06-28T01:00:00Z",
        "geo_metadata": None,
        "geo_sanity": {},
        "tiles_written": 0,
        "decode_artifact_path": None,
        "decoder_available": False,
        "production_rendering": False,
        "render_status": "placeholder",
    }
    criteria = evaluate_frame_criteria(evidence)
    by_id = {item["criterion_id"]: item for item in criteria}
    assert by_id["real_noaa_source"]["status"] == STATUS_FAILED
    assert by_id["tile_output_from_decoded"]["status"] == STATUS_FAILED


def test_proof_report_shape_stub_mode(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    report = generate_mrms_proof_report(db_session, storage, count=3, source_mode="stub")
    assert report["verified_mrms"] is False
    assert report["proof_only"] is True
    assert report["operator_review_required"] is True
    assert report["frame_count"] >= 1
    assert "aggregate_criteria" in report
    assert "criteria_counts" in report
    assert report["overall_status"] in (
        OVERALL_INSUFFICIENT,
        OVERALL_NOT_STARTED,
        "failed",
        "ready_for_operator_review",
    )


def test_missing_artifacts_insufficient_not_verified(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    report = generate_mrms_proof_report(db_session, storage, count=2, source_mode="stub")
    assert report["verified_mrms"] is False
    assert report["overall_status"] in (OVERALL_INSUFFICIENT, "failed")


def test_multi_frame_proof_aggregation(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    for idx in range(3):
        ts = f"2026-06-28T0{idx}:00:00Z"
        raw_path = storage.normalize_path("raw", "mrms", "reflectivity", f"multi_{idx}.grib2.gz")
        storage.write_bytes(raw_path, gzip.compress(b"GRIB" + b"\x00" * 8))
        _write_decode_fixture(storage, raw_path, timestamp=ts)
        db_session.add(
            RadarFile(
                product_id="mrms_reflectivity",
                timestamp=ts,
                raw_path=raw_path,
                source=MRMS_CATALOG_SOURCE,
                download_status="downloaded",
                sha256=storage.sha256(raw_path),
            )
        )
    db_session.commit()

    report = generate_mrms_proof_report(db_session, storage, count=3, source_mode="real")
    assert report["frame_count"] == 3
    multi = next(c for c in report["aggregate_criteria"] if c["criterion_id"] == "repeatable_multi_frame")
    assert multi["status"] in (STATUS_PASSED, "warning")


def test_proof_report_persistence(storage, db_session, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    report = generate_mrms_proof_report(db_session, storage, count=1, source_mode="stub")
    save_mrms_proof_report(storage, report)
    loaded = load_mrms_proof_report(storage)
    assert loaded is not None
    assert loaded["verified_mrms"] is False


def test_summary_includes_compact_proof_status(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    report = generate_mrms_proof_report(db_session, storage, count=2, source_mode="stub")
    save_mrms_proof_report(storage, report)

    response = client.get("/api/validation/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["mrms_proof_available"] is True
    assert body["mrms_proof"] is not None
    assert body["mrms_proof"]["verified_mrms"] is False
    assert body["mrms_proof"]["operator_review_required"] is True
    assert body["mrms_proof"]["proof_only"] is True


def test_proof_endpoint(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/proof")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["proof_only"] is True


def test_compact_proof_not_started():
    compact = compact_mrms_proof_report(None)
    assert compact["overall_status"] == OVERALL_NOT_STARTED
    assert compact["verified_mrms"] is False


def test_resolve_overall_insufficient_when_all_skipped():
    criteria = [
        {"criterion_id": "real_noaa_source", "status": STATUS_FAILED},
        {"criterion_id": "decoder_and_artifacts", "status": "skipped"},
    ]
    assert resolve_overall_proof_status(frame_count=1, aggregate_criteria=criteria) == "failed"


def test_production_tile_serving_still_gated_phase26(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    timestamp = "2026-06-28T03:00:00Z"
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase26_gate.grib2.gz"),
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
