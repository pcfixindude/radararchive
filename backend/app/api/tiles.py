from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.app.api.deps import ensure_plan_exists, resolve_demo_plan
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.services import access_control as access_service
from backend.app.services import catalog as catalog_service
from backend.app.services.decoded_tile_cache import serve_tile_with_optional_decode
from backend.app.services.storage import LocalStorage

router = APIRouter()


def _tile_response_headers(tile_mode: str, raw_kind: str = "") -> dict[str, str]:
    return {
        "Cache-Control": "no-store",
        "X-RadarArchive-Tile": tile_mode,
        "X-RadarArchive-Production-Rendering": "false",
        "X-RadarArchive-Raw-Kind": raw_kind,
    }


@router.get("/tiles/config")
def tiles_config() -> dict:
    """Dev endpoint: tile serving mode configuration."""
    return {
        "enable_decoded_tiles": settings.enable_decoded_tiles,
        "default_mode": "placeholder",
        "decoded_mode": "decoded-prototype",
        "production_rendering": False,
        "note": "Decoded tiles are prototype-only and require ENABLE_DECODED_TILES=true plus decode artifacts.",
    }


@router.get("/tiles/{layer}/{timestamp}/{z}/{x}/{y}.png")
def get_tile(
    layer: str,
    timestamp: str,
    z: int,
    x: int,
    y: int,
    plan: str = Depends(resolve_demo_plan),
    db: Session = Depends(get_db),
) -> Response:
    ensure_plan_exists(db, plan)
    reference_latest = catalog_service.latest_timestamp(db, layer)
    if reference_latest is None:
        raise HTTPException(status_code=404, detail="Tile unavailable for layer/timestamp")

    if not access_service.is_timestamp_allowed(
        db,
        plan,
        timestamp,
        reference_latest_iso=reference_latest,
    ):
        raise HTTPException(
            status_code=403,
            detail=access_service.plan_blocked_detail(db, plan, timestamp, reference_latest),
        )

    frame = catalog_service.get_frame_for_layer_timestamp(db, layer, timestamp)
    if frame is None:
        raise HTTPException(status_code=404, detail="Tile unavailable for layer/timestamp")

    storage = LocalStorage(settings.local_storage_root)
    served = serve_tile_with_optional_decode(
        storage,
        frame,
        timestamp,
        enable_decoded_tiles=settings.enable_decoded_tiles,
        z=z,
        x=x,
        y=y,
    )

    headers = _tile_response_headers(served.tile_mode, frame.raw_kind or "")
    if served.fallback:
        headers["X-RadarArchive-Tile-Fallback"] = "true"
    if served.from_cache:
        headers["X-RadarArchive-Tile-Cache"] = "hit"

    return Response(content=served.png_bytes, media_type="image/png", headers=headers)
