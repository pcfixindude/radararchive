"""Generate local candidate review readiness summary (Phase 87)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_review_readiness import (
    SUGGESTED_COMMAND,
    build_candidate_review_readiness_payload,
    compact_candidate_review_readiness,
    generate_candidate_review_readiness,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate local candidate review readiness summary (Phase 87)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Persist JSON/Markdown readiness summary under data/dev/",
    )
    args = parser.parse_args()

    print(
        "WARNING: Candidate review readiness is local advisory guidance only — NOT verified MRMS. "
        "Does not download, decode, render production tiles, clear alerts, or enable production rendering.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.refresh:
        report = generate_candidate_review_readiness(storage)
    else:
        report = build_candidate_review_readiness_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    compact = compact_candidate_review_readiness(storage)
    print("Candidate review readiness (local advisory only — NOT verified MRMS):")
    print(f"  chain_readiness_level: {compact.get('chain_readiness_level')}")
    print(f"  overall_readiness_level: {compact.get('overall_readiness_level')}")
    print(f"  review_chain_ready: {compact.get('review_chain_ready')}")
    print(f"  gated_preflight_still_blocked: {compact.get('gated_preflight_still_blocked')}")
    print(f"  next_operator_step: {compact.get('next_operator_step')}")
    print(f"  regeneration_recommended: {compact.get('regeneration_recommended')}")
    if compact.get("regeneration_reason"):
        print(f"  regeneration_reason: {compact.get('regeneration_reason')}")
    if args.refresh:
        print(f"  markdown_path: {report.get('markdown_path')}")
    print(f"  suggested_command: {SUGGESTED_COMMAND}")


if __name__ == "__main__":
    main()
