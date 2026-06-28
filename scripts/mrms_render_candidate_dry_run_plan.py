"""Generate local MRMS render candidate dry-run plan (advisory only; does not execute steps)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_dry_run_plan import (
    SUGGESTED_DRY_RUN_PLAN_COMMAND,
    build_render_candidate_dry_run_plan_payload,
    compact_render_candidate_dry_run_plan,
    generate_render_candidate_dry_run_plan,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate local MRMS render candidate dry-run plan (Phase 63 — advisory only)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Persist JSON/Markdown dry-run plan under data/dev/",
    )
    args = parser.parse_args()

    print(
        "WARNING: MRMS render candidate dry-run plan is local advisory guidance only — NOT verified MRMS. "
        "Does not download, decode, render, clear alerts, or authorize production use. "
        "Listed operator commands are NOT run by this phase.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        plan = generate_render_candidate_dry_run_plan(storage)
    else:
        plan = build_render_candidate_dry_run_plan_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return

    compact = compact_render_candidate_dry_run_plan(storage)
    print("MRMS render candidate dry-run plan (local advisory only — NOT verified MRMS):")
    print(f"  plan_status: {plan.get('plan_status')}")
    print(f"  plan_reason: {plan.get('plan_reason')}")
    print(f"  blocking_items: {len(plan.get('blocking_items') or [])}")
    print(f"  warnings: {len(plan.get('warnings') or [])}")
    print(f"  json_path: {plan.get('json_path') or compact.get('json_path')}")
    print(f"  markdown_path: {plan.get('markdown_path') or compact.get('markdown_path')}")
    print(f"  suggested_command: {compact.get('suggested_command') or SUGGESTED_DRY_RUN_PLAN_COMMAND}")
    print(f"  verified_mrms: {plan.get('verified_mrms')}")
    for item in plan.get("blocking_items") or []:
        print(f"  BLOCK: {item}")
    for item in plan.get("warnings") or []:
        print(f"  WARN: {item}")


if __name__ == "__main__":
    main()
