"""Process one queued render job (local dev worker)."""

from __future__ import annotations

import argparse
import json

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.storage import LocalStorage
from backend.app.workers.render_worker import process_next_render_job


def main() -> None:
    parser = argparse.ArgumentParser(description="Process one queued render job (Phase 17 worker).")
    parser.add_argument("--json-report", action="store_true", help="Print job JSON to stdout")
    args = parser.parse_args()

    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)

    job = process_next_render_job(session, storage)
    if job is None:
        print("No queued render jobs.")
        return

    if args.json_report:
        payload = {
            "id": job.id,
            "status": job.status,
            "progress_current": job.progress_current,
            "progress_total": job.progress_total,
            "tiles_written": job.tiles_written,
            "tiles_skipped": job.tiles_skipped,
            "output_bytes": job.output_bytes,
            "error_message": job.error_message,
            "prototype": True,
            "verified_mrms": False,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("Render worker complete (prototype — NOT verified MRMS):")
        print(f"  id: {job.id}")
        print(f"  status: {job.status}")
        print(f"  progress: {job.progress_current}/{job.progress_total}")
        print(f"  tiles_written: {job.tiles_written}")
        print(f"  tiles_skipped: {job.tiles_skipped}")
        print(f"  output_bytes: {job.output_bytes}")
        if job.error_message:
            print(f"  error: {job.error_message}")


if __name__ == "__main__":
    main()
