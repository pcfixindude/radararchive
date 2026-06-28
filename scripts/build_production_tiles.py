"""Build geo-warped production tile cache from decode artifacts (prototype only)."""

from __future__ import annotations

import argparse

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.production_tile_builder import build_production_tiles
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build production warped tile cache from decode artifacts (Phase 15 prototype)."
    )
    parser.add_argument("--layer", default="mrms_reflectivity", help="Catalog layer id")
    parser.add_argument("--z", type=int, default=0, help="Zoom level to build")
    parser.add_argument("--xy-limit", type=int, default=1, help="Build tiles for x/y in [0, limit)")
    parser.add_argument(
        "--mark-catalog",
        action="store_true",
        help="Mark matching catalog frames production_rendered (prototype only, fixture use).",
    )
    args = parser.parse_args()

    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)

    result = build_production_tiles(
        storage,
        session,
        layer=args.layer,
        z_levels=[args.z],
        xy_limit=args.xy_limit,
        mark_catalog=args.mark_catalog,
    )

    print("Production tile build complete (warping prototype — not verified MRMS):")
    print(f"  artifacts_found: {result.artifacts_found}")
    print(f"  built: {result.built}")
    print(f"  skipped: {result.skipped}")
    print(f"  catalog_marked: {result.catalog_marked}")
    for note in result.notes:
        print(f"  note: {note}")

    if result.artifacts_found == 0:
        print("\nNo decode artifacts to warp.")
        print("  1. Add test fixtures or: make decode-grib2")
        print("  2. make build-production-tiles")
        print("\nPlaceholder tiles remain the default (ENABLE_PRODUCTION_RADAR_TILES=false).")


if __name__ == "__main__":
    main()
