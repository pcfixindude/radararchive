"""Reflectivity color scale for local decoded preview (prototype only)."""

from __future__ import annotations

import struct
import zlib
from typing import Optional

NO_DATA_DBZ_THRESHOLD = -900.0
MRMS_NO_DATA_DBZ = -999.0

# dBZ break, R, G, B, A (prototype MRMS-style palette)
REFLECTIVITY_COLOR_STOPS: list[tuple[float, int, int, int, int]] = [
    (5.0, 4, 156, 217, 200),
    (10.0, 0, 197, 255, 210),
    (15.0, 0, 255, 0, 220),
    (20.0, 0, 200, 0, 220),
    (25.0, 255, 255, 0, 230),
    (30.0, 255, 200, 0, 230),
    (35.0, 255, 128, 0, 235),
    (40.0, 255, 0, 0, 240),
    (45.0, 255, 0, 255, 240),
    (50.0, 160, 0, 255, 245),
    (55.0, 255, 255, 255, 250),
]

COLOR_SCALE_MODE = "reflectivity_dbz"


def is_no_data_dbz(value: float) -> bool:
    return value <= NO_DATA_DBZ_THRESHOLD or value >= 1000.0


def dbz_to_rgba(dbz: float) -> tuple[int, int, int, int]:
    if is_no_data_dbz(dbz):
        return (0, 0, 0, 0)

    if dbz <= REFLECTIVITY_COLOR_STOPS[0][0]:
        _, r, g, b, a = REFLECTIVITY_COLOR_STOPS[0]
        return (r, g, b, max(0, a - 40))

    for index in range(len(REFLECTIVITY_COLOR_STOPS) - 1):
        low = REFLECTIVITY_COLOR_STOPS[index]
        high = REFLECTIVITY_COLOR_STOPS[index + 1]
        if dbz <= high[0]:
            span = high[0] - low[0]
            if span <= 0:
                return (high[1], high[2], high[3], high[4])
            ratio = (dbz - low[0]) / span
            r = int(low[1] + (high[1] - low[1]) * ratio)
            g = int(low[2] + (high[2] - low[2]) * ratio)
            b = int(low[3] + (high[3] - low[3]) * ratio)
            a = int(low[4] + (high[4] - low[4]) * ratio)
            return (r, g, b, a)

    _, r, g, b, a = REFLECTIVITY_COLOR_STOPS[-1]
    return (r, g, b, a)


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def encode_dbz_grid_png(
    grid: list[list[float]],
    *,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> bytes:
    """Encode a dBZ grid to RGBA PNG with no-data transparency."""
    grid_h = len(grid)
    grid_w = len(grid[0]) if grid_h else 0
    out_w = width or grid_w
    out_h = height or grid_h

    raw = b""
    for row in range(out_h):
        raw += b"\x00"
        gy = min(grid_h - 1, int(row * grid_h / max(1, out_h))) if grid_h else 0
        for col in range(out_w):
            gx = min(grid_w - 1, int(col * grid_w / max(1, out_w))) if grid_w else 0
            dbz = float(grid[gy][gx]) if grid_h and grid_w else MRMS_NO_DATA_DBZ
            r, g, b, a = dbz_to_rgba(dbz)
            raw += bytes([r, g, b, a])

    compressed = zlib.compress(raw, 9)
    ihdr = struct.pack(">IIBBBBB", out_w, out_h, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", compressed)
        + _png_chunk(b"IEND", b"")
    )
