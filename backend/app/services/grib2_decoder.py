"""GRIB2 raster decode prototype — optional dependencies, no production rendering."""

from __future__ import annotations

import json
import struct
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Protocol

from backend.app.services.grib2_inspector import (
    DecoderAvailability,
    Grib2InspectError,
    classify_raw_path,
    detect_decoder_availability,
    inspect_grib2_file,
    is_inspectable_grib2_path,
    stage_grib2_gz,
)
from backend.app.services.overlay_sync import extract_timestamp_from_raw_path
from backend.app.services.render_metadata import (
    build_geo_metadata_for_decode,
    enrich_geo_metadata_from_rasterio,
    write_geo_metadata,
)
from backend.app.services.storage import LocalStorage

DECODE_OUTPUT_ROOT = "data/staging/grib2_decode"
MANIFEST_NAME = "decode_manifest.json"
RASTER_RAW_NAME = "normalized.raw"
RASTER_TIF_NAME = "normalized.tif"


class Grib2DecodeError(Exception):
    """Raised when decode cannot proceed."""


@dataclass
class Grib2DecodeResult:
    raw_path: str
    raw_kind: str
    success: bool
    decoder_unavailable: bool = False
    decoder_used: Optional[str] = None
    staged_grib2_path: Optional[str] = None
    output_dir: Optional[str] = None
    manifest_path: Optional[str] = None
    raster_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    value_min: Optional[float] = None
    value_max: Optional[float] = None
    notes: list[str] = field(default_factory=list)
    error: Optional[str] = None


class RasterDecodeFn(Protocol):
    def __call__(self, grib_abs_path: Path, output_dir: Path) -> dict: ...


def decode_output_token(raw_path: str) -> str:
    """Deterministic folder token from a raw path."""
    name = raw_path.rsplit("/", 1)[-1]
    for suffix in (".grib2.gz", ".grib2", ".gz"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    if name.endswith(".stub"):
        name = name[: -len(".stub")]
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)
    return safe or "grib2_frame"


def build_decode_output_dir(storage: LocalStorage, raw_path: str) -> str:
    token = decode_output_token(raw_path)
    return storage.normalize_path(DECODE_OUTPUT_ROOT, token)


def _write_manifest(output_dir: Path, payload: dict) -> Path:
    manifest_path = output_dir / MANIFEST_NAME
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def _normalize_float32_grid(values: list[float]) -> tuple[bytes, float, float]:
    if not values:
        return b"", 0.0, 0.0
    vmin = min(values)
    vmax = max(values)
    if vmax == vmin:
        normalized = [0.0 for _ in values]
    else:
        normalized = [(v - vmin) / (vmax - vmin) for v in values]
    packed = struct.pack(f"{len(normalized)}f", *normalized)
    return packed, vmin, vmax


def decode_with_wgrib2_bin(
    grib_abs_path: Path,
    output_dir: Path,
    *,
    wgrib2_bin: str = "wgrib2",
    timeout: float = 60.0,
    runner: Optional[Callable[..., subprocess.CompletedProcess[str]]] = None,
) -> dict:
    """Export first GRIB message as IEEE binary grid via wgrib2 (optional tool)."""
    run = runner or subprocess.run
    bin_path = output_dir / "wgrib2_grid.bin"
    command = [wgrib2_bin, str(grib_abs_path), "-d", "1", "-bin", "-nh", "-ieee", "-o", str(bin_path)]
    completed = run(command, capture_output=True, text=True, timeout=timeout, check=False)
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        raise Grib2DecodeError(f"wgrib2 bin export failed: {stderr or 'unknown error'}")

    if not bin_path.exists():
        raise Grib2DecodeError("wgrib2 bin export did not produce output file.")

    raw_bytes = bin_path.read_bytes()
    if len(raw_bytes) % 4 != 0:
        raise Grib2DecodeError("wgrib2 bin output size is not float32-aligned.")

    count = len(raw_bytes) // 4
    values = list(struct.unpack(f"{count}f", raw_bytes))
    normalized_bytes, vmin, vmax = _normalize_float32_grid(values)

    raster_path = output_dir / RASTER_RAW_NAME
    raster_path.write_bytes(normalized_bytes)

    # wgrib2 bin export is a 1-D dump; treat as 1 x N for prototype metadata.
    return {
        "decoder": "wgrib2_bin",
        "width": count,
        "height": 1,
        "value_min": vmin,
        "value_max": vmax,
        "raster_path": raster_path.name,
        "source_grid_bytes": len(raw_bytes),
    }


def decode_with_rasterio(grib_abs_path: Path, output_dir: Path) -> dict:
    """Decode first band with rasterio when installed (optional)."""
    try:
        import rasterio
        import numpy as np
    except ImportError as exc:
        raise Grib2DecodeError("rasterio/numpy not available") from exc

    with rasterio.open(grib_abs_path) as dataset:
        data = dataset.read(1).astype("float32")
        height, width = data.shape
        vmin = float(np.nanmin(data))
        vmax = float(np.nanmax(data))
        if vmax == vmin:
            normalized = np.zeros_like(data, dtype="float32")
        else:
            normalized = ((data - vmin) / (vmax - vmin)).astype("float32")

        raster_path = output_dir / RASTER_TIF_NAME
        profile = dataset.profile.copy()
        profile.update(dtype="float32", count=1, compress="deflate")
        with rasterio.open(raster_path, "w", **profile) as dst:
            dst.write(normalized, 1)

    return {
        "decoder": "rasterio",
        "width": width,
        "height": height,
        "value_min": vmin,
        "value_max": vmax,
        "raster_path": raster_path.name,
    }


