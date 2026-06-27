from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models import AccessPlan
from backend.app.services.time_utils import parse_utc_iso


def list_access_plans(session: Session) -> list[AccessPlan]:
    return session.query(AccessPlan).order_by(AccessPlan.id).all()


def get_plan(session: Session, plan_id: str) -> Optional[AccessPlan]:
    return session.get(AccessPlan, plan_id)


def get_history_limit_days(session: Session, plan_id: str) -> Optional[int]:
    plan = get_plan(session, plan_id)
    if plan is None:
        return None
    return plan.history_days


def history_limit_label(history_days: Optional[int]) -> str:
    if history_days is None:
        return "Unrestricted history"
    if history_days == 0:
        return "Latest frame only"
    if history_days == 1:
        return "Recent history (1 day)"
    return f"Last {history_days} days"


def upgrade_message_for_plan(plan_id: str) -> str:
    messages = {
        "free": "Upgrade to Basic, Pro, or Business to unlock more historical radar replay.",
        "basic": "Upgrade to Pro or Business for longer historical replay windows.",
        "pro": "Upgrade to Business for unrestricted historical replay.",
        "business": "You have unrestricted demo access on the Business plan.",
    }
    return messages.get(plan_id, "Choose a higher plan to unlock more history.")


def is_timestamp_allowed(
    session: Session,
    plan_id: str,
    timestamp_iso: str,
    *,
    reference_latest_iso: str,
) -> bool:
    """Return True when a timestamp is within a plan window relative to catalog latest."""
    history_days = get_history_limit_days(session, plan_id)
    if history_days is None:
        return True

    if history_days == 0:
        return timestamp_iso == reference_latest_iso

    reference = parse_utc_iso(reference_latest_iso)
    frame_time = parse_utc_iso(timestamp_iso)
    oldest_allowed = reference - timedelta(days=history_days)
    return frame_time >= oldest_allowed


def filter_timestamps_by_plan(
    session: Session,
    plan_id: str,
    timestamps: list[str],
    *,
    reference_latest_iso: Optional[str],
) -> list[str]:
    if not timestamps or reference_latest_iso is None:
        return []

    return [
        timestamp
        for timestamp in timestamps
        if is_timestamp_allowed(
            session,
            plan_id,
            timestamp,
            reference_latest_iso=reference_latest_iso,
        )
    ]


def plan_blocked_detail(
    session: Session,
    plan_id: str,
    timestamp: str,
    reference_latest_iso: str,
) -> dict:
    plan = get_plan(session, plan_id)
    return {
        "error": "plan_limit_exceeded",
        "message": "Timestamp is outside the selected demo plan history window.",
        "plan": plan_id,
        "plan_name": plan.name if plan else plan_id,
        "timestamp": timestamp,
        "reference_latest": reference_latest_iso,
        "history_limit_label": history_limit_label(get_history_limit_days(session, plan_id)),
        "upgrade_message": upgrade_message_for_plan(plan_id),
    }
