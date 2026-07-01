"""Local-dev frame quality checks for decoded MRMS playback (diagnostic only)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from backend.app.services.decoded_tile_cache import load_decode_manifest
from backend.app.services.georef_overlay import GEOREF_QUALITY_PROTOTYPE
from backend.app.services.render_metadata import DEFAULT_MRMS_BOUNDS, load_geo_metadata
from backend.app.services.storage import LocalStorage

QUALITY_OK = "ok"
QUALITY_WARNING = "warning"
QUALITY_ERROR = "error"
QUALITY_UNAVAILABLE = "unavailable"

CHECK_ARTIFACTS = "artifacts"
CHECK_DECODE_MANIFEST = "decode_manifest"
CHECK_GRID_VALUES = "grid_values"
CHECK_DIMENSIONS = "dimensions"
CHECK_GEOREF_BOUNDS = "georef_bounds"
CHECK_TILE_PREVIEW = "tile_preview"

# Normalized prototype grids are 0..1; reflectivity decode may store raw dBZ in manifest.
NORMALIZED_MIN_SPAN = 1e-6
SUSPICIOUS_DBZ_MIN = -40.0
SUSPICIOUS_DBZ_MAX = 90.0


@dataclass
class FrameQualityCheck:
    name: str
    status: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_decode_manifest_payload(storage: LocalStorage, decode_output_dir: Optional[str]) -> Optional[dict[str, Any]]:
    if not decode_output_dir:
        return None
    manifest_path = storage.normalize_path(decode_output_dir, "decode_manifest.json")
    if not storage.path_exists(manifest_path):
        return None
    try:
        payload = json.loads(storage.absolute_path(manifest_path).read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _raster_value_span(storage: LocalStorage, raster_path: str) -> Optional[dict[str, float]]:
    try:
        import numpy as np
        import rasterio
    except ImportError:
        return None

    try:
        with rasterio.open(storage.absolute_path(raster_path)) as dataset:
            data = dataset.read(1, masked=True)
            if hasattr(data, "compressed"):
                values = data.compressed()
            else:
                values = np.asarray(data).ravel()
            if values.size == 0:
                return {"min": 0.0, "max": 0.0, "span": 0.0, "empty": 1.0}
            vmin = float(np.nanmin(values))
            vmax = float(np.nanmax(values))
            return {
                "min": vmin,
                "max": vmax,
                "span": vmax - vmin,
                "empty": float(np.mean(values == 0)),
            }
    except OSError:
        return None


def _check_artifacts(
    storage: LocalStorage,
    *,
    preview_path: Optional[str],
    decode_output_dir: Optional[str],
    overlay_visible: bool,
) -> FrameQualityCheck:
    details: dict[str, Any] = {
        "preview_path": preview_path,
        "decode_output_dir": decode_output_dir,
    }
    preview_ok = bool(preview_path and storage.path_exists(preview_path))
    details["preview_present"] = preview_ok

    if not decode_output_dir and not preview_path:
        return FrameQualityCheck(
            CHECK_ARTIFACTS,
            QUALITY_UNAVAILABLE,
            "No decode output or preview path to assess.",
            details,
        )

    if overlay_visible and not preview_ok:
        return FrameQualityCheck(
            CHECK_ARTIFACTS,
            QUALITY_ERROR,
            "Overlay visible but preview PNG is missing or unreadable.",
            details,
        )

    if not preview_ok:
        return FrameQualityCheck(
            CHECK_ARTIFACTS,
            QUALITY_WARNING,
            "Preview artifact not found — playback overlay may be empty.",
            details,
        )

    return FrameQualityCheck(
        CHECK_ARTIFACTS,
        QUALITY_OK,
        "Preview artifact present on disk.",
        details,
    )


def _check_decode_manifest(
    storage: LocalStorage,
    decode_output_dir: Optional[str],
    manifest_payload: Optional[dict[str, Any]],
) -> FrameQualityCheck:
    if not decode_output_dir:
        return FrameQualityCheck(
            CHECK_DECODE_MANIFEST,
            QUALITY_UNAVAILABLE,
            "No decode output directory.",
        )

    artifact = load_decode_manifest(storage, decode_output_dir)
    if artifact is None and manifest_payload is None:
        return FrameQualityCheck(
            CHECK_DECODE_MANIFEST,
            QUALITY_ERROR,
            "decode_manifest.json missing or invalid.",
            {"decode_output_dir": decode_output_dir},
        )

    payload = manifest_payload or {}
    width = payload.get("width") if manifest_payload else None
    height = payload.get("height") if manifest_payload else None
    if artifact is not None:
        width = artifact.width
        height = artifact.height

    return FrameQualityCheck(
        CHECK_DECODE_MANIFEST,
        QUALITY_OK,
        "Decode manifest readable.",
        {
            "width": width,
            "height": height,
            "decoder": payload.get("decoder") or (artifact.decoder if artifact else None),
            "raster_path": artifact.raster_path if artifact else payload.get("raster_path"),
        },
    )


def _check_grid_values(
    storage: LocalStorage,
    manifest_payload: Optional[dict[str, Any]],
    artifact: Any,
) -> FrameQualityCheck:
    details: dict[str, Any] = {}
    vmin = manifest_payload.get("value_min") if manifest_payload else None
    vmax = manifest_payload.get("value_max") if manifest_payload else None
    if vmin is not None:
        details["manifest_value_min"] = vmin
    if vmax is not None:
        details["manifest_value_max"] = vmax

    raster_span = None
    if artifact is not None:
        raster_span = _raster_value_span(storage, artifact.raster_path)
        if raster_span:
            details["raster_min"] = raster_span["min"]
            details["raster_max"] = raster_span["max"]
            details["raster_span"] = raster_span["span"]

    if raster_span is not None:
        if raster_span["span"] < NORMALIZED_MIN_SPAN:
            return FrameQualityCheck(
                CHECK_GRID_VALUES,
                QUALITY_WARNING,
                "Raster appears flat or all-nodata (very small value span).",
                details,
            )
        if raster_span.get("empty", 0) > 0.99:
            return FrameQualityCheck(
                CHECK_GRID_VALUES,
                QUALITY_WARNING,
                "Raster is almost entirely empty/zero.",
                details,
            )

    if vmin is not None and vmax is not None:
        if vmin == vmax:
            return FrameQualityCheck(
                CHECK_GRID_VALUES,
                QUALITY_WARNING,
                "Manifest reports identical min/max — grid may be empty or constant.",
                details,
            )
        span = float(vmax) - float(vmin)
        details["manifest_span"] = span
        if 0 <= float(vmin) <= 1 and 0 <= float(vmax) <= 1 and span < NORMALIZED_MIN_SPAN:
            return FrameQualityCheck(
                CHECK_GRID_VALUES,
                QUALITY_WARNING,
                "Normalized grid span is near zero.",
                details,
            )
        if float(vmin) < SUSPICIOUS_DBZ_MIN or float(vmax) > SUSPICIOUS_DBZ_MAX:
            return FrameQualityCheck(
                CHECK_GRID_VALUES,
                QUALITY_WARNING,
                "Manifest value range outside typical reflectivity bounds.",
                details,
            )

    if manifest_payload is None and artifact is None:
        return FrameQualityCheck(
            CHECK_GRID_VALUES,
            QUALITY_UNAVAILABLE,
            "No decode manifest for value-range checks.",
        )

    if raster_span is None and vmin is None and vmax is None:
        return FrameQualityCheck(
            CHECK_GRID_VALUES,
            QUALITY_WARNING,
            "Value range unavailable — rasterio/numpy not used; manifest lacks min/max.",
            details,
        )

    return FrameQualityCheck(
        CHECK_GRID_VALUES,
        QUALITY_OK,
        "Grid value range looks usable for prototype playback.",
        details,
    )


def _check_dimensions(
    storage: LocalStorage,
    decode_output_dir: Optional[str],
    manifest_payload: Optional[dict[str, Any]],
    artifact: Any,
    tile_preview: Optional[dict[str, Any]],
) -> FrameQualityCheck:
    if not decode_output_dir:
        return FrameQualityCheck(
            CHECK_DIMENSIONS,
            QUALITY_UNAVAILABLE,
            "No decode output directory for dimension checks.",
        )

    manifest_w = manifest_payload.get("width") if manifest_payload else None
    manifest_h = manifest_payload.get("height") if manifest_payload else None
    if artifact is not None:
        manifest_w = artifact.width
        manifest_h = artifact.height

    geo = load_geo_metadata(storage, decode_output_dir) if decode_output_dir else None
    details: dict[str, Any] = {
        "manifest_width": manifest_w,
        "manifest_height": manifest_h,
        "geo_width": geo.grid_width if geo else None,
        "geo_height": geo.grid_height if geo else None,
    }

    mismatches: list[str] = []
    if geo and manifest_w is not None and geo.grid_width and int(manifest_w) != int(geo.grid_width):
        mismatches.append(f"manifest width {manifest_w} != geo {geo.grid_width}")
    if geo and manifest_h is not None and geo.grid_height and int(manifest_h) != int(geo.grid_height):
        mismatches.append(f"manifest height {manifest_h} != geo {geo.grid_height}")

    if manifest_w in {None, 0} or manifest_h in {None, 0}:
        return FrameQualityCheck(
            CHECK_DIMENSIONS,
            QUALITY_WARNING,
            "Decode manifest missing non-zero width/height.",
            details,
        )

    if mismatches:
        return FrameQualityCheck(
            CHECK_DIMENSIONS,
            QUALITY_WARNING,
            "; ".join(mismatches),
            details,
        )

    if tile_preview and int(tile_preview.get("built") or 0) == 0 and manifest_w and manifest_h:
        return FrameQualityCheck(
            CHECK_DIMENSIONS,
            QUALITY_WARNING,
            "Tile preview metadata reports zero built tiles.",
            {**details, "tile_built": 0},
        )

    return FrameQualityCheck(
        CHECK_DIMENSIONS,
        QUALITY_OK,
        "Manifest and geo metadata dimensions agree.",
        details,
    )


def _check_georef_bounds(georef: Optional[dict[str, Any]]) -> FrameQualityCheck:
    if not georef:
        return FrameQualityCheck(
            CHECK_GEOREF_BOUNDS,
            QUALITY_UNAVAILABLE,
            "No georef metadata available.",
        )

    bounds = georef.get("bounds") or []
    details = {
        "bounds": bounds,
        "georef_quality": georef.get("georef_quality"),
        "bounds_source": georef.get("bounds_source"),
    }

    if len(bounds) != 4:
        return FrameQualityCheck(
            CHECK_GEOREF_BOUNDS,
            QUALITY_ERROR,
            "Bounds must be [west, south, east, north].",
            details,
        )

    west, south, east, north = (float(v) for v in bounds)
    if west >= east or south >= north:
        return FrameQualityCheck(
            CHECK_GEOREF_BOUNDS,
            QUALITY_ERROR,
            "Invalid bounds ordering (west>=east or south>=north).",
            details,
        )

    if list(bounds) == list(DEFAULT_MRMS_BOUNDS):
        return FrameQualityCheck(
            CHECK_GEOREF_BOUNDS,
            QUALITY_WARNING,
            "Using default CONUS prototype bounds — alignment may be approximate.",
            details,
        )

    if georef.get("georef_quality") == GEOREF_QUALITY_PROTOTYPE:
        return FrameQualityCheck(
            CHECK_GEOREF_BOUNDS,
            QUALITY_WARNING,
            "Prototype georef bounds — not verified MRMS placement.",
            details,
        )

    return FrameQualityCheck(
        CHECK_GEOREF_BOUNDS,
        QUALITY_OK,
        "WGS84 bounds present for overlay placement.",
        details,
    )


def _check_tile_preview(tile_preview: Optional[dict[str, Any]], preview_path: Optional[str]) -> FrameQualityCheck:
    if not tile_preview:
        return FrameQualityCheck(
            CHECK_TILE_PREVIEW,
            QUALITY_UNAVAILABLE,
            "No tile preview metadata.",
            {"preview_path": preview_path},
        )

    built = int(tile_preview.get("built") or 0)
    details = {
        "tile_mode": tile_preview.get("tile_mode"),
        "built": built,
        "max_z": tile_preview.get("max_z"),
    }
    if built == 0:
        return FrameQualityCheck(
            CHECK_TILE_PREVIEW,
            QUALITY_WARNING,
            "No local raster tiles built — single-image overlay only.",
            details,
        )
    return FrameQualityCheck(
        CHECK_TILE_PREVIEW,
        QUALITY_OK,
        f"Local tile preview built ({built} tiles).",
        details,
    )


def _aggregate_status(checks: list[FrameQualityCheck]) -> str:
    if not checks:
        return QUALITY_UNAVAILABLE
    statuses = {check.status for check in checks}
    if QUALITY_ERROR in statuses:
        return QUALITY_ERROR
    if all(status == QUALITY_UNAVAILABLE for status in statuses):
        return QUALITY_UNAVAILABLE
    if QUALITY_WARNING in statuses:
        return QUALITY_WARNING
    return QUALITY_OK


def assess_frame_quality(
    storage: LocalStorage,
    *,
    decode_output_dir: Optional[str] = None,
    preview_path: Optional[str] = None,
    georef: Optional[dict[str, Any]] = None,
    tile_preview: Optional[dict[str, Any]] = None,
    overlay_visible: bool = False,
    frame_report: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Run local-dev quality checks; advisory only — does not block playback."""
    if frame_report:
        decode_output_dir = decode_output_dir or frame_report.get("decode_output_dir")
        preview_paths = frame_report.get("preview_paths") or []
        if not preview_path and preview_paths:
            preview_path = preview_paths[0]
        tile_preview = tile_preview or frame_report.get("tile_preview")

    manifest_payload = _load_decode_manifest_payload(storage, decode_output_dir)
    artifact = load_decode_manifest(storage, decode_output_dir) if decode_output_dir else None

    checks = [
        _check_artifacts(
            storage,
            preview_path=preview_path,
            decode_output_dir=decode_output_dir,
            overlay_visible=overlay_visible,
        ),
        _check_decode_manifest(storage, decode_output_dir, manifest_payload),
        _check_grid_values(storage, manifest_payload, artifact),
        _check_dimensions(storage, decode_output_dir, manifest_payload, artifact, tile_preview),
        _check_georef_bounds(georef),
        _check_tile_preview(tile_preview, preview_path),
    ]

    overall = _aggregate_status(checks)
    measured: dict[str, Any] = {}
    for check in checks:
        measured.update(check.details)

    return {
        "status": overall,
        "checks": [check.to_dict() for check in checks],
        "measured": measured,
        "diagnostic_only": True,
        "verified_mrms": False,
        "local_dev_only": True,
        "prototype": True,
    }
