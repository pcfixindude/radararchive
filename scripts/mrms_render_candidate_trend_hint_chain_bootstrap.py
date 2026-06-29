"""Bootstrap sandbox comparison trend-hint chain (Phase 90)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_trend_hint_chain_bootstrap import (
    SUGGESTED_COMMAND,
    bootstrap_trend_hint_chain,
    build_trend_hint_chain_bootstrap_payload,
    compact_trend_hint_chain_bootstrap,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap sandbox comparison trend-hint chain (Phase 90)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Seed comparison history if needed and refresh trend-hint chain",
    )
    args = parser.parse_args()

    print(
        "WARNING: Trend-hint chain bootstrap is local advisory only — NOT verified MRMS. "
        "Does not force preflight when readiness gate is closed.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = bootstrap_trend_hint_chain(storage)
    else:
        report = build_trend_hint_chain_bootstrap_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_trend_hint_chain_bootstrap(storage)
    print("Candidate trend-hint chain bootstrap (local advisory only):")
    print(f"  bootstrap_status: {compact.get('bootstrap_status')}")
    print(f"  trend_hint_chain_ready: {compact.get('trend_hint_chain_ready')}")
    print(f"  rollup_status: {compact.get('rollup_status')}")
    print(f"  digest_status: {compact.get('digest_status')}")
    print(f"  chain_readiness_level: {compact.get('chain_readiness_level')}")
    print(f"  overall_readiness_level: {compact.get('overall_readiness_level')}")
    print(f"  preflight_not_run: {compact.get('preflight_not_run')}")
    print(f"  next_operator_step: {compact.get('next_operator_step')}")
    trend_blockers = compact.get("trend_hint_blockers") or []
    if trend_blockers:
        print("  trend_hint_blockers:")
        for item in trend_blockers:
            print(f"    - {item}")
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
