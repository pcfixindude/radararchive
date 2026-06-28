import json
import struct

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import (
    RENDER_STATUS_DECODED_PROTOTYPE,
    RENDER_STATUS_PLACEHOLDER,
    RENDER_STATUS_PRODUCTION_RENDERED,
)
from backend.app.services.decoded_tile_cache import (
    TILE_MODE_DECODED_PROTOTYPE,
    TILE_MODE_PLACEHOLDER,
    serve_tile_with_optional_decode,
)
from backend.app.services.grib2_decoder import MANIFEST_NAME, RASTER_RAW_NAME, build_decode_output_dir
from backend.app.services.processor import process_pending_frames
from backend.app.services.render_metadata import (
    GeoRenderMetadata,
    build_geo_metadata_for_decode,
    load_geo_metadata,
    write_geo_metadata,
)
from backend.app.services.render_status import (
    build_render_status_report,
    classify_frame_render_status,
    sync_catalog_render_metadata,
)


def _write_decode_fixture(storage, raw_path: str, *, width: int = 4, height: int = 4, with_geo: bool = True) -> str:
    output_dir = build_decode_output_dir(storage, raw_path)
    storage.ensure_directories(output_dir)

    grid_values = [i / 15.0 for i in range(width * height)]
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

    if with_geo:
        geo = build_geo_metadata_for_decode(grid_width=width, grid_height=height)
        write_geo_metadata(storage, output_dir, geo)

    return output_dir


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))


def test_geo_metadata_from_manifest_when_no_geo_file(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "geo_manifest_only.grib2.gz")
    output_dir = _write_decode_fixture(storage, raw_path, with_geo=False)

    geo = load_geo_metadata(storage, output_dir)
    assert geo is not None
    assert geo.grid_width == 4
    assert geo.grid_height == 4
    assert geo.production_rendering is False
    assert geo.geo_accurate is False


def test_geo_metadata_parses_written_file(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "geo_file.grib2.gz")
    output_dir = _write_decode_fixture(storage, raw_path, with_geo=True)

    geo = load_geo_metadata(storage, output_dir)
    assert geo is not None
    assert geo.product_name == "MRMS_ReflectivityAtLowestAltitude"
    assert geo.output_crs == "EPSG:3857"
    assert len(geo.bounds) == 4


def test_geo_render_metadata_roundtrip():
    meta = GeoRenderMetadata(
        product_name="test_product",
        valid_timestamp="2026-06-27T20:00:00Z",
        source_crs="EPSG:4326",
        output_crs="EPSG:3857",
        bounds=[-125.0, 24.0, -66.0, 50.0],
        grid_width=100,
        grid_height=50,
        pixel_size_x=0.01,
        pixel_size_y=0.01,
        transform=[1.0, 0.0, 0.0, 0.0, -1.0, 0.0],
    )
    restored = GeoRenderMetadata.from_dict(meta.to_dict())
    assert restored.grid_width == 100
    assert restored.transform == meta.transform


def test_classify_frame_render_status_decoded_prototype(db_session, storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "classify.grib2.gz")
    _write_decode_fixture(storage, raw_path)
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-25T12:00:00Z",
        raw_path=raw_path,
        processed_status="placeholder_for_real_raw",
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    info = classify_frame_render_status(storage, frame)
    assert info.render_status == RENDER_STATUS_DECODED_PROTOTYPE
    assert info.production_rendering is False
    assert info.has_decode_artifact is True
    assert info.has_geo_metadata is True


def test_build_render_status_report_with_fake_artifacts(db_session, storage):
    process_pending_frames(db_session, storage)
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "report.grib2.gz")
    _write_decode_fixture(storage, raw_path, with_geo=False)

    report = build_render_status_report(db_session, storage)
    assert report.total_frames >= 1
    assert report.decoded_prototype_artifacts >= 1
    assert report.production_rendered_frames == 0
    assert report.missing_geo_metadata >= 1
    assert any("production_rendered frames: 0" in note for note in report.notes)


def test_sync_catalog_never_marks_production_rendered(db_session, storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "sync.grib2.gz")
    _write_decode_fixture(storage, raw_path)
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-25T18:00:00Z",
        raw_path=raw_path,
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_DECODED_PROTOTYPE,
        production_rendering=True,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    updated = sync_catalog_render_metadata(db_session, storage)
    assert updated >= 1
    db_session.refresh(frame)
    assert frame.render_status == RENDER_STATUS_DECODED_PROTOTYPE
    assert frame.production_rendering is False


def test_production_flag_off_blocks_production_tile_serving(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "prod_block.grib2.gz")
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-25T20:00:00Z",
        raw_path=raw_path,
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=True,
        render_artifact_path=storage.normalize_path("tiles", "production", "fake.png"),
        source="mrms_discovered",
    )
    storage.write_bytes(frame.render_artifact_path, b"\x89PNG\r\n\x1a\n")

    served = serve_tile_with_optional_decode(
        storage,
        frame,
        frame.timestamp,
        enable_decoded_tiles=False,
        enable_production_radar_tiles=False,
        z=0,
        x=0,
        y=0,
    )
    assert served.render_status == RENDER_STATUS_PLACEHOLDER
    assert served.production_rendering is False


def test_production_flag_on_without_renderer_falls_back(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "prod_fallback.grib2.gz")
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-25T21:00:00Z",
        raw_path=raw_path,
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=True,
        render_artifact_path=storage.normalize_path("tiles", "production", "fake2.png"),
        source="mrms_discovered",
    )
    storage.write_bytes(frame.render_artifact_path, b"\x89PNG\r\n\x1a\n")

    served = serve_tile_with_optional_decode(
        storage,
        frame,
        frame.timestamp,
        enable_decoded_tiles=False,
        enable_production_radar_tiles=True,
        z=0,
        x=0,
        y=0,
    )
    assert served.render_status == RENDER_STATUS_PLACEHOLDER
    assert served.production_rendering is False
    assert served.fallback is True


def test_decoded_prototype_remains_non_production(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_decoded_tiles", True)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    _use_test_storage(monkeypatch, storage)
    timestamp = "2026-06-25T18:00:00Z"
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "headers.grib2.gz")
    storage.write_bytes(raw_path, b"grib2-placeholder-bytes")
    _write_decode_fixture(storage, raw_path)

    db_session.add(
        RadarFile(
            product_id="mrms_reflectivity",
            timestamp=timestamp,
            raw_path=raw_path,
            processed_status="placeholder_for_real_raw",
            source="mrms_discovered",
            raw_kind="mrms_real_grib2",
        )
    )
    db_session.commit()

    response = client.get(f"/tiles/mrms_reflectivity/{timestamp}/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-tile") == TILE_MODE_DECODED_PROTOTYPE
    assert response.headers.get("x-radararchive-production-rendering") == "false"
    assert response.headers.get("x-radararchive-render-status") == RENDER_STATUS_DECODED_PROTOTYPE


def test_placeholder_headers_report_non_production(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    _use_test_storage(monkeypatch, storage)
    process_pending_frames(db_session, storage)

    response = client.get("/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-tile") == TILE_MODE_PLACEHOLDER
    assert response.headers.get("x-radararchive-production-rendering") == "false"
    assert response.headers.get("x-radararchive-render-status") == RENDER_STATUS_PLACEHOLDER


def test_tiles_config_includes_production_flag(client):
    response = client.get("/tiles/config")
    assert response.status_code == 200
    body = response.json()
    assert body["enable_production_radar_tiles"] is False
    assert body["production_rendering"] is False
    assert body["production_rendering_enabled"] is False
