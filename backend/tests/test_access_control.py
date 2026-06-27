from datetime import datetime, timezone

from backend.app.models import RadarFile
from backend.app.models.radar_file import PROCESSED_STATUS_PENDING, PROCESSED_STATUS_PROCESSED
from backend.app.services import access_control as access_service


def test_access_plan_limits(db_session):
    plans = access_service.list_access_plans(db_session)
    plan_ids = {plan.id for plan in plans}
    assert plan_ids == {"free", "basic", "pro", "business"}

    assert access_service.get_history_limit_days(db_session, "free") == 0
    assert access_service.get_history_limit_days(db_session, "basic") == 7
    assert access_service.get_history_limit_days(db_session, "pro") == 90
    assert access_service.get_history_limit_days(db_session, "business") is None


def test_timestamp_allowed_uses_catalog_reference_latest(db_session):
    reference = "2026-06-27T20:20:00Z"
    latest = "2026-06-27T20:20:00Z"
    older_same_day = "2026-06-27T20:00:00Z"
    very_old = "2026-06-01T20:00:00Z"

    assert access_service.is_timestamp_allowed(
        db_session, "free", latest, reference_latest_iso=reference
    )
    assert not access_service.is_timestamp_allowed(
        db_session, "free", older_same_day, reference_latest_iso=reference
    )
    assert access_service.is_timestamp_allowed(
        db_session, "pro", older_same_day, reference_latest_iso=reference
    )
    assert not access_service.is_timestamp_allowed(
        db_session, "basic", very_old, reference_latest_iso=reference
    )
    assert access_service.is_timestamp_allowed(
        db_session, "business", very_old, reference_latest_iso=reference
    )


def test_filter_timestamps_by_plan(db_session):
    reference = "2026-06-27T20:20:00Z"
    timestamps = [
        "2026-06-27T20:00:00Z",
        "2026-06-27T20:05:00Z",
        "2026-06-27T20:20:00Z",
    ]

    free = access_service.filter_timestamps_by_plan(
        db_session, "free", timestamps, reference_latest_iso=reference
    )
    pro = access_service.filter_timestamps_by_plan(
        db_session, "pro", timestamps, reference_latest_iso=reference
    )

    assert free == ["2026-06-27T20:20:00Z"]
    assert pro == timestamps
