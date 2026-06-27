from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models import Layer, Product, RadarFile
from backend.app.schemas.catalog import Layer as LayerSchema


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
