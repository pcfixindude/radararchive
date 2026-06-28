"""Print review session export diff trend regeneration hint (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_review_session_export_diff_trend_hint import (
    build_review_session_export_diff_trend_hint_payload,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show review export diff trend regeneration hint (Phase 47 — local review only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    args = parser.parse_args()

    print(
        "WARNING: Export diff trend hint is local review evidence only — NOT verified MRMS. "
        "Does not clear alerts or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    payload = build_review_session_export_diff_trend_hint_payload(storage)
    hint = payload.get("hint") or {}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("Review session export diff trend hint (local review only — NOT verified MRMS):")
    print(
        f"  review_trend_regeneration_recommended: "
        f"{hint.get('review_trend_regeneration_recommended')}"
    )
    print(f"  reason: {hint.get('reason')}")
    print(f"  suggested_command: {hint.get('suggested_command')}")
    print(f"  trend: {hint.get('trend')}")
    print(f"  latest_export_diff_status: {hint.get('latest_export_diff_status')}")
    print(f"  current_mixed_or_worsened_streak: {hint.get('current_mixed_or_worsened_streak', 0)}")
    print(f"  current_worsened_streak: {hint.get('current_worsened_streak', 0)}")
    print(f"  export_is_stale: {hint.get('export_is_stale')}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")


if __name__ == "__main__":
    main()
