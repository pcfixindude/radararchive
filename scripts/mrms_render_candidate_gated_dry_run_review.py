"""Gated render candidate dry-run plan review (Phase 92)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_gated_dry_run_review import (
    SUGGESTED_COMMAND,
    build_gated_dry_run_review_payload,
    compact_gated_dry_run_review,
    review_gated_dry_run_plan,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review gated preflight and dry-run plan (Phase 92)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh preflight, resolve blockers, and review/generate dry-run plan when gated",
    )
    args = parser.parse_args()

    print(
        "WARNING: Gated dry-run plan review is local advisory only — NOT verified MRMS. "
        "Does not execute candidate steps or advance dry-run planning when preflight gate is closed.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = review_gated_dry_run_plan(storage)
    else:
        report = build_gated_dry_run_review_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_gated_dry_run_review(storage)
    print("Gated render candidate dry-run plan review (local advisory only):")
    print(f"  review_status: {compact.get('review_status')}")
    print(f"  preflight_level: {compact.get('preflight_level')}")
    print(f"  dry_run_plan_skipped: {compact.get('dry_run_plan_skipped')}")
    print(f"  dry_run_plan_status: {compact.get('dry_run_plan_status')}")
    print(f"  next_operator_step: {compact.get('next_operator_step')}")
    blockers = compact.get("remaining_blockers") or []
    if blockers:
        print("  remaining_blockers:")
        for item in blockers:
            print(f"    - {item}")
    preflight_blockers = compact.get("preflight_blocking_items") or []
    if preflight_blockers:
        print("  preflight_blocking_items:")
        for item in preflight_blockers:
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
