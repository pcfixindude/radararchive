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
        print(f"      group: {preset.get('group_title')} ({preset.get('group_id')})")
        print(f"      recommended: {preset.get('recommended')}")
        if preset.get("recommended_priority") is not None:
            print(f"      recommended_priority: {preset.get('recommended_priority')}")
        if preset.get("recommendation_reason"):
            print(f"      recommendation_reason: {preset.get('recommendation_reason')}")
        print(f"      when_to_use: {preset.get('when_to_use')}")
        if preset.get("suggested_action"):
            print(f"      suggested_action: {preset.get('suggested_action')}")
        if preset.get("short_reason"):
            print(f"      short_reason: {preset.get('short_reason')}")
        if preset.get("runbook_path"):
            section = preset.get("runbook_section")
            anchor = preset.get("runbook_anchor")
            runbook_line = f"      runbook: {preset.get('runbook_path')}"
            if section:
                runbook_line += f" — {section}"
            if anchor:
                runbook_line += f" (#{anchor})"
            print(runbook_line)
        print(f"      command: {preset.get('command')}")
        print("      copy_note: Copy command manually — script/UI does not execute commands.")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")


if __name__ == "__main__":
    main()
