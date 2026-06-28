import struct
import zlib


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def generate_placeholder_tile_png(
    *,
    width: int = 256,
    height: int = 256,
    z: int = 0,
    x: int = 0,
    y: int = 0,
) -> bytes:
    """Return a small obvious placeholder PNG tile (not real radar imagery)."""
    base_r, base_g, base_b, alpha = 59, 130, 246, 96
    r = min(255, base_r + ((x + y + z) * 17) % 80)
    g = min(255, base_g + ((x * 3 + z) * 11) % 60)
    b = min(255, base_b + ((y * 5 + z) * 13) % 70)

    raw = b""
    row = bytes([r, g, b, alpha]) * width
    for row_index in range(height):
        stripe = 20
        if (row_index // stripe + x + y + z) % 2 == 0:
            raw += b"\x00" + row
        else:
            raw += b"\x00" + bytes([r, g, b, max(40, alpha - 30)]) * width

    compressed = zlib.compress(raw, 9)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)

    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", compressed)
        + _png_chunk(b"IEND", b"")
    )


def _sample_grid_to_tile(
    grid: list[list[float]],
    *,
    z: int,
    x: int,
    y: int,
    width: int,
    height: int,
) -> list[list[float]]:
    grid_h = len(grid)
    grid_w = len(grid[0]) if grid_h else 0
    if grid_w == 0 or grid_h == 0:
        return [[0.0 for _ in range(width)] for _ in range(height)]

    num_tiles = max(1, 2**z)
    region_w = max(1, grid_w // num_tiles)
    region_h = max(1, grid_h // num_tiles)
    start_x = min(grid_w - 1, x * region_w)
    start_y = min(grid_h - 1, y * region_h)

    tile: list[list[float]] = []
    for row in range(height):
        gy = min(grid_h - 1, start_y + (row * region_h // max(1, height)))
        row_values: list[float] = []
        for col in range(width):
            gx = min(grid_w - 1, start_x + (col * region_w // max(1, width)))
            row_values.append(max(0.0, min(1.0, float(grid[gy][gx]))))
        tile.append(row_values)
    return tile


def generate_decoded_prototype_tile_png(
    grid: list[list[float]],
    *,
    z: int = 0,
    x: int = 0,
    y: int = 0,
    width: int = 256,
    height: int = 256,
) -> bytes:
    """Render a prototype PNG from a normalized 0..1 grid (not geo-accurate)."""
    sampled = _sample_grid_to_tile(grid, z=z, x=x, y=y, width=width, height=height)

    raw = b""
    for row in sampled:
        raw += b"\x00"
        for value in row:
            # Simple reflectivity-like blue→green→yellow→red prototype ramp.
            v = max(0.0, min(1.0, value))
            r = int(min(255, v * 510))
            g = int(min(255, max(0.0, (v - 0.25) * 340)))
            b = int(min(255, max(0.0, (0.6 - v) * 420)))
            alpha = 180 if v > 0.05 else 40
            raw += bytes([r, g, b, alpha])

    compressed = zlib.compress(raw, 9)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", compressed)
        + _png_chunk(b"IEND", b"")
    )
