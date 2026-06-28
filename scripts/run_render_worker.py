"""Process render jobs — one-shot or continuous local worker loop."""

from __future__ import annotations

import argparse
import json

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.storage import LocalStorage
from backend.app.workers.render_worker import process_next_render_job, run_worker_loop


def _print_job(job, *, json_report: bool) -> None:
    if json_report:
        payload = {
            "id": job.id,
            "status": job.status,
            "attempt_count": job.attempt_count,
            "max_attempts": job.max_attempts,
            "progress_current": job.progress_current,
            "progress_total": job.progress_total,
            "tiles_written": job.tiles_written,
            "tiles_skipped": job.tiles_skipped,
            "output_bytes": job.output_bytes,
            "error_message": job.error_message,
            "next_retry_at": job.next_retry_at,
            "prototype": True,
            "verified_mrms": False,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("Render worker complete (prototype — NOT verified MRMS):")
        print(f"  id: {job.id}")
        print(f"  status: {job.status}")
        print(f"  attempt: {job.attempt_count}/{job.max_attempts}")
        print(f"  progress: {job.progress_current}/{job.progress_total}")
        print(f"  tiles_written: {job.tiles_written}")
        print(f"  tiles_skipped: {job.tiles_skipped}")
        print(f"  output_bytes: {job.output_bytes}")
        if job.error_message:
            print(f"  error: {job.error_message}")
        if job.next_retry_at:
            print(f"  next_retry_at: {job.next_retry_at}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Process render jobs (Phase 18 worker).")
    parser.add_argument("--once", action="store_true", help="Process one job then exit")
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=100,
        help="Max jobs to process in continuous mode (default 100)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        help="Sleep seconds when queue is empty (continuous mode)",
    )
    parser.add_argument("--json-report", action="store_true", help="Print last job JSON to stdout")
    args = parser.parse_args()

    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)

    if args.once:
        job = process_next_render_job(session, storage)
        if job is None:
            print("No queued render jobs.")
            return
        _print_job(job, json_report=args.json_report)
        return

    print(
        f"Render worker loop starting (prototype — max_jobs={args.max_jobs}, sleep={args.sleep}s)"
    )
    processed = run_worker_loop(
        session,
        storage,
        max_jobs=args.max_jobs,
        sleep_seconds=args.sleep,
    )
    print(f"Render worker loop finished: processed {processed} job(s).")


if __name__ == "__main__":
    main()
