"""Gated sandbox acknowledgment history review (Phase 99)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_gated_ack_history import (
    SUGGESTED_COMMAND,
    build_gated_ack_history_payload,
    compact_gated_ack_history,
    review_gated_ack_history,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review gated acknowledgment history after upstream gates (Phase 99)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Run upstream gates and refresh acknowledgment history when comparison_ack_ready",
    )
    args = parser.parse_args()

    print(
        "WARNING: Gated acknowledgment history review is local advisory only — NOT verified MRMS. "
        "Does not run acknowledgment history when upstream gates are closed.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = review_gated_ack_history(storage)
    else:
        report = build_gated_ack_history_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_gated_ack_history(storage)
    print("Gated sandbox acknowledgment history review (local advisory only):")
    print(f"  review_status: {compact.get('review_status')}")
    print(f"  preflight_level: {compact.get('preflight_level')}")
    print(f"  ack_skipped: {compact.get('ack_skipped')}")
    print(f"  history_skipped: {compact.get('history_skipped')}")
    print(f"  rollup_status: {compact.get('rollup_status')}")
    print(f"  ack_history_count: {compact.get('ack_history_count')}")
    print(f"  next_operator_step: {compact.get('next_operator_step')}")
    for label, items in (
        ("preflight_blockers", compact.get("preflight_blockers") or []),
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
