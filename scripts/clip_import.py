"""Validate imported playback clip manifest and write readiness report to data/dev/."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.services.clip_import import build_clip_import_report
from backend.app.services.storage import LocalStorage

REPORT_JSON = "dev/clip_import_latest.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a saved playback clip manifest and print readiness summary (no ingest/decode work)."
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to playback clip manifest JSON (from make playback-export or UI download)",
    )
    parser.add_argument("--json", action="store_true", help="Print report JSON to stdout")
    args = parser.parse_args()

    print(
        "WARNING: Clip import is prototype only — NOT verified MRMS. "
        "This helper never runs ingest or decode work.",
        file=sys.stderr,
    )

    manifest_path = Path(args.file)
    if not manifest_path.is_file():
        raise SystemExit(f"Manifest file not found: {manifest_path}")

    try:
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in manifest file: {exc}") from exc

    storage = LocalStorage(settings.local_storage_root)
    init_db()
    session = get_session_factory()()
    try:
        if catalog_is_empty(session):
            seed_demo_catalog(session, storage=storage)
        report = build_clip_import_report(session, storage, manifest_data)
    finally:
        session.close()

    output_path = storage.normalize_path(REPORT_JSON)
    storage.ensure_directories(storage.normalize_path("dev"))
    storage.absolute_path(output_path).write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Clip import report (prototype only — NOT verified MRMS):")
        print(f"  valid: {report.get('valid')}")
        print(f"  import_status: {report.get('import_status')}")
        if report.get("errors"):
            print(f"  errors: {', '.join(report['errors'])}")
        if report.get("warnings"):
            print(f"  warnings: {', '.join(report['warnings'])}")
        summary = report.get("readiness_summary") or {}
        print(f"  frame_count: {summary.get('frame_count')}")
        print(f"  cache_ready: {summary.get('cache_ready_count')} decode_ready: {summary.get('decode_ready_count')}")
        print(f"  problem_frames: {summary.get('problem_count')}")
        manifest = report.get("manifest") or {}
        if manifest:
            print(f"  range: {manifest.get('range_start')} → {manifest.get('range_end')}")
            print(f"  loop_suggested: {manifest.get('loop_suggested')}")
        if report.get("suggested_commands"):
            print("  suggested_commands:")
            for command in report["suggested_commands"]:
                print(f"    {command}")
        print(f"  output: {Path(storage.absolute_path(output_path))}")

    if not report.get("valid"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
