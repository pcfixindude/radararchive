"""Tests for local color tile preview (Phase 106)."""

from __future__ import annotations

import json
import struct

from backend.app.config import settings
from backend.app.services.grib2_decoder import MANIFEST_NAME, RASTER_RAW_NAME, build_decode_output_dir
from backend.app.services.tile_preview import (
    LOCAL_TILE_ROOT,
    TILE_MODE_LOCAL_RASTER,
    build_local_tile_preview,
    load_local_tile_png,
    read_artifact_dbz_grid,
    render_color_preview_tile,
)
from backend.app.services.decoded_tile_cache import load_decode_manifest


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))


def _write_decode_fixture(storage, raw_path: str, *, width: int = 8, height: int = 4) -> str:
    output_dir = build_decode_output_dir(storage, raw_path)
    storage.ensure_directories(output_dir)
    grid_values = [i / 31.0 for i in range(width * height)]
    raster_path = storage.normalize_path(output_dir, RASTER_RAW_NAME)
    storage.write_bytes(raster_path, struct.pack(f"{len(grid_values)}f", *grid_values))
    manifest = {
        "prototype": True,
        "production_rendering": False,
        "raw_path": raw_path,
        "decoder": "mock",
        "width": width,
        "height": height,
        "value_min": -999.0,
        "value_max": 50.0,
        "raster_path": RASTER_RAW_NAME,
    }
    manifest_path = storage.normalize_path(output_dir, MANIFEST_NAME)
    storage.absolute_path(manifest_path).write_text(json.dumps(manifest), encoding="utf-8")
    return output_dir


def test_render_color_preview_tile_png(storage):
    grid = [[-999.0, 10.0, 25.0, 40.0] for _ in range(4)]
    png = render_color_preview_tile(grid, z=0, x=0, y=0, width=8, height=8)
    assert png.startswith(b"\x89PNG")


def test_build_local_tile_preview(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    raw_path = storage.normalize_path("raw", "mrms", "reflectivity", "fixture.grib2.gz")
    output_dir = _write_decode_fixture(storage, raw_path)
    artifact = load_decode_manifest(storage, output_dir)
    assert artifact is not None

    dbz_grid = read_artifact_dbz_grid(storage, artifact)
    assert dbz_grid is not None

    result = build_local_tile_preview(storage, artifact, z_levels=[0, 1], xy_limit=2)
    assert result.built == 8
    assert result.tile_mode == TILE_MODE_LOCAL_RASTER
    assert load_local_tile_png(storage, z=0, x=0, y=0) is not None
    assert storage.path_exists(storage.normalize_path(LOCAL_TILE_ROOT, "1", "0", "0.png"))
