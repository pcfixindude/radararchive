"""Export local Markdown digest for proof bundle diff escalation review."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.proof_bundle_diff_escalation_digest import (
    export_proof_bundle_diff_escalation_digest,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export local escalation digest Markdown (Phase 38 — local review only)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print JSON metadata")
    args = parser.parse_args()

    print(
        "WARNING: Escalation digest is local review only — NOT verified MRMS. "
        "Does not clear alerts, enable production rendering, or send external notifications.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    metadata = export_proof_bundle_diff_escalation_digest(storage)

    if args.json_report:
        print(json.dumps(metadata, indent=2, sort_keys=True))
        return

    print("Proof bundle diff escalation digest exported (local review only — NOT verified MRMS):")
    print(f"  generated_at: {metadata.get('generated_at')}")
    print(f"  markdown_path: {metadata.get('markdown_path')}")
    print(f"  json_path: {metadata.get('json_path')}")
    print(f"  latest_escalation_level: {metadata.get('latest_escalation_level')}")
    print(f"  urgent_count: {metadata.get('urgent_count', 0)}")
    print(f"  attention_count: {metadata.get('attention_count', 0)}")
    print(f"  verified_mrms: {metadata.get('verified_mrms')}")


if __name__ == "__main__":
    main()
