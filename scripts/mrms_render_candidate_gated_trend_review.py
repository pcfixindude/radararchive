"""Gated sandbox comparison trend hint review (Phase 97)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_gated_trend_review import (
    SUGGESTED_COMMAND,
    build_gated_trend_review_payload,
    compact_gated_trend_review,
    review_gated_trend_review,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review gated comparison trend hints after upstream gates (Phase 97)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Run upstream gates and refresh trend hints when comparison_history_ready",
    )
    args = parser.parse_args()

    print(
        "WARNING: Gated trend hint review is local advisory only — NOT verified MRMS. "
        "Does not run trend hints when upstream gates are closed.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = review_gated_trend_review(storage)
    else:
        report = build_gated_trend_review_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_gated_trend_review(storage)
    print("Gated sandbox comparison trend hint review (local advisory only):")
    print(f"  review_status: {compact.get('review_status')}")
    print(f"  preflight_level: {compact.get('preflight_level')}")
    print(f"  manifest_io_skipped: {compact.get('manifest_io_skipped')}")
    print(f"  comparison_skipped: {compact.get('comparison_skipped')}")
    print(f"  trend_skipped: {compact.get('trend_skipped')}")
    print(f"  history_status: {compact.get('history_status')}")
    print(f"  hint_status: {compact.get('hint_status')}")
    print(f"  trend: {compact.get('trend')}")
    print(f"  next_operator_step: {compact.get('next_operator_step')}")
    for label, items in (
        ("preflight_blockers", compact.get("preflight_blockers") or []),
        ("manifest_io_blockers", compact.get("manifest_io_blockers") or []),
        ("comparison_history_blockers", compact.get("comparison_history_blockers") or []),
        ("trend_blockers", compact.get("trend_blockers") or []),
        ("preflight_warnings", compact.get("preflight_warnings") or []),
    ):
        if items:
            print(f"  {label}:")
            for item in items:
                print(f"    - {item}")
    commands = compact.get("next_commands") or []
    if commands:
        print("  next_commands:")
        for cmd in commands:
            print(f"    - {cmd}")
    if args.refresh and isinstance(report, dict):
        print(f"  markdown_path: {report.get('markdown_path')}")
    print(f"  suggested_command: {SUGGESTED_COMMAND}")


if __name__ == "__main__":
    main()
