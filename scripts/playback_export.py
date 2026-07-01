"""Export bounded playback clip manifest to data/dev/ (prototype only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.services.playback_export import build_playback_export
from backend.app.services.storage import LocalStorage

EXPORT_JSON = "dev/playback_export_latest.json"


def _parse_timestamps(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    return parts or None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a bounded replay range as a local clip manifest (no ingest/decode work)."
    )
    parser.add_argument("--start", required=True, help="Range start timestamp (UTC ISO)")
    parser.add_argument("--end", required=True, help="Range end timestamp (UTC ISO)")
    parser.add_argument(
        "--timestamps",
        help="Optional comma-separated playback timestamps for frame selection",
    )
    parser.add_argument("--loop", action="store_true", help="Mark loop playback as suggested")
    parser.add_argument("--json", action="store_true", help="Print manifest JSON to stdout")
    args = parser.parse_args()

    print(
        "WARNING: Playback export is prototype only — NOT verified MRMS. "
        "This helper never runs ingest or decode work.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    init_db()
    session = get_session_factory()()
    try:
        if catalog_is_empty(session):
            seed_demo_catalog(session, storage=storage)
        manifest = build_playback_export(
            session,
            storage,
            range_start=args.start,
            range_end=args.end,
            timestamps=_parse_timestamps(args.timestamps),
            loop_suggested=args.loop,
        )
    finally:
        session.close()

    output_path = storage.normalize_path(EXPORT_JSON)
    storage.ensure_directories(storage.normalize_path("dev"))
    storage.absolute_path(output_path).write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        print("Playback clip export (prototype only — NOT verified MRMS):")
        print(f"  status: {manifest.get('status')}")
        print(f"  clip_id: {manifest.get('clip_id')}")
        print(f"  range: {manifest.get('range_start')} → {manifest.get('range_end')}")
        print(f"  frame_count: {manifest.get('frame_count')}")
        print(f"  cache_ready_count: {manifest.get('cache_ready_count')}")
        print(f"  decode_ready_count: {manifest.get('decode_ready_count')}")
        print(f"  output: {Path(storage.absolute_path(output_path))}")

    if manifest.get("status") in {"incomplete_range", "empty_range"}:
        raise SystemExit(2)
    if manifest.get("frame_count", 0) == 0:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
