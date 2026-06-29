"""Resolve and report MRMS render candidate preflight blockers (Phase 89)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight_blockers import (
    SUGGESTED_COMMAND,
    build_preflight_blockers_payload,
    compact_preflight_blockers,
    resolve_preflight_blockers,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve and report MRMS render candidate preflight blockers (Phase 89)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Run blocker resolution flow and persist report",
    )
    args = parser.parse_args()

    print(
        "WARNING: Preflight blocker resolution is local advisory only — NOT verified MRMS. "
        "Does not force preflight when readiness gate is closed.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = resolve_preflight_blockers(storage)
    else:
        report = build_preflight_blockers_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_preflight_blockers(storage)
    print("Candidate preflight blockers (local advisory only):")
    print(f"  resolution_status: {compact.get('resolution_status')}")
    print(f"  preflight_not_run: {compact.get('preflight_not_run')}")
    print(f"  preflight_level: {compact.get('preflight_level')}")
    print(f"  visual_readiness_level: {compact.get('visual_readiness_level')}")
    print(f"  next_operator_step: {compact.get('next_operator_step')}")
    blockers = compact.get("remaining_blockers") or []
    if blockers:
        print("  remaining_blockers:")
        for item in blockers:
            print(f"    - {item}")
    commands = compact.get("next_commands") or []
    if commands:
        print("  next_commands:")
        for cmd in commands:
            print(f"    - {cmd}")
    if args.refresh:
        print(f"  markdown_path: {report.get('markdown_path')}")
    print(f"  suggested_command: {SUGGESTED_COMMAND}")


if __name__ == "__main__":
    main()
