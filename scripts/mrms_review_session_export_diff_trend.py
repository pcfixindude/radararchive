"""Print review session export diff trend summary (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_review_session_export_diff import MAX_EXPORT_DIFF_HISTORY
from backend.app.services.mrms_review_session_export_diff_trends import (
    DEFAULT_TREND_WINDOW,
    build_review_session_export_diff_trend_payload,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show review session export diff trend (Phase 46 — local review only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument(
        "--limit",
        "--window",
        dest="window",
        type=int,
        default=DEFAULT_TREND_WINDOW,
        help=f"Trend window size (default {DEFAULT_TREND_WINDOW}, max {MAX_EXPORT_DIFF_HISTORY})",
    )
    args = parser.parse_args()

    print(
        "WARNING: Export diff trend is local review evidence only — NOT verified MRMS. "
        "Does not clear alerts or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    payload = build_review_session_export_diff_trend_payload(
        storage,
        window=max(1, min(args.window, MAX_EXPORT_DIFF_HISTORY)),
    )
    trend = payload.get("trend") or {}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("Review session export diff trend (local review only — NOT verified MRMS):")
    print(f"  trend: {trend.get('trend')}")
    print(f"  latest_status: {trend.get('latest_status')}")
    print(f"  latest_at: {trend.get('latest_at')}")
    print(f"  total_diffs: {trend.get('total_diffs', 0)}")
    print(
        f"  counts — improved {trend.get('improved_count', 0)}, "
        f"worsened {trend.get('worsened_count', 0)}, "
        f"mixed {trend.get('mixed_count', 0)}, "
        f"unchanged {trend.get('unchanged_count', 0)}"
    )
    print(f"  current_worsened_streak: {trend.get('current_worsened_streak', 0)}")
    print(
        f"  current_mixed_or_worsened_streak: "
        f"{trend.get('current_mixed_or_worsened_streak', 0)}"
    )
    print(f"  last_worsened_at: {trend.get('last_worsened_at')}")
    print(f"  last_improved_at: {trend.get('last_improved_at')}")
    print(f"  suggested_next_action: {trend.get('suggested_next_action')}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")


if __name__ == "__main__":
    main()
