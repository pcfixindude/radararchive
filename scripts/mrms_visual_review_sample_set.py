"""Build or refresh local MRMS visual review sample set (drilldown only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_visual_review_sample_set import (
    DEFAULT_SAMPLE_LIMIT,
    SELECTION_EXPLICIT,
    SELECTION_RECOMMENDED,
    SUGGESTED_SAMPLE_SET_COMMAND,
    build_visual_review_sample_set,
    compact_visual_review_sample_set,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build local MRMS visual review sample set (Phase 60 — drilldown only)."
    )
    parser.add_argument(
        "--recommended",
        action="store_true",
        default=True,
        help="Select a recommended small sample from the latest visual review manifest (default)",
    )
    parser.add_argument(
        "--explicit",
        action="store_true",
        help="Select explicit timestamps from the latest visual review manifest",
    )
    parser.add_argument(
        "--timestamps",
        type=str,
        default="",
        help="Comma-separated timestamps for --explicit selection",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_SAMPLE_LIMIT,
        help=f"Recommended sample size (max 10, default {DEFAULT_SAMPLE_LIMIT})",
    )
    parser.add_argument("--notes", type=str, default="", help="Optional operator notes")
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    args = parser.parse_args()

    print(
        "WARNING: MRMS visual review sample set is local drilldown evidence only — NOT verified MRMS. "
        "Does not download, decode, clear alerts, notify externally, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    selection_mode = SELECTION_EXPLICIT if args.explicit else SELECTION_RECOMMENDED
    timestamps = [item.strip() for item in args.timestamps.split(",") if item.strip()]
    sample_set = build_visual_review_sample_set(
        storage,
        selection_mode=selection_mode,
        limit=args.limit,
        timestamps=timestamps or None,
        notes=args.notes or None,
    )

    if args.json_report:
        print(json.dumps(sample_set, indent=2, sort_keys=True))
        return

    compact = compact_visual_review_sample_set(storage)
    print("MRMS visual review sample set (local drilldown only — NOT verified MRMS):")
    print(f"  created_at: {sample_set.get('created_at')}")
    print(f"  selection_mode: {sample_set.get('selection_mode')}")
    print(f"  entry_count: {sample_set.get('entry_count')}")
    print(f"  reason: {sample_set.get('reason')}")
    print(f"  source_visual_review_at: {sample_set.get('source_visual_review_at') or '—'}")
    print(f"  json_path: {sample_set.get('json_path')}")
    print(f"  markdown_path: {sample_set.get('markdown_path')}")
    print(f"  suggested_command: {compact.get('suggested_command') or SUGGESTED_SAMPLE_SET_COMMAND}")
    print(f"  verified_mrms: {sample_set.get('verified_mrms')}")
    entries = sample_set.get("entries") or []
    if entries:
        print("  entries:")
        for index, entry in enumerate(entries, start=1):
            print(
                f"    [{index}] {entry.get('timestamp')} — {entry.get('tile_mode')} — "
                f"{entry.get('primary_artifact_path') or '—'} "
                f"({entry.get('selection_reason')})"
            )
    else:
        print("  entries: none — generate a visual review manifest first with make mrms-visual-review")


if __name__ == "__main__":
    main()
