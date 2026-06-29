"""Refresh local candidate trend-hint acknowledgment status rollup (Phase 82)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_trend_hint_ack_status import (
    build_trend_hint_ack_status_payload,
    compact_trend_hint_ack_status,
    refresh_trend_hint_ack_status,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh local candidate trend-hint acknowledgment status rollup (Phase 82)."
    )
    parser.add_argument("--refresh", action="store_true", help="Persist JSON/Markdown status report")
    parser.add_argument("--json-report", action="store_true", help="Print JSON compact summary")
    args = parser.parse_args()

    print(
        "WARNING: Trend-hint acknowledgment status rollup is local advisory only — "
        "does NOT clear alerts, verify MRMS, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        status = refresh_trend_hint_ack_status(storage)
    else:
        status = build_trend_hint_ack_status_payload(storage)["latest"]

    compact = compact_trend_hint_ack_status(storage)
    if args.json_report:
        print(json.dumps(compact, indent=2, sort_keys=True))
        return

    print(f"Rollup status: {compact.get('rollup_status')}")
    print(f"Acknowledgment status: {compact.get('acknowledgment_status')}")
    print(f"Stale acknowledgment: {compact.get('stale_acknowledgment')}")
    if args.refresh:
        print(f"JSON: {status.get('json_path')}")
        print(f"Markdown: {status.get('markdown_path')}")


if __name__ == "__main__":
    main()
