"""Render status reporting and catalog sync for tile rendering guardrails."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models import RadarFile
from backend.app.models.radar_file import (
    is_placeholder_tile_status,
)
from backend.app.services.decoded_tile_cache import (
    find_decode_artifact_for_frame,
    list_decode_artifact_dirs,
)
from backend.app.services.render_metadata import (
    GEO_METADATA_NAME,
    RENDER_MODE_DECODED_PROTOTYPE,
    RENDER_MODE_PLACEHOLDER,
    RENDER_MODE_PRODUCTION,
    RENDER_STATUS_DECODED_PROTOTYPE,
    RENDER_STATUS_PLACEHOLDER,
    RENDER_STATUS_PRODUCTION_FAILED,
    RENDER_STATUS_PRODUCTION_PENDING,
    RENDER_STATUS_PRODUCTION_RENDERED,
    geo_metadata_path,
    load_geo_metadata,
)
from backend.app.services.storage import LocalStorage


@dataclass
class FrameRenderInfo:
    radar_file_id: int
    timestamp: str
    product_id: str
    render_status: str
    render_mode: str
    production_rendering: bool
    has_decode_artifact: bool
    has_geo_metadata: bool
    render_artifact_path: Optional[str] = None
    render_metadata_path: Optional[str] = None
    render_error: Optional[str] = None


@dataclass
class RenderStatusReport:
    total_frames: int
    placeholder_frames: int
    decoded_prototype_artifacts: int
    decoded_prototype_frames: int
    production_rendered_frames: int
    production_pending_frames: int
    production_failed_frames: int
    missing_geo_metadata: int
    frames: list[FrameRenderInfo] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def infer_render_mode(render_status: str) -> str:
    if render_status == RENDER_STATUS_DECODED_PROTOTYPE:
        return RENDER_MODE_DECODED_PROTOTYPE
    if render_status in (RENDER_STATUS_PRODUCTION_PENDING, RENDER_STATUS_PRODUCTION_RENDERED, RENDER_STATUS_PRODUCTION_FAILED):
        return RENDER_MODE_PRODUCTION
    return RENDER_MODE_PLACEHOLDER


def classify_frame_render_status(storage: LocalStorage, frame: RadarFile) -> FrameRenderInfo:
    artifact = find_decode_artifact_for_frame(storage, frame)
    has_artifact = artifact is not None
    geo_path: Optional[str] = None
    has_geo = False
    if has_artifact and artifact is not None:
        geo = load_geo_metadata(storage, artifact.output_dir)
        has_geo = geo is not None
        if has_geo:
            geo_path = storage.normalize_path(artifact.output_dir, GEO_METADATA_NAME)

    stored_status = frame.render_status or RENDER_STATUS_PLACEHOLDER
    production = bool(frame.production_rendering)

    if production and stored_status == RENDER_STATUS_PRODUCTION_RENDERED:
        render_status = RENDER_STATUS_PRODUCTION_RENDERED
    elif production and stored_status == RENDER_STATUS_PRODUCTION_FAILED:
        render_status = RENDER_STATUS_PRODUCTION_FAILED
    elif has_artifact:
        render_status = RENDER_STATUS_DECODED_PROTOTYPE
    elif production:
        render_status = RENDER_STATUS_PRODUCTION_PENDING
    elif is_placeholder_tile_status(frame.processed_status):
        render_status = RENDER_STATUS_PLACEHOLDER
    else:
        render_status = stored_status

    return FrameRenderInfo(
        radar_file_id=frame.id,
        timestamp=frame.timestamp,
        product_id=frame.product_id,
        render_status=render_status,
        render_mode=infer_render_mode(render_status),
        production_rendering=production,
        has_decode_artifact=has_artifact,
        has_geo_metadata=has_geo,
        render_artifact_path=artifact.raster_path if artifact else frame.render_artifact_path,
        render_metadata_path=geo_path or frame.render_metadata_path,
        render_error=frame.render_error,
    )


def build_render_status_report(session: Session, storage: LocalStorage) -> RenderStatusReport:
    rows = session.query(RadarFile).order_by(RadarFile.timestamp.asc()).all()
    frames = [classify_frame_render_status(storage, row) for row in rows]

    artifact_dirs = list_decode_artifact_dirs(storage)
    missing_geo = 0
    for output_dir in artifact_dirs:
        if not storage.path_exists(geo_metadata_path(storage, output_dir)):
            missing_geo += 1

    report = RenderStatusReport(
        total_frames=len(rows),
        placeholder_frames=sum(1 for f in frames if f.render_status == RENDER_STATUS_PLACEHOLDER),
        decoded_prototype_artifacts=len(artifact_dirs),
        decoded_prototype_frames=sum(1 for f in frames if f.render_status == RENDER_STATUS_DECODED_PROTOTYPE),
        production_rendered_frames=sum(1 for f in frames if f.render_status == RENDER_STATUS_PRODUCTION_RENDERED),
        production_pending_frames=sum(1 for f in frames if f.render_status == RENDER_STATUS_PRODUCTION_PENDING),
        production_failed_frames=sum(1 for f in frames if f.render_status == RENDER_STATUS_PRODUCTION_FAILED),
        missing_geo_metadata=missing_geo,
        frames=frames,
    )

    report.notes.append("Production rendering is disabled by default (ENABLE_PRODUCTION_RADAR_TILES=false).")
    report.notes.append("Decoded prototype artifacts are not marked production_rendered.")
    if report.production_rendered_frames == 0:
        report.notes.append("production_rendered frames: 0 (expected in Phase 14).")
    if missing_geo > 0:
        report.notes.append(f"{missing_geo} decode artifact(s) missing geo_metadata.json.")
    return report


def sync_catalog_render_metadata(session: Session, storage: LocalStorage, *, dry_run: bool = False) -> int:
    """Update catalog render fields from artifacts without enabling production rendering."""
    updated = 0
    for row in session.query(RadarFile).all():
        info = classify_frame_render_status(storage, row)
        if info.render_status == RENDER_STATUS_DECODED_PROTOTYPE:
            new_status = RENDER_STATUS_DECODED_PROTOTYPE
            new_mode = RENDER_MODE_DECODED_PROTOTYPE
            artifact_path = info.render_artifact_path
            metadata_path = info.render_metadata_path
        else:
            new_status = RENDER_STATUS_PLACEHOLDER if is_placeholder_tile_status(row.processed_status) else row.render_status
            new_mode = infer_render_mode(new_status)
            artifact_path = row.render_artifact_path
            metadata_path = row.render_metadata_path

        # Never auto-mark production_rendered from prototype artifacts.
        production = bool(row.production_rendering) and row.render_status == RENDER_STATUS_PRODUCTION_RENDERED

        changed = (
            row.render_status != new_status
            or row.render_mode != new_mode
            or row.production_rendering != production
            or row.render_artifact_path != artifact_path
            or row.render_metadata_path != metadata_path
        )
        if changed and not dry_run:
            row.render_status = new_status
            row.render_mode = new_mode
            row.production_rendering = production
            row.render_artifact_path = artifact_path
            row.render_metadata_path = metadata_path
            updated += 1
        elif changed:
            updated += 1

    if not dry_run:
        session.commit()
    return updated
