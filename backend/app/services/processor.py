from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models import RadarFile
from backend.app.models.radar_file import PROCESSED_STATUS_PENDING, PROCESSED_STATUS_PROCESSED
from backend.app.services.storage import LocalStorage
from backend.app.services.tile_service import generate_placeholder_tile_png
from backend.app.services.time_utils import format_utc_iso


@dataclass
class ProcessResult:
    radar_file_id: int
    product_id: str
    timestamp: str
    processed_path: str
    processed_at: str
    created: bool


@dataclass
class ProcessBatchResult:
    processed: list[ProcessResult]
    skipped: int


def _resolve_processed_png_path(storage: LocalStorage, row: RadarFile) -> str:
    token = row.timestamp.replace(":", "").replace("-", "")
    raw_path = row.raw_path or ""
    if "mrms/reflectivity" in raw_path or row.product_id == "mrms_reflectivity":
        return storage.normalize_path("processed", "mrms", "reflectivity", f"{token}.png")
    return storage.normalize_path("processed", "demo", row.product_id, f"{token}.png")


def _needs_processing(storage: LocalStorage, row: RadarFile) -> bool:
    if not row.raw_path or not storage.path_exists(row.raw_path):
        return False
    if row.processed_status != PROCESSED_STATUS_PROCESSED:
        return True
    if not row.processed_path or not storage.path_exists(row.processed_path):
        return True
    return False


def process_pending_frames(session: Session, storage: LocalStorage) -> ProcessBatchResult:
    """Process raw stub frames into processed placeholder PNG files (stub only)."""
    storage.ensure_storage_layout()
    now = format_utc_iso(datetime.now(timezone.utc))

    rows = session.query(RadarFile).order_by(RadarFile.timestamp.asc()).all()
    processed: list[ProcessResult] = []
    skipped = 0

    for row in rows:
        if not _needs_processing(storage, row):
            skipped += 1
            continue

        processed_path = _resolve_processed_png_path(storage, row)
        png_bytes = generate_placeholder_tile_png()
        already_processed = row.processed_status == PROCESSED_STATUS_PROCESSED

        storage.write_bytes(processed_path, png_bytes, overwrite=True)
        row.processed_path = processed_path
        row.processed_status = PROCESSED_STATUS_PROCESSED
        row.processed_at = now

        processed.append(
            ProcessResult(
                radar_file_id=row.id,
                product_id=row.product_id,
                timestamp=row.timestamp,
                processed_path=processed_path,
                processed_at=now,
                created=not already_processed,
            )
        )

    session.commit()
    return ProcessBatchResult(processed=processed, skipped=skipped)
