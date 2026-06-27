from sqlalchemy.orm import Session

from backend.app.models import RadarFile
from backend.app.models.radar_file import DOWNLOAD_STATUS_PENDING, PROCESSED_STATUS_PENDING
from backend.app.schemas.mrms import RegisterDiscoveredResult
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE, MrmsDiscoveredFile


def register_discovered_files(
    session: Session,
    discoveries: list[MrmsDiscoveredFile],
) -> RegisterDiscoveredResult:
    """Register discovered MRMS metadata rows without downloading or processing."""
    created = 0
    skipped = 0
    created_keys: list[str] = []

    for item in discoveries:
        existing = (
            session.query(RadarFile)
            .filter(
                (RadarFile.source_url == item.source_url)
                | (
                    (RadarFile.product_id == item.catalog_product_id)
                    & (RadarFile.timestamp == item.timestamp)
                )
            )
            .one_or_none()
        )
        if existing is not None:
            skipped += 1
            continue

        session.add(
            RadarFile(
                product_id=item.catalog_product_id,
                timestamp=item.timestamp,
                raw_path=item.object_key,
                processed_path=None,
                processed_status=PROCESSED_STATUS_PENDING,
                source=MRMS_CATALOG_SOURCE,
                source_provider=item.source_provider,
                source_url=item.source_url,
                file_size_bytes=item.size_bytes,
                download_status=DOWNLOAD_STATUS_PENDING,
            )
        )
        created += 1
        created_keys.append(item.object_key)

    session.commit()
    return RegisterDiscoveredResult(created=created, skipped=skipped, items=created_keys)
