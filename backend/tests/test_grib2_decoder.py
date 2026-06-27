import gzip
import struct
from pathlib import Path

import pytest

from backend.app.services.grib2_decoder import (
    DECODE_OUTPUT_ROOT,
    MANIFEST_NAME,
    RASTER_RAW_NAME,
    build_decode_output_dir,
    decode_grib2_file,
    decode_output_token,
)
from backend.app.services.grib2_inspector import DecoderAvailability
from backend.app.services.raw_file_classifier import RAW_KIND_MRMS_REAL_GRIB2
from backend.app.services.storage import LocalStorage


def test_decode_output_token_deterministic():
    path = "data/raw/mrms/reflectivity/20260626T200000Z_MRMS_ReflectivityAtLowestAltitude_00.50_20260626-200000.grib2.gz"
    assert decode_output_token(path) == (
        "20260626T200000Z_MRMS_ReflectivityAtLowestAltitude_00.50_20260626-200000"
    )


def test_build_decode_output_dir(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "sample.grib2.gz")
    out = build_decode_output_dir(storage, raw_path)
    assert out.startswith(f"{DECODE_OUTPUT_ROOT}/")
    assert out.endswith("sample")


def test_decode_no_decoder_returns_friendly_result(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "nodec.grib2.gz")
    storage.write_bytes(raw_path, gzip.compress(b"GRIB" + b"\x00" * 16))

    availability = DecoderAvailability(
        wgrib2=False,
        wgrib2_path=None,
        gdal=False,
        rasterio=False,
        pygrib=False,
        cfgrib=False,
    )
    result = decode_grib2_file(storage, raw_path, decoders=availability)

    assert result.success is False
    assert result.decoder_unavailable is True
    assert result.error is None
    assert any("Decoder unavailable" in note for note in result.notes)


def test_decode_rejects_bad_gzip(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "bad.grib2.gz")
    storage.write_bytes(raw_path, b"not-gzip")

    result = decode_grib2_file(
        storage,
        raw_path,
        decoders=DecoderAvailability(True, "/usr/bin/wgrib2", False, False, False, False),
    )

    assert result.success is False
    assert result.error is not None


def test_decode_rejects_missing_grib_magic(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "nomagic.grib2.gz")
    storage.write_bytes(raw_path, gzip.compress(b"NOGR" + b"\x00" * 8))

    result = decode_grib2_file(
        storage,
        raw_path,
        decoders=DecoderAvailability(False, None, False, False, False, False),
    )

    assert result.success is False
    assert "GRIB magic" in (result.error or "")


def test_decode_rejects_stub_file(storage):
    stub_path = storage.normalize_path("raw", "mrms", "reflectivity", "stub.grib2.gz.stub")
    storage.write_text(stub_path, "# stub")

    result = decode_grib2_file(storage, stub_path)

    assert result.success is False
    assert "not a real GRIB2" in (result.error or "")


def test_decode_with_injected_decoder_writes_manifest(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "mock.grib2.gz")
    storage.write_bytes(raw_path, gzip.compress(b"GRIB" + b"\x00" * 8))

    def fake_decoder(grib_abs_path: Path, output_dir: Path) -> dict:
        raster = output_dir / RASTER_RAW_NAME
        raster.write_bytes(struct.pack("4f", 0.0, 0.25, 0.5, 1.0))
        return {
            "decoder": "mock",
            "width": 2,
            "height": 2,
            "value_min": 0.0,
            "value_max": 10.0,
            "raster_path": RASTER_RAW_NAME,
        }

    availability = DecoderAvailability(
        wgrib2=False,
        wgrib2_path=None,
        gdal=False,
        rasterio=False,
        pygrib=False,
        cfgrib=False,
    )
    result = decode_grib2_file(
        storage,
        raw_path,
        decoders=availability,
        raster_decoder=fake_decoder,
    )

    assert result.success is True
    assert result.decoder_used == "mock"
    assert result.raw_kind == RAW_KIND_MRMS_REAL_GRIB2
    assert result.manifest_path is not None
    assert result.raster_path is not None
    assert storage.path_exists(result.manifest_path)
    assert storage.path_exists(result.raster_path)
    assert result.output_dir == build_decode_output_dir(storage, raw_path)


def test_decode_gzip_grib_magic_path_without_decoder(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "magic.grib2.gz")
    storage.write_bytes(raw_path, gzip.compress(b"GRIB" + b"\x01" * 12))

    result = decode_grib2_file(
        storage,
        raw_path,
        decoders=DecoderAvailability(False, None, False, False, False, False),
    )

    assert result.decoder_unavailable is True
    assert result.staged_grib2_path is not None
