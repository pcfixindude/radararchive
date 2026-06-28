import json
import struct
from typing import Optional

import pytest

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import (
    RENDER_STATUS_DECODED_PROTOTYPE,
    RENDER_STATUS_PLACEHOLDER,
    RENDER_STATUS_PRODUCTION_RENDERED,
)
from backend.app.services.decoded_tile_cache import (
    TILE_MODE_PLACEHOLDER,
    TILE_MODE_PRODUCTION_PROTOTYPE,
    serve_tile_with_optional_decode,
)
from backend.app.services.grib2_decoder import MANIFEST_NAME, RASTER_RAW_NAME, build_decode_output_dir
from backend.app.services.production_tile_builder import (
    build_production_tile_for_frame,
    build_production_tiles,
    mark_frame_production_prototype,
    render_production_warped_tile_png,
)
from backend.app.services.tile_pyramid import build_production_tile_repo_path, production_tile_cache_path
from backend.app.services.render_metadata import GeoRenderMetadata, write_geo_metadata
from backend.app.services.tile_pyramid import (
    production_tile_cache_path,
    validate_geo_metadata,
    warp_grid_to_tile_values,
)


def _write_warp_fixture(
    storage,
    raw_path: str,
    *,
    width: int = 8,
    height: int = 8,
    bounds: Optional[list[float]] = None,
    source_crs: Optional[str] = "EPSG:4326",
) -> tuple[str, GeoRenderMetadata]:
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
        source_crs=source_crs,
        output_crs="EPSG:3857",
        bounds=bounds or [-100.0, 35.0, -99.0, 36.0],
        grid_width=width,
        grid_height=height,
        geo_accurate=False,
        production_rendering=False,
        notes=["Test fixture"],
    )
    write_geo_metadata(storage, output_dir, metadata)
    return output_dir, metadata


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))


def test_validate_geo_metadata_accepts_fixture_bounds():
    meta = GeoRenderMetadata(
        product_name="test",
        valid_timestamp=None,
        source_crs="EPSG:4326",
        output_crs="EPSG:3857",
        bounds=[-100.0, 35.0, -99.0, 36.0],
        grid_width=8,
        grid_height=8,
    )
    result = validate_geo_metadata(meta)
    assert result.valid is True


def test_validate_geo_metadata_rejects_unsupported_source_crs():
    meta = GeoRenderMetadata(
        product_name="test",
        valid_timestamp=None,
        source_crs="EPSG:5070",
        output_crs="EPSG:3857",
        bounds=[-100.0, 35.0, -99.0, 36.0],
        grid_width=8,
        grid_height=8,
    )
    result = validate_geo_metadata(meta)
    assert result.valid is False
    assert any("unsupported source_crs" in err for err in result.errors)


def test_validate_geo_metadata_rejects_missing_grid():
    meta = GeoRenderMetadata(
        product_name="test",
        valid_timestamp=None,
        source_crs="EPSG:4326",
        output_crs="EPSG:3857",
        bounds=[-100.0, 35.0, -99.0, 36.0],
        grid_width=0,
        grid_height=8,
    )
    result = validate_geo_metadata(meta)
    assert result.valid is False


def test_production_tile_cache_path_parts():
    parts = production_tile_cache_path("mrms_reflectivity", "2026-06-25T18:00:00Z", 0, 0, 0)
    assert parts == ("tiles", "production", "mrms_reflectivity", "20260625T180000Z", "0", "0", "0.png")


def test_build_production_tile_repo_path(storage):
    path = build_production_tile_repo_path(
        storage, "mrms_reflectivity", "2026-06-25T18:00:00Z", 0, 0, 0
    )
    assert path.endswith("data/tiles/production/mrms_reflectivity/20260625T180000Z/0/0/0.png")


def test_warp_small_fake_raster_to_tile_png(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "warp_unit.grib2.gz")
    _output_dir, metadata = _write_warp_fixture(storage, raw_path)

    grid = [[i / 7.0 for i in range(8)] for _ in range(8)]
    warped = warp_grid_to_tile_values(grid, metadata, z=0, x=0, y=0, tile_size=16)
    assert warped is not None
    assert len(warped) == 16
    assert len(warped[0]) == 16

    png = render_production_warped_tile_png(grid, metadata, z=0, x=0, y=0, tile_size=16)
    assert png is not None
    assert png.startswith(b"\x89PNG\r\n\x1a\n")


