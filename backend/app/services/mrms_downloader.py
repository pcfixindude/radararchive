"""Download discovered MRMS GRIB2.gz files to local raw storage (no GRIB2 parse)."""

from __future__ import annotations

import gzip
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional, Protocol

import httpx
from sqlalchemy.orm import Session

from backend.app.config import MRMS_SOURCE_MODE_REAL, MRMS_SOURCE_MODE_STUB, settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import (
    DOWNLOAD_STATUS_DOWNLOADED,
    DOWNLOAD_STATUS_FAILED,
    DOWNLOAD_STATUS_PENDING,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.time_utils import format_utc_iso
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE

STUB_GRIB2GZ_TEXT = (
    "# RadarArchive stub GRIB2.gz placeholder — not real NOAA/MRMS data\n"
    "source: mrms_download_stub\n"
)


class MrmsDownloadError(Exception):
    """Raised when MRMS download fails (network, config)."""


class HttpGetBytes(Protocol):
    def __call__(self, url: str) -> bytes: ...


@dataclass
class DownloadResult:
    radar_file_id: int
    timestamp: str
    raw_path: str
    sha256: str
    file_size_bytes: int
    downloaded_at: str
    created: bool
    stub: bool


@dataclass
class DownloadBatchResult:
    downloaded: list[DownloadResult]
    skipped: int
    failed: list[tuple[int, str, str]]


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip())
    return cleaned or "mrms_file.grib2.gz"


def timestamp_token(timestamp: str) -> str:
    return timestamp.replace(":", "").replace("-", "")


def build_mrms_raw_path(
    storage: LocalStorage,
    *,
    product_id: str,
    timestamp: str,
    original_filename: str,
    stub: bool,
) -> str:
    """Safe local path under data/raw/mrms/reflectivity/."""
    token = timestamp_token(timestamp)
    safe_name = sanitize_filename(original_filename)
    if stub:
        return storage.normalize_path("raw", "mrms", "reflectivity", f"{token}_{safe_name}.stub")
    return storage.normalize_path("raw", "mrms", "reflectivity", f"{token}_{safe_name}")


def is_local_mrms_raw_path(path: Optional[str]) -> bool:
    return bool(path and path.startswith("data/raw/mrms/"))


def infer_original_filename(row: RadarFile) -> str:
    if row.source_url:
        return row.source_url.rsplit("/", 1)[-1]
    if row.raw_path and not is_local_mrms_raw_path(row.raw_path):
        return row.raw_path.rsplit("/", 1)[-1]
    return f"MRMS_{row.product_id}_{timestamp_token(row.timestamp)}.grib2.gz"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stub_payload(row: RadarFile) -> bytes:
    text = (
        f"{STUB_GRIB2GZ_TEXT}"
        f"product_id: {row.product_id}\n"
        f"timestamp: {row.timestamp}\n"
        f"source_url: {row.source_url or 'unknown'}\n"
    )
    return gzip.compress(text.encode("utf-8"))


def _default_http_get_bytes(url: str) -> bytes:
    timeout = settings.mrms_request_timeout_seconds
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.content
    except httpx.TimeoutException as exc:
        raise MrmsDownloadError(
            "MRMS download timed out. Check network connectivity or use stub mode."
        ) from exc
    except httpx.HTTPError as exc:
        raise MrmsDownloadError(
            f"MRMS download request failed: {exc}. Use stub mode for offline development."
        ) from exc


def _file_matches_catalog(
    storage: LocalStorage,
    row: RadarFile,
    raw_path: str,
) -> bool:
    if not storage.path_exists(raw_path):
        return False
    if row.sha256:
        return storage.sha256(raw_path) == row.sha256
    if row.file_size_bytes is not None:
        size = storage.absolute_path(raw_path).stat().st_size
        return size == row.file_size_bytes
    return True


def _already_downloaded(storage: LocalStorage, row: RadarFile, *, force: bool) -> bool:
    if force:
        return False
    if row.download_status != DOWNLOAD_STATUS_DOWNLOADED:
        return False
    if not is_local_mrms_raw_path(row.raw_path):
        return False
    return _file_matches_catalog(storage, row, row.raw_path)


def _fetch_bytes(
    row: RadarFile,
    *,
    mode: str,
    http_get_bytes: HttpGetBytes,
) -> tuple[bytes, bool]:
    resolved_mode = mode.lower()
    if resolved_mode == MRMS_SOURCE_MODE_STUB:
        return _stub_payload(row), True
    if resolved_mode != MRMS_SOURCE_MODE_REAL:
        raise MrmsDownloadError(f"Unknown download mode '{mode}'. Use 'stub' or 'real'.")
    if not row.source_url:
        raise MrmsDownloadError(f"Radar file {row.id} has no source_url for real download.")
    return http_get_bytes(row.source_url), False


