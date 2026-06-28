"""Benchmark one MRMS frame with per-stage timing (experimental prototype)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import MRMS_SOURCE_MODE_REAL, settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.mrms_benchmark import resolve_benchmark_source_mode, run_mrms_benchmark
from backend.app.services.storage import LocalStorage


def _print_report(report) -> None:
    print("MRMS benchmark report (experimental prototype — NOT verified MRMS):")
    print(f"  source_mode: {report.source_mode}")
    print(f"  min_zoom: {report.min_zoom}")
    print(f"  max_zoom: {report.max_zoom}")
    print("  stage_timings:")
    for timing in report.stage_timings:
        print(f"    - {timing.stage}: {timing.elapsed_seconds:.4f}s")
    print(f"  tiles_planned: {report.tiles_planned}")
    print(f"  tiles_written: {report.tiles_written}")
    print(f"  tiles_skipped: {report.tiles_skipped}")
    print(f"  output_bytes: {report.output_bytes}")
    print(f"  tile_build_elapsed_seconds: {report.tile_build_elapsed_seconds:.4f}")
    print(f"  decoder_used: {report.decoder_used}")
    print(f"  verified_mrms: {report.verified_mrms}")
    for warning in report.warnings:
        print(f"  warning: {warning}")
    for error in report.errors:
        print(f"  error: {error}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark MRMS pipeline stages for one frame (Phase 20 prototype)."
    )
    parser.add_argument("--real", action="store_true", help="Use real NOAA AWS mode")
    parser.add_argument("--limit", type=int, default=1, help="Max frames (default 1)")
    parser.add_argument("--min-zoom", type=int, default=0)
    parser.add_argument("--max-zoom", type=int, default=0)
    parser.add_argument(
        "--product",
        default="MRMS_ReflectivityAtLowestAltitude",
        help="MRMS product name",
    )
    parser.add_argument("--json-report", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    source_mode = resolve_benchmark_source_mode(real_requested=args.real)
    if source_mode == MRMS_SOURCE_MODE_REAL:
        print(
            "Real MRMS mode: network required. Benchmark output is prototype — not verified MRMS.\n",
            file=sys.stderr,
        )
    else:
        print(
            "Stub/offline mode (default): safe without network. "
            "Use --real for NOAA AWS benchmark.\n",
            file=sys.stderr,
        )

    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)
    try:
        report = run_mrms_benchmark(
            session,
            storage,
            product=args.product,
            limit=args.limit,
            source_mode=source_mode,
            min_zoom=args.min_zoom,
            max_zoom=args.max_zoom,
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
