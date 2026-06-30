"""Bulk download/register a bounded MRMS window for local playback."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import MRMS_SOURCE_MODE_REAL, settings
from backend.app.database import get_session_factory, init_db
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.services.mrms_bulk_ingest import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    run_bulk_local_ingest,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bulk ingest a bounded MRMS window into local catalog/raw storage."
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Explicitly use real NOAA MRMS network download (required)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Max frames to ingest (default {DEFAULT_LIMIT}, max {MAX_LIMIT})",
    )
    parser.add_argument(
        "--start",
        default=None,
        help="Optional ISO start timestamp for window filter",
    )
    parser.add_argument(
        "--end",
        default=None,
        help="Optional ISO end timestamp for window filter",
    )
    parser.add_argument(
        "--product",
        default="MRMS_ReflectivityAtLowestAltitude",
        help="MRMS product name",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even when local raw file already exists",
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    args = parser.parse_args()

    if not args.real and settings.mrms_source_mode != MRMS_SOURCE_MODE_REAL:
        print(
            "ERROR: Bulk ingest requires explicit --real flag for network download.",
            file=sys.stderr,
        )
        print("Example: make mrms-bulk-local-ingest ARGS='--real --limit 8'", file=sys.stderr)
        raise SystemExit(2)

    print(
        "WARNING: Bulk MRMS ingest is local prototype only — NOT verified MRMS. "
        "Production tile serving remains off.",
        file=sys.stderr,
    )

    mode = MRMS_SOURCE_MODE_REAL if args.real else settings.mrms_source_mode
    storage = LocalStorage(settings.local_storage_root)
    init_db()
    session = get_session_factory()()
    try:
        if catalog_is_empty(session):
            seed_demo_catalog(session, storage=storage)
        report = run_bulk_local_ingest(
            session,
            storage,
            mode=mode,
            product=args.product,
            start_time=args.start,
            end_time=args.end,
            limit=args.limit,
            force=args.force,
        )
        session.commit()
    finally:
        session.close()

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print("MRMS bulk local ingest (prototype only — NOT verified MRMS):")
    print(f"  ingest_status: {report.get('ingest_status')}")
    print(f"  mode: {report.get('mode')}")
    window = report.get("requested_window") or {}
    print(f"  window_limit: {window.get('limit')}")
    print(f"  frames_discovered: {report.get('frames_discovered')}")
    print(f"  frames_selected: {report.get('frames_selected')}")
    print(f"  frames_registered_created: {report.get('frames_registered_created')}")
    print(f"  frames_registered_skipped: {report.get('frames_registered_skipped')}")
    print(f"  frames_downloaded: {report.get('frames_downloaded')}")
    print(f"  frames_already_present: {report.get('frames_already_present')}")
    print(f"  frames_failed: {report.get('frames_failed')}")
    for ts in report.get("registered_timestamps") or []:
        print(f"  registered: {ts}")
    for path in report.get("raw_paths") or []:
        print(f"  raw_path: {path}")
    for item in report.get("failures") or []:
        print(f"  failure: {item.get('timestamp')} — {item.get('error')}")
    for cmd in report.get("next_commands") or []:
        print(f"  next: {cmd}")
    print(f"  json_path: {report.get('json_path')}")
    print(f"  markdown_path: {report.get('markdown_path')}")

    if report.get("ingest_status") in {"failed", "discovery_failed", "invalid_mode", "no_frames"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
