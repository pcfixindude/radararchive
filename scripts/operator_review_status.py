"""Print consolidated operator review status (read-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.operator_review_status import build_operator_review_status_payload
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show consolidated operator review status (Phase 49 — local review only)."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    args = parser.parse_args()

    print(
        "WARNING: Operator review status is local consolidation only — NOT verified MRMS. "
        "Does not clear alerts, notify externally, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    payload = build_operator_review_status_payload(storage)
    status = payload.get("status") or {}

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("Operator review status (local review only — NOT verified MRMS):")
    print(f"  status_level: {status.get('status_level')}")
    print(f"  status_reason: {status.get('status_reason')}")
    print(f"  top_recommended_action: {status.get('top_recommended_action')}")
    print(f"  top_suggested_command: {status.get('top_suggested_command')}")
    print(f"  review_session_recommended: {status.get('review_session_recommended')}")
    print(f"  review_export_recommended: {status.get('review_export_recommended')}")
    print(f"  digest_regeneration_recommended: {status.get('digest_regeneration_recommended')}")
    print(f"  evidence_trend: {status.get('evidence_trend')}")
    print(f"  latest_review_session_at: {status.get('latest_review_session_at')}")
    print(f"  latest_review_export_at: {status.get('latest_review_export_at')}")
    print(f"  latest_digest_at: {status.get('latest_digest_at')}")
    print(f"  open_attention_count: {status.get('open_attention_count')}")
    print(f"  active_guidance_count: {status.get('active_guidance_count')}")
    top_guidance = status.get("top_guidance_item") or {}
    if top_guidance:
        print(f"  top_guidance: {top_guidance.get('title')} — {top_guidance.get('path')}")
        if top_guidance.get("section_label"):
            print(f"  runbook_section: {top_guidance.get('section_label')}")
        if top_guidance.get("suggested_action"):
            print(f"  suggested_action: {top_guidance.get('suggested_action')}")
    print(f"  verified_mrms: {payload.get('verified_mrms')}")


if __name__ == "__main__":
    main()
