"""Local dev decoded map overlay — serves preview PNG + bounds metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

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
    SYNC_MATCHED,
    evaluate_overlay_sync,
    extract_candidate_timestamp,
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
    elif sync_status == "mismatch":
        labels.append("Time mismatch — overlay hidden")
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


def resolve_preview_repo_path(storage: LocalStorage, pipeline: Optional[dict[str, Any]]) -> Optional[str]:
    if pipeline:
        paths = pipeline.get("preview_paths") or []
        if paths:
            return paths[0]
    fallback = storage.normalize_path(PREVIEW_DIR, "preview_z0_x0_y0.png")
    if storage.path_exists(fallback):
        return fallback
    return None


def _pipeline_tile_fields(pipeline: Optional[dict[str, Any]], *, overlay_visible: bool) -> dict[str, Any]:
    if not pipeline:
        return {
            "color_scale_mode": None,
            "tile_mode": TILE_MODE_SINGLE_IMAGE,
            "tile_url_template": None,
            "tile_max_z": 0,
            "tile_count": 0,
            "tile_root": LOCAL_TILE_ROOT,
        }
    tile_preview = pipeline.get("tile_preview") or {}
    tile_mode = pipeline.get("tile_mode") or tile_preview.get("tile_mode") or TILE_MODE_SINGLE_IMAGE
    tile_count = int(tile_preview.get("built") or 0)
    tile_max_z = int(tile_preview.get("max_z") or 0)
    use_tiles = overlay_visible and tile_mode == TILE_MODE_LOCAL_RASTER and tile_count > 0
    return {
        "color_scale_mode": pipeline.get("color_scale_mode"),
        "tile_mode": tile_mode if use_tiles else TILE_MODE_SINGLE_IMAGE,
        "tile_url_template": TILE_API_TEMPLATE if use_tiles else None,
        "tile_max_z": tile_max_z if use_tiles else 0,
        "tile_count": tile_count if use_tiles else 0,
        "tile_root": LOCAL_TILE_ROOT,
    }


def build_decoded_overlay(
    storage: LocalStorage,
    *,
    selected_timestamp: Optional[str] = None,
) -> dict[str, Any]:
    pipeline = load_local_render_pipeline_report(storage)
    decode_retry = load_decode_retry_report(storage)
    preview_path = resolve_preview_repo_path(storage, pipeline)
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
    tile_fields = _pipeline_tile_fields(pipeline, overlay_visible=overlay_visible)

    preview_mtime = _file_mtime_iso(storage, preview_path) if preview_path else None
    ran_at = (pipeline or {}).get("ran_at") or (decode_retry or {}).get("ran_at")

    stale_hint = None
    if preview_mtime and ran_at and preview_mtime < ran_at:
        stale_hint = "Preview file older than last pipeline report — rerun make decode-retry"
    if sync["sync_status"] == "mismatch":
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


def load_preview_png_bytes(storage: LocalStorage) -> Optional[bytes]:
    pipeline = load_local_render_pipeline_report(storage)
    preview_path = resolve_preview_repo_path(storage, pipeline)
    if not preview_path or not storage.path_exists(preview_path):
        return None
    try:
        return storage.absolute_path(preview_path).read_bytes()
    except OSError:
        return None


def load_overlay_tile_png(storage: LocalStorage, *, z: int, x: int, y: int) -> Optional[bytes]:
    return load_local_tile_png(storage, z=z, x=x, y=y)
