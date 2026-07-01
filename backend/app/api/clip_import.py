"""Playback clip manifest import API — validate and assess readiness only."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas.clip_import import ClipImportRequest, ClipImportResponse
from backend.app.schemas.clip_remediation import (
    ClipRemediationRequest,
    ClipRemediationResponse,
)
from backend.app.services.clip_import import build_clip_import_report
from backend.app.services.clip_remediation import build_clip_remediation_plan
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
    payload["remediation_plan"] = build_clip_remediation_plan(payload)
    return ClipImportResponse(**payload)


@router.post("/clip-remediation", response_model=ClipRemediationResponse)
def post_clip_remediation(
    body: ClipRemediationRequest,
    session: Session = Depends(get_db),
) -> ClipRemediationResponse:
    """Build bounded warm/decode remediation plan from manifest or import report."""
    storage = _storage()
    import_report: dict
    if body.import_report is not None:
        import_report = body.import_report
    elif body.manifest is not None:
        import_report = build_clip_import_report(session, storage, body.manifest)
    else:
        import_report = {"valid": False, "manifest": None, "problem_frames": []}

    plan = build_clip_remediation_plan(import_report, limit=body.limit)
    return ClipRemediationResponse(**plan, import_report=import_report if body.manifest else None)
