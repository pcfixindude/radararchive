"""Record local MRMS operator sign-off (does NOT set verified_mrms=true)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_signoff import SignoffValidationError, create_signoff_and_refresh_alert
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record local operator sign-off for draft MRMS proof (Phase 27)."
    )
    parser.add_argument("--operator-name", help="Operator full name")
    parser.add_argument("--initials", help="Operator initials (alternative to name)")
    parser.add_argument("--notes", help="Operator review notes")
    parser.add_argument("--accepted-limitations", help="Accepted limitations statement")
    parser.add_argument("--proof-timestamp", help="Proof report generated_at to reference")
    parser.add_argument("--frame-count", type=int, help="Frames reviewed")
    parser.add_argument("--json", action="store_true", help="Print JSON record")
    args = parser.parse_args()

    print(
        "WARNING: Sign-off is local only — does NOT set verified_mrms=true "
        "and does NOT enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    try:
        record, _alert = create_signoff_and_refresh_alert(
            storage,
            operator_name=args.operator_name,
            operator_initials=args.initials,
            operator_notes=args.notes,
            accepted_limitations=args.accepted_limitations,
            proof_report_timestamp=args.proof_timestamp,
            frame_count_reviewed=args.frame_count,
        )
    except SignoffValidationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if args.json:
        print(json.dumps(record, indent=2, sort_keys=True))
        return

    print("Operator sign-off recorded (local only — NOT verified MRMS):")
    print(f"  signoff_id: {record.get('signoff_id')}")
    print(f"  created_at: {record.get('created_at')}")
    print(f"  operator: {record.get('operator_name') or record.get('operator_initials')}")
    print(f"  proof_report_timestamp: {record.get('proof_report_timestamp')}")
    print(f"  verified_mrms: {record.get('verified_mrms')}")
    print(f"  does_not_set_verified_mrms: {record.get('does_not_set_verified_mrms')}")
    print(f"  does_not_enable_production: {record.get('does_not_enable_production')}")
    print(f"  production_enabled: {record.get('production_enabled')}")


if __name__ == "__main__":
    main()
