"""MRMS catalog status helpers for dev/validation tooling."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models import RadarFile
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE


def build_catalog_status(session: Session, *, product_id: str = "mrms_reflectivity") -> dict[str, Any]:
    """Summarize MRMS catalog rows by download/process/render status."""
    query = session.query(RadarFile).filter(RadarFile.product_id == product_id)
    total = query.count()

    mrms_discovered = (
        session.query(RadarFile)
        .filter(RadarFile.product_id == product_id, RadarFile.source == MRMS_CATALOG_SOURCE)
        .count()
    )

    download_rows = (
        session.query(RadarFile.download_status, func.count(RadarFile.id))
        .filter(RadarFile.product_id == product_id)
        .group_by(RadarFile.download_status)
        .all()
    )
    processed_rows = (
        session.query(RadarFile.processed_status, func.count(RadarFile.id))
        .filter(RadarFile.product_id == product_id)
        .group_by(RadarFile.processed_status)
        .all()
    )
    render_rows = (
        session.query(RadarFile.render_status, func.count(RadarFile.id))
        .filter(RadarFile.product_id == product_id)
        .group_by(RadarFile.render_status)
        .all()
    )

    latest_row = (
        session.query(RadarFile.timestamp)
        .filter(RadarFile.product_id == product_id)
        .order_by(RadarFile.timestamp.desc())
        .first()
    )
    earliest_row = (
        session.query(RadarFile.timestamp)
        .filter(RadarFile.product_id == product_id)
        .order_by(RadarFile.timestamp.asc())
        .first()
    )

    latest_downloaded = (
        session.query(RadarFile.timestamp)
        .filter(
            RadarFile.product_id == product_id,
            RadarFile.download_status == "downloaded",
        )
        .order_by(RadarFile.timestamp.desc())
        .first()
    )

    return {
        "product_id": product_id,
        "total_frames": total,
        "mrms_discovered_frames": mrms_discovered,
        "download_status": {status: count for status, count in download_rows},
        "processed_status": {status: count for status, count in processed_rows},
        "render_status": {status: count for status, count in render_rows},
        "latest_timestamp": latest_row[0] if latest_row else None,
        "earliest_timestamp": earliest_row[0] if earliest_row else None,
        "latest_downloaded_timestamp": latest_downloaded[0] if latest_downloaded else None,
        "prototype": True,
        "verified_mrms": False,
    }
