"""Find real downloaded MRMS GRIB2.gz catalog candidates for inspection."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.app.models import RadarFile
from backend.app.services.raw_file_classifier import RAW_KIND_MRMS_REAL_GRIB2, classify_raw_file
from backend.app.services.storage import LocalStorage
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE


@dataclass(frozen=True)
class MrmsInspectCandidate:
    radar_file_id: int
    timestamp: str
    raw_path: str
    source: str
    raw_kind: str


def find_real_mrms_inspect_candidates(
    session: Session,
    storage: LocalStorage,
    *,
    limit: int = 1,
) -> list[MrmsInspectCandidate]:
    """Return latest catalog rows pointing at real local .grib2.gz files."""
    rows = (
        session.query(RadarFile)
        .filter(RadarFile.source == MRMS_CATALOG_SOURCE)
        .order_by(RadarFile.timestamp.desc())
        .all()
    )

    candidates: list[MrmsInspectCandidate] = []
    for row in rows:
        if not row.raw_path:
            continue
        raw_kind = row.raw_kind or classify_raw_file(row)
        if raw_kind != RAW_KIND_MRMS_REAL_GRIB2:
            continue
        if not row.raw_path.lower().endswith(".grib2.gz"):
            continue
        if not storage.path_exists(row.raw_path):
            continue
        candidates.append(
            MrmsInspectCandidate(
                radar_file_id=row.id,
                timestamp=row.timestamp,
                raw_path=row.raw_path,
                source=row.source,
                raw_kind=raw_kind,
            )
        )
        if len(candidates) >= limit:
            break
    return candidates
