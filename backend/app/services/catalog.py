from typing import Optional

from sqlalchemy.orm import Session

from backend.app.demo.layer_metadata import get_layer_tile_metadata
from backend.app.models import Layer, Product, RadarFile
from backend.app.models.radar_file import is_placeholder_tile_status
from backend.app.schemas.catalog import Layer as LayerSchema

MRMS_REFLECTIVITY_LAYER_ID = "mrms_reflectivity"


def list_layers(session: Session) -> list[LayerSchema]:
    rows = session.query(Layer).order_by(Layer.id).all()
    result: list[LayerSchema] = []
    for row in rows:
        metadata = get_layer_tile_metadata(row.id)
        result.append(
            LayerSchema(
                id=row.id,
                name=row.name,
                type=row.type,
                available=row.available,
                source=row.source,
                bounds=metadata.get("bounds"),
                minzoom=metadata.get("minzoom"),
                maxzoom=metadata.get("maxzoom"),
                tile_support=bool(metadata.get("tile_support")),
                placeholder=bool(metadata.get("placeholder")),
            )
        )
    return result


def list_times(session: Session, layer_id: str, *, processed_only: bool = False) -> list[str]:
    product_ids = [
        product.id
        for product in session.query(Product).filter(Product.layer_id == layer_id).all()
    ]
    if not product_ids:
        return []

    query = session.query(RadarFile).filter(RadarFile.product_id.in_(product_ids))
    rows = query.order_by(RadarFile.timestamp.asc()).all()
    if processed_only:
        return [row.timestamp for row in rows if is_placeholder_tile_status(row.processed_status)]
    return [row.timestamp for row in rows]


def latest_timestamp(session: Session, layer_id: str) -> Optional[str]:
    times = list_times(session, layer_id)
    return times[-1] if times else None


def get_frame_for_layer_timestamp(
    session: Session,
    layer_id: str,
    timestamp: str,
) -> Optional[RadarFile]:
    layer = session.get(Layer, layer_id)
    if layer is None or not layer.available:
        return None

    product_ids = [
        product.id
        for product in session.query(Product).filter(Product.layer_id == layer_id).all()
    ]
    if not product_ids:
        return None

    frame = (
        session.query(RadarFile)
        .filter(
            RadarFile.product_id.in_(product_ids),
            RadarFile.timestamp == timestamp,
        )
        .one_or_none()
    )
    if frame is None or not is_placeholder_tile_status(frame.processed_status):
        return None
    return frame


def frame_has_processed_tiles(session: Session, layer_id: str, timestamp: str) -> bool:
    return get_frame_for_layer_timestamp(session, layer_id, timestamp) is not None
