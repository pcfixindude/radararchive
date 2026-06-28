"""Tests for MRMS visual review sample-set selection (Phase 60)."""

from __future__ import annotations

import json
from typing import Optional

from backend.app.config import settings
from backend.app.services.mrms_visual_review import save_visual_review_report
from backend.app.services.mrms_visual_review_sample_set import (
    SAMPLE_SET_JSON,
    SAMPLE_SET_MD,
    SELECTION_EXPLICIT,
    SELECTION_RECOMMENDED,
    build_sample_set_markdown,
    build_visual_review_sample_set,
    compact_visual_review_sample_set,
    load_visual_review_sample_set,
    save_visual_review_sample_set,
    select_recommended_sample_entries,
)
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))


def _visual_report(
    *,
    created_at: str,
    artifacts: Optional[list[dict]] = None,
) -> dict:
    default_artifacts = [
        {
            "timestamp": "2026-06-28T12:00:00Z",
            "layer": "mrms_reflectivity",
            "tile_mode": "placeholder",
            "render_status": "placeholder",
            "raw_kind": "demo_seeded_stub",
            "artifact_paths_found": ["data/processed/demo-a.png"],
            "missing_artifacts": [],
        },
        {
            "timestamp": "2026-06-28T12:05:00Z",
            "layer": "mrms_reflectivity",
            "tile_mode": "decoded_prototype",
            "render_status": "decoded_prototype",
            "raw_kind": "demo_seeded_stub",
            "artifact_paths_found": ["data/processed/demo-b.png"],
            "missing_artifacts": ["tile_cache"],
        },
        {
            "timestamp": "2026-06-28T12:10:00Z",
            "layer": "mrms_reflectivity",
            "tile_mode": "production_gated",
            "render_status": "production_gated",
            "raw_kind": "demo_seeded_stub",
            "artifact_paths_found": ["data/processed/demo-c.png"],
            "missing_artifacts": [],
        },
    ]
    return {
        "created_at": created_at,
        "layers_inspected": ["mrms_reflectivity"],
        "timestamps_inspected": [item["timestamp"] for item in (artifacts or default_artifacts)],
        "frame_count": len(artifacts or default_artifacts),
        "artifact_count": len(artifacts or default_artifacts),
        "missing_artifact_count": 1,
        "tile_modes_found": ["placeholder", "decoded_prototype", "production_gated"],
        "artifacts": artifacts or default_artifacts,
        "json_path": "data/dev/mrms_visual_review_latest.json",
        "markdown_path": "data/dev/mrms_visual_review_latest.md",
        "verified_mrms": False,
        "local_visual_review_only": True,
    }


