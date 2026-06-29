"""Gated candidate artifact sandbox layout review (Phase 94)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_gated_sandbox_layout import (
    SUGGESTED_COMMAND,
    build_gated_sandbox_layout_payload,
    compact_gated_sandbox_layout,
    review_gated_sandbox_layout,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review gated sandbox layout after preflight, dry-run, and scaffold gates (Phase 94)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Run upstream gates and generate sandbox layout when scaffold_ready",
    )
    args = parser.parse_args()

    print(
        "WARNING: Gated sandbox layout review is local advisory only — NOT verified MRMS. "
        "Does not enable production rendering or generate layout when upstream gates are closed.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = review_gated_sandbox_layout(storage)
    else:
        report = build_gated_sandbox_layout_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_gated_sandbox_layout(storage)
    print("Gated candidate artifact sandbox layout review (local advisory only):")
    print(f"  review_status: {compact.get('review_status')}")
    print(f"  preflight_level: {compact.get('preflight_level')}")
    print(f"  dry_run_plan_skipped: {compact.get('dry_run_plan_skipped')}")
    print(f"  dry_run_plan_status: {compact.get('dry_run_plan_status')}")
    print(f"  scaffold_skipped: {compact.get('scaffold_skipped')}")
    print(f"  scaffold_status: {compact.get('scaffold_status')}")
    print(f"  sandbox_skipped: {compact.get('sandbox_skipped')}")
    print(f"  sandbox_status: {compact.get('sandbox_status')}")
    print(f"  sandbox_root: {compact.get('sandbox_root')}")
    print(f"  delete_performed: {compact.get('delete_performed')}")
    print(f"  next_operator_step: {compact.get('next_operator_step')}")
    for label, items in (
        ("preflight_blockers", compact.get("preflight_blockers") or []),
        ("dry_run_plan_blockers", compact.get("dry_run_plan_blockers") or []),
        ("scaffold_blockers", compact.get("scaffold_blockers") or []),
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
