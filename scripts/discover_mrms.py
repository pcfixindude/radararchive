"""Discover public MRMS object metadata and optionally register catalog rows."""

import argparse

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.services.mrms_discovery import register_discovered_files
from backend.app.services.storage import LocalStorage
from backend.app.sources.mrms import MrmsDiscoveryError, discover_latest_mrms


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover MRMS metadata (no GRIB2 download)")
    parser.add_argument(
        "--product",
        default="MRMS_ReflectivityAtLowestAltitude",
        help="MRMS product name",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max files to discover (default from MRMS_DISCOVERY_LIMIT config)",
    )
    parser.add_argument(
        "--register",
        action="store_true",
        help="Register discovered rows in SQLite catalog (default: discovery only)",
    )
    args = parser.parse_args()

    should_register = args.register

    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)
    try:
        if catalog_is_empty(session):
            seed_demo_catalog(session, storage=storage)

        discoveries = discover_latest_mrms(args.product, limit=args.limit)
        print(
            f"MRMS discovery complete (mode={settings.mrms_source_mode}, product={args.product}):"
        )
        print(f"  found: {len(discoveries)}")
        for item in discoveries:
            size = f"{item.size_bytes} bytes" if item.size_bytes is not None else "size unknown"
            print(f"  - {item.timestamp} {item.file_name} ({size})")
            print(f"    {item.source_url}")

        if should_register and discoveries:
            result = register_discovered_files(session, discoveries)
            print(f"Catalog registration: created={result.created}, skipped={result.skipped}")
        elif should_register:
            print("Catalog registration: nothing to register")
    except MrmsDiscoveryError as exc:
        print(f"MRMS discovery failed: {exc}")
        raise SystemExit(1) from exc
    finally:
        session.close()


if __name__ == "__main__":
    main()
