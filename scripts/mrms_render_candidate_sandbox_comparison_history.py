"""Refresh local MRMS render candidate sandbox comparison history."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox_comparison_history import (
    SUGGESTED_COMMAND,
    build_comparison_history_payload,
    compact_comparison_history,
    refresh_comparison_history_report,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Local MRMS render candidate sandbox comparison history (Phase 67)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh local comparison history summary report under data/dev/",
    )
    args = parser.parse_args()

    print(
        "WARNING: Sandbox comparison history is local advisory only — NOT verified MRMS. "
        "Does not download, decode, render, serve production tiles, clear alerts, or authorize production use.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = refresh_comparison_history_report(storage)
    else:
        report = build_comparison_history_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_comparison_history(storage)
    print("MRMS render candidate sandbox comparison history (local advisory only — NOT verified MRMS):")
    print(f"  history_status: {compact.get('history_status')}")
    print(f"  history_count: {compact.get('history_count')}")
    print(f"  latest_comparison_type: {compact.get('latest_comparison_type')}")
    print(f"  latest_comparison_status: {compact.get('latest_comparison_status')}")
    print(f"  json_path: {compact.get('json_path')}")
    print(f"  markdown_path: {compact.get('markdown_path')}")
    print(f"  suggested_command: {compact.get('suggested_command') or SUGGESTED_COMMAND}")
    print(f"  verified_mrms: {compact.get('verified_mrms')}")


if __name__ == "__main__":
    main()
