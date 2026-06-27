from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models import Layer, Product, RadarFile
from backend.app.models.radar_file import PROCESSED_STATUS_PROCESSED
from backend.app.schemas.catalog import Layer as LayerSchema

MRMS_REFLECTIVITY_LAYER_ID = "mrms_reflectivity"


def list_layers(session: Session) -> list[LayerSchema]:
    rows = session.query(Layer).order_by(Layer.id).all()
    return [
        LayerSchema(
            id=row.id,
            name=row.name,
            type=row.type,
            available=row.available,
            source=row.source,
        )
        for row in rows
    ]


def list_times(session: Session, layer_id: str) -> list[str]:
    product_ids = [
        product.id
        for product in session.query(Product).filter(Product.layer_id == layer_id).all()
    ]
    if not product_ids:
        return []

    rows = (
        session.query(RadarFile.timestamp)
        .filter(RadarFile.product_id.in_(product_ids))
        .order_by(RadarFile.timestamp.asc())
        .all()
    )
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

    return (
        session.query(RadarFile)
        .filter(
            RadarFile.product_id.in_(product_ids),
            RadarFile.timestamp == timestamp,
            RadarFile.processed_status == PROCESSED_STATUS_PROCESSED,
        )
        .one_or_none()
    )


def frame_has_processed_tiles(session: Session, layer_id: str, timestamp: str) -> bool:
    return get_frame_for_layer_timestamp(session, layer_id, timestamp) is not None
