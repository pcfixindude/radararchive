"""Warm per-frame decode cache for smooth local playback."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.services.frame_cache_warmer import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    run_cache_warm,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Warm per-frame decode cache for local MRMS playback."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Max frames to warm (default {DEFAULT_LIMIT}, max {MAX_LIMIT})",
    )
    parser.add_argument("--start", default=None, help="Optional ISO start timestamp")
    parser.add_argument("--end", default=None, help="Optional ISO end timestamp")
    parser.add_argument(
        "--product",
        default="mrms_reflectivity",
        help="Catalog product id filter",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-decode even when frame cache already exists",
    )
    parser.add_argument(
        "--include-stubs",
        action="store_true",
        help="Include non-real/stub frames (default: real local MRMS only)",
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    args = parser.parse_args()

    print(
        "WARNING: Frame cache warming is local prototype only — NOT verified MRMS. "
        "Production tile serving remains off.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    init_db()
    session = get_session_factory()()
    try:
        if catalog_is_empty(session):
            seed_demo_catalog(session, storage=storage)
        report = run_cache_warm(
            session,
            storage,
            start_time=args.start,
            end_time=args.end,
            limit=args.limit,
            product_id=args.product,
            force=args.force,
            real_only=not args.include_stubs,
        )
        session.commit()
    finally:
        session.close()

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print("MRMS frame cache warm (prototype only — NOT verified MRMS):")
    print(f"  warm_status: {report.get('warm_status')}")
    print(f"  window_source: {report.get('window_source')}")
    print(f"  frames_considered: {report.get('frames_considered')}")
    print(f"  frames_already_cached: {report.get('frames_already_cached')}")
    print(f"  frames_decoded: {report.get('frames_decoded')}")
    print(f"  frames_matched: {report.get('frames_matched')}")
    print(f"  frames_failed: {report.get('frames_failed')}")
    print(f"  elapsed_seconds: {report.get('elapsed_seconds')}")
    for ts in report.get("decoded_timestamps") or []:
        print(f"  decoded: {ts}")
    for ts in report.get("already_cached_timestamps") or []:
        print(f"  cached: {ts}")
    for item in report.get("failed_frames") or []:
        print(f"  failed: {item.get('timestamp')} — {item.get('message')}")
    for cmd in report.get("next_commands") or []:
        print(f"  next: {cmd}")
    print(f"  json_path: {report.get('json_path')}")
    print(f"  markdown_path: {report.get('markdown_path')}")

    if report.get("warm_status") in {"failed", "no_frames"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
