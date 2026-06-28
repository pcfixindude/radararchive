"""Tests for batch MRMS validation and catalog status (Phase 21)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from backend.app.config import settings
from backend.app.services.catalog_status import build_catalog_status
from backend.app.services.grib2_decoder import Grib2DecodeResult
from backend.app.services.grib2_inspector import Grib2InspectResult
from backend.app.services.mrms_batch_validation import (
    DEFAULT_BATCH_FRAME_COUNT,
    MAX_BATCH_FRAME_COUNT,
    resolve_batch_frame_count,
    run_mrms_batch_validation,
)
from backend.app.services.mrms_downloader import DownloadBatchResult, DownloadResult
from backend.app.services.validation_report_store import load_validation_history
from backend.app.sources.mrms import MrmsDiscoveredFile
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.decoded_tile_cache import TILE_MODE_PLACEHOLDER


def _discover_n(product, *, limit=None, mode=None):
    count = limit or 1
    return [
        MrmsDiscoveredFile(
            product="MRMS_ReflectivityAtLowestAltitude",
            catalog_product_id="mrms_reflectivity",
            timestamp=f"2026-06-25T{18 + i:02d}:00:00Z",
            file_name=f"MRMS_{i}.grib2.gz",
            object_key=f"CONUS/MRMS_{i}.grib2.gz",
            source_url=f"https://example.test/mrms_{i}.grib2.gz",
            source_provider="noaa-aws-stub",
            size_bytes=1000 + i,
        )
        for i in range(count)
    ]


def _download_batch(session, storage, limit, mode):
    items = []
    for i in range(limit):
        items.append(
            DownloadResult(
                radar_file_id=i + 1,
                timestamp=f"2026-06-25T{18 + i:02d}:00:00Z",
                raw_path=f"raw/mrms/reflectivity/frame_{i}.grib2.gz",
                sha256="abc",
                file_size_bytes=100,
                downloaded_at="2026-06-25T18:05:00Z",
                created=True,
                stub=False,
            )
        )
    return DownloadBatchResult(downloaded=items, skipped=0, failed=[])


def _inspect_ok(storage, raw_path):
    return Grib2InspectResult(
        raw_path=raw_path,
        raw_kind="mrms_real_grib2",
        file_exists=True,
        inspectable=True,
    )


def _decode_ok(storage, raw_path):
    return Grib2DecodeResult(
        raw_path=raw_path,
        raw_kind="mrms_real_grib2",
        success=True,
        output_dir="data/staging/grib2_decode/test",
    )


def test_resolve_batch_frame_count_default():
    count, warnings = resolve_batch_frame_count(0)
    assert count == DEFAULT_BATCH_FRAME_COUNT
    assert warnings


def test_resolve_batch_frame_count_cap():
    count, warnings = resolve_batch_frame_count(99)
    assert count == MAX_BATCH_FRAME_COUNT
    assert any("capping" in w.lower() for w in warnings)


def test_batch_validation_report_shape(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    candidates = [
        MagicMock(timestamp=f"2026-06-25T{18 + i:02d}:00:00Z", raw_path=f"raw/mrms/reflectivity/f{i}.grib2.gz")
        for i in range(3)
    ]

    with patch(
        "backend.app.services.mrms_batch_validation.detect_decoder_availability",
        return_value=MagicMock(any_decoder=True),
    ), patch(
        "backend.app.services.mrms_batch_validation.find_real_mrms_inspect_candidates",
        return_value=candidates,
    ), patch(
        "backend.app.services.mrms_batch_validation.build_production_tiles",
        return_value=MagicMock(
            tiles_planned=3,
            tiles_written=2,
            tiles_skipped_existing=1,
            output_bytes=500,
            errors=[],
        ),
    ):
        report = run_mrms_batch_validation(
            db_session,
            storage,
            frame_count=3,
            source_mode="stub",
            discover_fn=_discover_n,
            download_fn=_download_batch,
            inspect_fn=_inspect_ok,
            decode_fn=_decode_ok,
        )

    body = report.to_dict()
    assert body["batch"] is True
    assert body["requested_frame_count"] == 3
    assert body["effective_frame_count"] == 3
    assert body["discovered_count"] == 3
    assert body["downloaded_count"] == 3
    assert body["decoded_count"] == 3
    assert len(body["frame_summaries"]) == 3
    assert body["verified_mrms"] is False
    assert body["production_rendering_enabled"] is False
    assert body["elapsed_seconds"] >= 0


def test_batch_validation_stub_no_decoder_friendly(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    with patch(
        "backend.app.services.mrms_batch_validation.detect_decoder_availability",
        return_value=MagicMock(any_decoder=False),
    ), patch(
        "backend.app.services.mrms_batch_validation.find_real_mrms_inspect_candidates",
        return_value=[],
    ):
        report = run_mrms_batch_validation(
            db_session,
            storage,
            frame_count=3,
            source_mode="stub",
            discover_fn=_discover_n,
            download_fn=_download_batch,
        )

    assert report.decoded_count == 0
    assert report.verified_mrms is False
    assert any("stub" in w.lower() for w in report.warnings)


def test_validation_history_persistence(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)

    with patch(
        "backend.app.services.mrms_batch_validation.detect_decoder_availability",
        return_value=MagicMock(any_decoder=False),
    ), patch(
        "backend.app.services.mrms_batch_validation.find_real_mrms_inspect_candidates",
        return_value=[],
    ):
        run_mrms_batch_validation(
            db_session,
            storage,
            frame_count=2,
            source_mode="stub",
            discover_fn=_discover_n,
            download_fn=_download_batch,
        )

    history = load_validation_history(storage)
    assert len(history) >= 1
    assert history[0]["verified_mrms"] is False


def test_catalog_status_metrics(db_session):
    status = build_catalog_status(db_session)
    assert status["product_id"] == "mrms_reflectivity"
    assert status["total_frames"] >= 1
    assert "download_status" in status
    assert "processed_status" in status
    assert "render_status" in status
    assert status["verified_mrms"] is False


def test_api_catalog_status(client, db_session):
    response = client.get("/api/catalog/status")
    assert response.status_code == 200
    body = response.json()
    assert body["product_id"] == "mrms_reflectivity"
    assert body["verified_mrms"] is False


def test_api_validation_history(client, storage, monkeypatch):
    from backend.app.services.validation_report_store import save_validation_report

    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_validation_report(storage, {"source_mode": "stub", "discovered_count": 1, "batch": True})

    response = client.get("/api/validation/history")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 1
    assert body["verified_mrms"] is False


def test_validation_summary_includes_catalog(client, db_session):
    response = client.get("/api/validation/summary")
    assert response.status_code == 200
    body = response.json()
    assert "catalog" in body
    assert body["catalog"]["total_frames"] >= 1
    assert "validation_history_count" in body


def test_production_tile_serving_still_gated_phase21(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    timestamp = "2026-06-26T00:00:00Z"
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase21_gate.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=True,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    response = client.get(f"/tiles/mrms_reflectivity/{timestamp}/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"
    assert response.headers.get("x-radararchive-tile") in (TILE_MODE_PLACEHOLDER, "placeholder_for_real_raw")
