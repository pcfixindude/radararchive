"""Tests for local MRMS render pipeline (Phase 103)."""

from __future__ import annotations

import json
import struct

from backend.app.config import settings
from backend.app.demo.seed import seed_demo_catalog
from backend.app.models import RadarFile
from backend.app.services.grib2_decoder import MANIFEST_NAME, RASTER_RAW_NAME, build_decode_output_dir
from backend.app.services.mrms_local_render_pipeline import (
    PIPELINE_JSON,
    STATUS_DECODER_MISSING,
    STATUS_PREVIEW_OK,
    STATUS_STUB_INPUT,
    SUGGESTED_COMMAND,
    compact_local_render_pipeline,
    run_local_render_pipeline,
    select_pipeline_candidate,
)
from backend.app.services.raw_file_classifier import RAW_KIND_MRMS_REAL_GRIB2
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def _write_real_grib2_stub_file(storage, rel_path: str) -> None:
    storage.ensure_directories(rel_path.rsplit("/", 1)[0])
    storage.write_bytes(rel_path, b"\x1f\x8b" + b"GRIB" + b"\x00" * 20)


def _write_decode_fixture(storage, raw_path: str, *, width: int = 4, height: int = 4) -> str:
    output_dir = build_decode_output_dir(storage, raw_path)
    storage.ensure_directories(output_dir)
    grid_values = [i / 15.0 for i in range(width * height)]
    raster_path = storage.normalize_path(output_dir, RASTER_RAW_NAME)
    storage.write_bytes(raster_path, struct.pack(f"{len(grid_values)}f", *grid_values))
    manifest = {
        "prototype": True,
        "production_rendering": False,
        "raw_path": raw_path,
        "decoder": "mock",
        "width": width,
        "height": height,
        "raster_path": RASTER_RAW_NAME,
    }
    manifest_path = storage.normalize_path(output_dir, MANIFEST_NAME)
    storage.absolute_path(manifest_path).write_text(json.dumps(manifest), encoding="utf-8")
    return output_dir


def test_select_candidate_prefers_real_grib2(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "test.grib2.gz")
    _write_real_grib2_stub_file(storage, raw_path)
    row = RadarFile(
        timestamp="2026-06-28T12:00:00Z",
        product_id="mrms_reflectivity",
        source=MRMS_CATALOG_SOURCE,
        raw_path=raw_path,
        raw_kind=RAW_KIND_MRMS_REAL_GRIB2,
        download_status="downloaded",
    )
    db_session.add(row)
    db_session.commit()
    selected = select_pipeline_candidate(db_session, storage)
    assert selected is not None
    assert selected["is_real_grib2"] is True
    assert selected["raw_path"] == raw_path


def test_pipeline_stub_input_produces_placeholder_preview(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    seed_demo_catalog(db_session, storage=storage)
    report = run_local_render_pipeline(db_session, storage)
    assert report["pipeline_status"] in {STATUS_STUB_INPUT, STATUS_DECODER_MISSING, STATUS_PREVIEW_OK}
    assert report["produced_local_artifact"] is True
    assert report["preview_paths"]
    assert storage.absolute_path(PIPELINE_JSON).is_file()


def test_pipeline_decoded_preview_with_fixture(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "fixture.grib2.gz")
    _write_real_grib2_stub_file(storage, raw_path)
    row = RadarFile(
        timestamp="2026-06-28T12:00:00Z",
        product_id="mrms_reflectivity",
        source=MRMS_CATALOG_SOURCE,
        raw_path=raw_path,
        raw_kind=RAW_KIND_MRMS_REAL_GRIB2,
        download_status="downloaded",
    )
    db_session.add(row)
    db_session.commit()
    _write_decode_fixture(storage, raw_path)

    class _MockDecoder:
        any_decoder = True
        wgrib2 = True
        wgrib2_path = "/usr/bin/wgrib2"
        gdal = False
        rasterio = False
        pygrib = False
        cfgrib = False

        def summary_message(self) -> str:
            return "wgrib2 available"

    monkeypatch.setattr(
        "backend.app.services.mrms_local_render_pipeline.detect_decoder_availability",
        lambda: _MockDecoder(),
    )

    from backend.app.services.grib2_decoder import Grib2DecodeResult

    def _mock_decode(storage, raw_path, **kwargs):
        output_dir = _write_decode_fixture(storage, raw_path)
        return Grib2DecodeResult(
            raw_path=raw_path,
            raw_kind=RAW_KIND_MRMS_REAL_GRIB2,
            success=True,
            decoder_used="mock",
            output_dir=output_dir,
            manifest_path=storage.normalize_path(output_dir, MANIFEST_NAME),
            raster_path=storage.normalize_path(output_dir, RASTER_RAW_NAME),
            width=4,
            height=4,
        )

    monkeypatch.setattr(
        "backend.app.services.mrms_local_render_pipeline.decode_grib2_file",
        _mock_decode,
    )
    monkeypatch.setattr(
        "backend.app.services.mrms_local_render_pipeline.inspect_grib2_file",
        lambda storage, raw_path: type(
            "Inspect",
            (),
            {"inspectable": True, "file_exists": True, "raw_kind": RAW_KIND_MRMS_REAL_GRIB2, "error": None},
        )(),
    )

    report = run_local_render_pipeline(db_session, storage)
    assert report["pipeline_status"] == STATUS_PREVIEW_OK
    assert report["render_mode"] == "decoded_prototype"
    assert report["produced_local_artifact"] is True


def test_pipeline_decoder_missing_documents_blocker(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "real.grib2.gz")
    _write_real_grib2_stub_file(storage, raw_path)
    row = RadarFile(
        timestamp="2026-06-28T12:00:00Z",
        product_id="mrms_reflectivity",
        source=MRMS_CATALOG_SOURCE,
        raw_path=raw_path,
        raw_kind=RAW_KIND_MRMS_REAL_GRIB2,
        download_status="downloaded",
    )
    db_session.add(row)
    db_session.commit()

    class _NoDecoder:
        any_decoder = False
        wgrib2 = False
        wgrib2_path = None
        gdal = False
        rasterio = False
        pygrib = False
        cfgrib = False

        def summary_message(self) -> str:
            return "No GRIB2 decoder tools detected."

    monkeypatch.setattr(
        "backend.app.services.mrms_local_render_pipeline.detect_decoder_availability",
        lambda: _NoDecoder(),
    )
    monkeypatch.setattr(
        "backend.app.services.mrms_local_render_pipeline.inspect_grib2_file",
        lambda storage, raw_path: type(
            "Inspect",
            (),
            {"inspectable": True, "file_exists": True, "raw_kind": RAW_KIND_MRMS_REAL_GRIB2, "error": None},
        )(),
    )

    report = run_local_render_pipeline(db_session, storage)
    assert report["pipeline_status"] == STATUS_DECODER_MISSING
    assert report["blocker"] == "decoder_missing"
    assert report["produced_local_artifact"] is True
    assert report["render_mode"] == "placeholder_decoder_missing"


def test_compact_before_run(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_local_render_pipeline(storage)
    assert compact["available"] is False
    assert compact["suggested_command"] == SUGGESTED_COMMAND
