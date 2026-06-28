"""Show validation alert marker and grouped failure causes (dev/prototype)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import load_validation_alert, refresh_validation_alert


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show local validation alert marker (Phase 25 prototype)."
    )
    parser.add_argument("--refresh", action="store_true", help="Rebuild alert from failure log")
    parser.add_argument("--json", action="store_true", help="Print JSON alert")
    args = parser.parse_args()

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        alert = refresh_validation_alert(storage)
    else:
        alert = load_validation_alert(storage)
        if alert is None:
            alert = refresh_validation_alert(storage)

    if args.json:
        print(json.dumps(alert, indent=2, sort_keys=True))
        return

    print("Validation alert (experimental prototype — NOT verified MRMS):")
    print(f"  status: {alert.get('status')}")
    print(f"  operator_attention_needed: {alert.get('operator_attention_needed')}")
    print(f"  latest_run_at: {alert.get('latest_run_at')}")
    print(f"  updated_at: {alert.get('updated_at')}")
    print(f"  failure_count: {alert.get('failure_count')}")
    print(f"  warning_count: {alert.get('warning_count')}")
    print(f"  verified_mrms: {alert.get('verified_mrms')}")
    print(f"  suggested_next_action: {alert.get('suggested_next_action')}")
    grouped = alert.get("grouped_failure_causes") or []
    if grouped:
        print("  grouped_failure_causes:")
        for item in grouped[:10]:
            print(
                f"    - [{item.get('step')}] {item.get('cause')} "
                f"x{item.get('count')}: {item.get('message', '')[:80]}"
            )
    else:
        print("  grouped_failure_causes: (none)")
    print("\nSee docs/RUNBOOK_REAL_MRMS_VALIDATION.md and docs/VERIFIED_MRMS_CRITERIA.md", file=sys.stderr)


if __name__ == "__main__":
    main()
