"""Bulk ingest report helpers (local dev prototype)."""

from __future__ import annotations

from typing import Any, Optional

INGEST_SUCCESS = "success"
INGEST_PARTIAL_SUCCESS = "partial_success"
INGEST_NO_FRAMES_AVAILABLE = "no_frames_available"
INGEST_FAILED = "failed"
INGEST_DISCOVERY_FAILED = "discovery_failed"
INGEST_INVALID_MODE = "invalid_mode"

NEXT_RETRY_FAILED_COMMAND = "make mrms-bulk-local-ingest ARGS='--real --retry-failed'"
NEXT_RETRY_MISSING_COMMAND = "make mrms-bulk-local-ingest ARGS='--real --missing-only --limit 8'"


def resolve_ingest_status(
    *,
    selected_count: int,
    downloaded_count: int,
    already_present_count: int,
    repaired_count: int,
    failure_count: int,
) -> str:
    """Map frame outcomes to a final ingest status."""
    success_count = downloaded_count + already_present_count + repaired_count
    if selected_count == 0:
        return INGEST_NO_FRAMES_AVAILABLE
    if failure_count == 0 and success_count > 0:
        return INGEST_SUCCESS
    if success_count > 0 and failure_count > 0:
        return INGEST_PARTIAL_SUCCESS
    if success_count == 0:
        return INGEST_FAILED
    return INGEST_FAILED


def build_next_commands(
    *,
    ingest_status: str,
    has_failures: bool,
    warm_cache_command: str,
    warm_ingest_command: str,
    decode_command: str,
    playback_command: str,
) -> list[str]:
    commands: list[str] = []
    if ingest_status in {INGEST_SUCCESS, INGEST_PARTIAL_SUCCESS}:
        commands.extend([warm_cache_command, warm_ingest_command])
    if has_failures:
        commands.append(NEXT_RETRY_FAILED_COMMAND)
        commands.append(NEXT_RETRY_MISSING_COMMAND)
    commands.extend([decode_command, playback_command])
    return commands


def failure_record(
    *,
    radar_file_id: str,
    timestamp: str,
    error: str,
    attempts: int,
    retryable: bool,
    health: Optional[str] = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "radar_file_id": radar_file_id,
        "timestamp": timestamp,
        "error": error,
        "attempts": attempts,
        "retryable": retryable,
    }
    if health:
        record["health"] = health
    return record
