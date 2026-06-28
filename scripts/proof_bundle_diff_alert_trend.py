"""Print proof bundle diff alert trend summary (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.proof_bundle_diff_alert_trends import (
    DEFAULT_TREND_WINDOW,
    build_proof_bundle_diff_alert_trend_payload,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show proof bundle diff alert trend summary (Phase 35 — local monitoring only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument(
        "--window",
        type=int,
        default=DEFAULT_TREND_WINDOW,
        help=f"Recent history window (default {DEFAULT_TREND_WINDOW}, max 25)",
    )
    args = parser.parse_args()

    print(
        "WARNING: Diff alert trend is local evidence monitoring only — "
        "NOT verified MRMS. Does not enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(args.window, 25))
    payload = build_proof_bundle_diff_alert_trend_payload(storage, window=bounded)
    trend = payload.get("trend") or {}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("Proof bundle diff alert trend (local monitoring only — NOT verified MRMS):")
    print(f"  trend: {trend.get('trend')}")
    print(f"  latest_status: {trend.get('latest_status')}")
    print(f"  latest_at: {trend.get('latest_at')}")
    print(f"  current_attention_streak: {trend.get('current_attention_streak', 0)}")
    print(f"  recent_worsened_count: {trend.get('recent_worsened_count', 0)}")
    print(f"  recent_mixed_count: {trend.get('recent_mixed_count', 0)}")
    print(f"  recent_improved_count: {trend.get('recent_improved_count', 0)}")
    print(f"  recent_unchanged_count: {trend.get('recent_unchanged_count', 0)}")
    print(f"  last_worsened_at: {trend.get('last_worsened_at')}")
    print(f"  last_mixed_at: {trend.get('last_mixed_at')}")
    print(f"  last_improved_at: {trend.get('last_improved_at')}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")
    if trend.get("suggested_next_action"):
        print(f"  suggested_next_action: {trend.get('suggested_next_action')}")


if __name__ == "__main__":
    main()
