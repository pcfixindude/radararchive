"""Dev/prototype catalog status API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.validation import CatalogStatusResponse
from backend.app.services.catalog_status import build_catalog_status

router = APIRouter(prefix="/catalog", tags=["catalog-dev"])


@router.get("/status", response_model=CatalogStatusResponse)
def catalog_status(db: Session = Depends(get_db)) -> CatalogStatusResponse:
    """MRMS catalog counts by status (dev/prototype)."""
    payload = build_catalog_status(db)
    return CatalogStatusResponse(**payload)
