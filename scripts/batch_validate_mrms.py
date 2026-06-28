"""Batch validate multiple MRMS frames (experimental prototype)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import MRMS_SOURCE_MODE_REAL, settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.mrms_batch_validation import (
    DEFAULT_BATCH_FRAME_COUNT,
    MAX_BATCH_FRAME_COUNT,
    run_mrms_batch_validation,
)
from backend.app.services.mrms_validation import resolve_validation_source_mode
from backend.app.services.storage import LocalStorage


def _print_report(report) -> None:
    print("MRMS batch validation report (experimental prototype — NOT verified MRMS):")
    print(f"  source_mode: {report.source_mode}")
    print(f"  requested_frame_count: {report.requested_frame_count}")
    print(f"  effective_frame_count: {report.effective_frame_count}")
    print(f"  discovered_count: {report.discovered_count}")
    print(f"  registered_created: {report.registered_created}")
    print(f"  downloaded_count: {report.downloaded_count}")
    print(f"  inspected_count: {report.inspected_count}")
    print(f"  decoded_count: {report.decoded_count}")
    print(f"  render_jobs_enqueued: {report.render_jobs_enqueued}")
    print(f"  worker_jobs_processed: {report.worker_jobs_processed}")
    print(f"  tiles_planned: {report.tiles_planned}")
    print(f"  tiles_written: {report.tiles_written}")
    print(f"  tiles_skipped: {report.tiles_skipped}")
    print(f"  output_bytes: {report.output_bytes}")
    print(f"  elapsed_seconds: {report.elapsed_seconds:.4f}")
    print(f"  production_rendering_enabled: {report.production_rendering_enabled}")
    print(f"  verified_mrms: {report.verified_mrms}")
    print(f"  frame_summaries: {len(report.frame_summaries)}")
    for frame in report.frame_summaries:
        print(
            f"    - {frame.timestamp}: downloaded={frame.downloaded} "
            f"inspected={frame.inspected} decoded={frame.decoded}"
        )
    for warning in report.warnings:
        print(f"  warning: {warning}")
    for error in report.errors:
        print(f"  error: {error}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch validate MRMS frames (Phase 21 prototype)."
    )
    parser.add_argument("--real", action="store_true", help="Use real NOAA AWS mode")
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_BATCH_FRAME_COUNT,
        help=f"Frames to process (default {DEFAULT_BATCH_FRAME_COUNT}, max {MAX_BATCH_FRAME_COUNT})",
    )
    parser.add_argument(
        "--product",
        default="MRMS_ReflectivityAtLowestAltitude",
        help="MRMS product name",
    )
    parser.add_argument("--run-worker", action="store_true", help="Process one queued render job")
    parser.add_argument("--json-report", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    source_mode = resolve_validation_source_mode(real_requested=args.real)
    if source_mode == MRMS_SOURCE_MODE_REAL:
        print(
            f"Real MRMS mode: network required. Processing up to {args.count} frame(s). "
            "Output is prototype — not verified production radar.\n",
            file=sys.stderr,
        )
    else:
        print(
            f"Stub/offline mode: safe without network (count={args.count}, "
            f"max {MAX_BATCH_FRAME_COUNT}). Use --real for NOAA AWS.\n",
            file=sys.stderr,
        )

    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)
    try:
        report = run_mrms_batch_validation(
            session,
            storage,
            frame_count=args.count,
            product=args.product,
            source_mode=source_mode,
            run_worker=args.run_worker,
        )
    finally:
        session.close()

    if args.json_report:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        _print_report(report)

    if report.errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
