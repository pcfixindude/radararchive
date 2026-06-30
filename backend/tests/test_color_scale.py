"""Tests for reflectivity color scale (Phase 106)."""

from backend.app.services.color_scale import (
    COLOR_SCALE_MODE,
    MRMS_NO_DATA_DBZ,
    dbz_to_rgba,
    encode_dbz_grid_png,
    is_no_data_dbz,
)


def test_no_data_is_transparent():
    assert is_no_data_dbz(MRMS_NO_DATA_DBZ) is True
    assert dbz_to_rgba(MRMS_NO_DATA_DBZ) == (0, 0, 0, 0)


def test_reflectivity_color_increases_with_dbz():
    low = dbz_to_rgba(10.0)
    high = dbz_to_rgba(45.0)
    assert low[3] > 0
    assert high[3] > 0
    assert sum(high[:3]) >= sum(low[:3])


def test_encode_dbz_grid_png_produces_png():
    grid = [[MRMS_NO_DATA_DBZ, 20.0], [35.0, 50.0]]
    png = encode_dbz_grid_png(grid, width=4, height=4)
    assert png.startswith(b"\x89PNG")


def test_color_scale_mode_constant():
    assert COLOR_SCALE_MODE == "reflectivity_dbz"
