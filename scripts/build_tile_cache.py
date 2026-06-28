"""Pre-build prototype tile cache from Phase 12 decode artifacts."""

from backend.app.config import settings
from backend.app.services.decoded_tile_cache import build_tile_cache
from backend.app.services.storage import LocalStorage


def main() -> None:
    storage = LocalStorage(settings.local_storage_root)
    result = build_tile_cache(storage)

    print("Tile cache build complete (prototype only — not production rendering):")
    print(f"  artifacts_found: {result.artifacts_found}")
    print(f"  built: {result.built}")
    print(f"  skipped: {result.skipped}")
    for note in result.notes:
        print(f"  note: {note}")

    if result.artifacts_found == 0:
        print("\nNo decoded artifacts to cache.")
        print("  1. MRMS_SOURCE_MODE=real make download-mrms -- --register-discovered --limit 1")
        print("  2. make decode-grib2")
        print("  3. make build-tile-cache")
        print("\nPlaceholder tiles remain the default (ENABLE_DECODED_TILES=false).")


if __name__ == "__main__":
    main()
