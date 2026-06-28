"""Show bounded MRMS proof and regression history (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_proof_history import (
    build_proof_history_payload,
    build_regression_history_payload,
    build_signoffs_list_payload,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(description="Show MRMS proof review history (Phase 28 read-only).")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    parser.add_argument("--regression", action="store_true", help="Show regression history only")
    parser.add_argument("--signoffs", action="store_true", help="Show sign-offs only")
    args = parser.parse_args()

    storage = LocalStorage(settings.local_storage_root)

    if args.regression:
        payload = build_regression_history_payload(storage)
        label = "MRMS proof regression history"
    elif args.signoffs:
        payload = build_signoffs_list_payload(storage)
        label = "MRMS operator sign-offs (local only)"
    else:
        payload = build_proof_history_payload(storage)
        label = "MRMS proof report history"

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print(f"{label} (draft — NOT verified MRMS):")
    print(f"  verified_mrms: False")
    print(f"  count: {payload.get('count', 0)}")
    entries = payload.get("entries") or []
    for item in entries[:10]:
        if args.signoffs:
            print(
                f"  - {item.get('created_at')}: {item.get('operator')} "
                f"(proof {item.get('proof_report_timestamp')})"
            )
        elif args.regression:
            print(f"  - {item.get('checked_at')}: {item.get('summary')}")
        else:
            counts = item.get("criteria_counts") or {}
            print(
                f"  - {item.get('generated_at')}: {item.get('overall_status')} "
                f"frames={item.get('frame_count')} "
                f"passed={counts.get('passed', 0)} failed={counts.get('failed', 0)}"
            )
    print("\nSee docs/RUNBOOK_REAL_MRMS_VALIDATION.md", file=sys.stderr)


if __name__ == "__main__":
    main()
