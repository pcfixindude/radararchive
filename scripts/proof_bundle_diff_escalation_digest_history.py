"""Print proof bundle diff escalation digest export history (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.proof_bundle_diff_escalation_digest_history import (
    MAX_DIGEST_HISTORY,
    build_digest_export_history_payload,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show proof bundle diff escalation digest history (Phase 40 — local review only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument(
        "--limit",
        type=int,
        default=MAX_DIGEST_HISTORY,
        help=f"Max entries to show (default {MAX_DIGEST_HISTORY})",
    )
    args = parser.parse_args()

    print(
        "WARNING: Digest history is local review evidence only — NOT verified MRMS. "
        "Does not clear alerts or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(args.limit, MAX_DIGEST_HISTORY))
    payload = build_digest_export_history_payload(storage, limit=bounded)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("Proof bundle diff escalation digest history (local review only — NOT verified MRMS):")
    print(f"  count: {payload.get('count')}")
    print(f"  max_entries: {payload.get('max_entries')}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")
    latest = payload.get("latest")
    if latest:
        print(
            f"  latest: {latest.get('created_at')} — {latest.get('latest_escalation_level')} "
            f"({latest.get('latest_diff_status')})"
        )
    for entry in payload.get("entries") or []:
        print(
            f"  - {entry.get('created_at')}: {entry.get('latest_escalation_level')} "
            f"urgent={entry.get('urgent_count', 0)} attention={entry.get('attention_count', 0)}"
        )


if __name__ == "__main__":
    main()
