"""Local dev decoded map overlay — serves preview PNG + bounds metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.color_scale import COLOR_SCALE_MODE
from backend.app.services.decode_retry import load_decode_retry_report
from backend.app.services.georef_overlay import resolve_georef_overlay
from backend.app.services.mrms_local_render_pipeline import (
    PREVIEW_DIR,
    STATUS_DECODER_MISSING,
    STATUS_PREVIEW_OK,
    STATUS_STUB_INPUT,
    load_local_render_pipeline_report,
)
from backend.app.services.overlay_sync import (
    SYNC_DECODE_FAILED,
    SYNC_DECODER_MISSING,
    SYNC_MATCHED,
    SYNC_MISMATCH,
    SYNC_NO_CANDIDATE,
    SYNC_NO_LOCAL_CANDIDATE,
    SYNC_NO_SELECTION,
    SYNC_STALE_LATEST_FALLBACK,
    SYNC_STUB_INPUT,
    evaluate_overlay_sync,
    extract_candidate_timestamp,
    normalize_timestamp_iso,
)
from backend.app.services.selected_frame_decode import (
    FRAME_STATUS_DECODE_FAILED,
    FRAME_STATUS_DECODER_MISSING,
    FRAME_STATUS_MATCHED,
    FRAME_STATUS_NO_LOCAL_CANDIDATE,
    FRAME_STATUS_STUB_INPUT,
    resolve_selected_frame,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.tile_preview import (
    LOCAL_TILE_ROOT,
    TILE_MODE_LOCAL_RASTER,
    TILE_MODE_SINGLE_IMAGE,
    load_local_tile_png,
)

OVERLAY_STATUS_MISSING = "missing"
OVERLAY_STATUS_PLACEHOLDER = "placeholder"
OVERLAY_STATUS_DECODED_PROTOTYPE = "decoded_prototype"
OVERLAY_STATUS_DECODER_MISSING = "decoder_missing"
OVERLAY_STATUS_STUB = "stub_input"

PREVIEW_API_PATH = "/api/dev/decoded-overlay/preview.png"
TILE_API_TEMPLATE = "/api/dev/decoded-overlay/tiles/{z}/{x}/{y}.png"
SUGGESTED_REFRESH_COMMANDS = [
    "make decode-retry",
    "make mrms-local-render-pipeline",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_dev_only": True,
        "prototype": True,
        "production_tile_serving": settings.enable_production_radar_tiles,
    }


def _default_labels(
    *,
    overlay_status: str,
    color_scale_mode: Optional[str],
    sync_status: str,
) -> list[str]:
    labels = [
        "Local dev prototype overlay",
        "NOT verified MRMS",
        "NOT production tile serving",
    ]
    if color_scale_mode == COLOR_SCALE_MODE:
        labels.append("Reflectivity dBZ color scale (prototype)")
    if sync_status == SYNC_MATCHED:
        labels.append("Synced to selected catalog frame")
    elif sync_status == SYNC_MISMATCH:
        labels.append("Time mismatch — overlay hidden")
    elif sync_status == SYNC_NO_LOCAL_CANDIDATE:
        labels.append("No local MRMS file for selected frame")
    elif sync_status == SYNC_DECODE_FAILED:
        labels.append("Selected frame decode failed")
    elif sync_status == SYNC_DECODER_MISSING:
        labels.append("Decoder missing for selected frame")
    elif sync_status == SYNC_STUB_INPUT:
        labels.append("Stub input — download real GRIB2")
    elif sync_status == SYNC_STALE_LATEST_FALLBACK:
        labels.append("Latest preview available for different frame")
    if overlay_status == OVERLAY_STATUS_DECODED_PROTOTYPE:
        labels.append("Decoded prototype preview")
    elif overlay_status == OVERLAY_STATUS_PLACEHOLDER:
        labels.append("Placeholder preview — rerun decode-retry")
    elif overlay_status == OVERLAY_STATUS_DECODER_MISSING:
        labels.append("Decoder missing — install via make install-decoders")
    elif overlay_status == OVERLAY_STATUS_STUB:
        labels.append("Stub input — download real GRIB2")
    else:
        labels.append("No local preview yet — run make decode-retry")
    return labels


def _file_mtime_iso(storage: LocalStorage, repo_path: str) -> Optional[str]:
    try:
        mtime = storage.absolute_path(repo_path).stat().st_mtime
        return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except OSError:
        return None


def _overlay_status_from_pipeline(pipeline: dict[str, Any]) -> str:
    render_mode = pipeline.get("render_mode")
    pipeline_status = pipeline.get("pipeline_status")
    if render_mode == "decoded_prototype" and pipeline_status == STATUS_PREVIEW_OK:
        return OVERLAY_STATUS_DECODED_PROTOTYPE
    if pipeline_status == STATUS_DECODER_MISSING or render_mode == "placeholder_decoder_missing":
        return OVERLAY_STATUS_DECODER_MISSING
    if pipeline_status == STATUS_STUB_INPUT or render_mode == "placeholder_stub_input":
        return OVERLAY_STATUS_STUB
    if pipeline.get("produced_local_artifact"):
        return OVERLAY_STATUS_PLACEHOLDER
    return OVERLAY_STATUS_MISSING


def resolve_preview_repo_path(
    storage: LocalStorage,
    pipeline: Optional[dict[str, Any]],
    *,
    frame_report: Optional[dict[str, Any]] = None,
) -> Optional[str]:
    if frame_report:
        paths = frame_report.get("preview_paths") or []
        if paths and storage.path_exists(paths[0]):
            return paths[0]
    if pipeline:
        paths = pipeline.get("preview_paths") or []
        if paths:
            return paths[0]
    fallback = storage.normalize_path(PREVIEW_DIR, "preview_z0_x0_y0.png")
    if storage.path_exists(fallback):
        return fallback
    return None


def _pipeline_tile_fields(
    pipeline: Optional[dict[str, Any]],
    *,
    frame_report: Optional[dict[str, Any]],
    overlay_visible: bool,
) -> dict[str, Any]:
    source = frame_report if frame_report and frame_report.get("frame_status") == FRAME_STATUS_MATCHED else pipeline
    if not source:
        return {
            "color_scale_mode": None,
            "tile_mode": TILE_MODE_SINGLE_IMAGE,
            "tile_url_template": None,
            "tile_max_z": 0,
            "tile_count": 0,
            "tile_root": LOCAL_TILE_ROOT,
        }
    tile_preview = source.get("tile_preview") or {}
    tile_mode = source.get("tile_mode") or tile_preview.get("tile_mode") or TILE_MODE_SINGLE_IMAGE
    tile_count = int(tile_preview.get("built") or 0)
    tile_max_z = int(tile_preview.get("max_z") or 0)
    tile_root = source.get("tile_root") or LOCAL_TILE_ROOT
    use_tiles = overlay_visible and tile_mode == TILE_MODE_LOCAL_RASTER and tile_count > 0
    return {
        "color_scale_mode": source.get("color_scale_mode"),
        "tile_mode": tile_mode if use_tiles else TILE_MODE_SINGLE_IMAGE,
        "tile_url_template": TILE_API_TEMPLATE if use_tiles else None,
        "tile_max_z": tile_max_z if use_tiles else 0,
        "tile_count": tile_count if use_tiles else 0,
        "tile_root": tile_root,
    }


def _frame_status_to_sync(frame_status: str) -> str:
    mapping = {
        FRAME_STATUS_MATCHED: SYNC_MATCHED,
        FRAME_STATUS_NO_LOCAL_CANDIDATE: SYNC_NO_LOCAL_CANDIDATE,
        FRAME_STATUS_DECODE_FAILED: SYNC_DECODE_FAILED,
        FRAME_STATUS_DECODER_MISSING: SYNC_DECODER_MISSING,
        FRAME_STATUS_STUB_INPUT: SYNC_STUB_INPUT,
    }
    return mapping.get(frame_status, SYNC_MISMATCH)


def _build_from_frame_report(
    storage: LocalStorage,
    frame_report: dict[str, Any],
    *,
    latest_pipeline: Optional[dict[str, Any]],
    latest_preview_available: bool,
) -> dict[str, Any]:
    frame_status = frame_report.get("frame_status")
    sync_status = _frame_status_to_sync(str(frame_status))
    overlay_visible = frame_status == FRAME_STATUS_MATCHED
    selected = frame_report.get("selected_timestamp")
    candidate_ts = frame_report.get("candidate_timestamp")

    decode_output_dir = frame_report.get("decode_output_dir")
    preview_path = resolve_preview_repo_path(storage, latest_pipeline, frame_report=frame_report)
    artifact_available = bool(preview_path and storage.path_exists(preview_path))

    if (
        not overlay_visible
        and latest_preview_available
        and frame_report.get("fallback_latest_available")
        and latest_pipeline
    ):
        latest_ts = extract_candidate_timestamp(
            pipeline=latest_pipeline,
            decode_retry=None,
            geo=None,
            candidate_raw_path=(latest_pipeline.get("candidate") or {}).get("raw_path"),
        )
        if latest_ts and selected and normalize_timestamp_iso(selected) != latest_ts:
            sync_status = SYNC_STALE_LATEST_FALLBACK

    georef = resolve_georef_overlay(storage, decode_output_dir)
    tile_fields = _pipeline_tile_fields(
        latest_pipeline,
        frame_report=frame_report if overlay_visible else None,
        overlay_visible=overlay_visible,
    )

    overlay_status = OVERLAY_STATUS_DECODED_PROTOTYPE if overlay_visible else OVERLAY_STATUS_MISSING
    if frame_status == FRAME_STATUS_DECODER_MISSING:
        overlay_status = OVERLAY_STATUS_DECODER_MISSING
    elif frame_status == FRAME_STATUS_STUB_INPUT:
        overlay_status = OVERLAY_STATUS_STUB

    ran_at = frame_report.get("ran_at")
    preview_mtime = _file_mtime_iso(storage, preview_path) if preview_path else None
    stale_hint = None
    if sync_status == SYNC_STALE_LATEST_FALLBACK:
        stale_hint = (
            f"Latest local preview is for a different frame. "
            f"Selected {selected}; decode or download the selected timestamp."
        )
    elif not overlay_visible:
        stale_hint = frame_report.get("sync_message")

    color_scale_mode = tile_fields.get("color_scale_mode")
    action_commands = list(frame_report.get("action_commands") or SUGGESTED_REFRESH_COMMANDS)

    return {
        "available": artifact_available and overlay_visible,
        "artifact_available": artifact_available,
        "overlay_visible": overlay_visible,
        "overlay_status": overlay_status if artifact_available or overlay_visible else OVERLAY_STATUS_MISSING,
        "render_mode": frame_report.get("render_mode"),
        "pipeline_status": frame_report.get("pipeline_status"),
        "preview_url": PREVIEW_API_PATH if artifact_available and overlay_visible else None,
        "preview_path": preview_path if overlay_visible else None,
        "ran_at": ran_at,
        "preview_mtime": preview_mtime,
        "stale_hint": stale_hint,
        "bounds": georef["bounds"],
        "georef_mode": georef["georef_mode"],
        "georef_quality": georef["georef_quality"],
        "georef_notes": georef.get("georef_notes") or [],
        "geo_accurate": georef["geo_accurate"],
        "candidate_timestamp": candidate_ts,
        "selected_timestamp": selected,
        "sync_status": sync_status,
        "sync_message": frame_report.get("sync_message"),
        "frame_status": frame_status,
        "nearest_raw_timestamp": frame_report.get("nearest_raw_timestamp"),
        "nearest_decoded_timestamp": frame_report.get("nearest_decoded_timestamp"),
        "candidate_raw_path": frame_report.get("candidate_raw_path")
        or (frame_report.get("candidate") or {}).get("raw_path"),
        "decode_output_dir": decode_output_dir,
        "labels": _default_labels(
            overlay_status=overlay_status,
            color_scale_mode=color_scale_mode,
            sync_status=sync_status,
        ),
        "refresh_commands": action_commands,
        **tile_fields,
        **_safety_fields(),
    }


def build_decoded_overlay(
    storage: LocalStorage,
    *,
    selected_timestamp: Optional[str] = None,
    session: Optional[Session] = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    pipeline = load_local_render_pipeline_report(storage)
    decode_retry = load_decode_retry_report(storage)
    latest_preview_path = resolve_preview_repo_path(storage, pipeline)
    latest_preview_available = bool(latest_preview_path and storage.path_exists(latest_preview_path))

    if selected_timestamp and session is not None:
        frame_report = resolve_selected_frame(
            session,
            storage,
            selected_timestamp,
            force_refresh=force_refresh,
        )
        return _build_from_frame_report(
            storage,
            frame_report,
            latest_pipeline=pipeline,
            latest_preview_available=latest_preview_available,
        )

    preview_path = latest_preview_path
    overlay_status = _overlay_status_from_pipeline(pipeline) if pipeline else OVERLAY_STATUS_MISSING

    decode_output_dir = None
    if pipeline:
        decode_output_dir = pipeline.get("decode_output_dir")
    if decode_retry and decode_retry.get("decode", {}).get("output_dir"):
        decode_output_dir = decode_retry["decode"]["output_dir"]

    candidate_raw_path = None
    if pipeline and pipeline.get("candidate"):
        candidate_raw_path = pipeline["candidate"].get("raw_path")
    elif decode_retry and decode_retry.get("candidate"):
        candidate_raw_path = decode_retry["candidate"].get("raw_path")

    from backend.app.services.render_metadata import load_geo_metadata

    geo = load_geo_metadata(storage, decode_output_dir) if decode_output_dir else None
    candidate_timestamp = extract_candidate_timestamp(
        pipeline=pipeline,
        decode_retry=decode_retry,
        geo=geo,
        candidate_raw_path=candidate_raw_path,
    )
    sync = evaluate_overlay_sync(
        selected_timestamp=selected_timestamp,
        candidate_timestamp=candidate_timestamp,
    )
    overlay_visible = bool(sync["overlay_visible"])

    georef = resolve_georef_overlay(storage, decode_output_dir)
    tile_fields = _pipeline_tile_fields(pipeline, frame_report=None, overlay_visible=overlay_visible)

    preview_mtime = _file_mtime_iso(storage, preview_path) if preview_path else None
    ran_at = (pipeline or {}).get("ran_at") or (decode_retry or {}).get("ran_at")

    stale_hint = None
    if preview_mtime and ran_at and preview_mtime < ran_at:
        stale_hint = "Preview file older than last pipeline report — rerun make decode-retry"
    if sync["sync_status"] == SYNC_MISMATCH:
        stale_hint = sync["sync_message"]

    artifact_available = bool(preview_path and storage.path_exists(preview_path))
    available = artifact_available and overlay_visible

    color_scale_mode = tile_fields.get("color_scale_mode")
    return {
        "available": available,
        "artifact_available": artifact_available,
        "overlay_visible": overlay_visible,
        "overlay_status": overlay_status if artifact_available else OVERLAY_STATUS_MISSING,
        "render_mode": (pipeline or {}).get("render_mode"),
        "pipeline_status": (pipeline or {}).get("pipeline_status"),
        "preview_url": PREVIEW_API_PATH if artifact_available and overlay_visible else None,
        "preview_path": preview_path,
        "ran_at": ran_at,
        "preview_mtime": preview_mtime,
        "stale_hint": stale_hint,
        "bounds": georef["bounds"],
        "georef_mode": georef["georef_mode"],
        "georef_quality": georef["georef_quality"],
        "georef_notes": georef.get("georef_notes") or [],
        "geo_accurate": georef["geo_accurate"],
        "candidate_timestamp": sync.get("candidate_timestamp"),
        "selected_timestamp": sync.get("selected_timestamp"),
        "sync_status": sync["sync_status"],
        "sync_message": sync["sync_message"],
        "frame_status": None,
        "nearest_raw_timestamp": None,
        "nearest_decoded_timestamp": None,
        "candidate_raw_path": candidate_raw_path,
        "decode_output_dir": decode_output_dir,
        "labels": _default_labels(
            overlay_status=overlay_status if artifact_available else OVERLAY_STATUS_MISSING,
            color_scale_mode=color_scale_mode,
            sync_status=str(sync["sync_status"]),
        ),
        "refresh_commands": list(SUGGESTED_REFRESH_COMMANDS),
        **tile_fields,
        **_safety_fields(),
    }


def _active_frame_report(
    storage: LocalStorage,
    *,
    selected_timestamp: Optional[str] = None,
    session: Optional[Session] = None,
) -> Optional[dict[str, Any]]:
    if not selected_timestamp or session is None:
        return None
    normalized = normalize_timestamp_iso(selected_timestamp)
    if not normalized:
        return None
    from backend.app.services.selected_frame_decode import load_frame_cache, resolve_selected_frame

    cached = load_frame_cache(storage, normalized)
    if cached and cached.get("frame_status") == FRAME_STATUS_MATCHED:
        preview_paths = cached.get("preview_paths") or []
        if preview_paths and storage.path_exists(preview_paths[0]):
            return cached
    report = resolve_selected_frame(session, storage, normalized)
    if report.get("frame_status") == FRAME_STATUS_MATCHED:
        return report
    return None


def load_preview_png_bytes(
    storage: LocalStorage,
    *,
    selected_timestamp: Optional[str] = None,
    session: Optional[Session] = None,
) -> Optional[bytes]:
    frame_report = _active_frame_report(storage, selected_timestamp=selected_timestamp, session=session)
    pipeline = load_local_render_pipeline_report(storage)
    preview_path = resolve_preview_repo_path(storage, pipeline, frame_report=frame_report)
    if not preview_path or not storage.path_exists(preview_path):
        return None
    try:
        return storage.absolute_path(preview_path).read_bytes()
    except OSError:
        return None


def load_overlay_tile_png(
    storage: LocalStorage,
    *,
    z: int,
    x: int,
    y: int,
    selected_timestamp: Optional[str] = None,
    session: Optional[Session] = None,
) -> Optional[bytes]:
    frame_report = _active_frame_report(storage, selected_timestamp=selected_timestamp, session=session)
    tile_root = None
    if frame_report:
        tile_root = frame_report.get("tile_root")
    return load_local_tile_png(storage, z=z, x=x, y=y, tile_root=tile_root)
