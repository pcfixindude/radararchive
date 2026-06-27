"""Inspect GRIB2.gz metadata for evaluation — no production rendering."""

import argparse

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.grib2_inspect_catalog import find_real_mrms_inspect_candidates
from backend.app.services.grib2_inspector import detect_decoder_availability, inspect_grib2_file
from backend.app.services.storage import LocalStorage

NO_REAL_FILE_HINT = (
    "No real downloaded MRMS .grib2.gz file found in the catalog.\n"
    "To fetch one (requires network):\n"
    "  MRMS_SOURCE_MODE=real make download-mrms -- --register-discovered --limit 1"
)


def _print_availability() -> None:
    availability = detect_decoder_availability()
    print(availability.summary_message())
    print(f"  wgrib2={availability.wgrib2} gdal={availability.gdal} "
          f"rasterio={availability.rasterio} pygrib={availability.pygrib} cfgrib={availability.cfgrib}")
    print()


def _print_result(result) -> None:
    print(f"Raw path: {result.raw_path}")
    print(f"  raw_kind: {result.raw_kind}")
    print(f"  file_exists: {result.file_exists}")
    print(f"  inspectable: {result.inspectable}")
    if result.compressed_size_bytes is not None:
        print(f"  compressed_size_bytes: {result.compressed_size_bytes}")
    if result.decompressed_size_bytes is not None:
        print(f"  decompressed_size_bytes: {result.decompressed_size_bytes}")
    if result.staged_grib2_path:
        print(f"  staged_grib2_path: {result.staged_grib2_path}")
    if result.has_grib_magic is not None:
        print(f"  has_grib_magic: {result.has_grib_magic}")
    if result.decoder_used:
        print(f"  decoder_used: {result.decoder_used}")
    if result.metadata:
        print("  metadata:")
        for key, value in result.metadata.items():
            if key == "inventory_lines" and isinstance(value, list):
                print(f"    {key}: {len(value)} line(s)")
                for line in value[:5]:
                    print(f"      {line}")
                if len(value) > 5:
                    print(f"      ... ({len(value) - 5} more)")
            elif key != "inventory_text":
                print(f"    {key}: {value}")
    for note in result.notes:
        print(f"  note: {note}")
    if result.error:
        print(f"  error: {result.error}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect MRMS GRIB2.gz metadata (evaluation spike)")
    parser.add_argument("--file", help="Repo-relative or absolute path to a .grib2.gz file")
    parser.add_argument(
        "--latest-mrms",
        action="store_true",
        help="Inspect latest real downloaded MRMS file from catalog",
    )
    parser.add_argument("--limit", type=int, default=1, help="Max catalog files when using --latest-mrms")
    args = parser.parse_args()

    storage = LocalStorage(settings.local_storage_root)
    _print_availability()

    if args.file:
        raw_path = args.file
        if raw_path.startswith("/"):
            abs_path = raw_path
            rel = str(abs_path)
            for prefix in (str(storage.storage_root), "./data", "data"):
                if abs_path.startswith(prefix):
                    rel = "data/" + abs_path[len(prefix).lstrip("/") :]
                    break
            raw_path = rel if rel.startswith("data/") else args.file
        result = inspect_grib2_file(storage, raw_path)
        _print_result(result)
        if result.error:
            raise SystemExit(1)
        return

    if args.latest_mrms or not args.file:
        init_db()
        session = get_session_factory()()
        try:
            candidates = find_real_mrms_inspect_candidates(session, storage, limit=args.limit)
        finally:
            session.close()

        if not candidates:
            print(NO_REAL_FILE_HINT)
            raise SystemExit(0)

        for candidate in candidates:
            print(f"Catalog candidate id={candidate.radar_file_id} timestamp={candidate.timestamp}")
            result = inspect_grib2_file(storage, candidate.raw_path)
            _print_result(result)
            print()
        return

    parser.print_help()
    raise SystemExit(2)


if __name__ == "__main__":
    main()
