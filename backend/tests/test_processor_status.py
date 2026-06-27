from backend.app.models import RadarFile
from backend.app.models.radar_file import (
    PROCESSED_STATUS_PENDING,
    PROCESSED_STATUS_PLACEHOLDER_FOR_REAL_RAW,
    PROCESSED_STATUS_PLACEHOLDER_PROCESSED,
    PROCESSED_STATUS_REAL_DECODE_NOT_IMPLEMENTED,
)
from backend.app.services.collector import COLLECTOR_SOURCE, collect_mrms_reflectivity_once
from backend.app.services.mrms_discovery import register_discovered_files
from backend.app.services.mrms_downloader import download_mrms_row
from backend.app.services.processor import process_pending_frames
from backend.app.services.raw_file_classifier import (
    RAW_KIND_COLLECTOR_STUB,
    RAW_KIND_DEMO_SEEDED_STUB,
    RAW_KIND_MRMS_DOWNLOAD_STUB,
    RAW_KIND_MRMS_REAL_GRIB2,
    classify_raw_file,
)
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE, stub_discoveries


def test_processor_demo_seeded_stub(db_session, storage):
    result = process_pending_frames(db_session, storage)

    assert result.processed_count == 5
    assert result.placeholder_processed_count == 5
    assert result.placeholder_for_real_raw_count == 0
    assert result.failed_count == 0

    frame = db_session.query(RadarFile).filter(RadarFile.timestamp == "2026-06-27T20:00:00Z").one()
    assert frame.processed_status == PROCESSED_STATUS_PLACEHOLDER_PROCESSED
    assert frame.raw_kind == RAW_KIND_DEMO_SEEDED_STUB
    assert frame.processed_path.endswith(".png")
    assert "placeholder_for_real_raw" not in (frame.processed_path or "")


def test_processor_collector_stub(db_session, storage):
    collect_mrms_reflectivity_once(db_session, storage, timestamp="2026-06-27T21:00:00Z")

    result = process_pending_frames(db_session, storage)

    row = db_session.query(RadarFile).filter(RadarFile.timestamp == "2026-06-27T21:00:00Z").one()
    assert row.source == COLLECTOR_SOURCE
    assert row.raw_kind == RAW_KIND_COLLECTOR_STUB
    assert row.processed_status == PROCESSED_STATUS_PLACEHOLDER_PROCESSED
    assert any(item.timestamp == "2026-06-27T21:00:00Z" for item in result.results)


def test_processor_mrms_download_stub(db_session, storage):
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 1)
    register_discovered_files(db_session, discoveries)
    row = db_session.query(RadarFile).filter(RadarFile.source == MRMS_CATALOG_SOURCE).one()
    download_mrms_row(db_session, storage, row, mode="stub")

    process_pending_frames(db_session, storage)
    db_session.refresh(row)

    assert row.raw_kind == RAW_KIND_MRMS_DOWNLOAD_STUB
    assert row.processed_status == PROCESSED_STATUS_PLACEHOLDER_PROCESSED
    assert row.processed_path.endswith(".png")


def test_processor_real_grib2_not_marked_as_real_radar(db_session, storage):
    timestamp = "2026-06-25T12:00:00Z"
    raw_path = storage.normalize_path(
        "raw",
        "mrms",
        "reflectivity",
        "20260625T120000Z_MRMS_ReflectivityAtLowestAltitude_00.50_20260625-120000.grib2.gz",
    )
    storage.write_bytes(raw_path, b"\x1f\x8b" + b"fake gzip payload for test")

    row = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=raw_path,
        source=MRMS_CATALOG_SOURCE,
        source_url="https://example.com/test.grib2.gz",
        download_status="downloaded",
    )
    db_session.add(row)
    db_session.commit()

    result = process_pending_frames(db_session, storage)
    db_session.refresh(row)

    assert classify_raw_file(row) == RAW_KIND_MRMS_REAL_GRIB2
    assert row.processed_status == PROCESSED_STATUS_PLACEHOLDER_FOR_REAL_RAW
    assert row.processed_status != PROCESSED_STATUS_PLACEHOLDER_PROCESSED
    assert row.processed_path.endswith(".placeholder_for_real_raw.png")
    assert result.real_decode_pending_count >= 1


def test_real_decode_not_implemented_has_no_tiles(client, db_session):
    row = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-25T11:00:00Z",
        raw_path="data/raw/mrms/reflectivity/test.grib2.gz",
        processed_status=PROCESSED_STATUS_REAL_DECODE_NOT_IMPLEMENTED,
        source=MRMS_CATALOG_SOURCE,
    )
    db_session.add(row)
    db_session.commit()

    response = client.get("/tiles/mrms_reflectivity/2026-06-25T11:00:00Z/0/0/0.png")
    assert response.status_code == 404


def test_placeholder_tiles_only_for_placeholder_processed(client, db_session, storage):
    process_pending_frames(db_session, storage)

    ok = client.get("/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png")
    assert ok.status_code == 200
    assert ok.headers.get("x-radararchive-tile") == "placeholder"

    pending = client.get("/tiles/mrms_reflectivity/2099-01-01T00:00:00Z/0/0/0.png")
    assert pending.status_code == 404


def test_real_grib2_placeholder_tile_header(client, db_session, storage):
    timestamp = "2026-06-25T12:30:00Z"
    raw_path = storage.normalize_path(
        "raw",
        "mrms",
        "reflectivity",
        "20260625T123000Z_test.grib2.gz",
    )
    storage.write_bytes(raw_path, b"fake grib2 gz content")
    row = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=raw_path,
        source=MRMS_CATALOG_SOURCE,
    )
    db_session.add(row)
    db_session.commit()

    process_pending_frames(db_session, storage)

    response = client.get(f"/tiles/mrms_reflectivity/{timestamp}/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-tile") == "placeholder_for_real_raw"
    assert response.headers.get("x-radararchive-raw-kind") == RAW_KIND_MRMS_REAL_GRIB2


def test_process_once_summary_counts(db_session, storage):
    result = process_pending_frames(db_session, storage)

    assert result.processed_count == 5
    assert result.skipped_count == 0
    assert result.placeholder_processed_count == 5
    assert result.failed_count == 0

    second = process_pending_frames(db_session, storage)
    assert second.processed_count == 0
    assert second.skipped_count == 5


def test_processing_status_api(client, db_session, storage):
    process_pending_frames(db_session, storage)

    res = client.get("/api/sources/mrms/processing-status")
    assert res.status_code == 200
    body = res.json()
    assert body["placeholder_processed"] == 5
    assert body["pending"] == 0
