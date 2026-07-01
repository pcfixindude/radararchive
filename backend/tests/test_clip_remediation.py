"""Tests for imported clip batch remediation plan (Phase 126)."""

from __future__ import annotations

import json

from backend.app.config import settings
from backend.app.services.clip_import import build_clip_import_report
from backend.app.services.clip_remediation import (
    PLAN_STATUS_EMPTY,
    PLAN_STATUS_READY,
    build_clip_remediation_plan,
)
from backend.app.services.playback_export import EXPORT_KIND


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)


def _register_real_frame(db_session, storage, ts: str):
    from backend.app.models import Layer, Product, RadarFile
    from backend.app.services.raw_file_classifier import RAW_KIND_MRMS_REAL_GRIB2
    from backend.app.sources.mrms import MRMS_CATALOG_SOURCE

    layer = db_session.get(Layer, "mrms_reflectivity")
    if layer is None:
        layer = Layer(id="mrms_reflectivity", name="MRMS Reflectivity", type="raster", available=True)
        db_session.add(layer)
    product = db_session.get(Product, "mrms_reflectivity")
    if product is None:
        product = Product(id="mrms_reflectivity", layer_id="mrms_reflectivity", name="MRMS Reflectivity")
        db_session.add(product)
    raw_path = storage.normalize_path(
        "raw/mrms/reflectivity",
        f"MRMS_ReflectivityAtLowestAltitude.{ts.replace(':', '').replace('-', '')}.grib2.gz",
    )
    storage.ensure_directories(storage.normalize_path("raw/mrms/reflectivity"))
    storage.write_bytes(raw_path, b"fake-grib2")
    row = RadarFile(
        timestamp=ts,
        product_id="mrms_reflectivity",
        raw_path=raw_path,
        raw_kind=RAW_KIND_MRMS_REAL_GRIB2,
        source=MRMS_CATALOG_SOURCE,
    )
    db_session.add(row)
    db_session.commit()


def _sample_export_manifest(ts_old: str, ts_new: str) -> dict:
    return {
        "clip_id": "clip_test",
        "export_kind": EXPORT_KIND,
        "layer_id": "mrms_reflectivity",
        "range_start": ts_old,
        "range_end": ts_new,
        "range_order_adjusted": False,
        "loop_suggested": True,
        "frame_count": 2,
        "frames": [
            {
                "timestamp": ts_old,
                "index": 0,
                "cache_state": "ready",
                "cache_ready": True,
                "decode_ready": False,
            },
            {
                "timestamp": ts_new,
                "index": 1,
                "cache_state": "cold_no_manifest",
                "cache_ready": False,
                "decode_ready": False,
            },
        ],
        "exported_at": "2026-06-28T14:00:00Z",
        "status": "ready",
        "verified_mrms": False,
    }


def test_build_clip_remediation_plan_empty_when_all_ready():
    import_report = {
        "valid": True,
        "manifest": {"clip_id": "clip_ok", "range_start": "2026-06-28T13:00:00Z", "range_end": "2026-06-28T13:26:38Z"},
        "problem_frames": [],
    }
    plan = build_clip_remediation_plan(import_report)
    assert plan["plan_status"] == PLAN_STATUS_EMPTY
    assert plan["commands"] == []
    assert plan["commands_not_auto_run"] is True
    assert plan["verified_mrms"] is False


def test_build_clip_remediation_plan_groups_cold_frames(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts_old = "2026-06-28T13:00:00Z"
    ts_new = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts_old)
    _register_real_frame(db_session, storage, ts_new)

    import_report = build_clip_import_report(db_session, storage, _sample_export_manifest(ts_old, ts_new))
    plan = build_clip_remediation_plan(import_report)

    assert plan["plan_status"] == PLAN_STATUS_READY
    assert plan["group_summary"]["total_problem_count"] >= 1
    assert plan["group_summary"]["cold_count"] >= 1 or plan["group_summary"]["partial_count"] >= 1
    assert plan["problem_groups"]
    assert plan["commands"]
    assert plan["command_block"]
    assert "NOT auto-run" in plan["command_block"]
    assert any("mrms-warm-frame-cache" in step["command"] for step in plan["commands"])
    assert plan["does_not_run_ingest"] is True


