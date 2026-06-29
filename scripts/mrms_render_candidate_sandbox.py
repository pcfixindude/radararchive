"""Create/validate local MRMS render candidate artifact sandbox layout."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox import (
    DELETE_CONFIRM_FLAG,
    SUGGESTED_SANDBOX_COMMAND,
    build_render_candidate_sandbox_payload,
    compact_render_candidate_sandbox,
    generate_render_candidate_sandbox,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create/validate local MRMS render candidate sandbox (Phase 65 — local only)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON manifest")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Create/validate sandbox layout and persist JSON/Markdown report under data/dev/",
    )
    parser.add_argument(
        "--no-create-layout",
        action="store_true",
        help="Skip creating missing sandbox directories (report only)",
    )
    parser.add_argument(
        "--confirm-delete-dev-sandbox",
        dest="confirm_delete",
        action="store_true",
        help="Request sandbox cleanup deletion (still report-only in Phase 65)",
    )
    args = parser.parse_args()

    print(
        "WARNING: MRMS render candidate sandbox is local-only — NOT verified MRMS. "
        "Does not download, decode, render, serve production tiles, clear alerts, or authorize production use. "
        "Cleanup is report-only by default; Phase 65 does not delete files.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        manifest = generate_render_candidate_sandbox(
            storage,
            create_layout=not args.no_create_layout,
            confirm_delete_requested=args.confirm_delete,
        )
    else:
        manifest = build_render_candidate_sandbox_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return

    compact = compact_render_candidate_sandbox(storage)
    print("MRMS render candidate sandbox (local-only — NOT verified MRMS):")
    print(f"  sandbox_status: {manifest.get('sandbox_status')}")
    print(f"  sandbox_reason: {manifest.get('sandbox_reason')}")
    print(f"  sandbox_root: {manifest.get('sandbox_root') or compact.get('sandbox_root')}")
    print(f"  cleanup_mode: {manifest.get('cleanup_mode') or compact.get('cleanup_mode')}")
    print(f"  delete_performed: {manifest.get('delete_performed')}")
    print(f"  blocking_items: {len(manifest.get('blocking_items') or [])}")
    print(f"  warnings: {len(manifest.get('warnings') or [])}")
    print(f"  missing_subdirectories: {manifest.get('missing_subdirectories') or compact.get('missing_subdirectories')}")
    print(f"  json_path: {manifest.get('json_path') or compact.get('json_path')}")
    print(f"  markdown_path: {manifest.get('markdown_path') or compact.get('markdown_path')}")
    print(f"  suggested_command: {compact.get('suggested_command') or SUGGESTED_SANDBOX_COMMAND}")
    print(f"  verified_mrms: {manifest.get('verified_mrms')}")


if __name__ == "__main__":
    main()
