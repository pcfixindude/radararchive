import json
import struct

import pytest

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.services.decoded_tile_cache import (
    TILE_MODE_DECODED_PROTOTYPE,
    TILE_MODE_PLACEHOLDER,
    build_tile_cache,
    load_decode_manifest,
    serve_tile_with_optional_decode,
)
from backend.app.services.grib2_decoder import MANIFEST_NAME, RASTER_RAW_NAME, build_decode_output_dir
from backend.app.services.processor import process_pending_frames


def _write_decode_fixture(storage, raw_path: str, *, width: int = 4, height: int = 4) -> str:
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
    return output_dir


def test_load_decode_manifest_parses_fixture(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "fixture.grib2.gz")
    output_dir = _write_decode_fixture(storage, raw_path)

    artifact = load_decode_manifest(storage, output_dir)

    assert artifact is not None
    assert artifact.width == 4
    assert artifact.height == 4
    assert artifact.production_rendering is False


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))


def test_flag_off_uses_placeholder(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)
    _use_test_storage(monkeypatch, storage)
    process_pending_frames(db_session, storage)

    response = client.get("/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-tile") == TILE_MODE_PLACEHOLDER
    assert response.headers.get("x-radararchive-production-rendering") == "false"


def test_flag_on_no_artifact_falls_back_to_placeholder(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_decoded_tiles", True)
    _use_test_storage(monkeypatch, storage)
    process_pending_frames(db_session, storage)

    response = client.get("/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-tile") == TILE_MODE_PLACEHOLDER
    assert response.headers.get("x-radararchive-tile-fallback") == "true"


def test_flag_on_with_artifact_serves_decoded_prototype(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_decoded_tiles", True)
    _use_test_storage(monkeypatch, storage)
    timestamp = "2026-06-25T18:00:00Z"
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "decoded_frame.grib2.gz")
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
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert response.headers.get("x-radararchive-tile") == TILE_MODE_DECODED_PROTOTYPE
    assert response.headers.get("x-radararchive-production-rendering") == "false"
    assert response.headers.get("x-radararchive-render-status") == "decoded_prototype"


def test_plan_enforcement_still_blocks_tiles(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_decoded_tiles", True)
    _use_test_storage(monkeypatch, storage)
    process_pending_frames(db_session, storage)

    response = client.get(
        "/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png?plan=free"
    )
    assert response.status_code == 403


def test_build_tile_cache_no_artifacts(storage):
    result = build_tile_cache(storage)
    assert result.artifacts_found == 0
    assert result.built == 0
    assert any("decode-grib2" in note for note in result.notes)


def test_build_tile_cache_with_fixture(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "cache_test.grib2.gz")
    _write_decode_fixture(storage, raw_path)

    result = build_tile_cache(storage)
    assert result.artifacts_found == 1
    assert result.built >= 1


def test_tiles_config_endpoint(client):
    response = client.get("/tiles/config")
    assert response.status_code == 200
    body = response.json()
    assert body["enable_decoded_tiles"] is False
    assert body["production_rendering"] is False


def test_serve_tile_with_optional_decode_unit(storage):
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "unit.grib2.gz")
    _write_decode_fixture(storage, raw_path)
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-25T12:00:00Z",
        raw_path=raw_path,
        processed_status="placeholder_for_real_raw",
        source="mrms_discovered",
    )

    off = serve_tile_with_optional_decode(
        storage, frame, frame.timestamp, enable_decoded_tiles=False, z=0, x=0, y=0
    )
    assert off.tile_mode == "placeholder_for_real_raw"

    on = serve_tile_with_optional_decode(
        storage, frame, frame.timestamp, enable_decoded_tiles=True, z=0, x=0, y=0
    )
    assert on.tile_mode == TILE_MODE_DECODED_PROTOTYPE