def test_build_clip_remediation_plan_respects_limit(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts_list = [f"2026-06-28T13:{minute:02d}:00Z" for minute in range(0, 20, 2)]
    for ts in ts_list:
        _register_real_frame(db_session, storage, ts)

    manifest = {
        "export_kind": EXPORT_KIND,
        "range_start": ts_list[0],
        "range_end": ts_list[-1],
        "frames": [
            {
                "timestamp": ts,
                "index": index,
                "cache_state": "cold_no_manifest",
                "cache_ready": False,
                "decode_ready": False,
            }
            for index, ts in enumerate(ts_list)
        ],
    }
    import_report = build_clip_import_report(db_session, storage, manifest)
    plan = build_clip_remediation_plan(import_report, limit=3)

    assert plan["bounded_frame_limit"] == 3
    assert plan["group_summary"]["assessed_count"] <= 3
    assert plan["truncated"] is True


def test_clip_import_includes_remediation_plan(db_session, storage, monkeypatch, client):
    _use_test_storage(monkeypatch, storage)
    ts_old = "2026-06-28T13:00:00Z"
    ts_new = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts_old)
    _register_real_frame(db_session, storage, ts_new)

    response = client.post(
        "/api/dev/clip-import",
        json={"manifest": _sample_export_manifest(ts_old, ts_new)},
    )
    assert response.status_code == 200
    body = response.json()
    assert "remediation_plan" in body
    assert body["remediation_plan"]["plan_status"] in {PLAN_STATUS_READY, PLAN_STATUS_EMPTY}


def test_clip_remediation_api_from_manifest(client, storage, db_session, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    ts_old = "2026-06-28T13:00:00Z"
    ts_new = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts_old)
    _register_real_frame(db_session, storage, ts_new)

    response = client.post(
        "/api/dev/clip-remediation",
        json={"manifest": _sample_export_manifest(ts_old, ts_new), "limit": 8},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["plan_status"] == PLAN_STATUS_READY
    assert body["commands_not_auto_run"] is True
    assert body["command_block"]


def test_clip_remediation_api_from_import_report(client):
    import_report = {
        "valid": True,
        "manifest": {
            "clip_id": "clip_x",
            "range_start": "2026-06-28T13:00:00Z",
            "range_end": "2026-06-28T13:26:38Z",
        },
        "problem_frames": [
            {
                "timestamp": "2026-06-28T13:26:38Z",
                "readiness_summary": "cold",
                "cache_state": "cold_no_manifest",
                "decode_ready": False,
            }
        ],
    }
    response = client.post(
        "/api/dev/clip-remediation",
        json={"import_report": import_report},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["plan_status"] == PLAN_STATUS_READY
    assert body["group_summary"]["cold_count"] == 1


def test_clip_remediation_cli_from_manifest(db_session, storage, monkeypatch, tmp_path):
    _use_test_storage(monkeypatch, storage)
    ts_old = "2026-06-28T13:00:00Z"
    ts_new = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts_old)
    _register_real_frame(db_session, storage, ts_new)

    manifest_path = tmp_path / "clip.json"
    manifest_path.write_text(json.dumps(_sample_export_manifest(ts_old, ts_new)), encoding="utf-8")

    from scripts import clip_remediation as clip_remediation_script

    monkeypatch.setattr("sys.argv", ["clip_remediation.py", "--file", str(manifest_path)])
    clip_remediation_script.main()

    plan_path = storage.absolute_path("dev/clip_remediation_latest.json")
    assert plan_path.is_file()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["plan_status"] == PLAN_STATUS_READY


def test_clip_remediation_cli_from_import_report(db_session, storage, monkeypatch, tmp_path):
    _use_test_storage(monkeypatch, storage)
    ts_old = "2026-06-28T13:00:00Z"
    ts_new = "2026-06-28T13:26:38Z"
    _register_real_frame(db_session, storage, ts_old)
    _register_real_frame(db_session, storage, ts_new)

    import_report = build_clip_import_report(db_session, storage, _sample_export_manifest(ts_old, ts_new))
    report_path = tmp_path / "clip_import.json"
    report_path.write_text(json.dumps(import_report), encoding="utf-8")

    from scripts import clip_remediation as clip_remediation_script

    monkeypatch.setattr("sys.argv", ["clip_remediation.py", "--file", str(report_path)])
    clip_remediation_script.main()

    plan_path = storage.absolute_path("dev/clip_remediation_latest.json")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["commands"]
