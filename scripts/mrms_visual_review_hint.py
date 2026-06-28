"""Print stale visual review regeneration hint (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_visual_review_hint import build_visual_review_hint_payload
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show MRMS visual review regeneration hint (Phase 57 — local hint only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    args = parser.parse_args()

    print(
        "WARNING: Visual review hint is local guidance only — NOT verified MRMS. "
        "Does not download, decode, clear alerts, notify externally, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    payload = build_visual_review_hint_payload(storage)
    hint = payload.get("hint") or {}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("MRMS visual review hint (local hint only — NOT verified MRMS):")
    print(f"  visual_review_regeneration_recommended: {hint.get('visual_review_regeneration_recommended')}")
    print(f"  reason: {hint.get('reason')}")
    print(f"  suggested_command: {hint.get('suggested_command')}")
    print(f"  latest_visual_review_at: {hint.get('latest_visual_review_at')}")
    print(f"  latest_relevant_evidence_at: {hint.get('latest_relevant_evidence_at')}")
    print(f"  stale_visual_review: {hint.get('stale_visual_review')}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")


if __name__ == "__main__":
    main()
