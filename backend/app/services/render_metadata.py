"""Render status constants and geo-metadata structures for future production tiles."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from backend.app.services.storage import LocalStorage

GEO_METADATA_NAME = "geo_metadata.json"
DECODE_MANIFEST_NAME = "decode_manifest.json"

RENDER_STATUS_PLACEHOLDER = "placeholder"
RENDER_STATUS_DECODED_PROTOTYPE = "decoded_prototype"
RENDER_STATUS_PRODUCTION_PENDING = "production_pending"
RENDER_STATUS_PRODUCTION_RENDERED = "production_rendered"
RENDER_STATUS_PRODUCTION_FAILED = "production_failed"

RENDER_MODE_PLACEHOLDER = "placeholder"
RENDER_MODE_DECODED_PROTOTYPE = "decoded_prototype"
RENDER_MODE_PRODUCTION = "production"

# Approximate CONUS bounds for MRMS prototype metadata (not geo-verified).
DEFAULT_MRMS_BOUNDS = [-125.0, 24.0, -66.0, 50.0]
DEFAULT_OUTPUT_CRS = "EPSG:3857"


@dataclass
class GeoRenderMetadata:
    product_name: str
    valid_timestamp: Optional[str]
    source_crs: Optional[str]
    output_crs: str
    bounds: list[float]
    grid_width: int
    grid_height: int
    pixel_size_x: Optional[float] = None
    pixel_size_y: Optional[float] = None
    transform: Optional[list[float]] = None
    geo_accurate: bool = False
    production_rendering: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GeoRenderMetadata":
        return cls(
            product_name=str(payload.get("product_name", "unknown")),
            valid_timestamp=payload.get("valid_timestamp"),
            source_crs=payload.get("source_crs"),
            output_crs=str(payload.get("output_crs", DEFAULT_OUTPUT_CRS)),
            bounds=list(payload.get("bounds", DEFAULT_MRMS_BOUNDS)),
            grid_width=int(payload.get("grid_width", 0)),
            grid_height=int(payload.get("grid_height", 0)),
            pixel_size_x=payload.get("pixel_size_x"),
            pixel_size_y=payload.get("pixel_size_y"),
            transform=payload.get("transform"),
            geo_accurate=bool(payload.get("geo_accurate", False)),
            production_rendering=bool(payload.get("production_rendering", False)),
            notes=list(payload.get("notes", [])),
        )


def geo_metadata_path(storage: LocalStorage, output_dir: str) -> str:
    return storage.normalize_path(output_dir, GEO_METADATA_NAME)


def write_geo_metadata(
    storage: LocalStorage,
    output_dir: str,
    metadata: GeoRenderMetadata,
) -> str:
    path = geo_metadata_path(storage, output_dir)
    storage.write_text(path, json.dumps(metadata.to_dict(), indent=2, sort_keys=True) + "\n")
    return path


def load_geo_metadata(storage: LocalStorage, output_dir: str) -> Optional[GeoRenderMetadata]:
    path = geo_metadata_path(storage, output_dir)
    if not storage.path_exists(path):
        manifest_path = storage.normalize_path(output_dir, DECODE_MANIFEST_NAME)
        if storage.path_exists(manifest_path):
            return _geo_metadata_from_decode_manifest(storage, manifest_path)
        return None
    try:
        payload = json.loads(storage.absolute_path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return GeoRenderMetadata.from_dict(payload)


def _geo_metadata_from_decode_manifest(storage: LocalStorage, manifest_path: str) -> Optional[GeoRenderMetadata]:
    try:
        payload = json.loads(storage.absolute_path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    width = payload.get("width")
    height = payload.get("height")
    if width is None or height is None:
        return None
    return GeoRenderMetadata(
        product_name="MRMS_ReflectivityAtLowestAltitude",
        valid_timestamp=payload.get("valid_timestamp"),
        source_crs=payload.get("source_crs"),
        output_crs=DEFAULT_OUTPUT_CRS,
        bounds=list(payload.get("bounds", DEFAULT_MRMS_BOUNDS)),
        grid_width=int(width),
        grid_height=int(height),
        geo_accurate=False,
        production_rendering=False,
        notes=["Derived from decode_manifest.json — prototype, not geo-verified."],
    )


def enrich_geo_metadata_from_rasterio(
    storage: LocalStorage,
    raster_path: str,
    metadata: GeoRenderMetadata,
) -> GeoRenderMetadata:
    """Optional enrichment when rasterio is installed (not required)."""
    try:
        import rasterio
    except ImportError:
        metadata.notes.append("rasterio not available — CRS/bounds enrichment skipped.")
        return metadata

    try:
        with rasterio.open(storage.absolute_path(raster_path)) as dataset:
            if dataset.crs:
                metadata.source_crs = str(dataset.crs)
            if dataset.bounds:
                metadata.bounds = [
                    float(dataset.bounds.left),
                    float(dataset.bounds.bottom),
                    float(dataset.bounds.right),
                    float(dataset.bounds.top),
                ]
            if dataset.transform:
                metadata.transform = list(dataset.transform)[:6]
            if dataset.res:
                metadata.pixel_size_x = float(dataset.res[0])
                metadata.pixel_size_y = float(dataset.res[1])
            metadata.notes.append("Enriched from rasterio (optional).")
    except OSError:
        metadata.notes.append("rasterio open failed — using manifest defaults.")
    return metadata


def build_geo_metadata_for_decode(
    *,
    product_name: str = "MRMS_ReflectivityAtLowestAltitude",
    valid_timestamp: Optional[str] = None,
    grid_width: int,
    grid_height: int,
    bounds: Optional[list[float]] = None,
) -> GeoRenderMetadata:
    return GeoRenderMetadata(
        product_name=product_name,
        valid_timestamp=valid_timestamp,
        source_crs=None,
        output_crs=DEFAULT_OUTPUT_CRS,
        bounds=bounds or list(DEFAULT_MRMS_BOUNDS),
        grid_width=grid_width,
        grid_height=grid_height,
        geo_accurate=False,
        production_rendering=False,
        notes=[
            "Prototype geo metadata for future production rendering.",
            "Not geo-accurate — simple grid sampling in decoded prototype tiles.",
        ],
    )
