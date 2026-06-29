"""Refresh local sandbox comparison acknowledgment status trend review acknowledgment status trend hints (Phase 76)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_hint import (
    build_ack_status_trend_review_acknowledgment_status_trend_hint_payload,
    compact_ack_status_trend_review_acknowledgment_status_trend_hint,
    refresh_ack_status_trend_review_acknowledgment_status_trend_hint,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh local sandbox comparison acknowledgment status trend review acknowledgment "
            "status trend hints (Phase 76)."
        )
    )
    parser.add_argument("--refresh", action="store_true", help="Persist JSON/Markdown trend hint report")
    parser.add_argument("--json-report", action="store_true", help="Print JSON compact summary")
    args = parser.parse_args()

    print(
        "WARNING: Trend review acknowledgment status trend hints are local advisory only — "
        "does NOT clear alerts, verify MRMS, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        hint = refresh_ack_status_trend_review_acknowledgment_status_trend_hint(storage)
    else:
        hint = build_ack_status_trend_review_acknowledgment_status_trend_hint_payload(storage)["latest"]

    compact = compact_ack_status_trend_review_acknowledgment_status_trend_hint(storage)
    if args.json_report:
        print(json.dumps(compact, indent=2, sort_keys=True))
        return

    print(f"Hint status: {compact.get('hint_status')}")
    print(f"Trend: {compact.get('trend')}")
    print(f"Review recommended: {compact.get('trend_review_recommended')}")
    if args.refresh:
        print(f"JSON: {hint.get('json_path')}")
        print(f"Markdown: {hint.get('markdown_path')}")


if __name__ == "__main__":
    main()