def test_build_production_tile_for_frame_writes_cache(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "build_unit.grib2.gz")
    output_dir, metadata = _write_warp_fixture(storage, raw_path)
    from backend.app.services.decoded_tile_cache import load_decode_manifest

    artifact = load_decode_manifest(storage, output_dir)
    assert artifact is not None

    path = build_production_tile_for_frame(
        storage,
        layer="mrms_reflectivity",
        timestamp="2026-06-25T18:00:00Z",
        artifact=artifact,
        metadata=metadata,
        z=0,
        x=0,
        y=0,
    )
    assert path is not None
    assert storage.path_exists(path)


def test_build_production_tiles_safe_with_no_artifacts(storage):
    result = build_production_tiles(storage)
    assert result.artifacts_found == 0
    assert result.built == 0
    assert any("No decode artifacts" in note for note in result.notes)


def test_production_flag_off_blocks_production_tiles(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "gate_off.grib2.gz")
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-25T18:00:00Z",
        raw_path=raw_path,
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=True,
        source="mrms_discovered",
    )

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
    assert served.tile_mode in (TILE_MODE_PLACEHOLDER, "placeholder_for_real_raw")
    assert served.production_rendering is False
    assert served.render_status == RENDER_STATUS_PLACEHOLDER


def test_production_flag_on_gate_closed_blocks_production_tiles(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "gate_closed.grib2.gz")
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-25T18:00:00Z",
        raw_path=raw_path,
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_DECODED_PROTOTYPE,
        production_rendering=False,
        source="mrms_discovered",
    )

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


def test_production_flag_on_gate_open_tile_exists_serves_production(
    client, db_session, storage, monkeypatch
):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", True)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)
    _use_test_storage(monkeypatch, storage)

    timestamp = "2026-06-25T18:00:00Z"
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "prod_serve.grib2.gz")
    output_dir, metadata = _write_warp_fixture(storage, raw_path)
    from backend.app.services.decoded_tile_cache import load_decode_manifest

    artifact = load_decode_manifest(storage, output_dir)
    assert artifact is not None
    build_production_tile_for_frame(
        storage,
        layer="mrms_reflectivity",
        timestamp=timestamp,
        artifact=artifact,
        metadata=metadata,
        z=0,
        x=0,
        y=0,
    )

    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=raw_path,
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=True,
        source="mrms_discovered",
        raw_kind="mrms_real_grib2",
    )
    db_session.add(frame)
    db_session.commit()

    response = client.get(f"/tiles/mrms_reflectivity/{timestamp}/0/0/0.png")
    assert response.status_code == 200
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert response.headers.get("x-radararchive-tile") == TILE_MODE_PRODUCTION_PROTOTYPE
    assert response.headers.get("x-radararchive-production-rendering") == "true"
    assert response.headers.get("x-radararchive-render-status") == RENDER_STATUS_PRODUCTION_RENDERED


def test_production_fallback_headers_honest(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", True)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)
    _use_test_storage(monkeypatch, storage)

    timestamp = "2026-06-25T19:00:00Z"
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "prod_missing.grib2.gz")
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=raw_path,
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=True,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    response = client.get(f"/tiles/mrms_reflectivity/{timestamp}/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-tile") in (TILE_MODE_PLACEHOLDER, "placeholder_for_real_raw")
    assert response.headers.get("x-radararchive-production-rendering") == "false"
    assert response.headers.get("x-radararchive-tile-fallback") == "true"


def test_mark_frame_production_prototype_unit(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "mark.grib2.gz")
    output_dir, _metadata = _write_warp_fixture(storage, raw_path)
    from backend.app.services.decoded_tile_cache import load_decode_manifest
    from backend.app.services.render_metadata import geo_metadata_path

    artifact = load_decode_manifest(storage, output_dir)
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-25T18:00:00Z",
        raw_path=raw_path,
        processed_status="placeholder_for_real_raw",
        source="mrms_discovered",
    )
    mark_frame_production_prototype(
        frame,
        artifact=artifact,
        metadata_path=geo_metadata_path(storage, output_dir),
    )
    assert frame.render_status == RENDER_STATUS_PRODUCTION_RENDERED
    assert frame.production_rendering is True
