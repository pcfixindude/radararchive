"""Gated sandbox comparison acknowledgment review (Phase 98)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_gated_comparison_ack import (
    SUGGESTED_COMMAND,
    build_gated_comparison_ack_payload,
    compact_gated_comparison_ack,
    review_gated_comparison_ack,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review gated comparison acknowledgment after upstream gates (Phase 98)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Run upstream gates and refresh acknowledgment status when trend_hint_ready",
    )
    args = parser.parse_args()

    print(
        "WARNING: Gated comparison acknowledgment review is local advisory only — NOT verified MRMS. "
        "Does not run acknowledgment when upstream gates are closed.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = review_gated_comparison_ack(storage)
    else:
        report = build_gated_comparison_ack_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_gated_comparison_ack(storage)
    print("Gated sandbox comparison acknowledgment review (local advisory only):")
    print(f"  review_status: {compact.get('review_status')}")
    print(f"  preflight_level: {compact.get('preflight_level')}")
    print(f"  trend_skipped: {compact.get('trend_skipped')}")
    print(f"  ack_skipped: {compact.get('ack_skipped')}")
    print(f"  hint_status: {compact.get('hint_status')}")
    print(f"  rollup_status: {compact.get('rollup_status')}")
    print(f"  acknowledgment_status: {compact.get('acknowledgment_status')}")
    print(f"  next_operator_step: {compact.get('next_operator_step')}")
    for label, items in (
        ("preflight_blockers", compact.get("preflight_blockers") or []),
        ("trend_blockers", compact.get("trend_blockers") or []),
        ("ack_blockers", compact.get("ack_blockers") or []),
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
