"""Compare latest MRMS visual review against previous manifest (read-only except comparison persist)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_visual_review_compare import (
    build_visual_review_comparison_history_payload,
    build_visual_review_comparison_payload,
    record_visual_review_comparison,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare MRMS visual review manifests (Phase 57 — local review only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument(
        "--history",
        action="store_true",
        help="List bounded visual review comparison history instead of recording a new comparison",
    )
    parser.add_argument("--limit", type=int, default=25, help="History limit when using --history")
    args = parser.parse_args()

    print(
        "WARNING: Visual review comparison is local evidence only — NOT verified MRMS. "
        "Does not download, decode, clear alerts, notify externally, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)

    if args.history:
        payload = build_visual_review_comparison_history_payload(storage, limit=args.limit)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
            return
        entries = payload.get("entries") or []
        print("MRMS visual review comparison history (local review only — NOT verified MRMS):")
        print(f"  count: {payload.get('count')}")
        print(f"  max_entries: {payload.get('max_entries')}")
        for index, entry in enumerate(entries, start=1):
            print(
                f"  [{index}] {entry.get('compared_at')} — "
                f"status={entry.get('overall_visual_review_diff_status')}"
            )
        print(f"  verified_mrms: {payload.get('verified_mrms')}")
        return

    comparison = record_visual_review_comparison(storage)
    if args.json:
        payload = build_visual_review_comparison_payload(storage)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("MRMS visual review comparison (local review only — NOT verified MRMS):")
    print(f"  compared_at: {comparison.get('compared_at')}")
    print(f"  overall_visual_review_diff_status: {comparison.get('overall_visual_review_diff_status')}")
    print(f"  latest_created_at: {comparison.get('latest_created_at')}")
    print(f"  baseline_created_at: {comparison.get('baseline_created_at')}")
    print(f"  artifact_count_change: {comparison.get('artifact_count_change')}")
    print(f"  missing_artifact_count_change: {comparison.get('missing_artifact_count_change')}")
    print(f"  tile_modes_added: {comparison.get('tile_modes_added')}")
    print(f"  tile_modes_removed: {comparison.get('tile_modes_removed')}")
    print(f"  verified_mrms: {comparison.get('verified_mrms')}")


if __name__ == "__main__":
    main()
