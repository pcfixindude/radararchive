"""Generate local MRMS visual review artifacts (read-only inspection)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.mrms_visual_review import (
    SUGGESTED_VISUAL_REVIEW_COMMAND,
    build_mrms_visual_review_history_payload,
    generate_mrms_visual_review,
    load_visual_review_history,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate local MRMS visual review manifest (Phase 56 — local review only)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--history",
        action="store_true",
        help="List bounded visual review history instead of generating a new report",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="History entry limit when using --history (max 25)",
    )
    args = parser.parse_args()

    print(
        "WARNING: MRMS visual review is local evidence inspection only — NOT verified MRMS. "
        "Does not download, decode, clear alerts, notify externally, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)

    if args.history:
        payload = build_mrms_visual_review_history_payload(storage, limit=args.limit)
        if args.json_report:
            print(json.dumps(payload, indent=2, sort_keys=True))
            return
        entries = payload.get("entries") or []
        print("MRMS visual review history (local visual review only — NOT verified MRMS):")
        print(f"  count: {payload.get('count')}")
        print(f"  max_entries: {payload.get('max_entries')}")
        for index, entry in enumerate(entries, start=1):
            print(
                f"  [{index}] {entry.get('created_at')} — "
                f"frames={entry.get('frame_count')} artifacts={entry.get('artifact_count')} "
                f"missing={entry.get('missing_artifact_count')}"
            )
        print(f"  verified_mrms: {payload.get('verified_mrms')}")
        return

    init_db()
    session_factory = get_session_factory()
    with session_factory() as session:
        report = generate_mrms_visual_review(session, storage)

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print("MRMS visual review (local visual review only — NOT verified MRMS):")
    print(f"  created_at: {report.get('created_at')}")
    print(f"  layers_inspected: {', '.join(report.get('layers_inspected') or []) or '—'}")
    print(f"  frame_count: {report.get('frame_count')}")
    print(f"  artifact_count: {report.get('artifact_count')}")
    print(f"  missing_artifact_count: {report.get('missing_artifact_count')}")
    print(f"  tile_modes_found: {', '.join(report.get('tile_modes_found') or []) or '—'}")
    print(f"  json_path: {report.get('json_path')}")
    print(f"  markdown_path: {report.get('markdown_path')}")
    print(f"  suggested_next_command: {report.get('suggested_next_command') or SUGGESTED_VISUAL_REVIEW_COMMAND}")
    print(f"  verified_mrms: {report.get('verified_mrms')}")
    history_count = len(load_visual_review_history(storage))
    print(f"  history_count: {history_count}")


if __name__ == "__main__":
    main()
