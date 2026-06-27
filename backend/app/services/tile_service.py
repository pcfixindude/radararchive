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
