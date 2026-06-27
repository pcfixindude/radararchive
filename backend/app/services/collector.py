from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.radar_file import PROCESSED_STATUS_PENDING
from backend.app.models import RadarFile
from backend.app.services import catalog as catalog_service
from backend.app.services.storage import LocalStorage
from backend.app.services.time_utils import next_collection_timestamp

MRMS_REFLECTIVITY_PRODUCT_ID = "mrms_reflectivity"
MRMS_REFLECTIVITY_LAYER_ID = "mrms_reflectivity"
COLLECTOR_SOURCE = "collector_stub"


@dataclass
class CollectResult:
    product_id: str
    layer_id: str
    timestamp: str
    raw_path: str
    processed_path: str
    source: str
    created: bool
    raw_sha256: Optional[str] = None


def collect_mrms_reflectivity_once(
    session: Session,
    storage: LocalStorage,
    *,
    timestamp: Optional[str] = None,
) -> CollectResult:
    """Simulate one MRMS reflectivity collection run (stub only, not real NOAA data)."""
    storage.ensure_storage_layout()

    latest = catalog_service.latest_timestamp(session, MRMS_REFLECTIVITY_LAYER_ID)
    frame_timestamp = timestamp or next_collection_timestamp(latest)

    existing = (
        session.query(RadarFile)
        .filter(
            RadarFile.product_id == MRMS_REFLECTIVITY_PRODUCT_ID,
            RadarFile.timestamp == frame_timestamp,
        )
        .one_or_none()
    )
    if existing is not None:
        raw_sha256 = storage.sha256(existing.raw_path) if existing.raw_path and storage.path_exists(existing.raw_path) else None
        return CollectResult(
            product_id=existing.product_id,
            layer_id=MRMS_REFLECTIVITY_LAYER_ID,
            timestamp=existing.timestamp,
            raw_path=existing.raw_path or "",
            processed_path=existing.processed_path or "",
            source=existing.source,
            created=False,
            raw_sha256=raw_sha256,
        )

    raw_path, processed_path = storage.mrms_reflectivity_paths(frame_timestamp)

    raw_body = (
        "# RadarArchive collector stub - not real MRMS/NOAA data\n"
        f"product: {MRMS_REFLECTIVITY_PRODUCT_ID}\n"
        f"timestamp: {frame_timestamp}\n"
        f"source: {COLLECTOR_SOURCE}\n"
    )
    storage.write_text(raw_path, raw_body, overwrite=False)

    processed_dir = "/".join(processed_path.split("/")[:-1])
    storage.ensure_directories(processed_dir)

    row = RadarFile(
        product_id=MRMS_REFLECTIVITY_PRODUCT_ID,
        timestamp=frame_timestamp,
        raw_path=raw_path,
        processed_path=processed_path,
        processed_status=PROCESSED_STATUS_PENDING,
        source=COLLECTOR_SOURCE,
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    return CollectResult(
        product_id=row.product_id,
        layer_id=MRMS_REFLECTIVITY_LAYER_ID,
        timestamp=row.timestamp,
        raw_path=row.raw_path or raw_path,
        processed_path=row.processed_path or processed_path,
        source=row.source,
        created=True,
        raw_sha256=storage.sha256(raw_path),
    )
