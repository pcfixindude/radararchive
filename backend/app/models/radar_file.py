from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base

PROCESSED_STATUS_PENDING = "pending"
PROCESSED_STATUS_PROCESSED = "processed"

DOWNLOAD_STATUS_PENDING = "pending"
DOWNLOAD_STATUS_DOWNLOADED = "downloaded"
DOWNLOAD_STATUS_FAILED = "failed"


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

    product: Mapped["Product"] = relationship(back_populates="radar_files")
