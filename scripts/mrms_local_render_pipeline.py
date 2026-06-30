"""Fast-track local MRMS render pipeline (Phase 103)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.mrms_local_render_pipeline import (
    SUGGESTED_COMMAND,
    compact_local_render_pipeline,
    load_local_render_pipeline_report,
    run_local_render_pipeline,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run fast-track local MRMS render pipeline (candidate → decode → preview)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument("--z", type=int, default=0, help="Preview tile z")
    parser.add_argument("--x", type=int, default=0, help="Preview tile x")
    parser.add_argument("--y", type=int, default=0, help="Preview tile y")
    args = parser.parse_args()

    print(
        "WARNING: Local render pipeline is prototype only — NOT verified MRMS. "
        "Does not enable production tile serving.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    init_db()
    session = get_session_factory()()
    try:
        report = run_local_render_pipeline(session, storage, z=args.z, x=args.x, y=args.y)
        session.commit()
    finally:
        session.close()

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_local_render_pipeline(storage)
    print("Local MRMS render pipeline (prototype only — NOT verified MRMS):")
    print(f"  pipeline_status: {compact.get('pipeline_status')}")
    print(f"  render_attempt_status: {compact.get('render_attempt_status')}")
    print(f"  produced_local_artifact: {compact.get('produced_local_artifact')}")
    print(f"  render_mode: {compact.get('render_mode')}")
    print(f"  blocker: {compact.get('blocker')}")
    print(f"  candidate_raw_path: {compact.get('candidate_raw_path')}")
    for path in compact.get("preview_paths") or []:
        print(f"  preview_path: {path}")
    for item in report.get("errors") or []:
        print(f"  error: {item}")
    for item in report.get("warnings") or []:
        print(f"  warning: {item}")
    commands = compact.get("next_retry_commands") or []
    if commands:
        print("  next_retry_commands:")
        for cmd in commands:
            print(f"    - {cmd}")
    print(f"  next_phase_recommendation: {compact.get('next_phase_recommendation')}")
    print(f"  markdown_path: {report.get('markdown_path')}")
    print(f"  suggested_command: {SUGGESTED_COMMAND}")


if __name__ == "__main__":
    main()
