"""Warm per-frame decode cache for smooth local playback (prototype only)."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import Layer, Product, RadarFile
from backend.app.services.catalog import MRMS_REFLECTIVITY_LAYER_ID
from backend.app.services.frame_playback import is_frame_cached
from backend.app.services.mrms_bulk_ingest import (
    DEFAULT_LIMIT as INGEST_DEFAULT_LIMIT,
    MAX_LIMIT,
    load_bulk_ingest_report,
)
from backend.app.services.mrms_downloader import is_local_mrms_raw_path
from backend.app.services.overlay_sync import normalize_timestamp_iso
from backend.app.services.raw_file_classifier import classify_raw_file, is_real_grib2_raw_kind
from backend.app.services.selected_frame_decode import (
    FRAME_CACHE_ROOT,
    FRAME_STATUS_MATCHED,
    resolve_selected_frame,
)
from backend.app.services.storage import LocalStorage
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE

CACHE_WARM_JSON = "dev/mrms_cache_warm_latest.json"
CACHE_WARM_MD = "dev/mrms_cache_warm_latest.md"

DEFAULT_LIMIT = INGEST_DEFAULT_LIMIT
SUGGESTED_COMMAND = "make mrms-warm-frame-cache"
NEXT_PLAYBACK_COMMAND = "make backend && make frontend"
BULK_INGEST_COMMAND = "make mrms-bulk-local-ingest ARGS='--real --limit 8'"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_cache_warm_only": True,
        "does_not_enable_production": True,
        "does_not_claim_verified_mrms": True,
        "prototype": True,
        "production_tile_serving": settings.enable_production_radar_tiles,
    }


def _product_ids_for_layer(session: Session, layer_id: str) -> list[str]:
    return [
        product.id
        for product in session.query(Product).filter(Product.layer_id == layer_id).all()
    ]


def list_real_local_mrms_timestamps(
    session: Session,
    storage: LocalStorage,
    *,
    layer_id: str = MRMS_REFLECTIVITY_LAYER_ID,
    product_id: Optional[str] = None,
) -> list[str]:
    """Catalog timestamps with a local real .grib2.gz raw file."""
    layer = session.get(Layer, layer_id)
    if layer is None or not layer.available:
        return []

    product_ids = _product_ids_for_layer(session, layer_id)
    if product_id:
        product_ids = [pid for pid in product_ids if pid == product_id]
    if not product_ids:
        return []

    timestamps: list[str] = []
    rows = (
        session.query(RadarFile)
        .filter(RadarFile.product_id.in_(product_ids))
        .order_by(RadarFile.timestamp.asc())
        .all()
    )
    for row in rows:
        ts = normalize_timestamp_iso(row.timestamp)
        if not ts or not row.raw_path or not storage.path_exists(row.raw_path):
            continue
        if not is_local_mrms_raw_path(row.raw_path):
            continue
        raw_kind = row.raw_kind or classify_raw_file(row)
        if not is_real_grib2_raw_kind(raw_kind):
            continue
        if row.raw_path.endswith(".stub"):
            continue
        timestamps.append(ts)

    raw_dir = storage.normalize_path("raw/mrms/reflectivity")
    abs_dir = storage.absolute_path(raw_dir)
    if abs_dir.is_dir():
        from backend.app.services.overlay_sync import extract_timestamp_from_raw_path

        for path in abs_dir.iterdir():
            if not path.name.endswith(".grib2.gz") or path.name.endswith(".stub"):
                continue
            ts = extract_timestamp_from_raw_path(storage.normalize_path(raw_dir, path.name))
            if ts and ts not in timestamps:
                timestamps.append(ts)

    timestamps.sort()
    return timestamps


def select_cache_window(
    session: Session,
    storage: LocalStorage,
    *,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    product_id: Optional[str] = None,
    real_only: bool = True,
) -> tuple[list[str], str]:
    """Choose bounded timestamps for cache warming; prefer latest bulk ingest report."""
    bounded_limit = max(1, min(limit, MAX_LIMIT))
    source = "catalog_real_local"

    ingest = load_bulk_ingest_report(storage)
    candidates: list[str] = []
    if ingest:
        candidates = list(ingest.get("downloaded_timestamps") or [])
        if not candidates:
            candidates = list(ingest.get("registered_timestamps") or [])
        if candidates:
            source = "bulk_ingest_report"

    if not candidates:
        candidates = list_real_local_mrms_timestamps(
            session,
            storage,
            product_id=product_id,
        )

    if real_only:
        real_set = set(
            list_real_local_mrms_timestamps(session, storage, product_id=product_id)
        )
        candidates = [ts for ts in candidates if ts in real_set]

    candidates = sorted({normalize_timestamp_iso(ts) for ts in candidates if normalize_timestamp_iso(ts)})

    start = normalize_timestamp_iso(start_time) if start_time else None
    end = normalize_timestamp_iso(end_time) if end_time else None
    if start:
        candidates = [ts for ts in candidates if ts >= start]
    if end:
        candidates = [ts for ts in candidates if ts <= end]

    if len(candidates) > bounded_limit:
        candidates = candidates[-bounded_limit:]

    return candidates, source


def compact_cache_warm_status(storage: LocalStorage) -> dict[str, Any]:
    report = load_cache_warm_report(storage)
    if report is None:
        return {
            "cache_warm_available": False,
            "cache_warm_status": None,
            "cache_warm_matched": 0,
            "cache_warm_considered": 0,
            "playback_ready": False,
        }
    matched = int(report.get("frames_matched") or 0)
    considered = int(report.get("frames_considered") or 0)
    return {
        "cache_warm_available": True,
        "cache_warm_status": report.get("warm_status"),
        "cache_warm_matched": matched,
        "cache_warm_considered": considered,
        "playback_ready": matched > 0 and report.get("warm_status") in {"ok", "partial"},
        "cache_warm_ran_at": report.get("ran_at"),
        "cache_warm_json_path": report.get("json_path"),
    }


def run_cache_warm(
    session: Session,
    storage: LocalStorage,
    *,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    product_id: Optional[str] = None,
    force: bool = False,
    real_only: bool = True,
    resolve_fn: Optional[Callable[..., dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Decode/build preview+tiles for a bounded timestamp window into frame cache."""
    started = time.monotonic()
    bounded_limit = max(1, min(limit, MAX_LIMIT))
    requested_window = {
        "start_time": normalize_timestamp_iso(start_time) if start_time else None,
        "end_time": normalize_timestamp_iso(end_time) if end_time else None,
        "limit": bounded_limit,
        "product_id": product_id or "mrms_reflectivity",
        "real_only": real_only,
        "force": force,
    }

    timestamps, window_source = select_cache_window(
        session,
        storage,
        start_time=start_time,
        end_time=end_time,
        limit=bounded_limit,
        product_id=product_id,
        real_only=real_only,
    )

    if not timestamps:
        return save_cache_warm_report(
            storage,
            {
                "ran_at": _utc_now(),
                "warm_status": "no_frames",
                "window_source": window_source,
                "requested_window": requested_window,
                "frames_considered": 0,
                "frames_already_cached": 0,
                "frames_decoded": 0,
                "frames_failed": 0,
                "frames_matched": 0,
                "errors": ["No real local MRMS timestamps found for cache warming."],
                "next_commands": [BULK_INGEST_COMMAND, SUGGESTED_COMMAND, NEXT_PLAYBACK_COMMAND],
                "suggested_command": SUGGESTED_COMMAND,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                **_safety_fields(),
            },
        )

    resolver = resolve_fn or resolve_selected_frame
    already_cached: list[str] = []
    decoded: list[str] = []
    failed: list[dict[str, str]] = []
    cache_paths: list[str] = []

    for ts in timestamps:
        if not force and is_frame_cached(storage, ts):
            already_cached.append(ts)
            cached_manifest = storage.normalize_path(
                "dev/mrms_frame_cache",
                ts.replace(":", "").replace("-", ""),
                "frame_manifest.json",
            )
            cache_paths.append(cached_manifest)
            continue

        result = resolver(session, storage, ts, force_refresh=force)
        status = result.get("frame_status")
        cache_dir = result.get("cache_dir") or result.get("manifest_path")
        if cache_dir:
            cache_paths.append(str(cache_dir))

        if status == FRAME_STATUS_MATCHED:
            decoded.append(ts)
        else:
            failed.append(
                {
                    "timestamp": ts,
                    "frame_status": str(status),
                    "message": result.get("sync_message") or result.get("decode_error") or status,
                }
            )

    frames_matched = len(already_cached) + len(decoded)
    warm_status = "ok"
    if failed and frames_matched:
        warm_status = "partial"
    elif failed and not frames_matched:
        warm_status = "failed"

    report = {
        "ran_at": _utc_now(),
        "warm_status": warm_status,
        "window_source": window_source,
        "requested_window": requested_window,
        "frames_considered": len(timestamps),
        "frames_already_cached": len(already_cached),
        "frames_decoded": len(decoded),
        "frames_failed": len(failed),
        "frames_matched": frames_matched,
        "considered_timestamps": timestamps,
        "already_cached_timestamps": already_cached,
        "decoded_timestamps": decoded,
        "failed_frames": failed,
        "cache_root": FRAME_CACHE_ROOT,
        "cache_paths": cache_paths[:20],
        "errors": [item["message"] for item in failed],
        "next_commands": [NEXT_PLAYBACK_COMMAND],
        "suggested_command": SUGGESTED_COMMAND,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        **_safety_fields(),
    }
    return save_cache_warm_report(storage, report)


