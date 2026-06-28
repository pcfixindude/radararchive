"""SQLite-backed render job queue for production tile builds (dev/prototype)."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base

JOB_TYPE_PRODUCTION_TILES = "production_tiles"

JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELED = "canceled"

TERMINAL_JOB_STATUSES = frozenset(
    {JOB_STATUS_SUCCEEDED, JOB_STATUS_FAILED, JOB_STATUS_CANCELED}
)


class RenderJob(Base):
    __tablename__ = "render_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(String, nullable=False, default=JOB_TYPE_PRODUCTION_TILES)
    layer: Mapped[str] = mapped_column(String, nullable=False, default="mrms_reflectivity")
    timestamp: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    min_zoom: Mapped[int] = mapped_column(nullable=False, default=0)
    max_zoom: Mapped[int] = mapped_column(nullable=False, default=0)
    force: Mapped[bool] = mapped_column(nullable=False, default=False)
    mark_catalog: Mapped[bool] = mapped_column(nullable=False, default=False)
    artifact_limit: Mapped[Optional[int]] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default=JOB_STATUS_QUEUED, index=True)
    progress_current: Mapped[int] = mapped_column(nullable=False, default=0)
    progress_total: Mapped[int] = mapped_column(nullable=False, default=0)
    tiles_written: Mapped[int] = mapped_column(nullable=False, default=0)
    tiles_skipped: Mapped[int] = mapped_column(nullable=False, default=0)
    output_bytes: Mapped[int] = mapped_column(nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    finished_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
