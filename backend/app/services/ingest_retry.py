"""Bounded download retries for bulk MRMS ingest (local dev only)."""

from __future__ import annotations

import time
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from backend.app.services.mrms_downloader import DownloadResult, MrmsDownloadError
from backend.app.services.storage import LocalStorage

DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY_SEC = 0.5

PERMANENT_ERROR_MARKERS = (
    "404",
    "not found",
    "no source_url",
    "not an mrms_discovered",
    "unknown download mode",
    "has no source_url",
)

TRANSIENT_ERROR_MARKERS = (
    "timed out",
    "timeout",
    "request failed",
    "connection",
    "503",
    "502",
    "429",
    "temporary",
    "network",
)


def is_transient_download_error(message: str) -> bool:
    """Return True when a bounded retry may help."""
    lower = message.lower()
    if any(marker in lower for marker in PERMANENT_ERROR_MARKERS):
        return False
    return any(marker in lower for marker in TRANSIENT_ERROR_MARKERS)


def download_row_with_retry(
    session: Session,
    storage: LocalStorage,
    row: Any,
    *,
    force: bool,
    mode: str,
    download_fn: Callable[..., DownloadResult],
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay_sec: float = DEFAULT_RETRY_DELAY_SEC,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> tuple[Optional[DownloadResult], int, Optional[str]]:
    """Attempt download with bounded retries; preserve exact last error message."""
    bounded_retries = max(1, min(max_retries, 10))
    attempts = 0
    last_error: Optional[str] = None

    while attempts < bounded_retries:
        attempts += 1
        try:
            result = download_fn(
                session,
                storage,
                row,
                force=force,
                mode=mode,
            )
            return result, attempts, None
        except MrmsDownloadError as exc:
            last_error = str(exc)
            if not is_transient_download_error(last_error) or attempts >= bounded_retries:
                return None, attempts, last_error
            sleep_fn(retry_delay_sec)

    return None, attempts, last_error
