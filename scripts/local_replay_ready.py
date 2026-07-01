"""One-shot local replay setup — dry-run status by default; RUN=1 warms/decodes locally only."""

from __future__ import annotations

import argparse
import json
import os
import sys

from backend.app.database import get_session_factory, init_db
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.services.frame_cache_warmer import DEFAULT_LIMIT, MAX_LIMIT
from backend.app.services.local_replay_ready import build_local_replay_ready_plan, run_local_replay_ready
from backend.app.services.storage import LocalStorage
from backend.app.config import settings


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
        description="Check or run bounded local replay setup after ingest (no real MRMS download)."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=_env_int("LIMIT", DEFAULT_LIMIT),
        help=f"Max frames to assess/warm (default {DEFAULT_LIMIT}, max {MAX_LIMIT})",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        default=_env_bool("RUN"),
        help="Execute bounded local warm/decode steps only (Makefile: RUN=1)",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    print(
        "WARNING: Local replay setup is prototype only — NOT verified MRMS. "
        "This helper never runs real MRMS ingest/download.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    init_db()
    session = get_session_factory()()
    try:
        if catalog_is_empty(session):
            seed_demo_catalog(session, storage=storage)
        if args.run:
            report = run_local_replay_ready(session, storage, limit=args.limit, run=True)
            session.commit()
        else:
            report = build_local_replay_ready_plan(session, storage, limit=args.limit)
    finally:
        session.close()

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        if report.get("frame_count", 0) == 0:
            raise SystemExit(2)
        if args.run and not report.get("ready"):
            raise SystemExit(1)
        return

    print("Local replay setup (prototype only — NOT verified MRMS):")
    print(f"  ready: {report.get('ready')}")
    print(f"  ready_label: {report.get('ready_label')}")
    print(f"  dry_run: {report.get('dry_run')}")
    print(f"  frame_count: {report.get('frame_count')}")
    print(f"  window_source: {report.get('window_source')}")
    print(f"  decode_retry_status: {report.get('decode_retry_status')}")
    for item in report.get("checklist") or []:
        print(f"  step: {item.get('id')} [{item.get('status')}] — {item.get('message')}")
        if item.get("next_command"):
            print(f"    next: {item.get('next_command')}")
    if report.get("next_command"):
        print(f"  next_command: {report.get('next_command')}")
    if report.get("suggested_run_command"):
        print(f"  suggested_run_command: {report.get('suggested_run_command')}")
    for step in report.get("operator_steps") or []:
        print(f"  operator: {step}")
    if report.get("run_message"):
        print(f"  run_message: {report.get('run_message')}")
    for action in report.get("actions_run") or []:
        print(f"  action_run: {action.get('action')} — {action.get('status')}")

    if report.get("frame_count", 0) == 0:
        raise SystemExit(2)
    if args.run and not report.get("ready"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
