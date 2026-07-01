"""Build bounded remediation plan from clip import report or manifest — writes data/dev/."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.services.clip_import import build_clip_import_report
from backend.app.services.clip_remediation import (
    REPORT_JSON,
    build_clip_remediation_plan,
    is_clip_import_report,
    is_clip_manifest,
)
from backend.app.services.storage import LocalStorage


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Expected JSON object in {path}")
    return data


def _resolve_import_report(session, storage, data: dict) -> dict:
    if is_clip_import_report(data):
        if data.get("valid") is None and data.get("manifest") is not None:
            return build_clip_import_report(session, storage, data["manifest"])
        return data
    if is_clip_manifest(data):
        return build_clip_import_report(session, storage, data)
    raise SystemExit(
        "File is neither a clip import report nor a playback clip manifest "
        "(expected import_status/problem_frames or export_kind=playback_clip_manifest)."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build bounded warm/decode remediation plan from clip import report or manifest."
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to clip import report JSON or playback clip manifest JSON",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=8,
        help="Max problem frames to assess for commands (default 8, max 20)",
    )
    parser.add_argument("--json", action="store_true", help="Print plan JSON to stdout")
    args = parser.parse_args()

    print(
        "WARNING: Clip remediation plan is prototype only — NOT verified MRMS. "
        "Commands are NOT auto-run.",
        file=sys.stderr,
    )

    input_path = Path(args.file)
    if not input_path.is_file():
        raise SystemExit(f"Input file not found: {input_path}")

    data = _load_json(input_path)
    storage = LocalStorage(settings.local_storage_root)
    init_db()
    session = get_session_factory()()
    try:
        if catalog_is_empty(session):
            seed_demo_catalog(session, storage=storage)
        import_report = _resolve_import_report(session, storage, data)
        plan = build_clip_remediation_plan(import_report, limit=args.limit)
    finally:
        session.close()

    output_path = storage.normalize_path(REPORT_JSON)
    storage.ensure_directories(storage.normalize_path("dev"))
    storage.absolute_path(output_path).write_text(
        json.dumps(plan, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print("Clip remediation plan (prototype only — NOT verified MRMS):")
        print(f"  plan_status: {plan.get('plan_status')}")
        summary = plan.get("group_summary") or {}
        print(
            f"  problems: total={summary.get('total_problem_count')} "
            f"cold={summary.get('cold_count')} missing={summary.get('missing_count')} "
            f"failed={summary.get('failed_count')}"
        )
        print(f"  commands: {len(plan.get('commands') or [])} step(s)")
        print(f"  truncated: {plan.get('truncated')}")
        print(f"  output: {Path(storage.absolute_path(output_path))}")
        if plan.get("command_block"):
            print("")
            print(plan["command_block"])

    if plan.get("plan_status") == "invalid":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
