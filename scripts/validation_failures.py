"""View recent validation failure log entries (dev/prototype)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_failure_log import (
    MAX_FAILURE_ENTRIES,
    count_validation_failures,
    load_recent_validation_failures,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show recent validation failures from local dev log (Phase 24)."
    )
    parser.add_argument("--limit", type=int, default=10, help="Max entries to print (default 10)")
    parser.add_argument("--json", action="store_true", help="Print JSON array")
    args = parser.parse_args()

    storage = LocalStorage(settings.local_storage_root)
    limit = max(1, min(args.limit, 25))
    entries = load_recent_validation_failures(storage, limit=limit)
    total = count_validation_failures(storage)

    if args.json:
        print(
            json.dumps(
                {
                    "prototype": True,
                    "verified_mrms": False,
                    "count": total,
                    "max_entries": MAX_FAILURE_ENTRIES,
                    "entries": entries,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

    print("Validation failures (experimental prototype — NOT verified MRMS):")
    print(f"  total_logged: {total} (max {MAX_FAILURE_ENTRIES})")
    if not entries:
        print("  (no failures logged)")
        return
    for item in entries:
        print(
            f"  - {item.get('logged_at')} [{item.get('phase')}/{item.get('step')}] "
            f"{item.get('error_message') or '(warning)'}"
        )
        if item.get("command_context"):
            print(f"      context: {item.get('command_context')}")
        for warning in item.get("warnings", [])[:2]:
            print(f"      warning: {warning}")

    if total > limit:
        print(f"  (showing {limit} most recent; use --limit or --json for more)", file=sys.stderr)


if __name__ == "__main__":
    main()
