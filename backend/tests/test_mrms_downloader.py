import gzip

import pytest

from backend.app.models import RadarFile
from backend.app.models.radar_file import (
    DOWNLOAD_STATUS_DOWNLOADED,
    DOWNLOAD_STATUS_FAILED,
    DOWNLOAD_STATUS_PENDING,
)
from backend.app.services.mrms_discovery import register_discovered_files
from backend.app.services.mrms_downloader import (
    MrmsDownloadError,
    build_mrms_raw_path,
    download_mrms_row,
    download_pending_mrms,
    is_local_mrms_raw_path,
    sanitize_filename,
)
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE, stub_discoveries


def test_sanitize_filename():
    assert sanitize_filename("MRMS_ReflectivityAtLowestAltitude_00.50_20260626-200000.grib2.gz") == (
        "MRMS_ReflectivityAtLowestAltitude_00.50_20260626-200000.grib2.gz"
    )
    assert sanitize_filename("bad/name?.gz") == "bad_name_.gz"


def test_build_mrms_raw_path(storage):
    path = build_mrms_raw_path(
        storage,
        product_id="mrms_reflectivity",
        timestamp="2026-06-26T20:00:00Z",
        original_filename="MRMS_ReflectivityAtLowestAltitude_00.50_20260626-200000.grib2.gz",
        stub=True,
    )
    assert path.startswith("data/raw/mrms/reflectivity/")
    assert path.endswith(".grib2.gz.stub")


def test_is_local_mrms_raw_path():
    assert is_local_mrms_raw_path("data/raw/mrms/reflectivity/foo.grib2.gz.stub")
    assert not is_local_mrms_raw_path("CONUS/ReflectivityAtLowestAltitude_00.50/foo.grib2.gz")


def test_download_mrms_row_stub_writes_file(db_session, storage):
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 1)
    register_discovered_files(db_session, discoveries)
    row = (
        db_session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .one()
    )

    result = download_mrms_row(db_session, storage, row, mode="stub")

    assert result.created is True
    assert result.stub is True
    assert storage.path_exists(result.raw_path)
    assert len(result.sha256) == 64
    assert result.file_size_bytes > 0

    db_session.refresh(row)
    assert row.download_status == DOWNLOAD_STATUS_DOWNLOADED
    assert row.sha256 == result.sha256
    assert row.raw_path == result.raw_path
    assert row.downloaded_at is not None


def test_download_mrms_row_real_mode_mocked_http(db_session, storage):
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 1)
    register_discovered_files(db_session, discoveries)
    row = (
        db_session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .one()
    )
    payload = gzip.compress(b"fake grib2 payload")

    def fake_http(_url: str) -> bytes:
        return payload

    result = download_mrms_row(db_session, storage, row, mode="real", http_get_bytes=fake_http)

    assert result.created is True
    assert result.stub is False
    assert result.raw_path.endswith(".grib2.gz")
    assert not result.raw_path.endswith(".stub")
    assert storage.sha256(result.raw_path) == result.sha256


def test_download_skips_when_already_downloaded(db_session, storage):
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 1)
    register_discovered_files(db_session, discoveries)
    row = (
        db_session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .one()
    )

    first = download_mrms_row(db_session, storage, row, mode="stub")
    second = download_mrms_row(db_session, storage, row, mode="stub")

    assert first.created is True
    assert second.created is False
    assert second.raw_path == first.raw_path


def test_download_force_redownloads(db_session, storage):
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 1)
    register_discovered_files(db_session, discoveries)
    row = (
        db_session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .one()
    )

    first = download_mrms_row(db_session, storage, row, mode="stub")
    second = download_mrms_row(db_session, storage, row, mode="stub", force=True)

    assert first.created is True
    assert second.created is True
    assert second.sha256 == first.sha256


def test_download_pending_mrms_respects_limit(db_session, storage):
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 3)
    register_discovered_files(db_session, discoveries)

    batch = download_pending_mrms(db_session, storage, limit=2, mode="stub")

    assert len(batch.downloaded) == 2
    assert batch.skipped == 0


def test_download_marks_failed_on_error(db_session, storage):
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 1)
    register_discovered_files(db_session, discoveries)
    row = (
        db_session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .one()
    )

    def failing_http(_url: str) -> bytes:
        raise MrmsDownloadError("network down")

    with pytest.raises(MrmsDownloadError):
        download_mrms_row(db_session, storage, row, mode="real", http_get_bytes=failing_http)

    db_session.refresh(row)
    assert row.download_status == DOWNLOAD_STATUS_FAILED


def test_download_status_api(client, db_session, storage):
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 2)
    register_discovered_files(db_session, discoveries)
    row = (
        db_session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .order_by(RadarFile.timestamp.desc())
        .first()
    )
    download_mrms_row(db_session, storage, row, mode="stub")

    res = client.get("/api/sources/mrms/download-status")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    assert body["downloaded"] == 1
    assert body["pending"] == 1
