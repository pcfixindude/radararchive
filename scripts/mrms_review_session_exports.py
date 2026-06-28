"""List bounded MRMS proof review session export history (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_review_session_export import (
    MAX_EXPORT_HISTORY,
    build_review_session_export_payload,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List MRMS proof review session export history (Phase 43 — read-only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument(
        "--limit",
        type=int,
        default=MAX_EXPORT_HISTORY,
        help=f"Max entries (default {MAX_EXPORT_HISTORY})",
    )
    args = parser.parse_args()

    print(
        "WARNING: Review session export history is local review evidence only — NOT verified MRMS.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    payload = build_review_session_export_payload(storage)
    bounded = max(1, min(args.limit, MAX_EXPORT_HISTORY))
    payload["entries"] = (payload.get("entries") or [])[:bounded]
    payload["count"] = len(payload["entries"])

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("MRMS proof review session export history (local export only — NOT verified MRMS):")
    print(f"  count: {payload.get('count')}")
    print(f"  max_entries: {payload.get('max_entries')}")
    compact = payload.get("compact") or {}
    if compact.get("available"):
        print(
            f"  latest: {compact.get('created_at')} — {compact.get('operator')} "
            f"comparison={compact.get('comparison_status')} "
            f"open_attention={compact.get('open_attention_count', 0)}"
        )
    for entry in payload.get("entries") or []:
        print(
            f"  - {entry.get('created_at')}: {entry.get('operator')} "
            f"session={entry.get('session_id')} "
            f"comparison={entry.get('comparison_status')}"
        )

    hint = payload.get("regeneration_hint") or {}
    print(
        f"  review_export_regeneration_recommended: "
        f"{hint.get('review_export_regeneration_recommended')}"
    )
    if hint.get("reason"):
        print(f"  reason: {hint.get('reason')}")
    if hint.get("suggested_command"):
        print(f"  suggested_command: {hint.get('suggested_command')}")


if __name__ == "__main__":
    main()
