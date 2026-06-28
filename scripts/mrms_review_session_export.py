"""Export latest MRMS proof review session to local Markdown (local-only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_review_session_export import (
    ReviewSessionExportError,
    build_review_session_export_payload,
    export_latest_review_session,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export latest MRMS proof review session to Markdown (Phase 43 — local only)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print JSON metadata payload")
    args = parser.parse_args()

    print(
        "WARNING: Review session export is local only — does NOT verify MRMS, clear alerts, "
        "enable production rendering, or notify externally.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    try:
        metadata = export_latest_review_session(storage)
    except ReviewSessionExportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json_report:
        payload = build_review_session_export_payload(storage)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("MRMS proof review session export (local export only — NOT verified MRMS):")
    print(f"  created_at: {metadata.get('created_at')}")
    print(f"  export_path: {metadata.get('export_path')}")
    print(f"  session_id: {metadata.get('session_id')}")
    print(f"  operator: {metadata.get('operator')}")
    print(f"  comparison_status: {metadata.get('comparison_status')}")
    print(f"  open_attention_count: {metadata.get('open_attention_count')}")
    print(f"  verified_mrms: {metadata.get('verified_mrms')}")
    print(f"  local_export_only: {metadata.get('local_export_only')}")
    print(f"  does_not_clear_alerts: {metadata.get('does_not_clear_alerts')}")
    print(f"  does_not_enable_production: {metadata.get('does_not_enable_production')}")


if __name__ == "__main__":
    main()
