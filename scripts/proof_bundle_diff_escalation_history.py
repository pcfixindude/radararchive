"""Print proof bundle diff escalation history (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.proof_bundle_diff_escalation_history import (
    MAX_ESCALATION_HISTORY,
    build_proof_bundle_diff_escalation_history_payload,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show proof bundle diff escalation history (Phase 37 — local monitoring only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument(
        "--limit",
        type=int,
        default=MAX_ESCALATION_HISTORY,
        help=f"Max entries to show (default {MAX_ESCALATION_HISTORY})",
    )
    args = parser.parse_args()

    print(
        "WARNING: Escalation history is local evidence monitoring only — "
        "NOT verified MRMS. Does not clear alerts or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(args.limit, MAX_ESCALATION_HISTORY))
    payload = build_proof_bundle_diff_escalation_history_payload(storage, limit=bounded)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("Proof bundle diff escalation history (local monitoring only — NOT verified MRMS):")
    print(f"  count: {payload.get('count')}")
    print(f"  max_entries: {payload.get('max_entries')}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")
    latest = payload.get("latest")
    if latest:
        print(
            f"  latest: {latest.get('created_at')} — {latest.get('escalation_level')} "
            f"({latest.get('latest_diff_status')})"
        )
    for entry in payload.get("entries") or []:
        print(
            f"  - {entry.get('created_at')}: {entry.get('escalation_level')} "
            f"streak={entry.get('current_attention_streak', 0)} "
            f"stale_ack={entry.get('stale_acknowledgment')}"
        )


if __name__ == "__main__":
    main()
