"""Validate and assess imported playback clip manifests (prototype only)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.frame_quality_report import (
    READINESS_COLD,
    READINESS_FAILED,
    READINESS_INVALID,
    READINESS_MISSING,
    READINESS_PARTIAL,
    READINESS_READY,
    READINESS_STUB,
    build_frame_quality_report,
)
from backend.app.services.overlay_sync import normalize_timestamp_iso
from backend.app.services.playback_export import EXPORT_KIND, MAX_CLIP_FRAMES
from backend.app.services.storage import LocalStorage

IMPORT_STATUS_INVALID = "invalid"
IMPORT_STATUS_READY = "ready"
IMPORT_STATUS_PARTIAL = "partial"
IMPORT_STATUS_EMPTY = "empty"

PROBLEM_READINESS = {
    READINESS_COLD,
    READINESS_MISSING,
    READINESS_FAILED,
    READINESS_STUB,
    READINESS_PARTIAL,
    READINESS_INVALID,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_dev_only": True,
        "prototype": True,
        "production_tile_serving": settings.enable_production_radar_tiles,
        "status_only": True,
        "does_not_run_ingest": True,
        "does_not_run_decode": True,
    }


def _dedupe_commands(commands: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for command in commands:
        if command and command not in seen:
            seen.add(command)
            result.append(command)
    return result


def _coerce_manifest_dict(data: Any) -> tuple[Optional[dict[str, Any]], list[str]]:
    if not isinstance(data, dict):
        return None, ["Manifest must be a JSON object."]
    return data, []


def validate_clip_manifest(data: Any) -> tuple[Optional[dict[str, Any]], list[str], list[str]]:
    """Parse and validate exported clip manifest shape.

    Returns (normalized_manifest, errors, warnings).
    """
    raw, errors = _coerce_manifest_dict(data)
    if raw is None:
        return None, errors, []

    warnings: list[str] = []

    export_kind = raw.get("export_kind")
    if export_kind != EXPORT_KIND:
        errors.append(f"export_kind must be {EXPORT_KIND!r}.")

    if raw.get("verified_mrms") is True:
        errors.append("Manifest claims verified_mrms=true — rejected for local prototype import.")

    range_start = normalize_timestamp_iso(str(raw.get("range_start") or ""))
    range_end = normalize_timestamp_iso(str(raw.get("range_end") or ""))
    if not range_start:
        errors.append("range_start is missing or not a valid UTC ISO timestamp.")
    if not range_end:
        errors.append("range_end is missing or not a valid UTC ISO timestamp.")

    frames_raw = raw.get("frames")
    if frames_raw is None:
        warnings.append("frames list missing — import will use range endpoints only.")
        frames_raw = []
    elif not isinstance(frames_raw, list):
        errors.append("frames must be a list.")
        frames_raw = []

    normalized_frames: list[dict[str, Any]] = []
    if isinstance(frames_raw, list):
        for index, frame in enumerate(frames_raw):
            if not isinstance(frame, dict):
                errors.append(f"frames[{index}] must be an object.")
                continue
            ts = normalize_timestamp_iso(str(frame.get("timestamp") or ""))
            if not ts:
                errors.append(f"frames[{index}].timestamp is missing or invalid.")
                continue
            normalized_frames.append(
                {
                    "timestamp": ts,
                    "index": int(frame.get("index", index)),
                    "cache_state": str(frame.get("cache_state") or "unknown"),
                    "cache_ready": bool(frame.get("cache_ready")),
                    "decode_ready": bool(frame.get("decode_ready")),
                    "decode_status": frame.get("decode_status"),
                    "preview_paths": list(frame.get("preview_paths") or []),
                    "preview_path_count": int(frame.get("preview_path_count") or 0),
                }
            )

    if len(normalized_frames) > MAX_CLIP_FRAMES:
        warnings.append(
            f"Manifest lists {len(normalized_frames)} frames — only first {MAX_CLIP_FRAMES} will be assessed."
        )
        normalized_frames = normalized_frames[:MAX_CLIP_FRAMES]

    if errors:
        return None, errors, warnings

    normalized: dict[str, Any] = {
        "clip_id": str(raw.get("clip_id") or ""),
        "export_kind": EXPORT_KIND,
        "layer_id": str(raw.get("layer_id") or "mrms_reflectivity"),
        "range_start": range_start,
        "range_end": range_end,
        "range_order_adjusted": bool(raw.get("range_order_adjusted")),
        "loop_suggested": bool(raw.get("loop_suggested")),
        "frame_count": len(normalized_frames) or int(raw.get("frame_count") or 0),
        "cache_ready_count": int(raw.get("cache_ready_count") or 0),
        "decode_ready_count": int(raw.get("decode_ready_count") or 0),
        "missing_cache_count": int(raw.get("missing_cache_count") or 0),
        "cold_count": int(raw.get("cold_count") or 0),
        "failed_count": int(raw.get("failed_count") or 0),
        "frames": normalized_frames,
        "exported_at": str(raw.get("exported_at") or ""),
        "status": str(raw.get("status") or "ready"),
    }

    if not normalized["clip_id"]:
        normalized["clip_id"] = f"clip_import_{range_start}_{range_end}"

    if normalized["exported_at"]:
        warnings.append("Readiness counts are refreshed against current local cache/decode state.")

    return normalized, [], warnings


def _resolve_import_status(
    *,
    valid: bool,
    frame_count: int,
    problem_count: int,
) -> str:
    if not valid:
        return IMPORT_STATUS_INVALID
    if frame_count == 0:
        return IMPORT_STATUS_EMPTY
    if problem_count == 0:
        return IMPORT_STATUS_READY
    return IMPORT_STATUS_PARTIAL


def build_clip_import_report(
    session: Session,
    storage: LocalStorage,
    manifest_data: Any,
) -> dict[str, Any]:
    """Validate imported clip manifest and refresh readiness summary — status only."""
    normalized, errors, warnings = validate_clip_manifest(manifest_data)
    if normalized is None:
        return {
            "valid": False,
            "import_status": IMPORT_STATUS_INVALID,
            "errors": errors,
            "warnings": warnings,
            "manifest": None,
            "readiness_summary": {
                "frame_count": 0,
                "cache_ready_count": 0,
                "decode_ready_count": 0,
                "missing_count": 0,
                "cold_count": 0,
                "failed_count": 0,
                "stub_count": 0,
                "partial_count": 0,
                "problem_count": 0,
            },
            "problem_frames": [],
            "suggested_commands": [],
            "assessed_at": _utc_now(),
            **_safety_fields(),
        }

    timestamps = [frame["timestamp"] for frame in normalized["frames"]]
    if not timestamps:
        timestamps = [normalized["range_start"], normalized["range_end"]]

    quality_report = build_frame_quality_report(
        session,
        storage,
        timestamps=timestamps,
        layer_id=normalized["layer_id"],
    )

    quality_by_ts = {frame["timestamp"]: frame for frame in quality_report.get("frames") or []}

    problem_frames: list[dict[str, Any]] = []
    suggested_commands: list[str] = []
    cache_ready_count = 0
    decode_ready_count = 0

    for frame in normalized["frames"]:
        ts = frame["timestamp"]
        quality = quality_by_ts.get(ts)
        if quality:
            readiness = quality.get("readiness_summary") or READINESS_INVALID
            cache_state = quality.get("cache_state") or frame["cache_state"]
            decode_ready = bool(quality.get("decode_ready"))
            sync_message = quality.get("sync_message")
            suggested_commands.extend(quality.get("suggested_commands") or [])
        else:
            readiness = READINESS_INVALID
            cache_state = frame["cache_state"]
            decode_ready = frame["decode_ready"]
            sync_message = "Frame not assessed — outside quality report limit."

        if quality and quality.get("cache_ready"):
            cache_ready_count += 1
        if decode_ready:
            decode_ready_count += 1

        if readiness in PROBLEM_READINESS:
            problem_frames.append(
                {
                    "timestamp": ts,
                    "readiness_summary": readiness,
                    "cache_state": cache_state,
                    "decode_ready": decode_ready,
                    "sync_message": sync_message,
                }
            )

    frame_count = len(normalized["frames"]) or quality_report.get("frame_count") or 0
    problem_count = len(problem_frames)

    readiness_summary = {
        "frame_count": frame_count,
        "cache_ready_count": cache_ready_count,
        "decode_ready_count": decode_ready_count,
        "missing_count": quality_report.get("missing_count") or 0,
        "cold_count": quality_report.get("cold_count") or 0,
        "failed_count": quality_report.get("failed_count") or 0,
        "stub_count": quality_report.get("stub_count") or 0,
        "partial_count": quality_report.get("partial_count") or 0,
        "ready_count": quality_report.get("ready_count") or 0,
        "problem_count": problem_count,
        "truncated": bool(quality_report.get("truncated")),
    }

    import_status = _resolve_import_status(
        valid=True,
        frame_count=frame_count,
        problem_count=problem_count,
    )

    return {
        "valid": True,
        "import_status": import_status,
        "errors": [],
        "warnings": warnings,
        "manifest": normalized,
        "readiness_summary": readiness_summary,
        "problem_frames": problem_frames,
        "suggested_commands": _dedupe_commands(suggested_commands),
        "assessed_at": _utc_now(),
        **_safety_fields(),
    }
