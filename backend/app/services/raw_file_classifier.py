"""Classify radar raw files by source/type for processing decisions."""

from __future__ import annotations

from backend.app.models.radar_file import RadarFile
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE

RAW_KIND_DEMO_SEEDED_STUB = "demo_seeded_stub"
RAW_KIND_COLLECTOR_STUB = "collector_stub"
RAW_KIND_MRMS_DOWNLOAD_STUB = "mrms_download_stub"
RAW_KIND_MRMS_REAL_GRIB2 = "mrms_real_grib2"
RAW_KIND_UNKNOWN = "unknown"

PLACEHOLDER_RAW_KINDS = frozenset(
    {
        RAW_KIND_DEMO_SEEDED_STUB,
        RAW_KIND_COLLECTOR_STUB,
        RAW_KIND_MRMS_DOWNLOAD_STUB,
    }
)


def classify_raw_file(row: RadarFile) -> str:
    """Infer raw file kind from catalog source and local path."""
    raw = (row.raw_path or "").lower()

    if row.source == "demo" or "/raw/demo/" in raw:
        return RAW_KIND_DEMO_SEEDED_STUB

    if row.source == "collector_stub":
        return RAW_KIND_COLLECTOR_STUB

    if row.source == MRMS_CATALOG_SOURCE or "/raw/mrms/" in raw:
        if raw.endswith(".stub"):
            return RAW_KIND_MRMS_DOWNLOAD_STUB
        if raw.endswith(".grib2.gz"):
            return RAW_KIND_MRMS_REAL_GRIB2

    if raw.endswith(".grib2.stub"):
        return RAW_KIND_COLLECTOR_STUB

    return RAW_KIND_UNKNOWN


def is_placeholder_raw_kind(raw_kind: str) -> bool:
    return raw_kind in PLACEHOLDER_RAW_KINDS


def is_real_grib2_raw_kind(raw_kind: str) -> bool:
    return raw_kind == RAW_KIND_MRMS_REAL_GRIB2