def test_sample_set_compact_empty(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_visual_review_sample_set(storage)
    assert compact["available"] is False
    assert compact["entry_count"] == 0
    assert compact["verified_mrms"] is False
    assert compact["local_sample_set_only"] is True
    assert compact["does_not_clear_alerts"] is True
    assert compact["does_not_enable_production"] is True


def test_sample_set_without_visual_review_manifest(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    sample_set = build_visual_review_sample_set(storage)
    assert sample_set["entry_count"] == 0
    assert sample_set["reason"] == "no_visual_review_manifest"
    assert sample_set["verified_mrms"] is False
    assert storage.absolute_path(SAMPLE_SET_JSON).is_file()
    assert storage.absolute_path(SAMPLE_SET_MD).is_file()
    markdown = storage.absolute_path(SAMPLE_SET_MD).read_text(encoding="utf-8")
    assert "NOT" in markdown
    assert "verify MRMS" in markdown


def test_recommended_sample_selection_prioritizes_missing_and_diverse_modes(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    manifest = _visual_report(created_at="2026-06-28T20:00:00Z")
    entries = select_recommended_sample_entries(manifest, limit=2)
    assert len(entries) == 2
    timestamps = {entry["timestamp"] for entry in entries}
    assert "2026-06-28T12:05:00Z" in timestamps


def test_build_sample_set_from_visual_review_manifest(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    sample_set = build_visual_review_sample_set(
        storage,
        selection_mode=SELECTION_RECOMMENDED,
        limit=3,
    )
    assert sample_set["entry_count"] == 3
    assert sample_set["selection_mode"] == SELECTION_RECOMMENDED
    assert sample_set["source_visual_review_at"] == "2026-06-28T20:00:00Z"
    assert sample_set["json_path"].endswith("mrms_visual_review_sample_set.json")
    assert sample_set["markdown_path"].endswith("mrms_visual_review_sample_set.md")
    loaded = load_visual_review_sample_set(storage)
    assert loaded is not None
    assert loaded["entry_count"] == 3


def test_explicit_timestamp_selection(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    sample_set = build_visual_review_sample_set(
        storage,
        selection_mode=SELECTION_EXPLICIT,
        timestamps=["2026-06-28T12:00:00Z", "2026-06-28T12:10:00Z"],
    )
    assert sample_set["entry_count"] == 2
    timestamps = [entry["timestamp"] for entry in sample_set["entries"]]
    assert timestamps == ["2026-06-28T12:00:00Z", "2026-06-28T12:10:00Z"]


def test_sample_set_markdown_includes_entries_and_safety(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    sample_set = build_visual_review_sample_set(storage, limit=2)
    markdown = build_sample_set_markdown(sample_set)
    assert "Local Drilldown Only" in markdown
    assert "does **NOT** verify MRMS" in markdown
    assert "2026-06-28T12:05:00Z" in markdown
    assert "make mrms-visual-review-sample-set" in markdown


def test_sample_set_json_persistence_round_trip(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    payload = {
        "created_at": "2026-06-28T21:00:00Z",
        "selection_mode": SELECTION_RECOMMENDED,
        "limit": 5,
        "entries": [],
        "entry_count": 0,
        "context": {},
    }
    saved = save_visual_review_sample_set(storage, payload)
    abs_path = storage.absolute_path(SAMPLE_SET_JSON)
    loaded = json.loads(abs_path.read_text(encoding="utf-8"))
    assert loaded["created_at"] == saved["created_at"]
    assert loaded["verified_mrms"] is False
    assert loaded["local_sample_set_only"] is True


def test_summary_includes_sample_set_compact(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    build_visual_review_sample_set(storage, limit=2)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_visual_review_sample_set")
    assert compact is not None
    assert compact["available"] is True
    assert compact["entry_count"] == 2
    assert compact["verified_mrms"] is False


def test_sample_set_get_endpoint_empty(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-visual-review/sample-set")
    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_mrms"] is False
    assert payload["compact"]["available"] is False


def test_sample_set_post_endpoint_builds_recommended(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    response = client.post(
        "/api/validation/mrms-visual-review/sample-set",
        json={"selection_mode": "recommended", "limit": 2},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_mrms"] is False
    assert payload["does_not_clear_alerts"] is True
    assert payload["sample_set"]["entry_count"] == 2
    assert payload["compact"]["available"] is True


def test_sample_set_does_not_clear_alerts(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(storage, {"status": ALERT_FAILED, "reason": "proof_failed"})
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    build_visual_review_sample_set(storage, limit=2)
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert.get("status") == ALERT_FAILED


def test_sample_set_does_not_mutate_production_flags(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    sample_set = build_visual_review_sample_set(storage, limit=2)
    assert sample_set["verified_mrms"] is False
    assert settings.enable_production_radar_tiles is False


def test_sample_set_always_verified_mrms_false(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    sample_set = build_visual_review_sample_set(storage, limit=2)
    loaded = load_visual_review_sample_set(storage)
    compact = compact_visual_review_sample_set(storage)
    assert sample_set["verified_mrms"] is False
    assert loaded["verified_mrms"] is False
    assert compact["verified_mrms"] is False
