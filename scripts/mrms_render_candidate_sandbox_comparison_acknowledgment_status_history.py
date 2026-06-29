"""Refresh local sandbox comparison acknowledgment status history (Phase 71)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_history import (
    build_ack_status_history_payload,
    compact_ack_status_history,
    refresh_ack_status_history_report,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh local sandbox comparison acknowledgment status history (Phase 71)."
    )
    parser.add_argument("--refresh", action="store_true", help="Persist history summary Markdown report")
    parser.add_argument("--json-report", action="store_true", help="Print JSON compact summary")
    args = parser.parse_args()

    print(
        "WARNING: Acknowledgment status history is local advisory only — "
        "does NOT clear alerts, verify MRMS, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = refresh_ack_status_history_report(storage)
    else:
        report = build_ack_status_history_payload(storage)["latest"]

    compact = compact_ack_status_history(storage)
    if args.json_report:
        print(json.dumps(compact, indent=2, sort_keys=True))
        return

    print(f"History count: {compact.get('history_count')}")
    print(f"Latest rollup status: {compact.get('latest_rollup_status')}")
    print(f"Latest coverage change: {compact.get('latest_coverage_change')}")
    if args.refresh:
        print(f"Markdown: {report.get('markdown_path')}")


if __name__ == "__main__":
    main()
