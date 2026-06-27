from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models import AccessPlan


def list_access_plans(session: Session) -> list[AccessPlan]:
    return session.query(AccessPlan).order_by(AccessPlan.id).all()


def get_history_limit_days(session: Session, plan_id: str) -> Optional[int]:
    plan = session.get(AccessPlan, plan_id)
    if plan is None:
        return None
    return plan.history_days


def is_timestamp_allowed(
    session: Session,
    plan_id: str,
    timestamp_iso: str,
    *,
    now: Optional[datetime] = None,
) -> bool:
    """Return True when a timestamp is within a plan's history window."""
    history_days = get_history_limit_days(session, plan_id)
    if history_days is None:
        return True

    frame_time = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
    current = now or datetime.now(timezone.utc)
    oldest_allowed = current - timedelta(days=history_days)
    return frame_time >= oldest_allowed
