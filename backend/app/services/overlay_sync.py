"""Time sync between catalog selection and local decoded overlay."""

from __future__ import annotations

import re
from typing import Any, Optional

from backend.app.services.render_metadata import GeoRenderMetadata
from backend.app.services.time_utils import format_utc_iso, parse_utc_iso

SYNC_MATCHED = "matched"
SYNC_MISMATCH = "mismatch"
SYNC_NO_SELECTION = "no_selection"
SYNC_NO_CANDIDATE = "no_candidate_timestamp"

_FILENAME_TS_RE = re.compile(r"(\d{8}T\d{6}Z)")


def normalize_timestamp_iso(timestamp: Optional[str]) -> Optional[str]:
    if not timestamp or not str(timestamp).strip():
        return None
    try:
        return format_utc_iso(parse_utc_iso(str(timestamp).strip()))
    except (TypeError, ValueError):
        return None


def extract_timestamp_from_raw_path(raw_path: Optional[str]) -> Optional[str]:
    if not raw_path:
        return None
    match = _FILENAME_TS_RE.search(raw_path)
    if not match:
        return None
    token = match.group(1)
    iso = f"{token[0:4]}-{token[4:6]}-{token[6:8]}T{token[9:11]}:{token[11:13]}:{token[13:15]}Z"
    return normalize_timestamp_iso(iso)


def extract_candidate_timestamp(
    *,
    pipeline: Optional[dict[str, Any]],
    decode_retry: Optional[dict[str, Any]],
    geo: Optional[GeoRenderMetadata],
    candidate_raw_path: Optional[str],
) -> Optional[str]:
    for source in (
        (pipeline or {}).get("candidate") or {},
        (decode_retry or {}).get("candidate") or {},
    ):
        ts = normalize_timestamp_iso(source.get("timestamp"))
        if ts:
            return ts
    if geo and geo.valid_timestamp:
        ts = normalize_timestamp_iso(geo.valid_timestamp)
        if ts:
            return ts
    return extract_timestamp_from_raw_path(candidate_raw_path)


def evaluate_overlay_sync(
    *,
    selected_timestamp: Optional[str],
    candidate_timestamp: Optional[str],
) -> dict[str, Any]:
    selected = normalize_timestamp_iso(selected_timestamp)
    candidate = normalize_timestamp_iso(candidate_timestamp)

    if not candidate:
        return {
            "sync_status": SYNC_NO_CANDIDATE,
            "selected_timestamp": selected,
            "candidate_timestamp": None,
            "overlay_visible": False,
            "sync_message": "No decoded candidate timestamp in local report — run make decode-retry.",
        }
    if not selected:
        return {
            "sync_status": SYNC_NO_SELECTION,
            "selected_timestamp": None,
            "candidate_timestamp": candidate,
            "overlay_visible": False,
            "sync_message": f"Select catalog frame {candidate} to show decoded overlay.",
        }
    if selected == candidate:
        return {
            "sync_status": SYNC_MATCHED,
            "selected_timestamp": selected,
            "candidate_timestamp": candidate,
            "overlay_visible": True,
            "sync_message": "Decoded overlay synced to selected catalog frame.",
        }
    return {
        "sync_status": SYNC_MISMATCH,
        "selected_timestamp": selected,
        "candidate_timestamp": candidate,
        "overlay_visible": False,
        "sync_message": (
            f"Selected frame {selected} does not match decoded candidate {candidate}. "
            "Choose the matching timestamp or run make decode-retry for the selected frame."
        ),
    }
