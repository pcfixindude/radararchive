from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models import RadarFile
from backend.app.models.radar_file import (
    PROCESSED_STATUS_FAILED,
    PROCESSED_STATUS_PENDING,
    PROCESSED_STATUS_PLACEHOLDER_FOR_REAL_RAW,
    PROCESSED_STATUS_PLACEHOLDER_PROCESSED,
    is_placeholder_tile_status,
)
from backend.app.services.raw_file_classifier import (
    classify_raw_file,
    is_placeholder_raw_kind,
    is_real_grib2_raw_kind,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.tile_service import generate_placeholder_tile_png
from backend.app.services.time_utils import format_utc_iso


@dataclass
class ProcessResult:
    radar_file_id: int
    product_id: str
    timestamp: str
    raw_kind: str
    processed_status: str
    processed_path: Optional[str]
    processed_at: str
    created: bool
    outcome: str


@dataclass
class ProcessBatchResult:
    results: list[ProcessResult]
    processed_count: int
    skipped_count: int
    placeholder_processed_count: int
    placeholder_for_real_raw_count: int
    real_decode_pending_count: int
    failed_count: int

    @property
    def processed(self) -> list[ProcessResult]:
        """Backward-compatible alias for newly processed rows."""
        return [item for item in self.results if item.created]

    @property
    def skipped(self) -> int:
        """Backward-compatible alias."""
        return self.skipped_count


def _timestamp_token(timestamp: str) -> str:
    return timestamp.replace(":", "").replace("-", "")


def _resolve_stub_processed_png_path(storage: LocalStorage, row: RadarFile) -> str:
    token = _timestamp_token(row.timestamp)
    raw_path = row.raw_path or ""
    if "mrms/reflectivity" in raw_path or row.product_id == "mrms_reflectivity":
        return storage.normalize_path("processed", "mrms", "reflectivity", f"{token}.png")
    return storage.normalize_path("processed", "demo", row.product_id, f"{token}.png")


def _resolve_real_raw_preview_png_path(storage: LocalStorage, row: RadarFile) -> str:
    token = _timestamp_token(row.timestamp)
    return storage.normalize_path(
        "processed",
        "mrms",
        "reflectivity",
        f"{token}.placeholder_for_real_raw.png",
    )


def _needs_processing(storage: LocalStorage, row: RadarFile) -> bool:
    if not row.raw_path or not storage.path_exists(row.raw_path):
        return False
    if row.processed_status == PROCESSED_STATUS_FAILED:
        return True
    if not is_placeholder_tile_status(row.processed_status):
        return True
    if not row.processed_path or not storage.path_exists(row.processed_path):
        return True
    return False


def _write_placeholder_png(storage: LocalStorage, path: str) -> None:
    storage.write_bytes(path, generate_placeholder_tile_png(), overwrite=True)


def _process_stub_row(
    storage: LocalStorage,
    row: RadarFile,
    raw_kind: str,
    now: str,
) -> ProcessResult:
    processed_path = _resolve_stub_processed_png_path(storage, row)
    _write_placeholder_png(storage, processed_path)
    already_done = is_placeholder_tile_status(row.processed_status)

    row.raw_kind = raw_kind
    row.processed_path = processed_path
    row.processed_status = PROCESSED_STATUS_PLACEHOLDER_PROCESSED
    row.processed_at = now

    return ProcessResult(
        radar_file_id=row.id,
        product_id=row.product_id,
        timestamp=row.timestamp,
        raw_kind=raw_kind,
        processed_status=PROCESSED_STATUS_PLACEHOLDER_PROCESSED,
        processed_path=processed_path,
        processed_at=now,
        created=not already_done,
        outcome="placeholder_processed",
    )


def _process_real_grib2_row(
    storage: LocalStorage,
    row: RadarFile,
    raw_kind: str,
    now: str,
) -> ProcessResult:
    """Real GRIB2.gz — no decode; optional clearly labeled placeholder preview only."""
    processed_path = _resolve_real_raw_preview_png_path(storage, row)
    _write_placeholder_png(storage, processed_path)
    already_done = row.processed_status == PROCESSED_STATUS_PLACEHOLDER_FOR_REAL_RAW

    row.raw_kind = raw_kind
    row.processed_path = processed_path
    row.processed_status = PROCESSED_STATUS_PLACEHOLDER_FOR_REAL_RAW
    row.processed_at = now

    return ProcessResult(
        radar_file_id=row.id,
        product_id=row.product_id,
        timestamp=row.timestamp,
        raw_kind=raw_kind,
        processed_status=PROCESSED_STATUS_PLACEHOLDER_FOR_REAL_RAW,
        processed_path=processed_path,
        processed_at=now,
        created=not already_done,
        outcome="placeholder_for_real_raw",
    )


def process_pending_frames(session: Session, storage: LocalStorage) -> ProcessBatchResult:
    """Process raw files into placeholder PNGs; real GRIB2 remains decode-not-implemented."""
    storage.ensure_storage_layout()
    now = format_utc_iso(datetime.now(timezone.utc))

    rows = session.query(RadarFile).order_by(RadarFile.timestamp.asc()).all()
    results: list[ProcessResult] = []
    skipped_count = 0
    placeholder_processed_count = 0
    placeholder_for_real_raw_count = 0
    real_decode_pending_count = 0
    failed_count = 0

    for row in rows:
        if not _needs_processing(storage, row):
            skipped_count += 1
            continue

        raw_kind = classify_raw_file(row)

        try:
            if is_real_grib2_raw_kind(raw_kind):
                result = _process_real_grib2_row(storage, row, raw_kind, now)
                placeholder_for_real_raw_count += 1
                real_decode_pending_count += 1
            elif is_placeholder_raw_kind(raw_kind):
                result = _process_stub_row(storage, row, raw_kind, now)
                placeholder_processed_count += 1
            else:
                row.raw_kind = raw_kind
                row.processed_status = PROCESSED_STATUS_FAILED
                failed_count += 1
                results.append(
                    ProcessResult(
                        radar_file_id=row.id,
                        product_id=row.product_id,
                        timestamp=row.timestamp,
                        raw_kind=raw_kind,
                        processed_status=PROCESSED_STATUS_FAILED,
                        processed_path=None,
                        processed_at=now,
                        created=True,
                        outcome="failed",
                    )
                )
                continue
        except OSError:
            row.processed_status = PROCESSED_STATUS_FAILED
            failed_count += 1
            results.append(
                ProcessResult(
                    radar_file_id=row.id,
                    product_id=row.product_id,
                    timestamp=row.timestamp,
                    raw_kind=raw_kind,
                    processed_status=PROCESSED_STATUS_FAILED,
                    processed_path=None,
                    processed_at=now,
                    created=True,
                    outcome="failed",
                )
            )
            continue

        results.append(result)

    session.commit()

    processed_count = sum(1 for item in results if item.created and item.outcome != "failed")

    return ProcessBatchResult(
        results=results,
        processed_count=processed_count,
        skipped_count=skipped_count,
        placeholder_processed_count=placeholder_processed_count,
        placeholder_for_real_raw_count=placeholder_for_real_raw_count,
        real_decode_pending_count=real_decode_pending_count,
        failed_count=failed_count,
    )


def processing_status_summary(session: Session) -> dict:
    rows = session.query(RadarFile).all()
    summary = {
        "total": len(rows),
        "pending": 0,
        "placeholder_processed": 0,
        "placeholder_for_real_raw": 0,
        "real_decode_not_implemented": 0,
        "failed": 0,
    }
    for row in rows:
        status = row.processed_status
        if status == PROCESSED_STATUS_PLACEHOLDER_PROCESSED or status == "processed":
            summary["placeholder_processed"] += 1
        elif status == PROCESSED_STATUS_PLACEHOLDER_FOR_REAL_RAW:
            summary["placeholder_for_real_raw"] += 1
            summary["real_decode_not_implemented"] += 1
        elif status == PROCESSED_STATUS_FAILED:
            summary["failed"] += 1
        elif status == PROCESSED_STATUS_PENDING:
            summary["pending"] += 1
        elif status == PROCESSED_STATUS_REAL_DECODE_NOT_IMPLEMENTED:
            summary["real_decode_not_implemented"] += 1
        else:
            summary["pending"] += 1
    return summary