def _select_raster_decoder(
    availability: DecoderAvailability,
) -> Optional[str]:
    if availability.rasterio:
        return "rasterio"
    if availability.wgrib2:
        return "wgrib2_bin"
    return None


def decode_grib2_file(
    storage: LocalStorage,
    raw_path: str,
    *,
    decoders: Optional[DecoderAvailability] = None,
    wgrib2_runner: Optional[Callable[..., subprocess.CompletedProcess[str]]] = None,
    raster_decoder: Optional[RasterDecodeFn] = None,
    timeout: float = 60.0,
) -> Grib2DecodeResult:
    """Decode one GRIB2 file into a prototype normalized raster artifact."""
    raw_kind = classify_raw_path(raw_path)
    result = Grib2DecodeResult(
        raw_path=raw_path,
        raw_kind=raw_kind,
        success=False,
    )

    if not storage.path_exists(raw_path):
        result.error = f"File not found: {raw_path}"
        return result

    if not is_inspectable_grib2_path(raw_path, raw_kind):
        result.error = "File is not a real GRIB2 candidate (.grib2 or .grib2.gz required)."
        result.notes.append("Stub/demo files cannot be decoded.")
        return result

    inspect_result = inspect_grib2_file(
        storage,
        raw_path,
        decoders=decoders,
        wgrib2_runner=wgrib2_runner,
        timeout=timeout,
    )
    result.staged_grib2_path = inspect_result.staged_grib2_path

    if inspect_result.error:
        result.error = inspect_result.error
        return result

    if inspect_result.has_grib_magic is False:
        result.error = "Invalid GRIB2 content (missing GRIB magic)."
        return result

    availability = decoders or detect_decoder_availability()
    result.notes.append(availability.summary_message())

    if raster_decoder is not None:
        decoder_name = "custom"
    else:
        decoder_name = _select_raster_decoder(availability)
    if decoder_name is None:
        result.decoder_unavailable = True
        result.notes.append(
            "Decoder unavailable for raster prototype. Install rasterio (preferred) or wgrib2."
        )
        result.notes.append("Placeholder map tiles remain the default API behavior.")
        return result

    output_repo_dir = build_decode_output_dir(storage, raw_path)
    storage.ensure_directories(output_repo_dir)
    output_abs_dir = storage.absolute_path(output_repo_dir)
    output_abs_dir.mkdir(parents=True, exist_ok=True)

    if raw_path.lower().endswith(".grib2.gz"):
        staged_repo_path, _ = stage_grib2_gz(
            storage,
            raw_path,
            staging_dir="data/staging/grib2_inspect",
        )
        grib_abs_path = storage.absolute_path(staged_repo_path)
        result.staged_grib2_path = staged_repo_path
    else:
        grib_abs_path = storage.absolute_path(raw_path)

    try:
        if raster_decoder is not None:
            decode_info = raster_decoder(grib_abs_path, output_abs_dir)
        elif decoder_name == "rasterio":
            decode_info = decode_with_rasterio(grib_abs_path, output_abs_dir)
        else:
            decode_info = decode_with_wgrib2_bin(
                grib_abs_path,
                output_abs_dir,
                wgrib2_bin=availability.wgrib2_path or "wgrib2",
                timeout=timeout,
                runner=wgrib2_runner,
            )
    except Grib2DecodeError as exc:
        result.error = str(exc)
        return result

    geo = build_geo_metadata_for_decode(
        grid_width=int(decode_info.get("width") or 0),
        grid_height=int(decode_info.get("height") or 0),
        valid_timestamp=extract_timestamp_from_raw_path(raw_path),
    )
    raster_repo_for_geo = None
    raster_name = decode_info.get("raster_path")
    if raster_name:
        raster_repo_for_geo = storage.normalize_path(output_repo_dir, str(raster_name))
        geo = enrich_geo_metadata_from_rasterio(storage, raster_repo_for_geo, geo)
    geo_repo_path = write_geo_metadata(storage, output_repo_dir, geo)

    manifest_payload = {
        "prototype": True,
        "production_rendering": False,
        "raw_path": raw_path,
        "raw_kind": raw_kind,
        "staged_grib2_path": result.staged_grib2_path,
        "decoder": decode_info.get("decoder"),
        "width": decode_info.get("width"),
        "height": decode_info.get("height"),
        "value_min": decode_info.get("value_min"),
        "value_max": decode_info.get("value_max"),
        "raster_path": decode_info.get("raster_path"),
        "bounds": geo.bounds,
        "source_crs": geo.source_crs,
        "georef_quality": geo.georef_quality,
        "note": "Prototype decode artifact only. /tiles still serves placeholders.",
    }
    manifest_abs = _write_manifest(output_abs_dir, manifest_payload)

    result.success = True
    result.decoder_used = str(decode_info.get("decoder"))
    result.output_dir = output_repo_dir
    result.manifest_path = storage.normalize_path(output_repo_dir, MANIFEST_NAME)
    if raster_name:
        result.raster_path = storage.normalize_path(output_repo_dir, str(raster_name))
    result.width = decode_info.get("width")
    result.height = decode_info.get("height")
    result.value_min = decode_info.get("value_min")
    result.value_max = decode_info.get("value_max")
    result.notes.append(f"Wrote prototype manifest: {manifest_abs.name}")
    result.notes.append(f"Wrote geo metadata: {geo_repo_path.rsplit('/', 1)[-1]}")
    result.notes.append("Catalog processed_status and /tiles behavior were not changed.")

    return result
