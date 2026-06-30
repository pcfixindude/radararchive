"""Resolve operator review attention items for render-candidate preflight (Phase 101)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight_attention import (
    SUGGESTED_COMMAND,
    build_preflight_attention_payload,
    compact_preflight_attention,
    resolve_preflight_operator_attention,
    save_preflight_attention_report,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve operator review attention items for render-candidate preflight."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Attempt safe local advisory clears and persist attention report",
    )
    parser.add_argument(
        "--operator",
        default="PREFLIGHT",
        help="Operator initials for local advisory acknowledgments",
    )
    args = parser.parse_args()

    print(
        "WARNING: Preflight attention resolution is local advisory only — NOT verified MRMS. "
        "Does not clear alerts or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = save_preflight_attention_report(
            storage,
            resolve_preflight_operator_attention(
                storage,
                refresh=True,
                operator_initials=args.operator,
            ),
        )
    else:
        report = build_preflight_attention_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_preflight_attention(storage)
    print("Preflight operator attention resolution (local advisory only):")
    print(f"  resolution_status: {compact.get('resolution_status')}")
    print(f"  blocks_preflight: {compact.get('blocks_preflight')}")
    print(f"  open_attention_count: {compact.get('open_attention_count')}")
    print(f"  open_blocking_count: {compact.get('open_blocking_count')}")
    print(f"  next_operator_step: {compact.get('next_operator_step')}")
    print(f"  next_phase_recommendation: {compact.get('next_phase_recommendation')}")
    for label, items in (
        ("open_blocking_items", compact.get("open_blocking_items") or []),
        ("remaining_open_attention_items", compact.get("remaining_open_attention_items") or []),
    ):
        if items:
            print(f"  {label}:")
            for item in items:
                if isinstance(item, dict):
                    print(f"    - {item.get('text')}")
                else:
                    print(f"    - {item}")
    commands = compact.get("retry_commands") or []
    if commands:
        print("  retry_commands:")
        for cmd in commands:
            print(f"    - {cmd}")
    if args.refresh and isinstance(report, dict):
        print(f"  markdown_path: {report.get('markdown_path')}")
    print(f"  suggested_command: {SUGGESTED_COMMAND}")


if __name__ == "__main__":
    main()
