"""Print proof bundle diff alert escalation hints (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.proof_bundle_diff_escalation import (
    build_proof_bundle_diff_escalation_payload,
)
from backend.app.services.proof_bundle_diff_escalation_history import (
    record_escalation_from_storage,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show proof bundle diff alert escalation hints (Phase 36 — local guidance only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument(
        "--no-record",
        action="store_true",
        help="Do not append escalation snapshot to bounded history",
    )
    args = parser.parse_args()

    print(
        "WARNING: Diff alert escalation is local operator guidance only — "
        "NOT verified MRMS. Does not clear alerts or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if not args.no_record:
        record_escalation_from_storage(
            storage,
            source="proof_bundle_diff_escalation_cli",
            skip_duplicate=True,
        )
    payload = build_proof_bundle_diff_escalation_payload(storage)
    escalation = payload.get("escalation") or {}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("Proof bundle diff alert escalation (local guidance only — NOT verified MRMS):")
    print(f"  escalation_level: {escalation.get('escalation_level')}")
    print(f"  reason: {escalation.get('reason')}")
    print(f"  latest_diff_status: {escalation.get('latest_diff_status')}")
    print(f"  current_attention_streak: {escalation.get('current_attention_streak', 0)}")
    print(f"  acknowledgment_status: {escalation.get('acknowledgment_status')}")
    print(f"  stale_acknowledgment: {escalation.get('stale_acknowledgment')}")
    print(f"  latest_acknowledgment_at: {escalation.get('latest_acknowledgment_at')}")
    print(f"  latest_acknowledgment_operator: {escalation.get('latest_acknowledgment_operator')}")
    print(f"  suggested_next_action: {escalation.get('suggested_next_action')}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")
    print(f"  local_escalation_only: {payload.get('local_escalation_only')}")
    print(f"  does_not_clear_alerts: {payload.get('does_not_clear_alerts')}")
    guidance = escalation.get("guidance_items") or []
    if guidance:
        print("  guidance_items:")
        for item in guidance:
            anchor = item.get("anchor") or ""
            label = item.get("section_label") or item.get("title")
            print(f"    - {label} ({item.get('path')}{'#' + anchor if anchor else ''})")


if __name__ == "__main__":
    main()
