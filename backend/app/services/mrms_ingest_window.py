"""Guided MRMS ingest date/time window planning (local dev only — NOT verified MRMS)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from backend.app.services.mrms_bulk_ingest import DEFAULT_LIMIT, MAX_LIMIT
from backend.app.services.overlay_sync import normalize_timestamp_iso
from backend.app.services.time_utils import format_utc_iso, parse_utc_iso

PRESET_LAST_1H = "last_1h"
PRESET_LAST_3H = "last_3h"
PRESET_LAST_6H = "last_6h"
PRESET_CUSTOM = "custom"
PRESET_REPLAY_RANGE = "replay_range"

INGEST_WINDOW_PRESETS: dict[str, str] = {
    PRESET_LAST_1H: "Last 1 hour",
    PRESET_LAST_3H: "Last 3 hours",
    PRESET_LAST_6H: "Last 6 hours",
    PRESET_CUSTOM: "Custom start/end",
    PRESET_REPLAY_RANGE: "Current replay range",
}

PRESET_DURATION_HOURS: dict[str, float] = {
    PRESET_LAST_1H: 1.0,
    PRESET_LAST_3H: 3.0,
    PRESET_LAST_6H: 6.0,
}

MRMS_FRAME_INTERVAL_MINUTES = 2
LARGE_WINDOW_WARNING_HOURS = 6.0
GUIDED_INGEST_MAKE_TARGET = "make mrms-ingest-window"
SUGGESTED_GUIDED_COMMAND = f"{GUIDED_INGEST_MAKE_TARGET} PRESET=last_3h LIMIT=8"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(second=0, microsecond=0)


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_dev_only": True,
        "prototype": True,
        "requires_real_flag": True,
        "does_not_enable_production": True,
    }


def clamp_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_LIMIT))


def resolve_preset_window(
    preset: str,
    *,
    reference_time: Optional[datetime] = None,
    custom_start: Optional[str] = None,
    custom_end: Optional[str] = None,
    replay_start: Optional[str] = None,
    replay_end: Optional[str] = None,
) -> tuple[Optional[str], Optional[str], list[str]]:
    """Return normalized (start, end) for a preset plus any warnings."""
    warnings: list[str] = []
    now = reference_time or _utc_now()

    if preset == PRESET_CUSTOM:
        start = normalize_timestamp_iso(custom_start)
        end = normalize_timestamp_iso(custom_end)
        if not start or not end:
            warnings.append("Custom preset needs both start and end timestamps.")
            return start, end, warnings
        if parse_utc_iso(start) > parse_utc_iso(end):
            start, end = end, start
            warnings.append("Range order adjusted — start is now before end.")
        return start, end, warnings

    if preset == PRESET_REPLAY_RANGE:
        start = normalize_timestamp_iso(replay_start)
        end = normalize_timestamp_iso(replay_end)
        if not start or not end:
            warnings.append("Replay range preset needs both replay start and end frames.")
            return start, end, warnings
        if parse_utc_iso(start) > parse_utc_iso(end):
            start, end = end, start
            warnings.append("Replay range order adjusted — start is now before end.")
        return start, end, warnings

    hours = PRESET_DURATION_HOURS.get(preset)
    if hours is None:
        warnings.append(f"Unknown preset '{preset}'.")
        return None, None, warnings

    end = format_utc_iso(now)
    start = format_utc_iso(now - timedelta(hours=hours))
    return start, end, warnings


def estimate_frames_in_window(start_time: str, end_time: str) -> int:
    start = parse_utc_iso(start_time)
    end = parse_utc_iso(end_time)
    if end < start:
        start, end = end, start
    minutes = max(0.0, (end - start).total_seconds() / 60.0)
    return max(1, int(minutes // MRMS_FRAME_INTERVAL_MINUTES) + 1)


def window_duration_hours(start_time: str, end_time: str) -> float:
    start = parse_utc_iso(start_time)
    end = parse_utc_iso(end_time)
    if end < start:
        start, end = end, start
    return max(0.0, (end - start).total_seconds() / 3600.0)


def validate_ingest_window(
    start_time: Optional[str],
    end_time: Optional[str],
    limit: int,
) -> list[str]:
    warnings: list[str] = []
    bounded_limit = clamp_limit(limit)

    if bounded_limit != limit:
        warnings.append(f"Limit adjusted to bounded maximum of {MAX_LIMIT}.")

    if not start_time or not end_time:
        warnings.append("Start and end times are required for a bounded ingest window.")
        return warnings

    duration_hours = window_duration_hours(start_time, end_time)
    estimated = estimate_frames_in_window(start_time, end_time)

    if duration_hours > LARGE_WINDOW_WARNING_HOURS:
        warnings.append(
            f"Window spans {duration_hours:.1f}h — ingest remains capped at limit {bounded_limit}."
        )

    if estimated > bounded_limit:
        warnings.append(
            f"Window may contain ~{estimated} MRMS frames; only the latest {bounded_limit} will ingest."
        )

    return warnings


def build_bulk_ingest_argv(
    *,
    start_time: Optional[str],
    end_time: Optional[str],
    limit: int,
    warm_cache: bool = False,
    include_real: bool = True,
) -> list[str]:
    argv: list[str] = []
    if include_real:
        argv.append("--real")
    argv.extend(["--limit", str(clamp_limit(limit))])
    if start_time:
        argv.extend(["--start", start_time])
    if end_time:
        argv.extend(["--end", end_time])
    if warm_cache:
        argv.append("--warm-cache")
    return argv


def build_bulk_ingest_args(
    *,
    start_time: Optional[str],
    end_time: Optional[str],
    limit: int,
    warm_cache: bool = False,
    include_real: bool = True,
) -> str:
    return " ".join(
        build_bulk_ingest_argv(
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            warm_cache=warm_cache,
            include_real=include_real,
        )
    )


def build_bulk_ingest_command(
    *,
    start_time: Optional[str],
    end_time: Optional[str],
    limit: int,
    warm_cache: bool = False,
) -> str:
    args = build_bulk_ingest_args(
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        warm_cache=warm_cache,
        include_real=True,
    )
    return f"make mrms-bulk-local-ingest ARGS='{args}'"


def build_guided_make_command(
    *,
    preset: str,
    limit: int,
    warm_cache: bool = False,
    custom_start: Optional[str] = None,
    custom_end: Optional[str] = None,
    replay_start: Optional[str] = None,
    replay_end: Optional[str] = None,
) -> str:
    parts = [f"PRESET={preset}", f"LIMIT={clamp_limit(limit)}"]
    if warm_cache:
        parts.append("WARM_CACHE=1")
    if preset == PRESET_CUSTOM:
        if custom_start:
            parts.append(f"START={custom_start}")
        if custom_end:
            parts.append(f"END={custom_end}")
    if preset == PRESET_REPLAY_RANGE:
        if replay_start:
            parts.append(f"REPLAY_START={replay_start}")
        if replay_end:
            parts.append(f"REPLAY_END={replay_end}")
    return f"{GUIDED_INGEST_MAKE_TARGET} {' '.join(parts)}"


def build_ingest_window_plan(
    *,
    preset: str = PRESET_LAST_3H,
    limit: int = DEFAULT_LIMIT,
    warm_cache: bool = False,
    custom_start: Optional[str] = None,
    custom_end: Optional[str] = None,
    replay_start: Optional[str] = None,
    replay_end: Optional[str] = None,
    reference_time: Optional[datetime] = None,
) -> dict[str, Any]:
    """Build a dry-run ingest plan and visible commands — does not download."""
    start_time, end_time, preset_warnings = resolve_preset_window(
        preset,
        reference_time=reference_time,
        custom_start=custom_start,
        custom_end=custom_end,
        replay_start=replay_start,
        replay_end=replay_end,
    )
    bounded_limit = clamp_limit(limit)
    validation_warnings = (
        validate_ingest_window(start_time, end_time, bounded_limit) if start_time and end_time else []
    )
    warnings = preset_warnings + validation_warnings
    estimated_frames = (
        estimate_frames_in_window(start_time, end_time) if start_time and end_time else None
    )
    ready = bool(start_time and end_time)

    return {
        "preset": preset,
        "preset_label": INGEST_WINDOW_PRESETS.get(preset, preset),
        "start_time": start_time,
        "end_time": end_time,
        "limit": bounded_limit,
        "warm_cache": warm_cache,
        "estimated_frames_in_window": estimated_frames,
        "ready": ready,
        "warnings": warnings,
        "bulk_ingest_command": (
            build_bulk_ingest_command(
                start_time=start_time,
                end_time=end_time,
                limit=bounded_limit,
                warm_cache=warm_cache,
            )
            if ready
            else None
        ),
        "guided_command": build_guided_make_command(
            preset=preset,
            limit=bounded_limit,
            warm_cache=warm_cache,
            custom_start=start_time if preset == PRESET_CUSTOM else None,
            custom_end=end_time if preset == PRESET_CUSTOM else None,
            replay_start=start_time if preset == PRESET_REPLAY_RANGE else None,
            replay_end=end_time if preset == PRESET_REPLAY_RANGE else None,
        ),
        "next_commands": _next_commands_after_ingest(warm_cache),
        "operator_steps": [
            "Choose a date/time window preset or custom range.",
            "Review the generated command and warnings.",
            f"Run the bulk ingest command with explicit --real (or {GUIDED_INGEST_MAKE_TARGET} RUN=1 REAL=1).",
            "Run make mrms-warm-frame-cache if cache is cold.",
            "Run make decode-retry, then replay with range/loop.",
        ],
        **_safety_fields(),
    }


def _next_commands_after_ingest(warm_cache: bool) -> list[str]:
    commands = []
    if not warm_cache:
        commands.append("make mrms-warm-frame-cache")
    commands.extend(["make decode-retry", "make backend", "make frontend"])
    return commands
