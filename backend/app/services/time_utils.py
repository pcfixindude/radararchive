from datetime import datetime, timedelta, timezone
from typing import Optional


def parse_utc_iso(timestamp: str) -> datetime:
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def format_utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def next_collection_timestamp(
    latest: Optional[str],
    *,
    step_minutes: int = 5,
    now: Optional[datetime] = None,
) -> str:
    if latest:
        base = parse_utc_iso(latest) + timedelta(minutes=step_minutes)
        return format_utc_iso(base)

    current = now or datetime.now(timezone.utc)
    current = current.replace(second=0, microsecond=0)
    aligned_minute = (current.minute // step_minutes) * step_minutes
    aligned = current.replace(minute=aligned_minute)
    return format_utc_iso(aligned)


def timestamp_path_token(timestamp: str) -> str:
    return timestamp.replace(":", "").replace("-", "")
