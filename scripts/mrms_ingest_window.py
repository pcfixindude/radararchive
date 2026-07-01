"""Guided MRMS ingest window CLI — dry-run by default; explicit --real --run to download."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

from backend.app.services.mrms_ingest_window import (
    PRESET_CUSTOM,
    PRESET_LAST_1H,
    PRESET_LAST_3H,
    PRESET_LAST_6H,
    PRESET_REPLAY_RANGE,
    build_bulk_ingest_argv,
    build_ingest_window_plan,
)


def _env_bool(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plan or run a bounded MRMS ingest window (local prototype — NOT verified MRMS)."
    )
    parser.add_argument(
        "--preset",
        default=os.environ.get("PRESET", PRESET_LAST_3H),
        choices=[PRESET_LAST_1H, PRESET_LAST_3H, PRESET_LAST_6H, PRESET_CUSTOM, PRESET_REPLAY_RANGE],
        help="Window preset (Makefile: PRESET=last_3h)",
    )
    parser.add_argument("--start", default=os.environ.get("START"), help="Custom start ISO timestamp")
    parser.add_argument("--end", default=os.environ.get("END"), help="Custom end ISO timestamp")
    parser.add_argument(
        "--replay-start",
        default=os.environ.get("REPLAY_START"),
        help="Replay range start timestamp",
    )
    parser.add_argument(
        "--replay-end",
        default=os.environ.get("REPLAY_END"),
        help="Replay range end timestamp",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=_env_int("LIMIT", 8),
        help="Max frames to ingest (bounded, default 8)",
    )
    parser.add_argument(
        "--warm-cache",
        action="store_true",
        default=_env_bool("WARM_CACHE"),
        help="Include --warm-cache on bulk ingest when running",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        default=_env_bool("RUN"),
        help="Execute bulk ingest (default is dry-run print only)",
    )
    parser.add_argument(
        "--real",
        action="store_true",
        default=_env_bool("REAL"),
        help="Required with --run for explicit real MRMS network download",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON plan")
    args = parser.parse_args()

    plan = build_ingest_window_plan(
        preset=args.preset,
        limit=args.limit,
        warm_cache=args.warm_cache,
        custom_start=args.start,
        custom_end=args.end,
        replay_start=args.replay_start,
        replay_end=args.replay_end,
    )

    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
        if not args.run:
            return
    else:
        print("MRMS ingest window plan (prototype only — NOT verified MRMS):")
        print(f"  preset: {plan['preset_label']}")
        print(f"  start: {plan.get('start_time')}")
        print(f"  end: {plan.get('end_time')}")
        print(f"  limit: {plan.get('limit')}")
        print(f"  warm_cache: {plan.get('warm_cache')}")
        print(f"  ready: {plan.get('ready')}")
        for warning in plan.get("warnings") or []:
            print(f"  warning: {warning}")
        print(f"  bulk_ingest_command: {plan.get('bulk_ingest_command')}")
        print(f"  guided_command: {plan.get('guided_command')}")
        for step in plan.get("operator_steps") or []:
            print(f"  step: {step}")
        if not args.run:
            print("  dry_run: true — re-run with --run --real to download")
            return

    if not plan.get("ready"):
        print("ERROR: Ingest window is not ready — fix warnings and try again.", file=sys.stderr)
        raise SystemExit(2)

    if not args.real:
        print(
            "ERROR: Real MRMS download requires explicit --real flag.",
            file=sys.stderr,
        )
        print(f"Dry-run command: {plan.get('bulk_ingest_command')}", file=sys.stderr)
        raise SystemExit(2)

    print(
        "WARNING: Starting bounded real MRMS download — local prototype only, NOT verified MRMS.",
        file=sys.stderr,
    )

    bulk_argv = build_bulk_ingest_argv(
        start_time=plan.get("start_time"),
        end_time=plan.get("end_time"),
        limit=plan.get("limit", 8),
        warm_cache=plan.get("warm_cache", False),
        include_real=True,
    )
    script = os.path.join(os.path.dirname(__file__), "mrms_bulk_local_ingest.py")
    cmd = [sys.executable, script, *bulk_argv]
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
