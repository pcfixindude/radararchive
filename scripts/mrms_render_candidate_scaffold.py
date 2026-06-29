"""Generate local MRMS render candidate command scaffold (disabled-by-default)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_scaffold import (
    SUGGESTED_SCAFFOLD_COMMAND,
    build_render_candidate_scaffold_payload,
    compact_render_candidate_scaffold,
    generate_render_candidate_scaffold,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate local MRMS render candidate scaffold (Phase 64 — disabled-by-default)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Persist JSON/Markdown scaffold report under data/dev/",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Request execute mode (still blocked/no-op in Phase 64; no download/decode/render)",
    )
    args = parser.parse_args()

    print(
        "WARNING: MRMS render candidate scaffold is disabled-by-default — NOT verified MRMS. "
        "Does not download, decode, render, serve production tiles, clear alerts, or authorize production use. "
        "Phase 64 performs no side effects even with --execute.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        scaffold = generate_render_candidate_scaffold(
            storage,
            execute_requested=args.execute,
        )
    else:
        scaffold = build_render_candidate_scaffold_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(scaffold, indent=2, sort_keys=True))
        return

    compact = compact_render_candidate_scaffold(storage)
    print("MRMS render candidate scaffold (disabled-by-default — NOT verified MRMS):")
    print(f"  scaffold_status: {scaffold.get('scaffold_status')}")
    print(f"  scaffold_reason: {scaffold.get('scaffold_reason')}")
    print(f"  dry_run_mode: {scaffold.get('dry_run_mode')}")
    print(f"  execute_performed: {scaffold.get('execute_performed')}")
    print(f"  execute_blocked_reason: {scaffold.get('execute_blocked_reason')}")
    print(f"  blocking_items: {len(scaffold.get('blocking_items') or [])}")
    print(f"  warnings: {len(scaffold.get('warnings') or [])}")
    print(f"  json_path: {scaffold.get('json_path') or compact.get('json_path')}")
    print(f"  markdown_path: {scaffold.get('markdown_path') or compact.get('markdown_path')}")
    print(f"  suggested_command: {compact.get('suggested_command') or SUGGESTED_SCAFFOLD_COMMAND}")
    print(f"  verified_mrms: {scaffold.get('verified_mrms')}")


if __name__ == "__main__":
    main()
