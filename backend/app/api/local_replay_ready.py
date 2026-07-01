"""One-shot local replay setup API — status/plan only unless explicitly run elsewhere."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas.local_replay_ready import LocalReplayReadyResponse
from backend.app.services.frame_cache_warmer import DEFAULT_LIMIT, MAX_LIMIT
from backend.app.services.local_replay_ready import build_local_replay_ready_plan
from backend.app.services.storage import LocalStorage

router = APIRouter(prefix="/dev", tags=["dev-local"])


def _storage() -> LocalStorage:
    return LocalStorage(settings.local_storage_root)


@router.get("/local-replay-ready", response_model=LocalReplayReadyResponse)
def get_local_replay_ready(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Max frames to assess"),
    session: Session = Depends(get_db),
) -> LocalReplayReadyResponse:
    """Return post-ingest readiness checklist without running warm/decode/ingest."""
    payload = build_local_replay_ready_plan(session, _storage(), limit=limit)
    return LocalReplayReadyResponse(**payload)
