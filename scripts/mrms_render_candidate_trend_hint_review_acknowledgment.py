"""Record local candidate trend-hint review acknowledgments (Phase 81)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_trend_hint_review_acknowledgment import (
    TrendHintReviewAckValidationError,
    build_trend_hint_review_acknowledgments_payload,
    compact_trend_hint_review_acknowledgment_summary,
    create_trend_hint_review_acknowledgment,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record local candidate trend-hint review acknowledgment (Phase 81)."
    )
    parser.add_argument("--operator", dest="operator_initials", help="Operator initials")
    parser.add_argument("--note", required=True, help="Review note (required)")
    parser.add_argument(
        "--acknowledged-trend-review",
        action="store_true",
        help="Mark current trend review recommendation as acknowledged locally",
    )
    parser.add_argument("--json-report", action="store_true", help="Print JSON summary after recording")
    args = parser.parse_args()

    print(
        "WARNING: Trend-hint review acknowledgment is local evidence only — "
        "does NOT clear alerts, verify MRMS, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    try:
        record = create_trend_hint_review_acknowledgment(
            storage,
            operator_initials=args.operator_initials,
            note=args.note,
            acknowledged_trend_review=args.acknowledged_trend_review or None,
        )
    except TrendHintReviewAckValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    compact = compact_trend_hint_review_acknowledgment_summary(storage)
    if args.json_report:
        print(json.dumps({"acknowledgment": record, "compact": compact}, indent=2, sort_keys=True))
        return

    print(f"Recorded acknowledgment {record.get('acknowledgment_id')}")
    print(f"Operator: {record.get('operator')}")
    print(f"Trend review still recommended: {compact.get('trend_review_still_recommended')}")


if __name__ == "__main__":
    main()
