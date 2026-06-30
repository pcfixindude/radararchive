"""Tests for decoder setup and decode retry (Phase 104)."""

from __future__ import annotations

import json
import struct
from types import SimpleNamespace

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.services.decode_retry import RETRY_JSON, run_decode_retry
from backend.app.services.decoder_setup import (
    SETUP_JSON,
    SUGGESTED_DECODE_RETRY_COMMAND,
    SUGGESTED_INSTALL_COMMAND,
    gather_decoder_setup_status,
    install_decoders_in_venv,
    mac_setup_instructions,
    save_decoder_setup_report,
)
from backend.app.services.grib2_decoder import MANIFEST_NAME, RASTER_RAW_NAME, Grib2DecodeResult, build_decode_output_dir
from backend.app.services.mrms_local_render_pipeline import STATUS_PREVIEW_OK
from backend.app.services.raw_file_classifier import RAW_KIND_MRMS_REAL_GRIB2
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)


def test_gather_decoder_setup_status_shape(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    status = gather_decoder_setup_status()
    assert "decoder" in status
    assert "ready_for_decode" in status
    assert status["verified_mrms"] is False
    assert status["suggested_install_command"] == SUGGESTED_INSTALL_COMMAND


def test_mac_setup_instructions_include_decode_retry():
    steps = {item["step"] for item in mac_setup_instructions()}
    assert "install_python" in steps
    assert "retry_all" in steps


def test_save_decoder_setup_report(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = save_decoder_setup_report(storage, gather_decoder_setup_status())
    assert storage.absolute_path(SETUP_JSON).is_file()
    assert report["json_path"]


def test_install_decoders_in_venv_mock(monkeypatch):
  class _Completed:
      returncode = 0
      stdout = "ok"
      stderr = ""

  monkeypatch.setattr(
      "backend.app.services.decoder_setup.detect_decoder_availability",
      lambda: SimpleNamespace(
          any_decoder=True,
          wgrib2=False,
          wgrib2_path=None,
          gdal=False,
          rasterio=True,
          pygrib=False,
          cfgrib=False,
          summary_message=lambda: "rasterio",
      ),
  )
  result = install_decoders_in_venv(pip_runner=lambda *a, **k: _Completed())
  assert result["success"] is True
  assert result["install_attempted"] is True


def _write_real_grib2_stub_file(storage, rel_path: str) -> None:
    storage.ensure_directories(rel_path.rsplit("/", 1)[0])
    storage.write_bytes(rel_path, b"\x1f\x8b" + b"GRIB" + b"\x00" * 20)


def _write_decode_fixture(storage, raw_path: str, *, width: int = 8, height: int = 4) -> str:
    output_dir = build_decode_output_dir(storage, raw_path)
    storage.ensure_directories(output_dir)
    grid_values = [i / 31.0 for i in range(width * height)]
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


def test_decode_retry_decoder_missing(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    monkeypatch.setattr(
        "backend.app.services.decode_retry.detect_decoder_availability",
        lambda: SimpleNamespace(
            any_decoder=False,
            wgrib2=False,
            wgrib2_path=None,
            gdal=False,
            rasterio=False,
            pygrib=False,
            cfgrib=False,
            summary_message=lambda: "No decoders",
        ),
    )
    monkeypatch.setattr(
        "backend.app.services.decoder_setup.detect_decoder_availability",
        lambda: SimpleNamespace(
            any_decoder=False,
            wgrib2=False,
            wgrib2_path=None,
            gdal=False,
            rasterio=False,
            pygrib=False,
            cfgrib=False,
            summary_message=lambda: "No decoders",
        ),
    )
    report = run_decode_retry(db_session, storage)
    assert report["decode_retry_status"] == "decoder_missing"
    assert report["produced_decoded_preview"] is False
    assert storage.absolute_path(RETRY_JSON).is_file()


def test_decode_retry_success_with_mocks(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "fixture.grib2.gz")
    _write_real_grib2_stub_file(storage, raw_path)
    row = RadarFile(
        timestamp="2026-06-28T13:26:38Z",
        product_id="mrms_reflectivity",
        source=MRMS_CATALOG_SOURCE,
        raw_path=raw_path,
        raw_kind=RAW_KIND_MRMS_REAL_GRIB2,
        download_status="downloaded",
    )
    db_session.add(row)
    db_session.commit()

    decoder = SimpleNamespace(
        any_decoder=True,
        wgrib2=False,
        wgrib2_path=None,
        gdal=False,
        rasterio=True,
        pygrib=False,
        cfgrib=False,
        summary_message=lambda: "rasterio",
    )
    monkeypatch.setattr("backend.app.services.decode_retry.detect_decoder_availability", lambda: decoder)
    monkeypatch.setattr("backend.app.services.decoder_setup.detect_decoder_availability", lambda: decoder)

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
            width=8,
            height=4,
        )

    monkeypatch.setattr("backend.app.services.decode_retry.decode_grib2_file", _mock_decode)
    monkeypatch.setattr(
        "backend.app.services.mrms_local_render_pipeline.inspect_grib2_file",
        lambda storage, raw_path: SimpleNamespace(
            inspectable=True,
            file_exists=True,
            raw_kind=RAW_KIND_MRMS_REAL_GRIB2,
            error=None,
        ),
    )
    monkeypatch.setattr(
        "backend.app.services.mrms_local_render_pipeline.decode_grib2_file",
        _mock_decode,
    )

    report = run_decode_retry(db_session, storage)
    assert report["decode_success"] is True
    assert report["pipeline_status"] == STATUS_PREVIEW_OK
    assert report["render_mode"] == "decoded_prototype"
    assert report["produced_decoded_preview"] is True
    assert report["suggested_command"] == SUGGESTED_DECODE_RETRY_COMMAND
