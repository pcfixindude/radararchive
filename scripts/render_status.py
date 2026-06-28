"""Report render status for catalog frames and decode artifacts."""

from __future__ import annotations

import argparse

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.render_queue import get_queue_summary
from backend.app.services.render_status import build_render_status_report, sync_catalog_render_metadata
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(description="Report tile render status (Phase 14 guardrails).")
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Sync catalog render fields from artifacts (never marks production_rendered).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --sync, report changes without writing to the catalog.",
    )
    args = parser.parse_args()

    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)

    if args.sync:
        updated = sync_catalog_render_metadata(session, storage, dry_run=args.dry_run)
        action = "would update" if args.dry_run else "updated"
        print(f"Catalog sync: {action} {updated} frame(s).")

    report = build_render_status_report(session, storage)
    queue_summary = get_queue_summary(session)

    print("Render status report:")
    print(f"  total_frames: {report.total_frames}")
    print(f"  placeholder_frames: {report.placeholder_frames}")
    print(f"  decoded_prototype_artifacts: {report.decoded_prototype_artifacts}")
    print(f"  decoded_prototype_frames: {report.decoded_prototype_frames}")
    print(f"  production_rendered_frames: {report.production_rendered_frames}")
    print(f"  production_pending_frames: {report.production_pending_frames}")
    print(f"  production_failed_frames: {report.production_failed_frames}")
    print(f"  missing_geo_metadata: {report.missing_geo_metadata}")
    print(f"  ENABLE_DECODED_TILES: {settings.enable_decoded_tiles}")
    print(f"  ENABLE_PRODUCTION_RADAR_TILES: {settings.enable_production_radar_tiles}")

    print("Render queue summary:")
    print(f"  queued: {queue_summary.queued}")
    print(f"  running: {queue_summary.running}")
    print(f"  succeeded: {queue_summary.succeeded}")
    print(f"  failed: {queue_summary.failed}")
    print(f"  canceled: {queue_summary.canceled}")
    print(f"  total_tiles_written: {queue_summary.total_tiles_written}")
    print(f"  total_output_bytes: {queue_summary.total_output_bytes}")

    for note in report.notes:
        print(f"  note: {note}")

    if report.missing_geo_metadata:
        print("\nArtifacts missing geo_metadata.json — run make decode-grib2 to regenerate.")


if __name__ == "__main__":
    main()
