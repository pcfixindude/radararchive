"""Diff two local MRMS proof bundles (does NOT verify MRMS)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_NO_BASELINE,
    build_proof_bundle_diff_report,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare local MRMS proof bundles (Phase 31 — review only)."
    )
    parser.add_argument("--baseline", help="Baseline bundle folder repo path")
    parser.add_argument("--current", help="Current bundle folder repo path")
    parser.add_argument("--json-report", action="store_true", help="Print full JSON diff report")
    args = parser.parse_args()

    print(
        "WARNING: Proof bundle diff is local review only — NOT verified MRMS. "
        "Does not enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    report = build_proof_bundle_diff_report(
        storage,
        current_bundle_folder=args.current,
        baseline_bundle_folder=args.baseline,
    )

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print("MRMS proof bundle diff (local review only — NOT verified MRMS):")
    print(f"  overall_diff_status: {report.get('overall_diff_status')}")
    print(f"  checked_at: {report.get('checked_at')}")
    print(f"  evidence_changes_count: {report.get('evidence_changes_count')}")
    print(f"  verified_mrms: {report.get('verified_mrms')}")
    current = report.get("current_bundle") or {}
    baseline = report.get("baseline_bundle") or {}
    print(f"  current_bundle: {current.get('bundle_folder')}")
    print(f"  baseline_bundle: {baseline.get('bundle_folder')}")
    if report.get("warnings"):
        for warning in report["warnings"]:
            print(f"  warning: {warning}", file=sys.stderr)

    if report.get("overall_diff_status") == DIFF_NO_BASELINE:
        print(
            "\nNo baseline bundle — run make mrms-proof-bundle at least twice, then re-run diff.",
            file=sys.stderr,
        )
        raise SystemExit(0)


if __name__ == "__main__":
    main()
