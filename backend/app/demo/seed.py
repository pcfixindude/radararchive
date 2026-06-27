"""Seed demo catalog rows into SQLite for local development."""

from sqlalchemy.orm import Session

from backend.app.demo.catalog import (
    DEMO_ACCESS_PLANS,
    DEMO_LAYERS,
    DEMO_PRODUCTS,
    DEMO_TIMES,
)
from backend.app.models import AccessPlan, Layer, Product, RadarFile


def _demo_storage_paths(product_id: str, timestamp: str) -> tuple[str, str]:
    safe_timestamp = timestamp.replace(":", "").replace("-", "")
    raw_path = f"data/raw/demo/{product_id}/{safe_timestamp}.grib2.stub"
    processed_path = f"data/processed/demo/{product_id}/{safe_timestamp}.png.stub"
    return raw_path, processed_path


def seed_demo_catalog(session: Session, *, reset: bool = False) -> dict[str, int]:
    """Insert demo layers, products, radar files, and access plans."""
    if reset:
        session.query(RadarFile).delete()
        session.query(Product).delete()
        session.query(Layer).delete()
        session.query(AccessPlan).delete()
        session.flush()

    for row in DEMO_LAYERS:
        session.merge(
            Layer(
                id=str(row["id"]),
                name=str(row["name"]),
                type=str(row["type"]),
                available=bool(row["available"]),
                source=str(row["source"]),
            )
        )

    for row in DEMO_PRODUCTS:
        session.merge(
            Product(
                id=row["id"],
                layer_id=row["layer_id"],
                name=row["name"],
                source=row["source"],
            )
        )

    for timestamp in DEMO_TIMES:
        raw_path, processed_path = _demo_storage_paths("mrms_reflectivity", timestamp)
        existing = (
            session.query(RadarFile)
            .filter(RadarFile.product_id == "mrms_reflectivity", RadarFile.timestamp == timestamp)
            .one_or_none()
        )
        if existing is None:
            session.add(
                RadarFile(
                    product_id="mrms_reflectivity",
                    timestamp=timestamp,
                    raw_path=raw_path,
                    processed_path=processed_path,
                    source="demo",
                )
            )
        else:
            existing.raw_path = raw_path
            existing.processed_path = processed_path
            existing.source = "demo"

    for row in DEMO_ACCESS_PLANS:
        session.merge(
            AccessPlan(
                id=str(row["id"]),
                name=str(row["name"]),
                history_days=row["history_days"],
            )
        )

    session.commit()

    return {
        "layers": session.query(Layer).count(),
        "products": session.query(Product).count(),
        "radar_files": session.query(RadarFile).count(),
        "access_plans": session.query(AccessPlan).count(),
    }


def catalog_is_empty(session: Session) -> bool:
    return session.query(Layer).count() == 0
