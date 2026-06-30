"""Local dev decoded map overlay API — prototype only, not verified MRMS."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
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
    timestamp: Optional[str] = Query(None, description="Selected catalog timestamp for frame decode"),
    refresh: bool = Query(False, description="Force re-decode selected frame"),
    session: Session = Depends(get_db),
) -> DecodedOverlayResponse:
    """Compact local decoded preview overlay metadata for the map shell."""
    payload = build_decoded_overlay(
        _storage(),
        selected_timestamp=timestamp,
        session=session,
        force_refresh=refresh,
    )
    return DecodedOverlayResponse(**payload)


@router.get("/decoded-overlay/preview.png")
def get_decoded_overlay_preview(
    timestamp: Optional[str] = Query(None, description="Selected catalog timestamp"),
    session: Session = Depends(get_db),
) -> Response:
    """Serve local colorized decoded preview PNG for selected or latest frame."""
    png_bytes = load_preview_png_bytes(_storage(), selected_timestamp=timestamp, session=session)
    if png_bytes is None:
        raise HTTPException(status_code=404, detail="Local decoded preview PNG not found. Run make decode-retry.")
    return Response(content=png_bytes, media_type="image/png", headers=_TILE_HEADERS)


@router.get("/decoded-overlay/tiles/{z}/{x}/{y}.png")
def get_decoded_overlay_tile(
    z: int,
    x: int,
    y: int,
    timestamp: Optional[str] = Query(None, description="Selected catalog timestamp"),
    session: Session = Depends(get_db),
) -> Response:
    """Serve local dev color tile for selected or latest frame."""
    png_bytes = load_overlay_tile_png(
        _storage(),
        z=z,
        x=x,
        y=y,
        selected_timestamp=timestamp,
        session=session,
    )
    if png_bytes is None:
        raise HTTPException(
            status_code=404,
            detail=f"Local tile z={z} x={x} y={y} not found. Run make decode-retry.",
        )
    return Response(content=png_bytes, media_type="image/png", headers=_TILE_HEADERS)
