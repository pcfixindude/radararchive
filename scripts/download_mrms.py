"""Download discovered MRMS GRIB2.gz files to local raw storage (no GRIB2 parse)."""

import argparse

from backend.app.config import MRMS_SOURCE_MODE_REAL, MRMS_SOURCE_MODE_STUB, settings
from backend.app.database import get_session_factory, init_db
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.services.mrms_discovery import register_discovered_files
from backend.app.services.mrms_downloader import MrmsDownloadError, download_pending_mrms
from backend.app.services.storage import LocalStorage
from backend.app.sources.mrms import MrmsDiscoveryError, discover_latest_mrms


def main() -> None:
    parser = argparse.ArgumentParser(description="Download MRMS GRIB2.gz files (no parse)")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Max files to download (default 5)",
    )
    parser.add_argument(
        "--register-discovered",
        action="store_true",
        help="Discover + register catalog rows before downloading",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even when a local raw file already exists",
    )
    parser.add_argument(
        "--mode",
        choices=[MRMS_SOURCE_MODE_STUB, MRMS_SOURCE_MODE_REAL],
        default=None,
        help="Download mode (default from MRMS_SOURCE_MODE config)",
    )
    parser.add_argument(
        "--product",
        default="MRMS_ReflectivityAtLowestAltitude",
        help="MRMS product when using --register-discovered",
    )
    args = parser.parse_args()

    mode = args.mode or settings.mrms_source_mode
    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)

    try:
        if catalog_is_empty(session):
            seed_demo_catalog(session, storage=storage)

        if args.register_discovered:
            try:
                discoveries = discover_latest_mrms(args.product, limit=args.limit, mode=mode)
            except MrmsDiscoveryError as exc:
                print(f"MRMS discovery failed: {exc}")
                raise SystemExit(1) from exc
            reg = register_discovered_files(session, discoveries)
            print(
                f"Registered discovered rows: created={reg.created}, skipped={reg.skipped}"
            )

        result = download_pending_mrms(
            session,
            storage,
            limit=args.limit,
            force=args.force,
            mode=mode,
        )

        print(f"MRMS download complete (mode={mode}):")
        print(f"  downloaded: {len(result.downloaded)}")
        print(f"  skipped: {result.skipped}")
        print(f"  failed: {len(result.failed)}")
        for item in result.downloaded:
            label = "stub" if item.stub else "real"
            print(
                f"  - {item.timestamp} -> {item.raw_path} ({item.file_size_bytes} bytes, {label})"
            )
            print(f"    sha256={item.sha256}")
        for radar_id, timestamp, message in result.failed:
            print(f"  ! failed id={radar_id} {timestamp}: {message}")

        if result.failed:
            raise SystemExit(1)
    except MrmsDownloadError as exc:
        print(f"MRMS download failed: {exc}")
        raise SystemExit(1) from exc
    finally:
        session.close()


if __name__ == "__main__":
    main()
