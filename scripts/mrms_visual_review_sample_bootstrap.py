"""Bootstrap visual review sample set (Phase 91)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.mrms_visual_review_sample_bootstrap import (
    SUGGESTED_COMMAND,
    bootstrap_visual_sample_set,
    build_visual_sample_bootstrap_payload,
    compact_visual_sample_bootstrap,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap visual review sample set (Phase 91)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Create sample set, seed annotations, refresh readiness, resolve blockers",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Sample set entry limit when creating a new set",
    )
    args = parser.parse_args()

    print(
        "WARNING: Visual sample set bootstrap is local advisory only — NOT verified MRMS. "
        "Does not force preflight when visual readiness gate is closed.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        init_db()
        session_factory = get_session_factory()
        with session_factory() as session:
            report = bootstrap_visual_sample_set(
                storage,
                session,
                sample_limit=max(1, min(args.limit, 10)),
            )
    else:
        report = build_visual_sample_bootstrap_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_visual_sample_bootstrap(storage)
    print("Visual review sample set bootstrap (local advisory only):")
    print(f"  bootstrap_status: {compact.get('bootstrap_status')}")
    print(f"  visual_readiness_level: {compact.get('visual_readiness_level')}")
    print(f"  visual_readiness_reason: {compact.get('visual_readiness_reason')}")
    print(f"  review_readiness_level: {compact.get('review_readiness_level')}")
    print(f"  preflight_not_run: {compact.get('preflight_not_run')}")
    print(f"  next_operator_step: {compact.get('next_operator_step')}")
    visual_blockers = compact.get("visual_blockers") or []
    if visual_blockers:
        print("  visual_blockers:")
        for item in visual_blockers:
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
