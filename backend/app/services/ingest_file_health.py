"""Local raw MRMS file health checks for bulk ingest (prototype only)."""

from __future__ import annotations

from typing import Any, Optional

from backend.app.models import RadarFile
from backend.app.services.mrms_downloader import is_local_mrms_raw_path
from backend.app.services.storage import LocalStorage

HEALTH_VALID = "valid"
HEALTH_EMPTY = "empty"
HEALTH_MISSING = "missing"
HEALTH_CHECKSUM_MISMATCH = "checksum_mismatch"
HEALTH_NO_PATH = "no_path"

MIN_USABLE_RAW_BYTES = 64


def raw_file_health(
    storage: LocalStorage,
    raw_path: Optional[str],
    *,
    expected_sha256: Optional[str] = None,
) -> str:
    """Classify on-disk raw file usability."""
    if not raw_path or not is_local_mrms_raw_path(raw_path):
        return HEALTH_NO_PATH
    if not storage.path_exists(raw_path):
        return HEALTH_MISSING
    size = storage.absolute_path(raw_path).stat().st_size
    if size < MIN_USABLE_RAW_BYTES:
        return HEALTH_EMPTY
    if expected_sha256:
        actual = storage.sha256(raw_path)
        if actual != expected_sha256:
            return HEALTH_CHECKSUM_MISMATCH
    return HEALTH_VALID


def classify_row_raw_file(
    storage: LocalStorage,
    row: RadarFile,
    *,
    repair: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Decide whether a catalog row can reuse its local raw file."""
    if force:
        return {"action": "download", "health": HEALTH_MISSING, "reason": "force"}

    if not is_local_mrms_raw_path(row.raw_path):
        return {"action": "download", "health": HEALTH_NO_PATH, "reason": "no_local_path"}

    health = raw_file_health(storage, row.raw_path, expected_sha256=row.sha256)
    if health == HEALTH_VALID:
        return {"action": "already_present", "health": health, "reason": "valid_file"}

    if health in {HEALTH_EMPTY, HEALTH_MISSING, HEALTH_CHECKSUM_MISMATCH} and repair:
        return {"action": "repair", "health": health, "reason": health}

    if health == HEALTH_EMPTY:
        return {
            "action": "bad_file",
            "health": health,
            "reason": "existing raw file is empty or too small",
        }
    if health == HEALTH_CHECKSUM_MISMATCH:
        return {
            "action": "bad_file",
            "health": health,
            "reason": "existing raw file checksum mismatch",
        }
    if health == HEALTH_MISSING:
        return {"action": "download", "health": health, "reason": "missing_file"}

    return {"action": "download", "health": health, "reason": health}
