from fastapi import APIRouter, HTTPException, Query

from backend.app.config import settings
from backend.app.schemas.mrms import MrmsDiscoveredFileSchema, MrmsDiscoveryResponse
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
