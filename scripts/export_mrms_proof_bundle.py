"""Export local MRMS proof evidence bundle (does NOT verify MRMS)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.mrms_proof_bundle import export_mrms_proof_bundle
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export local MRMS proof evidence bundle (Phase 30 — evidence only)."
    )
    parser.add_argument(
        "--include-history",
        action="store_true",
        help="Include full proof/regression history JSON files (default: compact only)",
    )
    parser.add_argument("--no-history", action="store_true", help="Alias for default compact history")
    parser.add_argument("--json-report", action="store_true", help="Print manifest JSON")
    args = parser.parse_args()

    include_history = bool(args.include_history) and not args.no_history

    print(
        "WARNING: Proof bundle is local evidence only — NOT verified MRMS. "
        "Does not enable production rendering.",
        file=sys.stderr,
    )

    init_db()
    session_factory = get_session_factory()
    storage = LocalStorage(settings.local_storage_root)

    with session_factory() as session:
        manifest = export_mrms_proof_bundle(session, storage, include_history=include_history)

    if args.json_report:
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return

    print("MRMS proof bundle exported (local evidence only — NOT verified MRMS):")
    print(f"  bundle_id: {manifest.get('bundle_id')}")
    print(f"  created_at: {manifest.get('created_at')}")
    print(f"  bundle_folder: {manifest.get('bundle_folder')}")
    print(f"  zip_path: {manifest.get('zip_path')}")
    print(f"  file_count: {manifest.get('file_count')}")
    print(f"  files_missing: {len(manifest.get('files_missing') or [])}")
    print(f"  verified_mrms: {manifest.get('verified_mrms')}")
    print(f"  does_not_enable_production: {manifest.get('does_not_enable_production')}")
    print("  See bundle README.md for operator review notes.")


if __name__ == "__main__":
    main()
