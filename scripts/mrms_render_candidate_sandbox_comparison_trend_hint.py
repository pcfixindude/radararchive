"""Refresh local MRMS render candidate sandbox comparison trend hint."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox_comparison_trend_hint import (
    SUGGESTED_COMMAND,
    build_sandbox_comparison_trend_hint_payload,
    compact_sandbox_comparison_trend_hint,
    refresh_sandbox_comparison_trend_hint,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Local MRMS render candidate sandbox comparison trend hint (Phase 68)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Persist JSON/Markdown trend hint under data/dev/",
    )
    args = parser.parse_args()

    print(
        "WARNING: Sandbox comparison trend hints are local advisory only — NOT verified MRMS. "
        "Does not download, decode, render, serve production tiles, clear alerts, or authorize production use.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        hint = refresh_sandbox_comparison_trend_hint(storage)
    else:
        hint = build_sandbox_comparison_trend_hint_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(hint, indent=2, sort_keys=True))
        return

    compact = compact_sandbox_comparison_trend_hint(storage)
    print("MRMS render candidate sandbox comparison trend hint (local advisory only — NOT verified MRMS):")
    print(f"  hint_status: {hint.get('hint_status')}")
    print(f"  trend: {hint.get('trend')}")
    print(f"  trend_review_recommended: {hint.get('trend_review_recommended')}")
    print(f"  current_changed_streak: {hint.get('current_changed_streak')}")
    print(f"  recurring_signals: {hint.get('recurring_signals')}")
    print(f"  json_path: {hint.get('json_path') or compact.get('json_path')}")
    print(f"  suggested_command: {compact.get('suggested_command') or SUGGESTED_COMMAND}")
    print(f"  verified_mrms: {hint.get('verified_mrms')}")


if __name__ == "__main__":
    main()
