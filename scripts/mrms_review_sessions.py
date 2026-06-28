"""List local MRMS proof review sessions (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_review_session import (
    MAX_REVIEW_SESSIONS,
    build_review_sessions_payload,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List MRMS proof review sessions (Phase 41 — read-only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument(
        "--limit",
        type=int,
        default=MAX_REVIEW_SESSIONS,
        help=f"Max entries (default {MAX_REVIEW_SESSIONS})",
    )
    args = parser.parse_args()

    print(
        "WARNING: Review sessions are local review evidence only — NOT verified MRMS.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    bounded = max(1, min(args.limit, MAX_REVIEW_SESSIONS))
    payload = build_review_sessions_payload(storage, limit=bounded)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("MRMS proof review sessions (local review only — NOT verified MRMS):")
    print(f"  count: {payload.get('count')}")
    print(f"  max_entries: {payload.get('max_entries')}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")
    latest = payload.get("latest")
    if latest:
        print(
            f"  latest: {latest.get('created_at')} — {latest.get('operator')} "
            f"escalation={latest.get('latest_escalation_level')} "
            f"open_attention={latest.get('open_attention_count', 0)}"
        )
    for entry in payload.get("entries") or []:
        print(
            f"  - {entry.get('created_at')}: {entry.get('operator')} "
            f"escalation={entry.get('latest_escalation_level')} "
            f"open={entry.get('open_attention_count', 0)}"
        )


if __name__ == "__main__":
    main()
