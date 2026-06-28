"""Print proof bundle diff escalation history metrics (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.proof_bundle_diff_escalation_metrics import (
    build_proof_bundle_diff_escalation_metrics_payload,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show proof bundle diff escalation history metrics (Phase 38 — local review only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    args = parser.parse_args()

    print(
        "WARNING: Escalation metrics are local review evidence only — "
        "NOT verified MRMS. Does not clear alerts or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    payload = build_proof_bundle_diff_escalation_metrics_payload(storage)
    metrics = payload.get("metrics") or {}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("Proof bundle diff escalation metrics (local review only — NOT verified MRMS):")
    print(f"  total_snapshots: {metrics.get('total_snapshots', 0)}")
    print(f"  urgent_count: {metrics.get('urgent_count', 0)}")
    print(f"  attention_count: {metrics.get('attention_count', 0)}")
    print(f"  watch_count: {metrics.get('watch_count', 0)}")
    print(f"  none_count: {metrics.get('none_count', 0)}")
    print(f"  latest_level: {metrics.get('latest_level')}")
    print(f"  latest_at: {metrics.get('latest_at')}")
    print(f"  current_urgent_streak: {metrics.get('current_urgent_streak', 0)}")
    print(
        f"  current_attention_or_urgent_streak: "
        f"{metrics.get('current_attention_or_urgent_streak', 0)}"
    )
    print(f"  longest_urgent_streak: {metrics.get('longest_urgent_streak', 0)}")
    print(
        f"  longest_attention_or_urgent_streak: "
        f"{metrics.get('longest_attention_or_urgent_streak', 0)}"
    )
    print(f"  stale_acknowledgment_count: {metrics.get('stale_acknowledgment_count', 0)}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")


if __name__ == "__main__":
    main()
