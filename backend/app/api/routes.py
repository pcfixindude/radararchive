from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import ensure_plan_exists, resolve_demo_plan
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas.catalog import HealthResponse, LatestResponse, Layer
from backend.app.services import access_control as access_service
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
    plan: str = Depends(resolve_demo_plan),
    db: Session = Depends(get_db),
) -> list[str]:
    ensure_plan_exists(db, plan)
    timestamps = catalog_service.list_times(db, layer, processed_only=processed_only)
    reference_latest = catalog_service.latest_timestamp(db, layer)
    return access_service.filter_timestamps_by_plan(
        db,
        plan,
        timestamps,
        reference_latest_iso=reference_latest,
    )


@router.get("/latest", response_model=LatestResponse)
def latest(
    layer: str = Query(...),
    plan: str = Depends(resolve_demo_plan),
    db: Session = Depends(get_db),
) -> LatestResponse:
    ensure_plan_exists(db, plan)
    timestamps = catalog_service.list_times(db, layer)
    reference_latest = catalog_service.latest_timestamp(db, layer)
    allowed = access_service.filter_timestamps_by_plan(
        db,
        plan,
        timestamps,
        reference_latest_iso=reference_latest,
    )
    return LatestResponse(layer=layer, timestamp=allowed[-1] if allowed else None)
