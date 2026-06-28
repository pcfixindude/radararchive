import json
import struct
from typing import Optional
from unittest.mock import patch

from backend.app.config import settings
from backend.app.models.render_job import (
    JOB_STATUS_FAILED,
    JOB_STATUS_QUEUED,
    JOB_STATUS_RUNNING,
    JOB_STATUS_SUCCEEDED,
)
from backend.app.services.grib2_decoder import MANIFEST_NAME, RASTER_RAW_NAME, build_decode_output_dir
from backend.app.services.production_tile_builder import BuildProductionTilesResult
from backend.app.services.render_metadata import GeoRenderMetadata, write_geo_metadata
from backend.app.services.render_queue import enqueue_render_job, get_render_job, list_render_jobs
from backend.app.workers.render_worker import process_next_render_job, run_render_job


def _write_warp_fixture(
    storage,
    raw_path: str,
    *,
    width: int = 8,
    height: int = 8,
    bounds: Optional[list[float]] = None,
) -> str:
    output_dir = build_decode_output_dir(storage, raw_path)
    storage.ensure_directories(output_dir)

    grid_values = [i / (width * height - 1) for i in range(width * height)]
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

    metadata = GeoRenderMetadata(
        product_name="test_product",
        valid_timestamp="2026-06-25T18:00:00Z",
        source_crs="EPSG:4326",
        output_crs="EPSG:3857",
        bounds=bounds or [-100.0, 35.0, -99.0, 36.0],
        grid_width=width,
        grid_height=height,
        geo_accurate=False,
        production_rendering=False,
        notes=["Test fixture"],
    )
    write_geo_metadata(storage, output_dir, metadata)
    return output_dir


def test_enqueue_render_job(db_session):
    job = enqueue_render_job(db_session, min_zoom=0, max_zoom=1, force=True)
    assert job.id is not None
    assert job.status == JOB_STATUS_QUEUED
    assert job.min_zoom == 0
    assert job.max_zoom == 1
    assert job.force is True


def test_job_status_transitions(db_session, storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "queue_transition.grib2.gz")
    _write_warp_fixture(storage, raw_path)

    job = enqueue_render_job(db_session, min_zoom=0, max_zoom=0)
    assert job.status == JOB_STATUS_QUEUED

    processed = process_next_render_job(db_session, storage)
    assert processed is not None
    assert processed.id == job.id
    assert processed.status == JOB_STATUS_SUCCEEDED
    assert processed.progress_total >= 1
    assert processed.tiles_written >= 1
    assert processed.output_bytes > 0
    assert processed.finished_at is not None


def test_worker_processes_one_queued_job(db_session, storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "worker_one.grib2.gz")
    _write_warp_fixture(storage, raw_path)

    job = enqueue_render_job(db_session)
    first = process_next_render_job(db_session, storage)
    second = process_next_render_job(db_session, storage)

    assert first is not None
    assert first.status == JOB_STATUS_SUCCEEDED
    assert second is None


def test_failed_job_records_error(db_session, storage):
    job = enqueue_render_job(db_session)
    job.status = JOB_STATUS_RUNNING
    db_session.commit()

    with patch(
        "backend.app.workers.render_worker.build_production_tiles",
        side_effect=RuntimeError("simulated worker failure"),
    ):
        result = run_render_job(db_session, storage, job)

    assert result.status == JOB_STATUS_FAILED
    assert "simulated worker failure" in (result.error_message or "")


def test_failed_job_on_all_tiles_failed(db_session, storage):
    job = enqueue_render_job(db_session)
    job.status = JOB_STATUS_RUNNING
    db_session.commit()

    fake_result = BuildProductionTilesResult(
        tiles_planned=2,
        tiles_failed=2,
        tiles_written=0,
        errors=["warp failed"],
    )
    with patch(
        "backend.app.workers.render_worker.build_production_tiles",
        return_value=fake_result,
    ):
        result = run_render_job(db_session, storage, job)

    assert result.status == JOB_STATUS_FAILED


def test_progress_metrics_saved(db_session, storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "progress.grib2.gz")
    _write_warp_fixture(storage, raw_path)

    job = enqueue_render_job(db_session, min_zoom=0, max_zoom=0)
    processed = process_next_render_job(db_session, storage)

    assert processed.progress_current == processed.progress_total
    assert processed.tiles_written >= 1


def test_list_render_jobs(db_session):
    enqueue_render_job(db_session)
    enqueue_render_job(db_session, max_zoom=1)
    jobs = list_render_jobs(db_session, limit=10)
    assert len(jobs) >= 2
    assert jobs[0].id > jobs[1].id


def test_api_create_and_get_render_job(client):
    response = client.post(
        "/api/render/jobs",
        json={"min_zoom": 0, "max_zoom": 0, "force": False},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == JOB_STATUS_QUEUED
    assert body["prototype"] is True
    assert body["verified_mrms"] is False

    job_id = body["id"]
    get_resp = client.get(f"/api/render/jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == job_id


def test_api_list_render_jobs(client):
    client.post("/api/render/jobs", json={})
    response = client.get("/api/render/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) >= 1


def test_production_tile_serving_still_gated(client, db_session, storage, monkeypatch):
    from backend.app.models import RadarFile
    from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
    from backend.app.services.decoded_tile_cache import TILE_MODE_PLACEHOLDER

    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    timestamp = "2026-06-25T20:00:00Z"
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "gate.grib2.gz"),
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
