"""Bulk local MRMS catalog ingestion for multi-frame playback (prototype only)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from backend.app.config import MRMS_SOURCE_MODE_REAL, MRMS_SOURCE_MODE_STUB, settings
from backend.app.services.mrms_discovery import register_discovered_files
from backend.app.services.mrms_downloader import (
    DownloadResult,
    MrmsDownloadError,
    download_mrms_row,
    is_local_mrms_raw_path,
)
from backend.app.services.overlay_sync import normalize_timestamp_iso
from backend.app.services.storage import LocalStorage
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE, MrmsDiscoveredFile, MrmsDiscoveryError, discover_latest_mrms

INGEST_JSON = "dev/mrms_bulk_ingest_latest.json"
INGEST_MD = "dev/mrms_bulk_ingest_latest.md"

DEFAULT_LIMIT = 8
MAX_LIMIT = 20
MAX_DISCOVERY_LIMIT = 40

SUGGESTED_COMMAND = "make mrms-bulk-local-ingest ARGS='--real --limit 8'"
NEXT_DECODE_COMMAND = "make decode-retry"
NEXT_PLAYBACK_COMMAND = "make backend && make frontend"
NEXT_CACHE_WARM_COMMAND = "make mrms-warm-frame-cache"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_bulk_ingest_only": True,
        "does_not_enable_production": True,
        "does_not_claim_verified_mrms": True,
        "prototype": True,
    }


def plan_ingest_window(
    discoveries: list[MrmsDiscoveredFile],
    *,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
) -> list[MrmsDiscoveredFile]:
    """Select up to `limit` frames, defaulting to the latest timestamps in range."""
    bounded_limit = max(1, min(limit, MAX_LIMIT))
    rows = list(discoveries)
    rows.sort(key=lambda item: item.timestamp)

    start = normalize_timestamp_iso(start_time) if start_time else None
    end = normalize_timestamp_iso(end_time) if end_time else None

    if start:
        rows = [row for row in rows if normalize_timestamp_iso(row.timestamp) >= start]
    if end:
        rows = [row for row in rows if normalize_timestamp_iso(row.timestamp) <= end]

    if len(rows) > bounded_limit:
        rows = rows[-bounded_limit:]
    return rows


def _catalog_rows_for_discoveries(
    session: Session,
    discoveries: list[MrmsDiscoveredFile],
) -> list:
    from backend.app.models import RadarFile

    rows = []
    for item in discoveries:
        row = (
            session.query(RadarFile)
            .filter(
                RadarFile.source == MRMS_CATALOG_SOURCE,
                RadarFile.timestamp == item.timestamp,
            )
            .one_or_none()
        )
        if row is not None:
            rows.append(row)
    return rows


def run_bulk_local_ingest(
    session: Session,
    storage: LocalStorage,
    *,
    mode: str,
    product: str = "MRMS_ReflectivityAtLowestAltitude",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = DEFAULT_LIMIT,
    force: bool = False,
    discover_fn: Optional[Callable[..., list[MrmsDiscoveredFile]]] = None,
    download_fn: Optional[Callable] = None,
) -> dict[str, Any]:
    """Discover, register, and download a bounded MRMS window for local playback."""
    resolved_mode = mode.lower()
    if resolved_mode not in {MRMS_SOURCE_MODE_REAL, MRMS_SOURCE_MODE_STUB}:
        return save_bulk_ingest_report(
            storage,
            {
                "ran_at": _utc_now(),
                "ingest_status": "invalid_mode",
                "mode": mode,
                "errors": [f"Unsupported mode '{mode}'. Use --real for network ingest."],
                "suggested_command": SUGGESTED_COMMAND,
                **_safety_fields(),
            },
        )

    bounded_limit = max(1, min(limit, MAX_LIMIT))
    requested_window = {
        "start_time": normalize_timestamp_iso(start_time) if start_time else None,
        "end_time": normalize_timestamp_iso(end_time) if end_time else None,
        "limit": bounded_limit,
        "product": product,
    }

    discover = discover_fn or discover_latest_mrms
    discovery_limit = min(MAX_DISCOVERY_LIMIT, max(bounded_limit * 2, bounded_limit))

    try:
        discovered = discover(product, limit=discovery_limit, mode=resolved_mode)
    except MrmsDiscoveryError as exc:
        return save_bulk_ingest_report(
            storage,
            {
                "ran_at": _utc_now(),
                "ingest_status": "discovery_failed",
                "mode": resolved_mode,
                "requested_window": requested_window,
                "errors": [str(exc)],
                "suggested_command": SUGGESTED_COMMAND,
                **_safety_fields(),
            },
        )

    selected = plan_ingest_window(
        discovered,
        start_time=start_time,
        end_time=end_time,
        limit=bounded_limit,
    )

    registration = register_discovered_files(session, selected)
    catalog_rows = _catalog_rows_for_discoveries(session, selected)

    downloaded: list[DownloadResult] = []
    already_present: list[str] = []
    failures: list[dict[str, str]] = []
    row_downloader = download_fn or download_mrms_row

    for row in catalog_rows:
        try:
            result = row_downloader(
                session,
                storage,
                row,
                force=force,
                mode=resolved_mode,
            )
            if result.created:
                downloaded.append(result)
            else:
                already_present.append(result.timestamp)
        except MrmsDownloadError as exc:
            failures.append(
                {
                    "radar_file_id": str(row.id),
                    "timestamp": row.timestamp,
                    "error": str(exc),
                }
            )

    registered_timestamps = sorted({item.timestamp for item in selected})
    downloaded_timestamps = sorted({item.timestamp for item in downloaded})
    raw_paths = [item.raw_path for item in downloaded]
    raw_paths.extend(
        row.raw_path
        for row in catalog_rows
        if row.raw_path
        and is_local_mrms_raw_path(row.raw_path)
        and row.timestamp in already_present
    )

    ingest_status = "ok"
    if failures and downloaded:
        ingest_status = "partial"
    elif failures and not downloaded and not already_present:
        ingest_status = "failed"
    elif not selected:
        ingest_status = "no_frames"

    report = {
        "ran_at": _utc_now(),
        "ingest_status": ingest_status,
        "mode": resolved_mode,
        "requested_window": requested_window,
        "frames_discovered": len(discovered),
        "frames_selected": len(selected),
        "frames_registered_created": registration.created,
        "frames_registered_skipped": registration.skipped,
        "frames_downloaded": len(downloaded),
        "frames_already_present": len(already_present),
        "frames_failed": len(failures),
        "registered_timestamps": registered_timestamps,
        "downloaded_timestamps": downloaded_timestamps,
        "already_present_timestamps": sorted(already_present),
        "raw_paths": raw_paths,
        "failures": failures,
        "errors": [item["error"] for item in failures],
        "next_commands": [NEXT_CACHE_WARM_COMMAND, NEXT_DECODE_COMMAND, NEXT_PLAYBACK_COMMAND],
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }
    return save_bulk_ingest_report(storage, report)


def build_ingest_markdown(report: dict[str, Any]) -> str:
    window = report.get("requested_window") or {}
    lines = [
        "# MRMS bulk local ingest (prototype)",
        "",
        "> **WARNING:** Local dev bulk ingest only — NOT verified MRMS production data.",
        "",
        f"- Ran at: {report.get('ran_at')}",
        f"- Status: **{report.get('ingest_status')}**",
        f"- Mode: {report.get('mode')}",
        f"- Product: {window.get('product')}",
        f"- Window limit: {window.get('limit')}",
        f"- Start: {window.get('start_time') or '—'}",
        f"- End: {window.get('end_time') or '—'}",
        "",
        "## Counts",
        "",
        f"- Discovered: {report.get('frames_discovered')}",
        f"- Selected: {report.get('frames_selected')}",
        f"- Registered (created): {report.get('frames_registered_created')}",
        f"- Registered (skipped): {report.get('frames_registered_skipped')}",
        f"- Downloaded: {report.get('frames_downloaded')}",
        f"- Already present: {report.get('frames_already_present')}",
        f"- Failed: {report.get('frames_failed')}",
        "",
        "## Timestamps",
        "",
    ]
    for ts in report.get("registered_timestamps") or []:
        lines.append(f"- `{ts}`")
    if report.get("failures"):
        lines.extend(["", "## Failures", ""])
        for item in report["failures"]:
            lines.append(f"- {item.get('timestamp')}: {item.get('error')}")
    lines.extend(["", "## Next", ""])
    for cmd in report.get("next_commands") or []:
        lines.append(f"- `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def save_bulk_ingest_report(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
    json_path = storage.normalize_path(INGEST_JSON)
    md_path = storage.normalize_path(INGEST_MD)
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
    storage.absolute_path(md_path).write_text(build_ingest_markdown(report), encoding="utf-8")
    return report


def load_bulk_ingest_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    json_path = storage.normalize_path(INGEST_JSON)
    if not storage.path_exists(json_path):
        return None
    try:
        data = json.loads(storage.absolute_path(json_path).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None
