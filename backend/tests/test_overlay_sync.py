"""Tests for overlay time sync (Phase 107)."""

from backend.app.services.overlay_sync import (
    SYNC_MATCHED,
    SYNC_MISMATCH,
    SYNC_NO_CANDIDATE,
    SYNC_NO_SELECTION,
    evaluate_overlay_sync,
    extract_candidate_timestamp,
    extract_timestamp_from_raw_path,
    normalize_timestamp_iso,
)


def test_normalize_timestamp_iso():
    assert normalize_timestamp_iso("2026-06-28T13:26:38Z") == "2026-06-28T13:26:38Z"


def test_extract_timestamp_from_raw_path():
    ts = extract_timestamp_from_raw_path(
        "data/raw/mrms/reflectivity/20260628T132638Z_MRMS_ReflectivityAtLowestAltitude_00.50_20260628-132638.grib2.gz"
    )
    assert ts == "2026-06-28T13:26:38Z"


def test_evaluate_overlay_sync_matched():
    result = evaluate_overlay_sync(
        selected_timestamp="2026-06-28T13:26:38Z",
        candidate_timestamp="2026-06-28T13:26:38Z",
    )
    assert result["sync_status"] == SYNC_MATCHED
    assert result["overlay_visible"] is True


def test_evaluate_overlay_sync_mismatch():
    result = evaluate_overlay_sync(
        selected_timestamp="2026-06-27T20:00:00Z",
        candidate_timestamp="2026-06-28T13:26:38Z",
    )
    assert result["sync_status"] == SYNC_MISMATCH
    assert result["overlay_visible"] is False
    assert "does not match" in result["sync_message"]


def test_evaluate_overlay_sync_no_selection():
    result = evaluate_overlay_sync(selected_timestamp=None, candidate_timestamp="2026-06-28T13:26:38Z")
    assert result["sync_status"] == SYNC_NO_SELECTION
    assert result["overlay_visible"] is False


def test_extract_candidate_timestamp_from_pipeline():
    ts = extract_candidate_timestamp(
        pipeline={"candidate": {"timestamp": "2026-06-28T13:26:38Z"}},
        decode_retry=None,
        geo=None,
        candidate_raw_path=None,
    )
    assert ts == "2026-06-28T13:26:38Z"


def test_evaluate_overlay_sync_no_candidate():
    result = evaluate_overlay_sync(selected_timestamp="2026-06-28T13:26:38Z", candidate_timestamp=None)
    assert result["sync_status"] == SYNC_NO_CANDIDATE
