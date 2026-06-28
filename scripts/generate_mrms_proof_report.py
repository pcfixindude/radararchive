"""Generate draft MRMS proof report (evidence only — NOT verified MRMS)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.mrms_proof_report import (
    generate_mrms_proof_report,
    resolve_proof_source_mode,
    save_mrms_proof_report,
    write_operator_signoff_template_copy,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate draft verified-MRMS proof report (Phase 26 — evidence only)."
    )
    parser.add_argument("--count", type=int, default=3, help="Frames to evaluate (max 10)")
    parser.add_argument("--real", action="store_true", help="Evaluate real downloaded .grib2.gz only (explicit)")
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    args = parser.parse_args()

    if args.real:
        print(
            "WARNING: --real mode evaluates real MRMS catalog rows only; "
            "does not download. Network not required for this command.",
            file=sys.stderr,
        )

    print(
        "WARNING: Proof report is draft tooling — NOT verified MRMS. verified_mrms stays false.",
        file=sys.stderr,
    )

    storage_root = settings.local_storage_root
    from backend.app.services.storage import LocalStorage

    storage = LocalStorage(storage_root)
    source_mode = resolve_proof_source_mode(real=args.real)

    init_db()
    session = get_session_factory()()
    try:
        report = generate_mrms_proof_report(
            session,
            storage,
            count=args.count,
            source_mode=source_mode,
        )
        save_mrms_proof_report(storage, report)
        signoff_path = write_operator_signoff_template_copy(storage)
        report["signoff_template_copy"] = signoff_path
    finally:
        session.close()

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    counts = report.get("criteria_counts") or {}
    print("MRMS proof report (draft — NOT verified MRMS):")
    print(f"  overall_status: {report.get('overall_status')}")
    print(f"  source_mode: {report.get('source_mode')}")
    print(f"  frame_count: {report.get('frame_count')}")
    print(f"  verified_mrms: {report.get('verified_mrms')}")
    print(f"  operator_review_required: {report.get('operator_review_required')}")
    print(
        f"  criteria: passed={counts.get('passed', 0)} failed={counts.get('failed', 0)} "
        f"warning={counts.get('warning', 0)} skipped={counts.get('skipped', 0)} "
        f"unknown={counts.get('unknown', 0)}"
    )
    print(f"  signoff_template: docs/MRMS_OPERATOR_SIGNOFF_TEMPLATE.md")
    print(f"  local_copy: {signoff_path}")
    for warning in report.get("warnings") or []:
        print(f"  warning: {warning}")
    print("\nSee docs/VERIFIED_MRMS_CRITERIA.md", file=sys.stderr)


if __name__ == "__main__":
    main()
