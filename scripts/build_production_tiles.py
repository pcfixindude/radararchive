"""Build geo-warped production tile cache from decode artifacts (prototype only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.production_tile_builder import (
    DEFAULT_MAX_ZOOM,
    DEFAULT_MIN_ZOOM,
    MAX_ALLOWED_ZOOM,
    build_production_tiles,
)
from backend.app.services.storage import LocalStorage


def _print_console_summary(result) -> None:
    print("Production tile build complete (warping prototype — NOT verified real MRMS):")
    print(f"  artifacts_found: {result.artifacts_found}")
    print(f"  frames_considered: {result.frames_considered}")
    print(f"  frames_skipped: {result.frames_skipped}")
    print(f"  zooms_built: {result.zooms_built}")
    print(f"  tiles_planned: {result.tiles_planned}")
    print(f"  tiles_written: {result.tiles_written}")
    print(f"  tiles_skipped_existing: {result.tiles_skipped_existing}")
    print(f"  tiles_failed: {result.tiles_failed}")
    print(f"  output_bytes: {result.output_bytes}")
    print(f"  elapsed_seconds: {result.elapsed_seconds}")
    print(f"  catalog_marked: {result.catalog_marked}")
    print(f"  dry_run: {result.dry_run}")
    print(f"  force: {result.force}")
    if result.errors:
        print(f"  errors: {len(result.errors)}")
        for err in result.errors[:10]:
            print(f"    - {err}")
    for note in result.notes:
        print(f"  note: {note}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build production warped tile cache from decode artifacts (Phase 16 prototype)."
    )
    parser.add_argument("--layer", default="mrms_reflectivity", help="Catalog layer id")
    parser.add_argument(
        "--min-zoom",
        type=int,
        default=DEFAULT_MIN_ZOOM,
        help=f"Minimum zoom (default {DEFAULT_MIN_ZOOM}, safe)",
    )
    parser.add_argument(
        "--max-zoom",
        type=int,
        default=DEFAULT_MAX_ZOOM,
        help=f"Maximum zoom (default {DEFAULT_MAX_ZOOM}, capped at {MAX_ALLOWED_ZOOM})",
    )
    parser.add_argument("--limit", type=int, default=None, help="Max decode artifacts to consider")
    parser.add_argument("--force", action="store_true", help="Rebuild tiles even when cache exists")
    parser.add_argument("--dry-run", action="store_true", help="Plan tiles without writing files")
    parser.add_argument("--json-report", action="store_true", help="Print JSON benchmark report to stdout")
    parser.add_argument(
        "--mark-catalog",
        action="store_true",
        help="Mark matching catalog frames production_rendered (PROTOTYPE ONLY — fixture/test).",
    )
    args = parser.parse_args()

    if args.mark_catalog:
        print(
            "WARNING: --mark-catalog sets production_rendered on matching catalog frames.\n"
            "         This is a WARPING PROTOTYPE ONLY — not verified real MRMS production output.\n"
            "         Use only for fixtures/tests. Real MRMS rows should not be marked casually.\n",
            file=sys.stderr,
        )

    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)

    result = build_production_tiles(
        storage,
        session,
        layer=args.layer,
        min_zoom=args.min_zoom,
        max_zoom=args.max_zoom,
        force=args.force,
        dry_run=args.dry_run,
        limit=args.limit,
        mark_catalog=args.mark_catalog,
    )

    if args.json_report:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        _print_console_summary(result)

    if result.artifacts_found == 0 and not args.json_report:
        print("\nNo decode artifacts to warp.")
        print("  1. Add test fixtures or: make decode-grib2")
        print("  2. make build-production-tiles")
        print("\nPlaceholder tiles remain the default (ENABLE_PRODUCTION_RADAR_TILES=false).")


if __name__ == "__main__":
    main()
