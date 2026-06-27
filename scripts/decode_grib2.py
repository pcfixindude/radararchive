"""Decode GRIB2.gz to prototype normalized raster (optional dependencies)."""

import argparse

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.grib2_decoder import decode_grib2_file
from backend.app.services.grib2_inspect_catalog import find_real_mrms_inspect_candidates
from backend.app.services.grib2_inspector import detect_decoder_availability
from backend.app.services.storage import LocalStorage

NO_REAL_FILE_HINT = (
    "No real downloaded MRMS .grib2.gz file found in the catalog.\n"
    "To fetch one (requires network):\n"
    "  MRMS_SOURCE_MODE=real make download-mrms -- --register-discovered --limit 1"
)


def _print_availability() -> None:
    availability = detect_decoder_availability()
    print(availability.summary_message())
    print(
        f"  wgrib2={availability.wgrib2} gdal={availability.gdal} "
        f"rasterio={availability.rasterio} pygrib={availability.pygrib} cfgrib={availability.cfgrib}"
    )
    print("Prototype decode prefers rasterio, then wgrib2 bin export.")
    print("Placeholder /tiles behavior is unchanged.\n")


def _print_result(result) -> None:
    print(f"Raw path: {result.raw_path}")
    print(f"  raw_kind: {result.raw_kind}")
    print(f"  success: {result.success}")
    print(f"  decoder_unavailable: {result.decoder_unavailable}")
    if result.decoder_used:
        print(f"  decoder_used: {result.decoder_used}")
    if result.staged_grib2_path:
        print(f"  staged_grib2_path: {result.staged_grib2_path}")
    if result.output_dir:
        print(f"  output_dir: {result.output_dir}")
    if result.manifest_path:
        print(f"  manifest_path: {result.manifest_path}")
    if result.raster_path:
        print(f"  raster_path: {result.raster_path}")
    if result.width is not None and result.height is not None:
        print(f"  grid: {result.width} x {result.height}")
    if result.value_min is not None and result.value_max is not None:
        print(f"  value_range: {result.value_min} .. {result.value_max}")
    for note in result.notes:
        print(f"  note: {note}")
    if result.error:
        print(f"  error: {result.error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Decode GRIB2 prototype raster (optional deps)")
    parser.add_argument("--file", help="Repo-relative path to .grib2 or .grib2.gz")
    parser.add_argument(
        "--latest-mrms",
        action="store_true",
        help="Decode latest real downloaded MRMS file from catalog",
    )
    parser.add_argument("--limit", type=int, default=1, help="Max files for --latest-mrms")
    args = parser.parse_args()

    storage = LocalStorage(settings.local_storage_root)
    _print_availability()

    if args.file:
        result = decode_grib2_file(storage, args.file)
        _print_result(result)
        if result.error:
            raise SystemExit(1)
        if result.decoder_unavailable:
            raise SystemExit(0)
        return

    init_db()
    session = get_session_factory()()
    try:
        candidates = find_real_mrms_inspect_candidates(session, storage, limit=args.limit)
    finally:
        session.close()

    if not candidates:
        print(NO_REAL_FILE_HINT)
        raise SystemExit(0)

    exit_code = 0
    for candidate in candidates:
        print(f"Catalog candidate id={candidate.radar_file_id} timestamp={candidate.timestamp}")
        result = decode_grib2_file(storage, candidate.raw_path)
        _print_result(result)
        print()
        if result.error:
            exit_code = 1
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
