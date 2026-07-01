"""Write per-frame quality drill-down report to data/dev/ (prototype only)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.services.frame_quality_report import build_frame_quality_report
from backend.app.services.storage import LocalStorage

REPORT_JSON = "dev/frame_quality_latest.json"


def _parse_timestamps(raw: str) -> list[str]:
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not parts:
        raise SystemExit("At least one timestamp is required (--timestamps)")
    return parts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect per-frame cache/decode/quality readiness (no ingest/decode work)."
    )
    parser.add_argument(
        "--timestamps",
        required=True,
        help="Comma-separated UTC ISO timestamps to inspect",
    )
    parser.add_argument("--json", action="store_true", help="Print report JSON to stdout")
    args = parser.parse_args()

    print(
        "WARNING: Frame quality report is prototype only — NOT verified MRMS. "
        "This helper never runs ingest or decode work.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    init_db()
    session = get_session_factory()()
    try:
        if catalog_is_empty(session):
            seed_demo_catalog(session, storage=storage)
        report = build_frame_quality_report(
            session,
            storage,
            timestamps=_parse_timestamps(args.timestamps),
        )
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
        print("Frame quality report (prototype only — NOT verified MRMS):")
        print(f"  frame_count: {report.get('frame_count')}")
        print(f"  ready: {report.get('ready_count')} partial: {report.get('partial_count')}")
        print(f"  cold: {report.get('cold_count')} missing: {report.get('missing_count')}")
        print(f"  failed: {report.get('failed_count')} stub: {report.get('stub_count')}")
        print(f"  output: {storage.absolute_path(output_path)}")

    if report.get("frame_count", 0) == 0:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
