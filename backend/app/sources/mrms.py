"""MRMS public source discovery (listing only — no GRIB2 download/parse)."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, List, Optional, Protocol

import httpx

from backend.app.config import MRMS_SOURCE_MODE_REAL, MRMS_SOURCE_MODE_STUB, settings

MRMS_SOURCE_PROVIDER = "noaa_aws"
MRMS_CATALOG_SOURCE = "mrms_discovered"

# NOAA open-data bucket layout (see docs/DATA_SOURCES.md).
MRMS_PRODUCTS = {
    "MRMS_ReflectivityAtLowestAltitude": {
        "folder": "ReflectivityAtLowestAltitude_00.50",
        "catalog_product_id": "mrms_reflectivity",
        "filename_prefix": "MRMS_ReflectivityAtLowestAltitude_00.50",
    },
}

MRMS_FILENAME_RE = re.compile(
    r"MRMS_ReflectivityAtLowestAltitude_00\.50_(\d{8})-(\d{6})\.grib2\.gz$",
    re.IGNORECASE,
)

S3_NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}


class MrmsDiscoveryError(Exception):
    """Raised when MRMS discovery fails (network, parse, config)."""


@dataclass(frozen=True)
class MrmsDiscoveredFile:
    product: str
    timestamp: str
    object_key: str
    source_url: str
    file_name: str
    size_bytes: Optional[int]
    source_provider: str = MRMS_SOURCE_PROVIDER
    catalog_product_id: str = "mrms_reflectivity"


class HttpGetter(Protocol):
    def __call__(self, url: str) -> str: ...


def mrms_stamp_to_iso(date_yyyymmdd: str, time_hhmmss: str) -> str:
    return (
        f"{date_yyyymmdd[0:4]}-{date_yyyymmdd[4:6]}-{date_yyyymmdd[6:8]}"
        f"T{time_hhmmss[0:2]}:{time_hhmmss[2:4]}:{time_hhmmss[4:6]}Z"
    )


def parse_mrms_object_key(object_key: str, product: str = "MRMS_ReflectivityAtLowestAltitude") -> Optional[MrmsDiscoveredFile]:
    """Parse a NOAA MRMS S3 object key into normalized discovery metadata."""
    meta = MRMS_PRODUCTS.get(product)
    if meta is None:
        return None

    file_name = object_key.rsplit("/", 1)[-1]
    match = MRMS_FILENAME_RE.search(file_name)
    if match is None:
        return None

    date_part, time_part = match.group(1), match.group(2)
    timestamp = mrms_stamp_to_iso(date_part, time_part)
    bucket = settings.mrms_s3_bucket
    source_url = f"https://{bucket}.s3.amazonaws.com/{object_key}"

    return MrmsDiscoveredFile(
        product=product,
        timestamp=timestamp,
        object_key=object_key,
        source_url=source_url,
        file_name=file_name,
        size_bytes=None,
        catalog_product_id=meta["catalog_product_id"],
    )


def build_date_prefix(product: str, date_yyyymmdd: str) -> str:
    meta = MRMS_PRODUCTS[product]
    return f"{settings.mrms_s3_region_prefix}/{meta['folder']}/{date_yyyymmdd}/"


def build_s3_list_url(prefix: str, max_keys: int = 1000) -> str:
    bucket = settings.mrms_s3_bucket
    return (
        f"https://{bucket}.s3.amazonaws.com/"
        f"?list-type=2&prefix={prefix}&max-keys={max_keys}"
    )


def parse_list_objects_xml(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    items: list[dict] = []
    for contents in root.findall("s3:Contents", S3_NS):
        key = contents.findtext("s3:Key", default="", namespaces=S3_NS)
        size_text = contents.findtext("s3:Size", default="", namespaces=S3_NS)
        if not key:
            continue
        size_bytes = int(size_text) if size_text.isdigit() else None
        items.append({"key": key, "size_bytes": size_bytes})
    return items


def _default_http_get(url: str) -> str:
    timeout = settings.mrms_request_timeout_seconds
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.TimeoutException as exc:
        raise MrmsDiscoveryError(
            "MRMS discovery timed out. Check network connectivity or use MRMS_SOURCE_MODE=stub."
        ) from exc
    except httpx.HTTPError as exc:
        raise MrmsDiscoveryError(
            f"MRMS discovery request failed: {exc}. Use MRMS_SOURCE_MODE=stub for offline development."
        ) from exc


def list_recent_object_keys(
    product: str,
    *,
    lookback_days: int,
    http_get: Callable[[str], str] = _default_http_get,
) -> list[dict]:
    now = datetime.now(timezone.utc)
    collected: list[dict] = []

    for day_offset in range(lookback_days):
        day = now - timedelta(days=day_offset)
        date_str = day.strftime("%Y%m%d")
        prefix = build_date_prefix(product, date_str)
        url = build_s3_list_url(prefix)
        xml_text = http_get(url)
        collected.extend(parse_list_objects_xml(xml_text))

    return collected


def stub_discoveries(product: str, limit: int) -> List[MrmsDiscoveredFile]:
    """Offline-safe sample listings for tests and MRMS_SOURCE_MODE=stub."""
    # Use 20260626 timestamps so catalog registration does not collide with demo seed (20260627).
    samples = [
        "CONUS/ReflectivityAtLowestAltitude_00.50/20260626/MRMS_ReflectivityAtLowestAltitude_00.50_20260626-200000.grib2.gz",
        "CONUS/ReflectivityAtLowestAltitude_00.50/20260626/MRMS_ReflectivityAtLowestAltitude_00.50_20260626-195500.grib2.gz",
        "CONUS/ReflectivityAtLowestAltitude_00.50/20260626/MRMS_ReflectivityAtLowestAltitude_00.50_20260626-195000.grib2.gz",
        "CONUS/ReflectivityAtLowestAltitude_00.50/20260626/MRMS_ReflectivityAtLowestAltitude_00.50_20260626-194500.grib2.gz",
        "CONUS/ReflectivityAtLowestAltitude_00.50/20260626/MRMS_ReflectivityAtLowestAltitude_00.50_20260626-194000.grib2.gz",
        "CONUS/ReflectivityAtLowestAltitude_00.50/20260626/MRMS_ReflectivityAtLowestAltitude_00.50_20260626-193500.grib2.gz",
        "CONUS/ReflectivityAtLowestAltitude_00.50/20260626/MRMS_ReflectivityAtLowestAltitude_00.50_20260626-193000.grib2.gz",
        "CONUS/ReflectivityAtLowestAltitude_00.50/20260626/MRMS_ReflectivityAtLowestAltitude_00.50_20260626-192500.grib2.gz",
        "CONUS/ReflectivityAtLowestAltitude_00.50/20260626/MRMS_ReflectivityAtLowestAltitude_00.50_20260626-192000.grib2.gz",
        "CONUS/ReflectivityAtLowestAltitude_00.50/20260626/MRMS_ReflectivityAtLowestAltitude_00.50_20260626-191500.grib2.gz",
    ]
    discoveries: list[MrmsDiscoveredFile] = []
    for key in samples[:limit]:
        parsed = parse_mrms_object_key(key, product)
        if parsed is not None:
            discoveries.append(
                MrmsDiscoveredFile(
                    product=parsed.product,
                    timestamp=parsed.timestamp,
                    object_key=parsed.object_key,
                    source_url=parsed.source_url,
                    file_name=parsed.file_name,
                    size_bytes=123456,
                    catalog_product_id=parsed.catalog_product_id,
                )
            )
    return discoveries


def discover_latest_mrms(
    product: str = "MRMS_ReflectivityAtLowestAltitude",
    *,
    limit: Optional[int] = None,
    mode: Optional[str] = None,
    http_get: Optional[HttpGetter] = None,
) -> List[MrmsDiscoveredFile]:
    """Discover latest MRMS candidate files (metadata only, no download)."""
    if product not in MRMS_PRODUCTS:
        raise MrmsDiscoveryError(f"Unsupported MRMS product: {product}")

    resolved_limit = limit or settings.mrms_discovery_limit
    resolved_mode = (mode or settings.mrms_source_mode).lower()

    if resolved_mode == MRMS_SOURCE_MODE_STUB:
        return stub_discoveries(product, resolved_limit)

    if resolved_mode != MRMS_SOURCE_MODE_REAL:
        raise MrmsDiscoveryError(
            f"Unknown MRMS_SOURCE_MODE '{resolved_mode}'. Use 'stub' or 'real'."
        )

    getter = http_get or _default_http_get
    raw_items = list_recent_object_keys(
        product,
        lookback_days=settings.mrms_discovery_lookback_days,
        http_get=getter,
    )

    parsed: list[MrmsDiscoveredFile] = []
    for item in raw_items:
        discovery = parse_mrms_object_key(item["key"], product)
        if discovery is None:
            continue
        parsed.append(
            MrmsDiscoveredFile(
                product=discovery.product,
                timestamp=discovery.timestamp,
                object_key=discovery.object_key,
                source_url=discovery.source_url,
                file_name=discovery.file_name,
                size_bytes=item.get("size_bytes"),
                catalog_product_id=discovery.catalog_product_id,
            )
        )

    parsed.sort(key=lambda row: row.timestamp, reverse=True)

    # De-dupe by object key while preserving order.
    seen: set[str] = set()
    unique: list[MrmsDiscoveredFile] = []
    for row in parsed:
        if row.object_key in seen:
            continue
        seen.add(row.object_key)
        unique.append(row)

    return unique[:resolved_limit]
