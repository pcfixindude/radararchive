"""Tests for guided MRMS ingest window planning (Phase 119)."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.mrms_ingest_window import (
    PRESET_CUSTOM,
    PRESET_LAST_1H,
    PRESET_LAST_3H,
    PRESET_REPLAY_RANGE,
    build_bulk_ingest_command,
    build_ingest_window_plan,
    clamp_limit,
    estimate_frames_in_window,
    resolve_preset_window,
    validate_ingest_window,
)

REFERENCE = datetime(2026, 6, 28, 14, 0, tzinfo=timezone.utc)


def test_clamp_limit_bounds():
    assert clamp_limit(0) == 1
    assert clamp_limit(8) == 8
    assert clamp_limit(99) == 20


def test_resolve_preset_last_3h():
    start, end, warnings = resolve_preset_window(PRESET_LAST_3H, reference_time=REFERENCE)
    assert warnings == []
    assert start == "2026-06-28T11:00:00Z"
    assert end == "2026-06-28T14:00:00Z"


def test_resolve_preset_custom_normalizes_order():
    start, end, warnings = resolve_preset_window(
        PRESET_CUSTOM,
        custom_start="2026-06-28T15:00:00Z",
        custom_end="2026-06-28T12:00:00Z",
    )
    assert start == "2026-06-28T12:00:00Z"
    assert end == "2026-06-28T15:00:00Z"
    assert any("adjusted" in warning for warning in warnings)


def test_resolve_replay_range_preset():
    start, end, warnings = resolve_preset_window(
        PRESET_REPLAY_RANGE,
        replay_start="2026-06-28T13:00:00Z",
        replay_end="2026-06-28T13:20:00Z",
    )
    assert warnings == []
    assert start.endswith("13:00:00Z")
    assert end.endswith("13:20:00Z")


def test_estimate_frames_in_window():
    estimated = estimate_frames_in_window("2026-06-28T13:00:00Z", "2026-06-28T13:10:00Z")
    assert estimated == 6


def test_validate_ingest_window_warns_on_large_span():
    warnings = validate_ingest_window(
        "2026-06-27T12:00:00Z",
        "2026-06-28T20:00:00Z",
        limit=8,
    )
    assert any("Window spans" in warning for warning in warnings)
    assert any("latest 8" in warning for warning in warnings)


def test_build_bulk_ingest_command_requires_real_flag():
    command = build_bulk_ingest_command(
        start_time="2026-06-28T12:00:00Z",
        end_time="2026-06-28T14:00:00Z",
        limit=8,
        warm_cache=True,
    )
    assert command.startswith("make mrms-bulk-local-ingest ARGS='")
    assert "--real" in command
    assert "--limit 8" in command
    assert "--start 2026-06-28T12:00:00Z" in command
    assert "--end 2026-06-28T14:00:00Z" in command
    assert "--warm-cache" in command


def test_build_ingest_window_plan_dry_run():
    plan = build_ingest_window_plan(
        preset=PRESET_LAST_1H,
        limit=8,
        reference_time=REFERENCE,
    )
    assert plan["ready"] is True
    assert plan["requires_real_flag"] is True
    assert plan["verified_mrms"] is False
    assert plan["bulk_ingest_command"]
    assert "make mrms-ingest-window" in plan["guided_command"]
    assert "make mrms-warm-frame-cache" in plan["next_commands"]


def test_ingest_window_plan_api():
    client = TestClient(app)
    response = client.get(
        "/api/dev/ingest-window/plan",
        params={
            "preset": PRESET_LAST_3H,
            "limit": 8,
            "warm_cache": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["preset"] == PRESET_LAST_3H
    assert payload["bulk_ingest_command"]
    assert payload["requires_real_flag"] is True
    assert payload["verified_mrms"] is False


def test_ingest_window_cli_dry_run_by_default(capsys):
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/mrms_ingest_window.py", "--preset", PRESET_LAST_1H, "--json"],
        capture_output=True,
        text=True,
        cwd=".",
        env={**dict(__import__("os").environ), "PYTHONPATH": "."},
    )
    assert result.returncode == 0
    payload = __import__("json").loads(result.stdout)
    assert payload["ready"] is True
    assert payload["bulk_ingest_command"]
    assert "--real" in payload["bulk_ingest_command"]


def test_ingest_window_custom_requires_start_end():
    plan = build_ingest_window_plan(preset=PRESET_CUSTOM, limit=8)
    assert plan["ready"] is False
    assert any("start and end" in warning.lower() for warning in plan["warnings"])


def test_ingest_window_cli_requires_real_to_run():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/mrms_ingest_window.py", "--preset", PRESET_LAST_1H, "--run"],
        capture_output=True,
        text=True,
        cwd=".",
        env={**dict(__import__("os").environ), "PYTHONPATH": "."},
    )
    assert result.returncode == 2
    assert "explicit --real" in result.stderr
