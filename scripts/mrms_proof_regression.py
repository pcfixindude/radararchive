"""Run MRMS proof regression check (dev/prototype)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_proof_regression import run_proof_regression_check
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import refresh_validation_alert


def main() -> None:
    parser = argparse.ArgumentParser(description="Check MRMS proof regressions (Phase 27 prototype).")
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    parser.add_argument("--refresh-alert", action="store_true", help="Refresh validation alert marker")
    args = parser.parse_args()

    print(
        "WARNING: Proof regression check is draft tooling — NOT verified MRMS.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    report = run_proof_regression_check(storage)
    if args.refresh_alert:
        refresh_validation_alert(storage)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print("MRMS proof regression (draft — NOT verified MRMS):")
    print(f"  regression_status: {report.get('regression_status')}")
    print(f"  regression_detected: {report.get('regression_detected')}")
    print(f"  regression_count: {report.get('regression_count')}")
    print(f"  checked_at: {report.get('checked_at')}")
    print(f"  verified_mrms: {report.get('verified_mrms')}")
    for finding in report.get("findings") or []:
        print(f"  finding: {finding.get('kind')}: {finding.get('message')}")
    print("\nSee docs/RUNBOOK_REAL_MRMS_VALIDATION.md", file=sys.stderr)


if __name__ == "__main__":
    main()
