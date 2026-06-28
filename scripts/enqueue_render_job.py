"""Enqueue a production tile render job (dev queue — prototype only)."""

from __future__ import annotations

import argparse
import sys

from backend.app.database import get_session_factory, init_db
from backend.app.services.render_queue import enqueue_render_job


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enqueue a production tile render job (Phase 17 — NOT verified MRMS)."
    )
    parser.add_argument("--layer", default="mrms_reflectivity")
    parser.add_argument("--timestamp", default=None, help="Optional catalog timestamp")
    parser.add_argument("--min-zoom", type=int, default=0)
    parser.add_argument("--max-zoom", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Max decode artifacts")
    parser.add_argument(
        "--mark-catalog",
        action="store_true",
        help="Mark catalog production_rendered after build (PROTOTYPE ONLY).",
    )
    args = parser.parse_args()

    if args.mark_catalog:
        print(
            "WARNING: --mark-catalog will mark matching frames production_rendered.\n"
            "         WARPING PROTOTYPE ONLY — not verified real MRMS output.\n",
            file=sys.stderr,
        )

    init_db()
    session = get_session_factory()()
    job = enqueue_render_job(
        session,
        layer=args.layer,
        timestamp=args.timestamp,
        min_zoom=args.min_zoom,
        max_zoom=args.max_zoom,
        force=args.force,
        mark_catalog=args.mark_catalog,
        artifact_limit=args.limit,
    )

    print("Render job enqueued (prototype — run make render-worker-once to process):")
    print(f"  id: {job.id}")
    print(f"  status: {job.status}")
    print(f"  layer: {job.layer}")
    print(f"  min_zoom: {job.min_zoom}")
    print(f"  max_zoom: {job.max_zoom}")
    print(f"  force: {job.force}")
    print(f"  mark_catalog: {job.mark_catalog}")


if __name__ == "__main__":
    main()
