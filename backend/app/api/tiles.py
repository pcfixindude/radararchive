from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services import catalog as catalog_service
from backend.app.services.tile_service import generate_placeholder_tile_png

router = APIRouter()


@router.get("/tiles/{layer}/{timestamp}/{z}/{x}/{y}.png")
def get_tile(
    layer: str,
    timestamp: str,
    z: int,
    x: int,
    y: int,
    db: Session = Depends(get_db),
) -> Response:
    frame = catalog_service.get_frame_for_layer_timestamp(db, layer, timestamp)
    if frame is None:
        raise HTTPException(status_code=404, detail="Tile unavailable for layer/timestamp")

    png_bytes = generate_placeholder_tile_png(z=z, x=x, y=y)
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Cache-Control": "no-store", "X-RadarArchive-Tile": "placeholder"},
    )
