from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas.catalog import HealthResponse, LatestResponse, Layer
from backend.app.services import catalog as catalog_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=settings.version)


@router.get("/layers", response_model=list[Layer])
def layers(db: Session = Depends(get_db)) -> list[Layer]:
    return catalog_service.list_layers(db)


@router.get("/times", response_model=list[str])
def times(
    layer: str = Query(...),
    processed_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> list[str]:
    return catalog_service.list_times(db, layer, processed_only=processed_only)


@router.get("/latest", response_model=LatestResponse)
def latest(layer: str = Query(...), db: Session = Depends(get_db)) -> LatestResponse:
    timestamp = catalog_service.latest_timestamp(db, layer)
    return LatestResponse(layer=layer, timestamp=timestamp)
