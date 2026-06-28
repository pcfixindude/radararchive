"""Benchmark multi-zoom tile rendering through the render queue (experimental prototype)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import MRMS_SOURCE_MODE_REAL, settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.mrms_benchmark import resolve_benchmark_source_mode
from backend.app.services.render_queue_benchmark import (
    DEFAULT_MAX_ZOOM,
    DEFAULT_MIN_ZOOM,
    DEFAULT_QUEUE_BENCHMARK_COUNT,
    MAX_QUEUE_BENCHMARK_COUNT,
    run_render_queue_benchmark,
)
from backend.app.services.storage import LocalStorage


def _print_report(report) -> None:
    print("Render queue benchmark (experimental prototype — NOT verified MRMS):")
    print(f"  source_mode: {report.source_mode}")
    print(f"  effective_count: {report.effective_count}")
    print(f"  min_zoom: {report.min_zoom}")
    print(f"  max_zoom: {report.max_zoom}")
    print(f"  dry_run: {report.dry_run}")
    print(f"  jobs_enqueued: {report.jobs_enqueued}")
    print(f"  jobs_processed: {report.jobs_processed}")
    print(f"  jobs_succeeded: {report.jobs_succeeded}")
    print(f"  jobs_failed: {report.jobs_failed}")
    print(f"  total_tiles_written: {report.total_tiles_written}")
    print(f"  total_tiles_skipped: {report.total_tiles_skipped}")
    print(f"  total_output_bytes: {report.total_output_bytes}")
    print(f"  total_elapsed_seconds: {report.total_elapsed_seconds:.4f}")
    print(f"  verified_mrms: {report.verified_mrms}")
    for summary in report.job_summaries:
        print(
            f"    - job {summary.job_id} ({summary.timestamp}): "
            f"status={summary.status} tiles={summary.tiles_written} "
            f"elapsed={summary.elapsed_seconds:.4f}s"
        )
    for warning in report.warnings:
        print(f"  warning: {warning}")
    for error in report.errors:
        print(f"  error: {error}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark multi-zoom tile builds through the render queue (Phase 22)."
    )
    parser.add_argument("--real", action="store_true", help="Use real NOAA AWS mode label")
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_QUEUE_BENCHMARK_COUNT,
        help=f"Frames/jobs to benchmark (default {DEFAULT_QUEUE_BENCHMARK_COUNT}, max {MAX_QUEUE_BENCHMARK_COUNT})",
    )
    parser.add_argument("--min-zoom", type=int, default=DEFAULT_MIN_ZOOM)
    parser.add_argument("--max-zoom", type=int, default=DEFAULT_MAX_ZOOM)
    parser.add_argument("--force", action="store_true", help="Force rebuild existing tiles")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan jobs only; do not enqueue or run worker",
    )
    parser.add_argument("--json-report", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    source_mode = resolve_benchmark_source_mode(real_requested=args.real)
    print(
        "WARNING: Queue benchmark output is prototype tooling — not verified MRMS production.",
        file=sys.stderr,
    )
    if args.max_zoom > 1 or args.count > DEFAULT_QUEUE_BENCHMARK_COUNT:
        print(
            f"WARNING: Higher zoom/count increases tile volume; caps apply (max count {MAX_QUEUE_BENCHMARK_COUNT}).",
            file=sys.stderr,
        )
    if source_mode == MRMS_SOURCE_MODE_REAL:
        print(
            "Real mode label: ensure local MRMS catalog/decode artifacts exist. "
            "Network discovery is not run by this command.\n",
            file=sys.stderr,
        )
    else:
        print(
            "Stub/offline mode (default): safe without network. "
            "Use --real or MRMS_SOURCE_MODE=real when local real files exist.\n",
            file=sys.stderr,
        )

    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)
    try:
        report = run_render_queue_benchmark(
            session,
            storage,
            count=args.count,
            min_zoom=args.min_zoom,
            max_zoom=args.max_zoom,
            force=args.force,
            dry_run=args.dry_run,
            source_mode=source_mode,
        )
    finally:
        session.close()

    if args.json_report:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        _print_report(report)

    if report.errors and report.jobs_succeeded == 0 and not args.dry_run:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
