"""Refresh local candidate trend-hint review chain digest (Phase 84)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_trend_hint_review_digest import (
    build_trend_hint_review_digest_payload,
    compact_trend_hint_review_digest,
    refresh_trend_hint_review_digest,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh local candidate trend-hint review chain digest (Phase 84)."
    )
    parser.add_argument("--refresh", action="store_true", help="Persist JSON/Markdown digest report")
    parser.add_argument("--json-report", action="store_true", help="Print JSON compact summary")
    args = parser.parse_args()

    print(
        "WARNING: Trend-hint review chain digest is local advisory only — "
        "does NOT clear alerts, verify MRMS, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        digest = refresh_trend_hint_review_digest(storage)
    else:
        digest = build_trend_hint_review_digest_payload(storage)["latest"]

    compact = compact_trend_hint_review_digest(storage)
    if args.json_report:
        print(json.dumps(compact, indent=2, sort_keys=True))
        return

    print(f"Digest status: {compact.get('digest_status')}")
    print(f"Rollup status: {compact.get('rollup_status')}")
    print(f"History count: {compact.get('history_count')}")
    print(f"Latest coverage change: {compact.get('latest_coverage_change')}")
    if args.refresh:
        print(f"JSON: {digest.get('json_path')}")
        print(f"Markdown: {digest.get('markdown_path')}")


if __name__ == "__main__":
    main()
