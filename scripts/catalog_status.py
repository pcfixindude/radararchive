"""Print MRMS catalog status counts (dev/prototype)."""

from __future__ import annotations

import argparse
import json

from backend.app.database import get_session_factory, init_db
from backend.app.services.catalog_status import build_catalog_status


def main() -> None:
    parser = argparse.ArgumentParser(description="MRMS catalog status (Phase 21 dev).")
    parser.add_argument("--json-report", action="store_true", help="Print JSON")
    args = parser.parse_args()

    init_db()
    session = get_session_factory()()
    try:
        status = build_catalog_status(session)
    finally:
        session.close()

    if args.json_report:
        print(json.dumps(status, indent=2, sort_keys=True))
        return

    print("MRMS catalog status (prototype — NOT verified MRMS):")
    print(f"  product_id: {status['product_id']}")
    print(f"  total_frames: {status['total_frames']}")
    print(f"  mrms_discovered_frames: {status['mrms_discovered_frames']}")
    print(f"  latest_timestamp: {status['latest_timestamp']}")
    print(f"  earliest_timestamp: {status['earliest_timestamp']}")
    print(f"  latest_downloaded_timestamp: {status['latest_downloaded_timestamp']}")
    print("  download_status:")
    for key, value in status["download_status"].items():
        print(f"    {key}: {value}")
    print("  processed_status:")
    for key, value in status["processed_status"].items():
        print(f"    {key}: {value}")
    print("  render_status:")
    for key, value in status["render_status"].items():
        print(f"    {key}: {value}")


if __name__ == "__main__":
    main()
