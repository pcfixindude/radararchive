"""Compare local MRMS proof review sessions (read-only by default)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_review_session_compare import (
    build_review_session_comparison_payload,
    record_review_session_comparison,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare latest vs previous MRMS proof review session (Phase 42 — read-only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    args = parser.parse_args()

    print(
        "WARNING: Review session comparison is local review evidence only — NOT verified MRMS.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    record_review_session_comparison(storage)
    payload = build_review_session_comparison_payload(storage)
    compact = payload.get("compact") or {}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("MRMS proof review session comparison (local comparison only — NOT verified MRMS):")
    print(f"  overall_review_diff_status: {compact.get('overall_review_diff_status')}")
    print(f"  compared_at: {compact.get('compared_at')}")
    print(
        f"  baseline: {compact.get('baseline_created_at')} — {compact.get('baseline_operator')}"
    )
    print(f"  latest: {compact.get('latest_created_at')} — {compact.get('latest_operator')}")
    open_change = compact.get("open_attention_count_change") or {}
    if open_change:
        print(
            f"  open_attention_count: baseline={open_change.get('baseline')} "
            f"latest={open_change.get('latest')}"
        )
    reviewed_change = compact.get("checklist_reviewed_count_change") or {}
    if reviewed_change:
        print(
            f"  checklist_reviewed_count: baseline={reviewed_change.get('baseline')} "
            f"latest={reviewed_change.get('latest')}"
        )
    not_reviewed_change = compact.get("checklist_not_reviewed_count_change") or {}
    if not_reviewed_change:
        print(
            f"  checklist_not_reviewed_count: baseline={not_reviewed_change.get('baseline')} "
            f"latest={not_reviewed_change.get('latest')}"
        )
    improvements = compact.get("improvements") or []
    regressions = compact.get("regressions") or []
    if improvements:
        print(f"  improvements: {', '.join(improvements)}")
    if regressions:
        print(f"  regressions: {', '.join(regressions)}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")
    print(f"  local_comparison_only: {payload.get('local_comparison_only')}")
    print(f"  does_not_clear_alerts: {payload.get('does_not_clear_alerts')}")
    print(f"  does_not_enable_production: {payload.get('does_not_enable_production')}")


if __name__ == "__main__":
    main()
