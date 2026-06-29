"""Local MRMS render candidate sandbox manifest import/export."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox_import_export import (
    SUGGESTED_EXPORT_COMMAND,
    SUGGESTED_IMPORT_EXPORT_COMMAND,
    build_render_candidate_sandbox_import_export_payload,
    compact_render_candidate_sandbox_import_export,
    export_candidate_sandbox_manifest,
    import_candidate_sandbox_manifest,
    run_import_export_workflow,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Local MRMS render candidate sandbox manifest import/export (Phase 66)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON status report")
    parser.add_argument("--export", action="store_true", help="Generate local export manifest/report")
    parser.add_argument("--import", dest="do_import", action="store_true", help="Validate/import export manifest")
    parser.add_argument(
        "--import-from",
        dest="import_from",
        default=None,
        help="Optional export JSON path to import (defaults to latest export)",
    )
    args = parser.parse_args()

    print(
        "WARNING: Sandbox manifest import/export is local metadata only — NOT verified MRMS. "
        "Does not download, decode, render, serve production tiles, clear alerts, or authorize production use.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    if args.export and args.do_import:
        result = run_import_export_workflow(storage, export=True, import_after_export=True)
    elif args.export:
        result = export_candidate_sandbox_manifest(storage)
    elif args.do_import:
        result = import_candidate_sandbox_manifest(storage, source_json_path=args.import_from)
    else:
        result = build_render_candidate_sandbox_import_export_payload(storage)["latest"]

    if args.json_report:
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    compact = compact_render_candidate_sandbox_import_export(storage)
    print("MRMS render candidate sandbox import/export (local metadata only — NOT verified MRMS):")
    print(f"  import_export_status: {result.get('import_export_status')}")
    print(f"  schema_version: {result.get('schema_version') or compact.get('schema_version')}")
    print(f"  latest_export_json_path: {compact.get('latest_export_json_path')}")
    print(f"  latest_import_json_path: {compact.get('latest_import_json_path')}")
    print(f"  missing_inputs: {len(compact.get('missing_inputs') or [])}")
    print(f"  blockers: {len(compact.get('blockers') or [])}")
    print(f"  warnings: {len(compact.get('warnings') or [])}")
    print(f"  suggested_export_command: {compact.get('suggested_export_command') or SUGGESTED_EXPORT_COMMAND}")
    print(
        "  suggested_import_export_command: "
        f"{compact.get('suggested_import_export_command') or SUGGESTED_IMPORT_EXPORT_COMMAND}"
    )
    print(f"  verified_mrms: {result.get('verified_mrms')}")


if __name__ == "__main__":
    main()
