"""Playback clip manifest import API — validate and assess readiness only."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas.clip_import import ClipImportRequest, ClipImportResponse
from backend.app.services.clip_import import build_clip_import_report
from backend.app.services.storage import LocalStorage

router = APIRouter(prefix="/dev", tags=["dev-local"])


def _storage() -> LocalStorage:
    return LocalStorage(settings.local_storage_root)


@router.post("/clip-import", response_model=ClipImportResponse)
def post_clip_import(
    body: ClipImportRequest,
    session: Session = Depends(get_db),
) -> ClipImportResponse:
    """Validate an imported clip manifest and refresh local readiness summary."""
    payload = build_clip_import_report(session, _storage(), body.manifest)
    return ClipImportResponse(**payload)
