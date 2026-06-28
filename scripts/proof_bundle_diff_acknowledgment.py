"""Record local proof bundle diff alert acknowledgment (does NOT clear alerts)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.proof_bundle_diff_acknowledgment import (
    DiffAcknowledgmentValidationError,
    create_diff_acknowledgment,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record local diff alert acknowledgment (Phase 35 — does NOT verify MRMS)."
    )
    parser.add_argument("--operator", help="Operator initials or name")
    parser.add_argument("--operator-name", help="Operator full name")
    parser.add_argument("--operator-initials", help="Operator initials")
    parser.add_argument("--note", required=True, help="Acknowledgment note (required)")
    parser.add_argument("--json", action="store_true", help="Print JSON record")
    args = parser.parse_args()

    print(
        "WARNING: Diff alert acknowledgment is local review only — "
        "does NOT clear alerts, verify MRMS, or enable production rendering.",
        file=sys.stderr,
    )

    operator_name = args.operator_name
    operator_initials = args.operator_initials or args.operator
    if args.operator and not operator_initials and not operator_name:
        if len(args.operator.strip()) <= 4:
            operator_initials = args.operator.strip()
        else:
            operator_name = args.operator.strip()

    storage = LocalStorage(settings.local_storage_root)
    try:
        record = create_diff_acknowledgment(
            storage,
            operator_name=operator_name,
            operator_initials=operator_initials,
            note=args.note,
        )
    except DiffAcknowledgmentValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if args.json:
        print(json.dumps(record, indent=2, sort_keys=True))
        return

    print("Diff alert acknowledgment recorded (local only — does NOT clear alerts):")
    print(f"  acknowledgment_id: {record.get('acknowledgment_id')}")
    print(f"  created_at: {record.get('created_at')}")
    print(f"  operator: {record.get('operator')}")
    print(f"  related_diff_status: {record.get('related_diff_status')}")
    print(f"  verified_mrms: {record.get('verified_mrms')}")
    print(f"  does_not_clear_alerts: {record.get('does_not_clear_alerts')}")


if __name__ == "__main__":
    main()
