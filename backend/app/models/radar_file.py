from typing import Optional

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base

PROCESSED_STATUS_PENDING = "pending"
PROCESSED_STATUS_PLACEHOLDER_PROCESSED = "placeholder_processed"
PROCESSED_STATUS_REAL_DECODE_PENDING = "real_decode_pending"
PROCESSED_STATUS_REAL_DECODE_NOT_IMPLEMENTED = "real_decode_not_implemented"
PROCESSED_STATUS_PLACEHOLDER_FOR_REAL_RAW = "placeholder_for_real_raw"
PROCESSED_STATUS_FAILED = "failed"

# Legacy alias kept for migration/tests referencing old value.
PROCESSED_STATUS_PROCESSED = PROCESSED_STATUS_PLACEHOLDER_PROCESSED

PLACEHOLDER_TILE_STATUSES = frozenset(
    {
        PROCESSED_STATUS_PLACEHOLDER_PROCESSED,
        PROCESSED_STATUS_PLACEHOLDER_FOR_REAL_RAW,
        "processed",  # legacy rows before Phase 10 migration
    }
)

DOWNLOAD_STATUS_PENDING = "pending"
DOWNLOAD_STATUS_DOWNLOADED = "downloaded"
DOWNLOAD_STATUS_FAILED = "failed"

RENDER_STATUS_PLACEHOLDER = "placeholder"
RENDER_STATUS_DECODED_PROTOTYPE = "decoded_prototype"
RENDER_STATUS_PRODUCTION_PENDING = "production_pending"
RENDER_STATUS_PRODUCTION_RENDERED = "production_rendered"
RENDER_STATUS_PRODUCTION_FAILED = "production_failed"

RENDER_MODE_PLACEHOLDER = "placeholder"
RENDER_MODE_DECODED_PROTOTYPE = "decoded_prototype"
RENDER_MODE_PRODUCTION = "production"


def is_placeholder_tile_status(status: str) -> bool:
    return status in PLACEHOLDER_TILE_STATUSES


class RadarFile(Base):
    __tablename__ = "radar_files"
    __table_args__ = (UniqueConstraint("product_id", "timestamp", name="uq_radar_files_product_timestamp"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    timestamp: Mapped[str] = mapped_column(String, nullable=False, index=True)
    raw_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    processed_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    processed_status: Mapped[str] = mapped_column(String, nullable=False, default=PROCESSED_STATUS_PENDING)
    processed_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="demo")
    source_provider: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(nullable=True)
    sha256: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    download_status: Mapped[str] = mapped_column(String, nullable=False, default=DOWNLOAD_STATUS_PENDING)
    downloaded_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    raw_kind: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    render_status: Mapped[str] = mapped_column(String, nullable=False, default=RENDER_STATUS_PLACEHOLDER)
    render_mode: Mapped[str] = mapped_column(String, nullable=False, default=RENDER_MODE_PLACEHOLDER)
    production_rendering: Mapped[bool] = mapped_column(nullable=False, default=False)
    render_artifact_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    render_metadata_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    render_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rendered_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="radar_files")
