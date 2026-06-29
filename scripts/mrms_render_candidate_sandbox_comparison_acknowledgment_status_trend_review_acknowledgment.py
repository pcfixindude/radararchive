"""Record local acknowledgment status trend hint review acknowledgment (Phase 73)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment import (
    AckStatusTrendReviewAcknowledgmentValidationError,
    build_ack_status_trend_review_acknowledgments_payload,
    create_ack_status_trend_review_acknowledgment,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record local acknowledgment status trend hint review acknowledgment (Phase 73)."
    )
    parser.add_argument("--operator", help="Operator initials or name")
    parser.add_argument("--operator-name", help="Operator full name")
    parser.add_argument("--operator-initials", help="Operator initials")
    parser.add_argument("--note", required=True, help="Acknowledgment note (required)")
    parser.add_argument(
        "--acknowledged-trend-review",
        action="store_true",
        help="Mark that operator reviewed the current status trend recommendation",
    )
    parser.add_argument("--list", action="store_true", help="List recent acknowledgments")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    print(
        "WARNING: Status trend review acknowledgment is local only — "
        "does NOT clear alerts, verify MRMS, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)

    if args.list:
        payload = build_ack_status_trend_review_acknowledgments_payload(storage)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
            return
        print(f"Acknowledgments: {payload['count']}")
        latest = payload.get("latest")
        if latest:
            print(f"Latest: {latest.get('created_at')} — {latest.get('operator')}")
        return

    operator_name = args.operator_name
    operator_initials = args.operator_initials or args.operator
    if args.operator and not operator_initials and not operator_name:
        if len(args.operator.strip()) <= 4:
            operator_initials = args.operator.strip()
        else:
            operator_name = args.operator.strip()

    try:
        record = create_ack_status_trend_review_acknowledgment(
            storage,
            operator_name=operator_name,
            operator_initials=operator_initials,
            note=args.note,
            acknowledged_trend_review=args.acknowledged_trend_review or None,
        )
    except AckStatusTrendReviewAcknowledgmentValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if args.json:
        print(json.dumps(record, indent=2, sort_keys=True))
        return

    print("Status trend review acknowledgment recorded (local only — does NOT clear alerts):")
    print(f"  operator: {record.get('operator')}")
    print(f"  related_trend: {record.get('related_trend')}")
    print(f"  related_hint_status: {record.get('related_hint_status')}")


if __name__ == "__main__":
    main()
