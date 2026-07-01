"""Tests for MRMS bulk local ingest (Phase 110+) and ingestion robustness (Phase 113)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import DOWNLOAD_STATUS_DOWNLOADED
from backend.app.services.ingest_file_health import HEALTH_EMPTY, raw_file_health
from backend.app.services.ingest_report import (
    INGEST_FAILED,
    INGEST_PARTIAL_SUCCESS,
    INGEST_SUCCESS,
    NEXT_RETRY_FAILED_COMMAND,
)
from backend.app.services.ingest_retry import (
    download_row_with_retry,
    is_transient_download_error,
)
from backend.app.services.mrms_bulk_ingest import (
    DEFAULT_LIMIT,
    load_bulk_ingest_report,
    plan_ingest_window,
    run_bulk_local_ingest,
    save_bulk_ingest_report,
)
from backend.app.services.mrms_discovery import register_discovered_files
from backend.app.services.mrms_downloader import MrmsDownloadError, download_mrms_row
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE, stub_discoveries


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)


def test_plan_ingest_window_latest_limit():
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 10)
    selected = plan_ingest_window(discoveries, limit=5)
    assert len(selected) == 5
    timestamps = [item.timestamp for item in selected]
    assert timestamps == sorted(timestamps)
    assert timestamps[-1] == max(item.timestamp for item in discoveries)


def test_plan_ingest_window_start_end_filter():
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 6)
    selected = plan_ingest_window(
        discoveries,
        start_time="2026-06-26T19:30:00Z",
        end_time="2026-06-26T20:00:00Z",
        limit=10,
    )
    assert selected
    for item in selected:
        assert "2026-06-26T19:30:00Z" <= item.timestamp <= "2026-06-26T20:00:00Z"


def test_run_bulk_local_ingest_stub_registers_and_downloads(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)

    def _discover(product, *, limit, mode, http_get=None):
        return stub_discoveries(product, limit)

    report = run_bulk_local_ingest(
        db_session,
        storage,
        mode="stub",
        limit=5,
        discover_fn=_discover,
        download_fn=download_mrms_row,
    )

    assert report["ingest_status"] == INGEST_SUCCESS
    assert report["frames_selected"] == 5
    assert report["frames_registered_created"] == 5
    assert report["frames_downloaded"] == 5
    assert len(report["registered_timestamps"]) == 5
    assert report["json_path"]
    assert load_bulk_ingest_report(storage) is not None

    rows = (
        db_session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .order_by(RadarFile.timestamp.asc())
        .all()
    )
    assert len(rows) == 5
    for row in rows:
        assert row.raw_path.startswith("data/raw/mrms/reflectivity/")


def test_run_bulk_local_ingest_skips_duplicate_registration(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 3)
    register_discovered_files(db_session, discoveries[:2])
    for row in (
        db_session.query(RadarFile).filter(RadarFile.source == MRMS_CATALOG_SOURCE).all()
    ):
        download_mrms_row(db_session, storage, row, mode="stub")

    def _discover(product, *, limit, mode, http_get=None):
        return stub_discoveries(product, limit)

    report = run_bulk_local_ingest(
        db_session,
        storage,
        mode="stub",
        limit=3,
        discover_fn=_discover,
        download_fn=download_mrms_row,
    )

    assert report["frames_registered_skipped"] >= 2
    assert report["frames_already_present"] >= 2
    assert report["frames_downloaded"] == 1


def test_bulk_ingest_default_limit_is_bounded():
    assert 5 <= DEFAULT_LIMIT <= 10


def test_is_transient_download_error():
    assert is_transient_download_error("MRMS download timed out. Check network connectivity.")
    assert not is_transient_download_error("Radar file 1 has no source_url for real download.")
    assert not is_transient_download_error("MRMS download request failed: 404 not found")


def test_download_row_with_retry_transient_then_success(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 1)
    register_discovered_files(db_session, discoveries)
    row = (
        db_session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .one()
    )

    calls = {"count": 0}

    def _flaky_download(session, storage, radar_row, *, force=False, mode=None, http_get_bytes=None):
        calls["count"] += 1
        if calls["count"] == 1:
            raise MrmsDownloadError("MRMS download timed out. Check network connectivity.")
        return download_mrms_row(session, storage, radar_row, force=force, mode="stub")

    result, attempts, error = download_row_with_retry(
        db_session,
        storage,
        row,
        force=False,
        mode="stub",
        download_fn=_flaky_download,
        max_retries=3,
        retry_delay_sec=0,
        sleep_fn=lambda _seconds: None,
    )

    assert error is None
    assert result is not None
    assert result.created
    assert attempts == 2
    assert calls["count"] == 2


def test_download_row_with_retry_permanent_failure(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 1)
    register_discovered_files(db_session, discoveries)
    row = (
        db_session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .one()
    )

    def _permanent_failure(session, storage, radar_row, *, force=False, mode=None, http_get_bytes=None):
        raise MrmsDownloadError("Radar file 1 has no source_url for real download.")

    result, attempts, error = download_row_with_retry(
        db_session,
        storage,
        row,
        force=False,
        mode="real",
        download_fn=_permanent_failure,
        max_retries=3,
        retry_delay_sec=0,
        sleep_fn=lambda _seconds: None,
    )

    assert result is None
    assert attempts == 1
    assert "no source_url" in (error or "")


def test_run_bulk_local_ingest_partial_success(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)

    def _discover(product, *, limit, mode, http_get=None):
        return stub_discoveries(product, 3)

    fail_once = {"used": False}

    def _mixed_download(session, storage, row, *, force=False, mode=None, http_get_bytes=None):
        if not fail_once["used"]:
            fail_once["used"] = True
            raise MrmsDownloadError("MRMS download timed out. Check network connectivity.")
        return download_mrms_row(session, storage, row, force=force, mode="stub")

    report = run_bulk_local_ingest(
        db_session,
        storage,
        mode="stub",
        limit=3,
        discover_fn=_discover,
        download_fn=_mixed_download,
        max_retries=1,
        retry_delay_sec=0,
    )

    assert report["ingest_status"] == INGEST_PARTIAL_SUCCESS
    assert report["frames_downloaded"] == 2
    assert report["frames_failed"] == 1
    assert len(report["failures"]) == 1
    assert report["failures"][0]["error"]
    assert NEXT_RETRY_FAILED_COMMAND in report["next_commands"]


def test_raw_file_health_empty_and_valid(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 1)
    register_discovered_files(db_session, discoveries)
    row = (
        db_session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .one()
    )
    download_mrms_row(db_session, storage, row, mode="stub")
    assert raw_file_health(storage, row.raw_path, expected_sha256=row.sha256) == "valid"

    storage.write_bytes(row.raw_path, b"", overwrite=True)
    assert raw_file_health(storage, row.raw_path) == HEALTH_EMPTY


def test_run_bulk_local_ingest_repair_zero_byte_file(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 1)
    register_discovered_files(db_session, discoveries)
    row = (
        db_session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .one()
    )
    download_mrms_row(db_session, storage, row, mode="stub")
    storage.write_bytes(row.raw_path, b"", overwrite=True)
    row.download_status = DOWNLOAD_STATUS_DOWNLOADED
    db_session.commit()

    def _discover(product, *, limit, mode, http_get=None):
        return stub_discoveries(product, 1)

    report = run_bulk_local_ingest(
        db_session,
        storage,
        mode="stub",
        limit=1,
        repair=True,
        discover_fn=_discover,
        download_fn=download_mrms_row,
    )

    assert report["ingest_status"] == INGEST_SUCCESS
    assert report["frames_repaired"] == 1
    assert raw_file_health(storage, row.raw_path) == "valid"


def test_run_bulk_local_ingest_bad_file_without_repair_fails(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 1)
    register_discovered_files(db_session, discoveries)
    row = (
        db_session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .one()
    )
    download_mrms_row(db_session, storage, row, mode="stub")
    storage.write_bytes(row.raw_path, b"", overwrite=True)
    row.download_status = DOWNLOAD_STATUS_DOWNLOADED
    db_session.commit()

    def _discover(product, *, limit, mode, http_get=None):
        return stub_discoveries(product, 1)

    report = run_bulk_local_ingest(
        db_session,
        storage,
        mode="stub",
        limit=1,
        discover_fn=_discover,
        download_fn=download_mrms_row,
    )

    assert report["ingest_status"] == INGEST_FAILED
    assert report["frames_failed"] == 1
    assert "empty" in report["failures"][0]["error"].lower()


def test_run_bulk_local_ingest_retry_failed_from_report(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 2)
    register_discovered_files(db_session, discoveries)
    rows = (
        db_session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .order_by(RadarFile.timestamp.asc())
        .all()
    )
    failed_row = rows[0]
    good_row = rows[1]
    download_mrms_row(db_session, storage, good_row, mode="stub")

    save_bulk_ingest_report(
        storage,
        {
            "ingest_status": INGEST_PARTIAL_SUCCESS,
            "frames_discovered": 2,
            "failures": [
                {
                    "timestamp": failed_row.timestamp,
                    "error": "MRMS download timed out. Check network connectivity.",
                    "attempts": 3,
                }
            ],
            "downloaded_timestamps": [good_row.timestamp],
        },
    )

    report = run_bulk_local_ingest(
        db_session,
        storage,
        mode="stub",
        retry_failed=True,
        download_fn=download_mrms_row,
    )

    assert report["recovery_mode"] == "retry_failed"
    assert report["ingest_status"] == INGEST_SUCCESS
    assert report["frames_downloaded"] == 1
    assert report["frames_failed"] == 0


def test_run_bulk_local_ingest_missing_only_skips_valid(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 2)
    register_discovered_files(db_session, discoveries)
    rows = (
        db_session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .order_by(RadarFile.timestamp.asc())
        .all()
    )
    download_mrms_row(db_session, storage, rows[0], mode="stub")

    def _discover(product, *, limit, mode, http_get=None):
        return stub_discoveries(product, 2)

    report = run_bulk_local_ingest(
        db_session,
        storage,
        mode="stub",
        limit=2,
        missing_only=True,
        discover_fn=_discover,
        download_fn=download_mrms_row,
    )

    assert report["recovery_mode"] == "missing_only"
    assert report["frames_skipped"] == 1
    assert report["frames_downloaded"] == 1
    assert report["ingest_status"] == INGEST_SUCCESS


def test_warm_cache_eligible_on_partial_success(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)

    def _discover(product, *, limit, mode, http_get=None):
        return stub_discoveries(product, 2)

    fail_once = {"used": False}

    def _mixed_download(session, storage, row, *, force=False, mode=None, http_get_bytes=None):
        if not fail_once["used"]:
            fail_once["used"] = True
            raise MrmsDownloadError("MRMS download timed out. Check network connectivity.")
        return download_mrms_row(session, storage, row, force=force, mode="stub")

    report = run_bulk_local_ingest(
        db_session,
        storage,
        mode="stub",
        limit=2,
        discover_fn=_discover,
        download_fn=_mixed_download,
        max_retries=1,
        retry_delay_sec=0,
    )

    assert report["ingest_status"] == INGEST_PARTIAL_SUCCESS
    assert "make mrms-warm-frame-cache" in report["next_commands"]
