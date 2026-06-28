"""Print review session export diff metadata (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_review_session_export_diff import (
    MAX_EXPORT_DIFF_HISTORY,
    build_review_session_export_diff_payload,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show review session export diff metadata (Phase 45 — local review only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument(
        "--history",
        action="store_true",
        help="Print bounded export diff history instead of latest compact summary",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=MAX_EXPORT_DIFF_HISTORY,
        help=f"Max diff history entries (default {MAX_EXPORT_DIFF_HISTORY})",
    )
    args = parser.parse_args()

    print(
        "WARNING: Review export diff metadata is local review evidence only — NOT verified MRMS. "
        "Does not clear alerts or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    payload = build_review_session_export_diff_payload(storage)
    if args.limit < MAX_EXPORT_DIFF_HISTORY:
        payload["entries"] = (payload.get("entries") or [])[: max(1, min(args.limit, 25))]
        payload["count"] = len(payload["entries"])

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    compact = payload.get("compact") or {}
    if args.history:
        print("Review session export diff history (local review only — NOT verified MRMS):")
        print(f"  history_count: {payload.get('count', 0)}")
        print(f"  verified_mrms: {payload.get('verified_mrms')}")
        for index, entry in enumerate(payload.get("entries") or [], start=1):
            print(
                f"  [{index}] {entry.get('compared_at')} — "
                f"status={entry.get('overall_export_diff_status')} — "
                f"session_changed={entry.get('session_changed')}"
            )
        return

    print("Review session export diff (local review only — NOT verified MRMS):")
    print(f"  overall_export_diff_status: {compact.get('overall_export_diff_status')}")
    print(f"  compared_at: {compact.get('compared_at')}")
    print(f"  latest_export_created_at: {compact.get('latest_export_created_at')}")
    print(f"  baseline_export_created_at: {compact.get('baseline_export_created_at')}")
    print(f"  session_changed: {compact.get('session_changed')}")
    print(f"  open_attention_count_change: {compact.get('open_attention_count_change')}")
    print(f"  improvements: {compact.get('improvements') or []}")
    print(f"  regressions: {compact.get('regressions') or []}")
    print(f"  history_count: {compact.get('history_count', 0)}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")


if __name__ == "__main__":
    main()
