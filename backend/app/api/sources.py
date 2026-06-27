from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas.mrms import (
    MrmsDiscoveredFileSchema,
    MrmsDiscoveryResponse,
    MrmsDownloadStatusResponse,
    MrmsProcessingStatusResponse,
)
from backend.app.services.mrms_downloader import download_status_summary
from backend.app.services.processor import processing_status_summary
from backend.app.sources.mrms import MrmsDiscoveryError, discover_latest_mrms

router = APIRouter()


@router.get("/sources/mrms/latest", response_model=MrmsDiscoveryResponse)
def mrms_latest_sources(
    product: str = Query("MRMS_ReflectivityAtLowestAltitude"),
    limit: int = Query(default=5, ge=1, le=50),
) -> MrmsDiscoveryResponse:
    """Dev endpoint: list latest discovered MRMS object metadata (no GRIB2 download)."""
    try:
        discoveries = discover_latest_mrms(product, limit=limit)
    except MrmsDiscoveryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    items = [
        MrmsDiscoveredFileSchema(
            product=row.product,
            timestamp=row.timestamp,
            object_key=row.object_key,
            source_url=row.source_url,
            file_name=row.file_name,
            size_bytes=row.size_bytes,
            source_provider=row.source_provider,
            catalog_product_id=row.catalog_product_id,
        )
        for row in discoveries
    ]

    return MrmsDiscoveryResponse(
        mode=settings.mrms_source_mode,
        product=product,
        count=len(items),
        items=items,
    )


@router.get("/sources/mrms/download-status", response_model=MrmsDownloadStatusResponse)
def mrms_download_status(session: Session = Depends(get_db)) -> MrmsDownloadStatusResponse:
    """Dev endpoint: download status counts for mrms_discovered catalog rows."""
    summary = download_status_summary(session)
    return MrmsDownloadStatusResponse(mode=settings.mrms_source_mode, **summary)


@router.get("/sources/mrms/processing-status", response_model=MrmsProcessingStatusResponse)
def mrms_processing_status(session: Session = Depends(get_db)) -> MrmsProcessingStatusResponse:
    """Dev endpoint: processing status counts for all catalog rows."""
    summary = processing_status_summary(session)
    return MrmsProcessingStatusResponse(**summary)
