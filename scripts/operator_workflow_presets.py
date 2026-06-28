"""Print operator workflow presets (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.operator_workflow_presets import build_operator_workflow_presets_payload
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show local operator workflow presets (Phase 52 — read-only guidance)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    args = parser.parse_args()

    print(
        "WARNING: Operator workflow presets are local guidance only — NOT verified MRMS. "
        "Does not clear alerts, notify externally, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    payload = build_operator_workflow_presets_payload(storage)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("Operator workflow presets (local workflow guidance only — NOT verified MRMS):")
    print(f"  recommended_count: {payload.get('recommended_count')}")
    for preset in payload.get("presets") or []:
        marker = "*" if preset.get("recommended") else " "
        print(f"  {marker} {preset.get('preset_id')}: {preset.get('title')}")
        print(f"      when_to_use: {preset.get('when_to_use')}")
        print(f"      command: {preset.get('command')}")
        if preset.get("recommended"):
            print(f"      recommendation_reason: {preset.get('recommendation_reason')}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")


if __name__ == "__main__":
    main()
