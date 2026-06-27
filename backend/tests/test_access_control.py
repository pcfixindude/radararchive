from datetime import datetime, timezone

from backend.app.services import access_control as access_service


def test_access_plan_limits(db_session):
    plans = access_service.list_access_plans(db_session)
    plan_ids = {plan.id for plan in plans}
    assert plan_ids == {"free", "basic", "pro", "business"}

    assert access_service.get_history_limit_days(db_session, "basic") == 7
    assert access_service.get_history_limit_days(db_session, "pro") == 90
    assert access_service.get_history_limit_days(db_session, "business") is None


def test_timestamp_allowed_within_plan_window(db_session):
    now = datetime(2026, 6, 27, 21, 0, tzinfo=timezone.utc)
    recent = "2026-06-27T20:20:00Z"
    old = "2026-06-01T20:00:00Z"

    assert access_service.is_timestamp_allowed(db_session, "pro", recent, now=now)
    assert not access_service.is_timestamp_allowed(db_session, "free", old, now=now)
    assert access_service.is_timestamp_allowed(db_session, "business", old, now=now)
