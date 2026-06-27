from backend.app.services.time_utils import format_utc_iso, next_collection_timestamp, parse_utc_iso


def test_parse_and_format_utc_iso():
    parsed = parse_utc_iso("2026-06-27T20:20:00Z")
    assert format_utc_iso(parsed) == "2026-06-27T20:20:00Z"


def test_next_collection_timestamp_from_latest():
    assert next_collection_timestamp("2026-06-27T20:20:00Z") == "2026-06-27T20:25:00Z"
