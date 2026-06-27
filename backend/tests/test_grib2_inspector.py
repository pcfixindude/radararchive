import gzip
import subprocess

import pytest

from backend.app.services.grib2_inspector import (
    DecoderAvailability,
    build_wgrib2_inventory_command,
    classify_raw_path,
    detect_decoder_availability,
    inspect_fixture_bytes,
    inspect_grib2_file,
    is_inspectable_grib2_path,
    stage_grib2_gz,
)
from backend.app.services.raw_file_classifier import (
    RAW_KIND_DEMO_SEEDED_STUB,
    RAW_KIND_MRMS_DOWNLOAD_STUB,
    RAW_KIND_MRMS_REAL_GRIB2,
)
from backend.app.services.storage import LocalStorage


def test_classify_raw_path_kinds():
    assert classify_raw_path("data/raw/demo/mrms_reflectivity/foo.grib2.stub") == RAW_KIND_DEMO_SEEDED_STUB
    assert classify_raw_path("data/raw/mrms/reflectivity/foo.grib2.gz.stub") == RAW_KIND_MRMS_DOWNLOAD_STUB
    assert classify_raw_path("data/raw/mrms/reflectivity/foo.grib2.gz") == RAW_KIND_MRMS_REAL_GRIB2


def test_is_inspectable_grib2_path():
    assert is_inspectable_grib2_path("data/raw/mrms/reflectivity/a.grib2.gz")
    assert not is_inspectable_grib2_path("data/raw/mrms/reflectivity/a.grib2.gz.stub")


def test_build_wgrib2_inventory_command():
    assert build_wgrib2_inventory_command("/tmp/test.grib2") == ["wgrib2", "-s", "/tmp/test.grib2"]
    assert build_wgrib2_inventory_command("/tmp/test.grib2", wgrib2_bin="/opt/wgrib2") == [
        "/opt/wgrib2",
        "-s",
        "/tmp/test.grib2",
    ]


def test_detect_decoder_availability_no_tools():
    availability = detect_decoder_availability(which=lambda _name: None)
    assert availability.any_decoder is False
    assert "No GRIB2 decoder" in availability.summary_message()


def test_detect_decoder_availability_wgrib2():
    availability = detect_decoder_availability(which=lambda name: "/usr/bin/wgrib2" if name == "wgrib2" else None)
    assert availability.wgrib2 is True
    assert availability.any_decoder is True


def test_inspect_missing_file(storage):
    result = inspect_grib2_file(storage, "data/raw/mrms/reflectivity/missing.grib2.gz")
    assert result.file_exists is False
    assert result.error is not None


def test_inspect_stub_file_not_inspectable(storage):
    stub_path = storage.normalize_path("raw", "mrms", "reflectivity", "test.grib2.gz.stub")
    storage.write_text(stub_path, "# stub", overwrite=True)

    result = inspect_grib2_file(storage, stub_path)

    assert result.inspectable is False
    assert result.raw_kind == RAW_KIND_MRMS_DOWNLOAD_STUB
    assert "stub/demo placeholder" in result.notes[0]


def test_inspect_without_decoder_reports_gzip_and_magic(storage):
    grib_payload = b"GRIB" + b"\x00" * 100
    compressed = gzip.compress(grib_payload)
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "sample.grib2.gz")
    storage.write_bytes(raw_path, compressed)

    availability = DecoderAvailability(
        wgrib2=False,
        wgrib2_path=None,
        gdal=False,
        rasterio=False,
        pygrib=False,
        cfgrib=False,
    )
    result = inspect_grib2_file(storage, raw_path, decoders=availability)

    assert result.inspectable is True
    assert result.has_grib_magic is True
    assert result.compressed_size_bytes == len(compressed)
    assert result.decoder_used is None
    assert any("No decoder installed" in note for note in result.notes)


def test_stage_grib2_gz(storage):
    payload = gzip.compress(b"GRIB" + b"\x01" * 20)
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "stage_test.grib2.gz")
    storage.write_bytes(raw_path, payload)

    staged_path, size = stage_grib2_gz(storage, raw_path)

    assert size == 24
    assert storage.path_exists(staged_path)
    assert storage.absolute_path(staged_path).read_bytes().startswith(b"GRIB")


def test_inspect_with_mock_wgrib2(storage):
    grib_payload = b"GRIB" + b"\x00" * 50
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "wgrib2_test.grib2.gz")
    storage.write_bytes(raw_path, gzip.compress(grib_payload))

    def fake_runner(command, *, timeout):
        assert command[0] == "/usr/bin/wgrib2"
        assert command[1] == "-s"
        return subprocess.CompletedProcess(command, 0, stdout="1:0:d=202606271200:REFC:surface\n", stderr="")

    availability = DecoderAvailability(
        wgrib2=True,
        wgrib2_path="/usr/bin/wgrib2",
        gdal=False,
        rasterio=False,
        pygrib=False,
        cfgrib=False,
    )
    result = inspect_grib2_file(storage, raw_path, decoders=availability, wgrib2_runner=fake_runner)

    assert result.decoder_used == "wgrib2"
    assert result.metadata["message_count"] == 1
    assert "REFC" in result.metadata["inventory_lines"][0]


def test_inspect_fixture_bytes_helper():
    payload = gzip.compress(b"GRIB" + b"\x00" * 10)
    result = inspect_fixture_bytes(
        payload,
        decoders=DecoderAvailability(False, None, False, False, False, False),
    )
    assert result.has_grib_magic is True


def test_find_real_mrms_candidates_with_downloaded_file(db_session, storage):
    from backend.app.models import RadarFile
    from backend.app.services.grib2_inspect_catalog import find_real_mrms_inspect_candidates
    from backend.app.sources.mrms import MRMS_CATALOG_SOURCE

    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "real_sample.grib2.gz")
    storage.write_bytes(raw_path, gzip.compress(b"GRIB" + b"\x00" * 8))
    db_session.add(
        RadarFile(
            product_id="mrms_reflectivity",
            timestamp="2026-06-24T12:00:00Z",
            raw_path=raw_path,
            source=MRMS_CATALOG_SOURCE,
            download_status="downloaded",
        )
    )
    db_session.commit()

    candidates = find_real_mrms_inspect_candidates(db_session, storage, limit=1)
    assert len(candidates) == 1
    assert candidates[0].raw_path == raw_path
