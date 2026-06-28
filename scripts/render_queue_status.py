"""Report render queue summary metrics (dev/prototype)."""

from __future__ import annotations

import argparse
import json

from backend.app.database import get_session_factory, init_db
from backend.app.services.render_queue import get_queue_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Render queue status (Phase 18).")
    parser.add_argument("--json-report", action="store_true", help="Print JSON summary")
    args = parser.parse_args()

    init_db()
    session = get_session_factory()()
    summary = get_queue_summary(session)

    if args.json_report:
        print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
        return

    print("Render queue summary (prototype — NOT verified MRMS):")
    print(f"  queued: {summary.queued}")
    print(f"  running: {summary.running}")
    print(f"  succeeded: {summary.succeeded}")
    print(f"  failed: {summary.failed}")
    print(f"  canceled: {summary.canceled}")
    print(f"  total_tiles_written: {summary.total_tiles_written}")
    print(f"  total_output_bytes: {summary.total_output_bytes}")


if __name__ == "__main__":
    main()
