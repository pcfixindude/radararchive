from fastapi import APIRouter, Query

from backend.app.config import settings
from backend.app.demo.catalog import DEMO_LAYERS, DEMO_TIMES
from backend.app.schemas.catalog import HealthResponse, LatestResponse, Layer

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=settings.version)


@router.get("/layers", response_model=list[Layer])
def layers() -> list[Layer]:
    return [Layer.model_validate(layer) for layer in DEMO_LAYERS]


@router.get("/times", response_model=list[str])
def times(layer: str = Query(...)) -> list[str]:
    if layer != "mrms_reflectivity":
        return []
    return DEMO_TIMES


@router.get("/latest", response_model=LatestResponse)
def latest(layer: str = Query(...)) -> LatestResponse:
    timestamp = DEMO_TIMES[-1] if layer == "mrms_reflectivity" else None
    return LatestResponse(layer=layer, timestamp=timestamp)
