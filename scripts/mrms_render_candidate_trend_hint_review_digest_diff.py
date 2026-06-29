"""Show local candidate trend-hint review digest diff (Phase 86)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_trend_hint_review_digest_diff import (
    MAX_DIFF_HISTORY,
    build_trend_hint_review_digest_diff_payload,
    refresh_trend_hint_review_digest_diff,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show local candidate trend-hint review digest diff (Phase 86)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print JSON payload")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Recompute diff from latest digest history entries",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=MAX_DIFF_HISTORY,
        help=f"Max diff history entries (default {MAX_DIFF_HISTORY})",
    )
    args = parser.parse_args()

    print(
        "WARNING: Trend-hint review digest diff is local advisory only — "
        "does NOT clear alerts, verify MRMS, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        refresh_trend_hint_review_digest_diff(storage)
    payload = build_trend_hint_review_digest_diff_payload(storage)
    if args.limit < MAX_DIFF_HISTORY:
        payload["entries"] = (payload.get("entries") or [])[: max(1, min(args.limit, MAX_DIFF_HISTORY))]
        payload["count"] = len(payload["entries"])

    if args.json_report:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    compact = payload.get("compact") or {}
    print("Candidate trend-hint review digest diff (local review only — NOT verified MRMS):")
    print(f"  diff_status: {compact.get('diff_status')}")
    print(f"  checked_at: {compact.get('checked_at')}")
    print(f"  history_count: {compact.get('history_count', 0)}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")
    if compact.get("suggested_command"):
        print(f"  suggested_command: {compact.get('suggested_command')}")


if __name__ == "__main__":
    main()
