"""Validation remediation for render-candidate preflight (Phase 102)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_validation_remediation import (
    SUGGESTED_COMMAND,
    build_validation_remediation_payload,
    compact_validation_remediation,
    remediate_validation_failures,
    save_validation_remediation_report,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remediate validation/proof failures for render-candidate preflight."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Analyze and document stub-mode failures for preflight (does not clear alerts)",
    )
    args = parser.parse_args()

    print(
        "WARNING: Validation remediation is local advisory only — NOT verified MRMS. "
        "Does not clear alerts or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = save_validation_remediation_report(
            storage,
            remediate_validation_failures(storage, refresh=True),
        )
    else:
        report = build_validation_remediation_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_validation_remediation(storage)
    print("Validation remediation for preflight (local advisory only):")
    print(f"  remediation_status: {compact.get('remediation_status')}")
    print(f"  blocks_preflight: {compact.get('blocks_preflight')}")
    print(f"  stub_mode_documented: {compact.get('stub_mode_documented')}")
    print(f"  validation_alert_status: {compact.get('validation_alert_status')}")
    print(f"  next_operator_step: {compact.get('next_operator_step')}")
    print(f"  next_phase_recommendation: {compact.get('next_phase_recommendation')}")
    remaining = compact.get("remaining_real_failures") or []
    if remaining:
        print("  remaining_real_failures:")
        for item in remaining:
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
