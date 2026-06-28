"""Validate experimental MRMS pipeline end-to-end (prototype — not verified production)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import MRMS_SOURCE_MODE_REAL, settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.mrms_batch_validation import MAX_BATCH_FRAME_COUNT, run_mrms_batch_validation
from backend.app.services.mrms_validation import resolve_validation_source_mode, run_mrms_validation
from backend.app.services.storage import LocalStorage


def _print_report(report) -> None:
    if getattr(report, "batch", False):
        print("MRMS batch validation report (experimental prototype — NOT verified MRMS):")
        print(f"  source_mode: {report.source_mode}")
        print(f"  effective_frame_count: {report.effective_frame_count}")
        print(f"  discovered_count: {report.discovered_count}")
        print(f"  downloaded_count: {report.downloaded_count}")
        print(f"  decoded_count: {report.decoded_count}")
        print(f"  elapsed_seconds: {report.elapsed_seconds:.4f}")
        print(f"  verified_mrms: {report.verified_mrms}")
        for warning in report.warnings:
            print(f"  warning: {warning}")
        for error in report.errors:
            print(f"  error: {error}")
        return

    print("MRMS validation report (experimental prototype — NOT verified MRMS):")
    print(f"  source_mode: {report.source_mode}")
    print(f"  discovered_count: {report.discovered_count}")
    print(f"  registered_created: {report.registered_created}")
    print(f"  registered_skipped: {report.registered_skipped}")
    print(f"  downloaded_count: {report.downloaded_count}")
    print(f"  download_skipped: {report.download_skipped}")
    print(f"  inspected_count: {report.inspected_count}")
    print(f"  decoded_count: {report.decoded_count}")
    print(f"  render_jobs_enqueued: {report.render_jobs_enqueued}")
    print(f"  worker_jobs_processed: {report.worker_jobs_processed}")
    print(f"  stale_jobs_recovered: {report.stale_jobs_recovered}")
    print(f"  decoder_available: {report.decoder_available}")
    print(f"  production_rendering_enabled: {report.production_rendering_enabled}")
    print(f"  verified_mrms: {report.verified_mrms}")
    tile = report.tile_cache
    print("  tile_cache:")
    print(f"    tiles_written: {tile.tiles_written}")
    print(f"    tiles_skipped: {tile.tiles_skipped}")
    print(f"    output_bytes: {tile.output_bytes}")
    print(f"    job_id: {tile.job_id}")
    print(f"    job_status: {tile.job_status}")
    for warning in report.warnings:
        print(f"  warning: {warning}")
    for error in report.errors:
        print(f"  error: {error}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate MRMS discover/download/decode/render pipeline (Phase 19 prototype)."
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use real NOAA AWS mode (or set MRMS_SOURCE_MODE=real)",
    )
    parser.add_argument("--limit", type=int, default=1, help="Max frames (default 1)")
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help=f"Alias for --limit; values >1 use batch validation (max {MAX_BATCH_FRAME_COUNT})",
    )
    parser.add_argument(
        "--product",
        default="MRMS_ReflectivityAtLowestAltitude",
        help="MRMS product name",
    )
    parser.add_argument(
        "--run-worker",
        action="store_true",
        help="Process one queued render job after enqueue",
    )
    parser.add_argument("--json-report", action="store_true", help="Print JSON report to stdout")
    args = parser.parse_args()
    frame_count = args.count if args.count is not None else args.limit

    source_mode = resolve_validation_source_mode(real_requested=args.real)
    if source_mode == MRMS_SOURCE_MODE_REAL:
        print(
            "Real MRMS mode: network required for NOAA AWS download. "
            "Output remains prototype — not verified production radar.\n",
            file=sys.stderr,
        )
    else:
        print(
            "Stub/offline mode (default): safe without network. "
            "Use --real or MRMS_SOURCE_MODE=real for NOAA AWS validation.\n",
            file=sys.stderr,
        )

    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)
    try:
        if frame_count > 1:
            report = run_mrms_batch_validation(
                session,
                storage,
                frame_count=frame_count,
                product=args.product,
                source_mode=source_mode,
                run_worker=args.run_worker,
            )
        else:
            report = run_mrms_validation(
                session,
                storage,
                product=args.product,
                limit=1,
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
