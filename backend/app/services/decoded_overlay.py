"""Local dev decoded map overlay — serves preview PNG + bounds metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.decode_retry import load_decode_retry_report
from backend.app.services.mrms_local_render_pipeline import (
    PREVIEW_DIR,
    STATUS_DECODER_MISSING,
    STATUS_PREVIEW_OK,
    STATUS_STUB_INPUT,
    load_local_render_pipeline_report,
)
from backend.app.services.render_metadata import DEFAULT_MRMS_BOUNDS, load_geo_metadata
from backend.app.services.storage import LocalStorage

OVERLAY_STATUS_MISSING = "missing"
OVERLAY_STATUS_PLACEHOLDER = "placeholder"
OVERLAY_STATUS_DECODED_PROTOTYPE = "decoded_prototype"
OVERLAY_STATUS_DECODER_MISSING = "decoder_missing"
OVERLAY_STATUS_STUB = "stub_input"

PREVIEW_API_PATH = "/api/dev/decoded-overlay/preview.png"
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


def _default_labels(*, overlay_status: str) -> list[str]:
    labels = [
        "Local dev prototype overlay",
        "NOT verified MRMS",
        "NOT production tile serving",
    ]
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


def _resolve_georef(
    storage: LocalStorage,
    decode_output_dir: Optional[str],
) -> tuple[list[float], str, bool]:
    if not decode_output_dir:
        return list(DEFAULT_MRMS_BOUNDS), "prototype_bounds", False

    geo = load_geo_metadata(storage, decode_output_dir)
    if geo is None or len(geo.bounds) != 4:
        return list(DEFAULT_MRMS_BOUNDS), "prototype_bounds", False

    georef_mode = "prototype_bounds"
    if any("Enriched from rasterio" in note for note in geo.notes):
        georef_mode = "rasterio_bounds"
    return [float(v) for v in geo.bounds], georef_mode, bool(geo.geo_accurate)


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
    preview_dir = storage.normalize_path(PREVIEW_DIR)
    fallback = storage.normalize_path(PREVIEW_DIR, "preview_z0_x0_y0.png")
    if storage.path_exists(fallback):
        return fallback
    return None


def build_decoded_overlay(storage: LocalStorage) -> dict[str, Any]:
    pipeline = load_local_render_pipeline_report(storage)
    decode_retry = load_decode_retry_report(storage)
    preview_path = resolve_preview_repo_path(storage, pipeline)
    overlay_status = _overlay_status_from_pipeline(pipeline) if pipeline else OVERLAY_STATUS_MISSING

    decode_output_dir = None
    if pipeline:
        decode_output_dir = pipeline.get("decode_output_dir")
    if decode_retry and decode_retry.get("decode", {}).get("output_dir"):
        decode_output_dir = decode_retry["decode"]["output_dir"]

    bounds, georef_mode, geo_accurate = _resolve_georef(storage, decode_output_dir)
    preview_mtime = _file_mtime_iso(storage, preview_path) if preview_path else None
    ran_at = (pipeline or {}).get("ran_at") or (decode_retry or {}).get("ran_at")

    stale_hint = None
    if preview_mtime and ran_at and preview_mtime < ran_at:
        stale_hint = "Preview file older than last pipeline report — rerun make decode-retry"

    available = bool(preview_path and storage.path_exists(preview_path))
    candidate_raw_path = None
    if pipeline and pipeline.get("candidate"):
        candidate_raw_path = pipeline["candidate"].get("raw_path")
    elif decode_retry and decode_retry.get("candidate"):
        candidate_raw_path = decode_retry["candidate"].get("raw_path")

    return {
        "available": available,
        "overlay_status": overlay_status if available else OVERLAY_STATUS_MISSING,
        "render_mode": (pipeline or {}).get("render_mode"),
        "pipeline_status": (pipeline or {}).get("pipeline_status"),
        "preview_url": PREVIEW_API_PATH if available else None,
        "preview_path": preview_path,
        "ran_at": ran_at,
        "preview_mtime": preview_mtime,
        "stale_hint": stale_hint,
        "bounds": bounds,
        "georef_mode": georef_mode,
        "geo_accurate": geo_accurate,
        "candidate_raw_path": candidate_raw_path,
        "decode_output_dir": decode_output_dir,
        "labels": _default_labels(overlay_status=overlay_status if available else OVERLAY_STATUS_MISSING),
        "refresh_commands": list(SUGGESTED_REFRESH_COMMANDS),
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
