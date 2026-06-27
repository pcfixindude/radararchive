from backend.app.sources.mrms import (
    build_date_prefix,
    discover_latest_mrms,
    mrms_stamp_to_iso,
    parse_list_objects_xml,
    parse_mrms_object_key,
    stub_discoveries,
)
from backend.app.config import MRMS_SOURCE_MODE_STUB


SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Contents>
    <Key>CONUS/ReflectivityAtLowestAltitude_00.50/20260627/MRMS_ReflectivityAtLowestAltitude_00.50_20260627-200000.grib2.gz</Key>
    <Size>1048576</Size>
  </Contents>
  <Contents>
    <Key>CONUS/ReflectivityAtLowestAltitude_00.50/20260627/MRMS_ReflectivityAtLowestAltitude_00.50_20260627-195500.grib2.gz</Key>
    <Size>1048000</Size>
  </Contents>
  <Contents>
    <Key>CONUS/ReflectivityAtLowestAltitude_00.50/20260627/README.txt</Key>
    <Size>42</Size>
  </Contents>
</ListBucketResult>
"""


def test_mrms_stamp_to_iso():
    assert mrms_stamp_to_iso("20260627", "200000") == "2026-06-27T20:00:00Z"


def test_parse_mrms_object_key():
    key = (
        "CONUS/ReflectivityAtLowestAltitude_00.50/20260627/"
        "MRMS_ReflectivityAtLowestAltitude_00.50_20260627-200000.grib2.gz"
    )
    parsed = parse_mrms_object_key(key)
    assert parsed is not None
    assert parsed.product == "MRMS_ReflectivityAtLowestAltitude"
    assert parsed.timestamp == "2026-06-27T20:00:00Z"
    assert parsed.file_name.endswith(".grib2.gz")
    assert parsed.source_provider == "noaa_aws"
    assert "noaa-mrms-pds.s3.amazonaws.com" in parsed.source_url


def test_parse_mrms_object_key_rejects_non_matching_files():
    assert parse_mrms_object_key("CONUS/README.txt") is None


def test_parse_list_objects_xml():
    items = parse_list_objects_xml(SAMPLE_XML)
    assert len(items) == 3
    assert items[0]["key"].endswith("200000.grib2.gz")
    assert items[0]["size_bytes"] == 1048576


def test_build_date_prefix():
    prefix = build_date_prefix("MRMS_ReflectivityAtLowestAltitude", "20260627")
    assert prefix == "CONUS/ReflectivityAtLowestAltitude_00.50/20260627/"


def test_stub_discoveries_respects_limit():
    rows = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 3)
    assert len(rows) == 3
    assert rows[0].timestamp >= rows[-1].timestamp


def test_discover_latest_mrms_stub_mode():
    rows = discover_latest_mrms(
        "MRMS_ReflectivityAtLowestAltitude",
        limit=5,
        mode=MRMS_SOURCE_MODE_STUB,
    )
    assert len(rows) == 5
    assert all(row.source_provider == "noaa_aws" for row in rows)


def test_discover_latest_mrms_real_mode_with_mock_http():
    def fake_http(_url: str) -> str:
        return SAMPLE_XML

    rows = discover_latest_mrms(
        "MRMS_ReflectivityAtLowestAltitude",
        limit=5,
        mode="real",
        http_get=fake_http,
    )
    assert len(rows) == 2
    assert rows[0].timestamp == "2026-06-27T20:00:00Z"
    assert rows[0].size_bytes == 1048576
