"""Run gated MRMS render candidate preflight attempt (Phase 88)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight_attempt import (
    SUGGESTED_COMMAND,
    attempt_gated_preflight,
    build_preflight_attempt_payload,
    compact_preflight_attempt,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run gated MRMS render candidate preflight attempt (Phase 88)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Run gated preflight attempt (skips when review readiness has blockers)",
    )
    args = parser.parse_args()

    print(
        "WARNING: Gated preflight attempt is local advisory only — NOT verified MRMS. "
        "Does not download, decode, render production tiles, clear alerts, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = attempt_gated_preflight(storage)
    else:
        report = build_preflight_attempt_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_preflight_attempt(storage)
    print("Gated MRMS render candidate preflight attempt (local advisory only):")
    print(f"  attempt_status: {compact.get('attempt_status')}")
    print(f"  readiness_level: {compact.get('readiness_level')}")
    print(f"  gate_open: {compact.get('gate_open')}")
    print(f"  preflight_not_run: {compact.get('preflight_not_run')}")
    print(f"  preflight_level: {compact.get('preflight_level')}")
    print(f"  next_operator_step: {compact.get('next_operator_step')}")
    if compact.get("gate_reason"):
        print(f"  gate_reason: {compact.get('gate_reason')}")
    print(f"  suggested_command: {SUGGESTED_COMMAND}")


if __name__ == "__main__":
    main()
