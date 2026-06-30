"""Tests for MRMS bulk local ingest (Phase 110)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.services.mrms_bulk_ingest import (
    DEFAULT_LIMIT,
    load_bulk_ingest_report,
    plan_ingest_window,
    run_bulk_local_ingest,
)
from backend.app.services.mrms_discovery import register_discovered_files
from backend.app.services.mrms_downloader import download_mrms_row
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

    assert report["ingest_status"] == "ok"
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
