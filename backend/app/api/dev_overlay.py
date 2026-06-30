"""Local dev decoded map overlay API — prototype only, not verified MRMS."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from backend.app.config import settings
from backend.app.schemas.dev_overlay import DecodedOverlayResponse
from backend.app.services.decoded_overlay import (
    build_decoded_overlay,
    load_overlay_tile_png,
    load_preview_png_bytes,
)
from backend.app.services.storage import LocalStorage

router = APIRouter(prefix="/dev", tags=["dev-local"])

_TILE_HEADERS = {
    "X-RadarArchive-Overlay": "decoded-prototype",
    "X-RadarArchive-Verified-Mrms": "false",
    "X-RadarArchive-Production-Tiles": "false",
    "Cache-Control": "no-store",
}


def _storage() -> LocalStorage:
    return LocalStorage(settings.local_storage_root)


@router.get("/decoded-overlay", response_model=DecodedOverlayResponse)
def get_decoded_overlay(
    timestamp: Optional[str] = Query(None, description="Selected catalog timestamp for overlay sync"),
) -> DecodedOverlayResponse:
    """Compact local decoded preview overlay metadata for the map shell."""
    payload = build_decoded_overlay(_storage(), selected_timestamp=timestamp)
    return DecodedOverlayResponse(**payload)


@router.get("/decoded-overlay/preview.png")
def get_decoded_overlay_preview() -> Response:
    """Serve latest local colorized decoded preview PNG from data/dev/."""
    png_bytes = load_preview_png_bytes(_storage())
    if png_bytes is None:
        raise HTTPException(status_code=404, detail="Local decoded preview PNG not found. Run make decode-retry.")
    return Response(content=png_bytes, media_type="image/png", headers=_TILE_HEADERS)


@router.get("/decoded-overlay/tiles/{z}/{x}/{y}.png")
def get_decoded_overlay_tile(z: int, x: int, y: int) -> Response:
    """Serve local dev color tile from data/dev/mrms_local_render_tiles/."""
    png_bytes = load_overlay_tile_png(_storage(), z=z, x=x, y=y)
    if png_bytes is None:
        raise HTTPException(
            status_code=404,
            detail=f"Local tile z={z} x={x} y={y} not found. Run make decode-retry.",
        )
    return Response(content=png_bytes, media_type="image/png", headers=_TILE_HEADERS)
