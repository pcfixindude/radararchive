"""Cron-friendly scheduled local validation wrapper (experimental prototype)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import MRMS_SOURCE_MODE_REAL, settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.scheduled_validation import (
    DEFAULT_SCHEDULED_COUNT,
    DEFAULT_SCHEDULED_MAX_ZOOM,
    DEFAULT_SCHEDULED_MIN_ZOOM,
    run_scheduled_validation,
)
from backend.app.services.storage import LocalStorage


def _print_report(report) -> None:
    print("Scheduled validation report (experimental prototype — NOT verified MRMS):")
    print(f"  ran_at: {report.ran_at}")
    print(f"  source_mode: {report.source_mode}")
    print(f"  success: {report.success}")
    print(f"  exit_code: {report.exit_code}")
    print(f"  effective_count: {report.effective_count}")
    print(f"  min_zoom: {report.min_zoom}")
    print(f"  max_zoom: {report.max_zoom}")
    print(f"  elapsed_seconds: {report.elapsed_seconds:.4f}")
    print("  steps:")
    for step in report.steps:
        print(f"    - {step.name}: {step.status} ({step.elapsed_seconds:.4f}s)")
    if report.batch_validation:
        batch = report.batch_validation
        print(
            f"  batch: discovered={batch.get('discovered_count', 0)} "
            f"decoded={batch.get('decoded_count', 0)}"
        )
    if report.queue_benchmark:
        queue = report.queue_benchmark
        print(
            f"  queue benchmark: jobs_succeeded={queue.get('jobs_succeeded', 0)} "
            f"tiles_written={queue.get('total_tiles_written', 0)}"
        )
    print(f"  verified_mrms: {report.verified_mrms}")
    for warning in report.warnings:
        print(f"  warning: {warning}")
    for error in report.errors:
        print(f"  error: {error}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run scheduled local validation pipeline (Phase 23 prototype)."
    )
    parser.add_argument("--real", action="store_true", help="Use real NOAA AWS mode (intentional)")
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_SCHEDULED_COUNT,
        help=f"Batch/queue frame count (default {DEFAULT_SCHEDULED_COUNT})",
    )
    parser.add_argument("--min-zoom", type=int, default=DEFAULT_SCHEDULED_MIN_ZOOM)
    parser.add_argument("--max-zoom", type=int, default=DEFAULT_SCHEDULED_MAX_ZOOM)
    parser.add_argument("--json-report", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    print(
        "WARNING: Scheduled validation is prototype tooling — not verified MRMS production.",
        file=sys.stderr,
    )
    if args.real:
        print(
            "Real mode: may download NOAA MRMS data; optional decoder required for full success.\n",
            file=sys.stderr,
        )
    else:
        print(
            "Stub/offline mode (default): safe without network. "
            "Use --real only when intentional.\n",
            file=sys.stderr,
        )

    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)
    try:
        report = run_scheduled_validation(
            session,
            storage,
            count=args.count,
            min_zoom=args.min_zoom,
            max_zoom=args.max_zoom,
            real_requested=args.real,
        )
    finally:
        session.close()

    if args.json_report:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        _print_report(report)

    raise SystemExit(report.exit_code)


if __name__ == "__main__":
    main()