def download_mrms_row(
    session: Session,
    storage: LocalStorage,
    row: RadarFile,
    *,
    force: bool = False,
    mode: Optional[str] = None,
    http_get_bytes: Optional[HttpGetBytes] = None,
) -> DownloadResult:
    """Download one discovered MRMS catalog row to local raw storage."""
    if row.source != MRMS_CATALOG_SOURCE:
        raise MrmsDownloadError(f"Radar file {row.id} is not an mrms_discovered row.")

    if _already_downloaded(storage, row, force=force):
        assert row.raw_path is not None
        return DownloadResult(
            radar_file_id=row.id,
            timestamp=row.timestamp,
            raw_path=row.raw_path,
            sha256=row.sha256 or storage.sha256(row.raw_path),
            file_size_bytes=row.file_size_bytes or storage.absolute_path(row.raw_path).stat().st_size,
            downloaded_at=row.downloaded_at or "",
            created=False,
            stub=row.raw_path.endswith(".stub"),
        )

    resolved_mode = (mode or settings.mrms_source_mode).lower()
    getter = http_get_bytes or _default_http_get_bytes
    original_name = infer_original_filename(row)
    stub = resolved_mode == MRMS_SOURCE_MODE_STUB

    try:
        payload, is_stub = _fetch_bytes(row, mode=resolved_mode, http_get_bytes=getter)
    except MrmsDownloadError:
        row.download_status = DOWNLOAD_STATUS_FAILED
        session.commit()
        raise

    raw_path = build_mrms_raw_path(
        storage,
        product_id=row.product_id,
        timestamp=row.timestamp,
        original_filename=original_name,
        stub=is_stub,
    )
    checksum = _sha256_bytes(payload)
    downloaded_at = format_utc_iso(datetime.now(timezone.utc))

    storage.write_bytes(raw_path, payload, overwrite=force)
    row.raw_path = raw_path
    row.file_size_bytes = len(payload)
    row.sha256 = checksum
    row.download_status = DOWNLOAD_STATUS_DOWNLOADED
    row.downloaded_at = downloaded_at
    session.commit()

    return DownloadResult(
        radar_file_id=row.id,
        timestamp=row.timestamp,
        raw_path=raw_path,
        sha256=checksum,
        file_size_bytes=len(payload),
        downloaded_at=downloaded_at,
        created=True,
        stub=is_stub,
    )


def download_pending_mrms(
    session: Session,
    storage: LocalStorage,
    *,
    limit: int = 5,
    force: bool = False,
    mode: Optional[str] = None,
    http_get_bytes: Optional[HttpGetBytes] = None,
) -> DownloadBatchResult:
    """Download up to `limit` pending mrms_discovered rows."""
    storage.ensure_directories("data/raw/mrms/reflectivity")

    rows = (
        session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .filter(RadarFile.source_url.isnot(None))
        .order_by(RadarFile.timestamp.desc())
        .all()
    )

    downloaded: list[DownloadResult] = []
    failed: list[tuple[int, str, str]] = []
    skipped = 0
    attempted = 0

    for row in rows:
        if attempted >= limit:
            break
        if not force and row.download_status == DOWNLOAD_STATUS_DOWNLOADED:
            if is_local_mrms_raw_path(row.raw_path) and _file_matches_catalog(storage, row, row.raw_path):
                skipped += 1
                continue

        attempted += 1
        try:
            result = download_mrms_row(
                session,
                storage,
                row,
                force=force,
                mode=mode,
                http_get_bytes=http_get_bytes,
            )
            if result.created:
                downloaded.append(result)
            else:
                skipped += 1
        except MrmsDownloadError as exc:
            failed.append((row.id, row.timestamp, str(exc)))

    return DownloadBatchResult(downloaded=downloaded, skipped=skipped, failed=failed)


def download_status_summary(session: Session) -> dict:
    """Counts of mrms_discovered download states for dev API."""
    rows = session.query(RadarFile).filter(RadarFile.source == MRMS_CATALOG_SOURCE).all()
    summary = {
        "total": len(rows),
        "pending": 0,
        "downloaded": 0,
        "failed": 0,
    }
    for row in rows:
        status = row.download_status or DOWNLOAD_STATUS_PENDING
        if status == DOWNLOAD_STATUS_DOWNLOADED:
            summary["downloaded"] += 1
        elif status == DOWNLOAD_STATUS_FAILED:
            summary["failed"] += 1
        else:
            summary["pending"] += 1
    return summary
