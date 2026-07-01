"""Resolve and decode local MRMS for a selected catalog timestamp (prototype only)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.models import Layer, Product, RadarFile
from backend.app.services.catalog import MRMS_REFLECTIVITY_LAYER_ID
from backend.app.services.color_scale import COLOR_SCALE_MODE
from backend.app.services.decoded_tile_cache import (
    DecodeArtifact,
    find_decode_artifact_for_frame,
    load_decode_manifest,
)
from backend.app.services.decoder_setup import SUGGESTED_DECODE_RETRY_COMMAND, SUGGESTED_INSTALL_COMMAND
from backend.app.services.grib2_decoder import build_decode_output_dir, decode_grib2_file
from backend.app.services.georef_overlay import resolve_georef_overlay
from backend.app.services.grib2_inspector import detect_decoder_availability
from backend.app.services.overlay_sync import (
    extract_timestamp_from_raw_path,
    normalize_timestamp_iso,
)
from backend.app.services.raw_file_classifier import (
    RAW_KIND_MRMS_REAL_GRIB2,
    classify_raw_file,
    is_placeholder_raw_kind,
    is_real_grib2_raw_kind,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.tile_preview import (
    TILE_MODE_LOCAL_RASTER,
    TILE_MODE_SINGLE_IMAGE,
    build_local_tile_preview_at_root,
    compact_tile_preview,
    render_color_preview_from_artifact,
)
from backend.app.services.time_utils import parse_utc_iso

FRAME_CACHE_ROOT = "dev/mrms_frame_cache"
FRAME_MANIFEST_NAME = "frame_manifest.json"

FRAME_STATUS_MATCHED = "matched"
FRAME_STATUS_NO_LOCAL_CANDIDATE = "no_local_candidate"
FRAME_STATUS_DECODE_FAILED = "decode_failed"
FRAME_STATUS_DECODER_MISSING = "decoder_missing"
FRAME_STATUS_STUB_INPUT = "stub_input"

DOWNLOAD_MRMS_COMMAND = (
    "make mrms-bulk-local-ingest ARGS='--real --limit 8'"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _timestamp_token(timestamp: str) -> str:
    return normalize_timestamp_iso(timestamp).replace(":", "").replace("-", "")


def frame_cache_dir(storage: LocalStorage, timestamp: str) -> str:
    return storage.normalize_path(FRAME_CACHE_ROOT, _timestamp_token(timestamp))


def frame_manifest_path(storage: LocalStorage, timestamp: str) -> str:
    return storage.normalize_path(frame_cache_dir(storage, timestamp), FRAME_MANIFEST_NAME)


def load_frame_cache(storage: LocalStorage, timestamp: str) -> Optional[dict[str, Any]]:
    path = frame_manifest_path(storage, timestamp)
    if not storage.path_exists(path):
        return None
    try:
        data = json.loads(storage.absolute_path(path).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def save_frame_cache(storage: LocalStorage, timestamp: str, report: dict[str, Any]) -> dict[str, Any]:
    cache_dir = frame_cache_dir(storage, timestamp)
    storage.ensure_directories(cache_dir)
    path = frame_manifest_path(storage, timestamp)
    report = {**report, "cache_dir": cache_dir, "manifest_path": path}
    storage.absolute_path(path).write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


def _product_ids_for_layer(session: Session, layer_id: str) -> list[str]:
    return [
        product.id
        for product in session.query(Product).filter(Product.layer_id == layer_id).all()
    ]


def find_catalog_frame(session: Session, layer_id: str, timestamp: str) -> Optional[RadarFile]:
    layer = session.get(Layer, layer_id)
    if layer is None or not layer.available:
        return None
    product_ids = _product_ids_for_layer(session, layer_id)
    if not product_ids:
        return None
    return (
        session.query(RadarFile)
        .filter(
            RadarFile.product_id.in_(product_ids),
            RadarFile.timestamp == timestamp,
        )
        .one_or_none()
    )


def scan_raw_mrms_path_for_timestamp(storage: LocalStorage, timestamp: str) -> Optional[str]:
    token = _timestamp_token(timestamp)
    raw_dir = storage.normalize_path("raw/mrms/reflectivity")
    abs_dir = storage.absolute_path(raw_dir)
    if not abs_dir.is_dir():
        return None
    for path in sorted(abs_dir.iterdir()):
        if not path.is_file():
            continue
        name = path.name
        if token not in name or not name.endswith(".grib2.gz"):
            continue
        if name.endswith(".stub"):
            continue
        return storage.normalize_path(raw_dir, name)
    return None


def _candidate_from_frame(frame: RadarFile, storage: LocalStorage) -> dict[str, Any]:
    raw_kind = frame.raw_kind or classify_raw_file(frame)
    raw_exists = bool(frame.raw_path and storage.path_exists(frame.raw_path))
    return {
        "radar_file_id": frame.id,
        "timestamp": frame.timestamp,
        "raw_path": frame.raw_path if raw_exists else None,
        "raw_kind": raw_kind,
        "source": frame.source,
        "is_real_grib2": is_real_grib2_raw_kind(raw_kind) and raw_exists,
        "is_placeholder": is_placeholder_raw_kind(raw_kind) or not raw_exists,
        "selection": "catalog",
    }


def find_local_mrms_candidate(
    session: Session,
    storage: LocalStorage,
    timestamp: str,
    *,
    layer_id: str = MRMS_REFLECTIVITY_LAYER_ID,
) -> Optional[dict[str, Any]]:
    normalized = normalize_timestamp_iso(timestamp)
    if not normalized:
        return None

    frame = find_catalog_frame(session, layer_id, normalized)
    if frame is not None and frame.raw_path and storage.path_exists(frame.raw_path):
        candidate = _candidate_from_frame(frame, storage)
        if candidate.get("is_real_grib2"):
            return candidate
        if not candidate.get("is_placeholder"):
            return candidate

    raw_path = scan_raw_mrms_path_for_timestamp(storage, normalized)
    if raw_path:
        ts = extract_timestamp_from_raw_path(raw_path) or normalized
        raw_kind = RAW_KIND_MRMS_REAL_GRIB2
        return {
            "radar_file_id": frame.id if frame is not None else None,
            "timestamp": ts,
            "raw_path": raw_path,
            "raw_kind": raw_kind,
            "source": "filesystem_scan",
            "is_real_grib2": True,
            "is_placeholder": False,
            "selection": "filesystem",
        }

    if frame is not None and frame.raw_path:
        return _candidate_from_frame(frame, storage)
    return None


def list_local_mrms_timestamps(session: Session, storage: LocalStorage) -> dict[str, list[str]]:
    raw_timestamps: list[str] = []
    decoded_timestamps: list[str] = []

    product_ids = _product_ids_for_layer(session, MRMS_REFLECTIVITY_LAYER_ID)
    if product_ids:
        rows = (
            session.query(RadarFile)
            .filter(RadarFile.product_id.in_(product_ids), RadarFile.raw_path.isnot(None))
            .order_by(RadarFile.timestamp.asc())
            .all()
        )
        for row in rows:
            ts = normalize_timestamp_iso(row.timestamp)
            if not ts:
                continue
            raw_kind = row.raw_kind or classify_raw_file(row)
            if row.raw_path and storage.path_exists(row.raw_path):
                if is_real_grib2_raw_kind(raw_kind):
                    raw_timestamps.append(ts)
                    if load_decode_manifest(storage, build_decode_output_dir(storage, row.raw_path)):
                        decoded_timestamps.append(ts)
                elif not is_placeholder_raw_kind(raw_kind):
                    raw_timestamps.append(ts)

    raw_dir = storage.normalize_path("raw/mrms/reflectivity")
    abs_dir = storage.absolute_path(raw_dir)
    if abs_dir.is_dir():
        for path in abs_dir.iterdir():
            if not path.name.endswith(".grib2.gz") or path.name.endswith(".stub"):
                continue
            ts = extract_timestamp_from_raw_path(storage.normalize_path(raw_dir, path.name))
            if ts and ts not in raw_timestamps:
                raw_timestamps.append(ts)
                output_dir = build_decode_output_dir(storage, storage.normalize_path(raw_dir, path.name))
                if load_decode_manifest(storage, output_dir) and ts not in decoded_timestamps:
                    decoded_timestamps.append(ts)

    raw_timestamps.sort()
    decoded_timestamps.sort()
    return {"raw": raw_timestamps, "decoded": decoded_timestamps}


def nearest_timestamp(timestamps: list[str], target: str) -> Optional[str]:
    if not timestamps:
        return None
    target_dt = parse_utc_iso(target)
    return min(
        timestamps,
        key=lambda ts: abs((parse_utc_iso(ts) - target_dt).total_seconds()),
    )


def _write_frame_preview(
    storage: LocalStorage,
    cache_dir: str,
    png_bytes: bytes,
    *,
    z: int = 0,
    x: int = 0,
    y: int = 0,
) -> str:
    preview_path = storage.normalize_path(cache_dir, f"preview_z{z}_x{x}_y{y}.png")
    storage.ensure_directories(cache_dir)
    storage.write_bytes(preview_path, png_bytes, overwrite=True)
    return preview_path


def _build_frame_preview(
    storage: LocalStorage,
    artifact: DecodeArtifact,
    cache_dir: str,
) -> dict[str, Any]:
    tile_root = storage.normalize_path(cache_dir, "tiles")
    png_bytes = render_color_preview_from_artifact(storage, artifact, z=0, x=0, y=0)
    color_scale_mode = COLOR_SCALE_MODE
    if png_bytes is None:
        from backend.app.services.decoded_tile_cache import render_decoded_prototype_tile

        png_bytes = render_decoded_prototype_tile(storage, artifact, z=0, x=0, y=0)
        color_scale_mode = "grayscale_fallback"
    if png_bytes is None:
        return {
            "success": False,
            "error": "Decode artifact present but preview render returned None.",
        }

    preview_path = _write_frame_preview(storage, cache_dir, png_bytes)
    tile_preview = build_local_tile_preview_at_root(
        storage,
        artifact,
        tile_root=tile_root,
        z_levels=[0, 1],
        xy_limit=2,
    )
    tile_mode = TILE_MODE_SINGLE_IMAGE
    if tile_preview.built > 0 and tile_preview.tile_mode == TILE_MODE_LOCAL_RASTER:
        tile_mode = TILE_MODE_LOCAL_RASTER

    return {
        "success": True,
        "preview_paths": [preview_path],
        "color_scale_mode": color_scale_mode,
        "tile_mode": tile_mode,
        "tile_preview": compact_tile_preview(tile_preview),
        "tile_root": tile_root,
        "render_mode": "decoded_prototype",
    }


def resolve_selected_frame(
    session: Session,
    storage: LocalStorage,
    selected_timestamp: str,
    *,
    layer_id: str = MRMS_REFLECTIVITY_LAYER_ID,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Resolve, decode if needed, and cache preview/tiles for a selected catalog timestamp."""
    if catalog_is_empty(session):
        seed_demo_catalog(session, storage=storage)

    selected = normalize_timestamp_iso(selected_timestamp)
    if not selected:
        return {
            "frame_status": FRAME_STATUS_NO_LOCAL_CANDIDATE,
            "selected_timestamp": selected_timestamp,
            "sync_message": "Invalid timestamp format.",
            "action_commands": [SUGGESTED_DECODE_RETRY_COMMAND],
        }

    if not force_refresh:
        cached = load_frame_cache(storage, selected)
        if cached and cached.get("frame_status") == FRAME_STATUS_MATCHED:
            preview_paths = cached.get("preview_paths") or []
            if preview_paths and storage.path_exists(preview_paths[0]):
                return cached

    candidate = find_local_mrms_candidate(session, storage, selected, layer_id=layer_id)
    available = list_local_mrms_timestamps(session, storage)

    if candidate is None or not candidate.get("raw_path"):
        nearest_raw = nearest_timestamp(available["raw"], selected)
        nearest_decoded = nearest_timestamp(available["decoded"], selected)
        return save_frame_cache(
            storage,
            selected,
            {
                "ran_at": _utc_now(),
                "frame_status": FRAME_STATUS_NO_LOCAL_CANDIDATE,
                "selected_timestamp": selected,
                "candidate_timestamp": None,
                "nearest_raw_timestamp": nearest_raw,
                "nearest_decoded_timestamp": nearest_decoded,
                "sync_message": (
                    f"No local MRMS .grib2.gz for {selected}. "
                    + (f"Nearest local raw: {nearest_raw}. " if nearest_raw else "")
                    + "Download real MRMS or select a timestamp with a local file."
                ),
                "action_commands": [DOWNLOAD_MRMS_COMMAND, SUGGESTED_DECODE_RETRY_COMMAND],
                "fallback_latest_available": True,
            },
        )

    raw_path = candidate["raw_path"]
    candidate_ts = normalize_timestamp_iso(candidate.get("timestamp")) or selected

    if candidate.get("is_placeholder") or not candidate.get("is_real_grib2"):
        return save_frame_cache(
            storage,
            selected,
            {
                "ran_at": _utc_now(),
                "frame_status": FRAME_STATUS_STUB_INPUT,
                "selected_timestamp": selected,
                "candidate_timestamp": candidate_ts,
                "candidate": candidate,
                "sync_message": (
                    f"Catalog frame {selected} has stub/placeholder raw only. "
                    f"Run `{DOWNLOAD_MRMS_COMMAND}` for real GRIB2."
                ),
                "action_commands": [DOWNLOAD_MRMS_COMMAND, SUGGESTED_DECODE_RETRY_COMMAND],
                "fallback_latest_available": True,
            },
        )

    availability = detect_decoder_availability()
    if not availability.any_decoder:
        return save_frame_cache(
            storage,
            selected,
            {
                "ran_at": _utc_now(),
                "frame_status": FRAME_STATUS_DECODER_MISSING,
                "selected_timestamp": selected,
                "candidate_timestamp": candidate_ts,
                "candidate": candidate,
                "sync_message": availability.summary_message(),
                "action_commands": [SUGGESTED_INSTALL_COMMAND, SUGGESTED_DECODE_RETRY_COMMAND],
                "fallback_latest_available": True,
            },
        )

    frame = session.get(RadarFile, candidate["radar_file_id"]) if candidate.get("radar_file_id") else None
    output_dir = build_decode_output_dir(storage, raw_path)
    artifact: Optional[DecodeArtifact] = None
    if frame is not None:
        artifact = find_decode_artifact_for_frame(storage, frame)
    if artifact is None:
        artifact = load_decode_manifest(storage, output_dir)

    if artifact is None:
        decode_result = decode_grib2_file(storage, raw_path)
        if not decode_result.success:
            return save_frame_cache(
                storage,
                selected,
                {
                    "ran_at": _utc_now(),
                    "frame_status": FRAME_STATUS_DECODE_FAILED,
                    "selected_timestamp": selected,
                    "candidate_timestamp": candidate_ts,
                    "candidate": candidate,
                    "decode_output_dir": output_dir,
                    "decode_error": decode_result.error,
                    "sync_message": decode_result.error or f"Decode failed for {selected}.",
                    "action_commands": [
                        f"make decode-grib2 ARGS='--file {raw_path}'",
                        SUGGESTED_DECODE_RETRY_COMMAND,
                    ],
                    "fallback_latest_available": True,
                },
            )
        artifact = load_decode_manifest(storage, output_dir)

    if artifact is None:
        return save_frame_cache(
            storage,
            selected,
            {
                "ran_at": _utc_now(),
                "frame_status": FRAME_STATUS_DECODE_FAILED,
                "selected_timestamp": selected,
                "candidate_timestamp": candidate_ts,
                "candidate": candidate,
                "decode_output_dir": output_dir,
                "sync_message": "Decode succeeded but manifest missing.",
                "action_commands": [SUGGESTED_DECODE_RETRY_COMMAND],
                "fallback_latest_available": True,
            },
        )

    cache_dir = frame_cache_dir(storage, selected)
    preview_build = _build_frame_preview(storage, artifact, cache_dir)
    if not preview_build.get("success"):
        return save_frame_cache(
            storage,
            selected,
            {
                "ran_at": _utc_now(),
                "frame_status": FRAME_STATUS_DECODE_FAILED,
                "selected_timestamp": selected,
                "candidate_timestamp": candidate_ts,
                "candidate": candidate,
                "decode_output_dir": output_dir,
                "sync_message": preview_build.get("error") or "Preview build failed.",
                "action_commands": [SUGGESTED_DECODE_RETRY_COMMAND],
                "fallback_latest_available": True,
            },
        )

    georef = resolve_georef_overlay(storage, output_dir)

    return save_frame_cache(
        storage,
        selected,
        {
            "ran_at": _utc_now(),
            "frame_status": FRAME_STATUS_MATCHED,
            "selected_timestamp": selected,
            "candidate_timestamp": candidate_ts,
            "candidate": candidate,
            "candidate_raw_path": raw_path,
            "decode_output_dir": output_dir,
            "preview_paths": preview_build["preview_paths"],
            "color_scale_mode": preview_build["color_scale_mode"],
            "tile_mode": preview_build["tile_mode"],
            "tile_preview": preview_build["tile_preview"],
            "tile_root": preview_build["tile_root"],
            "render_mode": preview_build["render_mode"],
            "pipeline_status": "preview_ok",
            "bounds": georef["bounds"],
            "georef_mode": georef["georef_mode"],
            "georef_quality": georef["georef_quality"],
            "georef_notes": georef.get("georef_notes") or [],
            "bounds_source": georef.get("bounds_source"),
            "geo_accurate": georef["geo_accurate"],
            "sync_message": "Selected frame decoded and cached for local overlay.",
            "action_commands": [SUGGESTED_DECODE_RETRY_COMMAND],
            "fallback_latest_available": False,
        },
    )