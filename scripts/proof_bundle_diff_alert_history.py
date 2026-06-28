"""Print bounded proof bundle diff alert history (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.proof_bundle_diff_alert_history import (
    MAX_ALERT_HISTORY,
    build_proof_bundle_diff_alert_history_payload,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show proof bundle diff alert timeline (Phase 34 — local monitoring only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help=f"Max entries to show (default 10, max {MAX_ALERT_HISTORY})",
    )
    args = parser.parse_args()

    print(
        "WARNING: Proof bundle diff alert history is local evidence monitoring only — "
        "NOT verified MRMS. Does not enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(args.limit, MAX_ALERT_HISTORY))
    payload = build_proof_bundle_diff_alert_history_payload(storage, limit=bounded)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("Proof bundle diff alert history (local monitoring only — NOT verified MRMS):")
    print(f"  count: {payload.get('count', 0)}")
    print(f"  max_entries: {payload.get('max_entries', MAX_ALERT_HISTORY)}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")
    latest = payload.get("latest")
    if latest:
        print(
            f"  latest: {latest.get('created_at')} — {latest.get('diff_status')} "
            f"(attention={latest.get('operator_attention_needed')})"
        )
    else:
        print("  latest: none — run make mrms-proof-bundle-diff or make scheduled-proof-bundle")
    for entry in payload.get("entries") or []:
        print(
            f"  - {entry.get('created_at')}: {entry.get('diff_status')} "
            f"changes={entry.get('evidence_changes_count', 0)} "
            f"attention={entry.get('operator_attention_needed')}"
        )


if __name__ == "__main__":
    main()
