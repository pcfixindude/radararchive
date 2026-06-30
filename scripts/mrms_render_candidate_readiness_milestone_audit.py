"""MRMS candidate readiness milestone audit (Phase 100)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_readiness_milestone_audit import (
    SUGGESTED_COMMAND,
    build_readiness_milestone_audit_payload,
    compact_readiness_milestone_audit,
    run_readiness_milestone_audit,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consolidated MRMS candidate readiness milestone audit (Phase 100)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh gated readiness chain then write milestone audit",
    )
    args = parser.parse_args()

    print(
        "WARNING: Readiness milestone audit is local advisory only — NOT verified MRMS. "
        "Does not enable production rendering or clear alerts.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = run_readiness_milestone_audit(storage, refresh_chain=True)
    else:
        report = build_readiness_milestone_audit_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_readiness_milestone_audit(storage)
    print("MRMS candidate readiness milestone audit (local advisory only):")
    print(f"  audit_status: {compact.get('audit_status')}")
    print(f"  preflight_level: {compact.get('preflight_level')}")
    print(f"  root_gate: {compact.get('root_gate')}")
    print(f"  blocker_category: {compact.get('blocker_category')}")
    print(f"  next_operator_step: {compact.get('next_operator_step')}")
    print(f"  next_phase_recommendation: {compact.get('next_phase_recommendation')}")
    print(f"  add_gated_wrapper_recommended: {compact.get('add_gated_wrapper_recommended')}")
    for label, items in (
        ("preflight_blockers", compact.get("preflight_blockers") or []),
        ("preflight_warnings", compact.get("preflight_warnings") or []),
        (
            "downstream_blocked_only_because_preflight",
            compact.get("downstream_blocked_only_because_preflight") or [],
        ),
    ):
        if items:
            print(f"  {label}:")
            for item in items:
                print(f"    - {item}")
    gates = compact.get("gates") or []
    if gates:
        print("  gates:")
        for gate in gates:
            suffix = " (preflight-only)" if gate.get("blocked_only_because_preflight") else ""
            print(
                f"    - {gate.get('label')}: {gate.get('review_status')} "
                f"ready={gate.get('ready')} skipped={gate.get('skipped')}{suffix}"
            )
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
