"""Print proof bundle diff escalation digest diff metadata (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.proof_bundle_diff_escalation_digest_diff import (
    MAX_DIGEST_DIFF_HISTORY,
    build_digest_diff_payload,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show digest export diff metadata (Phase 40 — local review only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument(
        "--limit",
        type=int,
        default=MAX_DIGEST_DIFF_HISTORY,
        help=f"Max diff history entries (default {MAX_DIGEST_DIFF_HISTORY})",
    )
    args = parser.parse_args()

    print(
        "WARNING: Digest diff metadata is local review evidence only — NOT verified MRMS. "
        "Does not clear alerts or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    payload = build_digest_diff_payload(storage)
    if args.limit < MAX_DIGEST_DIFF_HISTORY:
        payload["entries"] = (payload.get("entries") or [])[: max(1, min(args.limit, 25))]
        payload["count"] = len(payload["entries"])

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    compact = payload.get("compact") or {}
    hint = payload.get("regeneration_hint") or {}
    print("Proof bundle diff escalation digest diff (local review only — NOT verified MRMS):")
    print(f"  overall_digest_diff_status: {compact.get('overall_digest_diff_status')}")
    print(f"  checked_at: {compact.get('checked_at')}")
    print(f"  history_count: {compact.get('history_count', 0)}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")
    print(
        f"  regeneration_recommended: {hint.get('digest_regeneration_recommended')} "
        f"reason={hint.get('reason')}"
    )
    if hint.get("suggested_command"):
        print(f"  suggested_command: {hint.get('suggested_command')}")


if __name__ == "__main__":
    main()