def build_cache_warm_markdown(report: dict[str, Any]) -> str:
    window = report.get("requested_window") or {}
    lines = [
        "# MRMS frame cache warm (prototype)",
        "",
        "> **WARNING:** Local dev cache warming only — NOT verified MRMS production rendering.",
        "",
        f"- Ran at: {report.get('ran_at')}",
        f"- Status: **{report.get('warm_status')}**",
        f"- Window source: {report.get('window_source')}",
        f"- Elapsed: {report.get('elapsed_seconds')}s",
        f"- Limit: {window.get('limit')}",
        f"- Start: {window.get('start_time') or '—'}",
        f"- End: {window.get('end_time') or '—'}",
        "",
        "## Counts",
        "",
        f"- Considered: {report.get('frames_considered')}",
        f"- Already cached: {report.get('frames_already_cached')}",
        f"- Decoded: {report.get('frames_decoded')}",
        f"- Matched total: {report.get('frames_matched')}",
        f"- Failed: {report.get('frames_failed')}",
        "",
        "## Timestamps",
        "",
    ]
    for ts in report.get("considered_timestamps") or []:
        lines.append(f"- `{ts}`")
    if report.get("failed_frames"):
        lines.extend(["", "## Failures", ""])
        for item in report["failed_frames"]:
            lines.append(f"- {item.get('timestamp')}: {item.get('message')}")
    lines.extend(["", "## Next", ""])
    for cmd in report.get("next_commands") or []:
        lines.append(f"- `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def save_cache_warm_report(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
    json_path = storage.normalize_path(CACHE_WARM_JSON)
    md_path = storage.normalize_path(CACHE_WARM_MD)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    report = {
        **report,
        "json_path": json_path,
        "markdown_path": md_path,
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(build_cache_warm_markdown(report), encoding="utf-8")
    return report


def load_cache_warm_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    json_path = storage.normalize_path(CACHE_WARM_JSON)
    if not storage.path_exists(json_path):
        return None
    try:
        data = json.loads(storage.absolute_path(json_path).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None
