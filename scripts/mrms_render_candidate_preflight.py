"""Generate local MRMS render candidate preflight report (advisory only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight import (
    SUGGESTED_PREFLIGHT_COMMAND,
    build_render_candidate_preflight_payload,
    compact_render_candidate_preflight,
    generate_render_candidate_preflight,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate local MRMS render candidate preflight (Phase 62 — advisory only)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Persist JSON/Markdown preflight report under data/dev/",
    )
    args = parser.parse_args()

    print(
        "WARNING: MRMS render candidate preflight is local advisory guidance only — NOT verified MRMS. "
        "candidate_preflight_ready is NOT production authorization. "
        "Does not download, decode, render production tiles, clear alerts, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = generate_render_candidate_preflight(storage)
    else:
        report = build_render_candidate_preflight_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_render_candidate_preflight(storage)
    print("MRMS render candidate preflight (local advisory only — NOT verified MRMS):")
    print(f"  preflight_level: {report.get('preflight_level')}")
    print(f"  preflight_reason: {report.get('preflight_reason')}")
    print(f"  blocking_items: {len(report.get('blocking_items') or [])}")
    print(f"  warnings: {len(report.get('warnings') or [])}")
    print(f"  json_path: {report.get('json_path') or compact.get('json_path')}")
    print(f"  markdown_path: {report.get('markdown_path') or compact.get('markdown_path')}")
    print(f"  suggested_command: {compact.get('suggested_command') or SUGGESTED_PREFLIGHT_COMMAND}")
    print(f"  verified_mrms: {report.get('verified_mrms')}")
    for item in report.get("blocking_items") or []:
        print(f"  BLOCK: {item}")
    for item in report.get("warnings") or []:
        print(f"  WARN: {item}")


if __name__ == "__main__":
    main()
