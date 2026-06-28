"""Tests for MRMS visual review comparison and hints (Phase 57)."""

from __future__ import annotations

import json

from typing import Optional

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import (
    PROCESSED_STATUS_PLACEHOLDER_PROCESSED,
    RENDER_STATUS_DECODED_PROTOTYPE,
    RENDER_STATUS_PLACEHOLDER,
)
from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_IMPROVED,
    DIFF_MIXED,
    DIFF_NO_BASELINE,
    DIFF_UNCHANGED,
    DIFF_WORSENED,
)
from backend.app.services.mrms_visual_review import (
    VISUAL_REVIEW_LATEST_JSON,
    VISUAL_REVIEW_PREVIOUS_JSON,
    save_visual_review_report,
)
from backend.app.services.mrms_visual_review_compare import (
    COMPARISON_HISTORY_PATH,
    COMPARISON_LATEST_PATH,
    compare_visual_reviews,
    compact_visual_review_comparison_summary,
    load_latest_visual_review_comparison,
    record_visual_review_comparison,
)
from backend.app.services.mrms_visual_review_hint import (
    build_visual_review_hint,
    compact_visual_review_hint,
)
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary
from backend.app.services.validation_report_store import save_latest_validation_report


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))


def _visual_report(
    *,
    created_at: str,
    artifact_count: int = 1,
    missing_artifact_count: int = 0,
    frame_count: int = 1,
    tile_modes: Optional[list[str]] = None,
    artifacts: Optional[list[dict]] = None,
) -> dict:
    return {
        "created_at": created_at,
        "layers_inspected": ["mrms_reflectivity"],
        "timestamps_inspected": ["2026-06-28T12:00:00Z"],
        "frame_count": frame_count,
        "artifact_count": artifact_count,
        "missing_artifact_count": missing_artifact_count,
        "tile_modes_found": tile_modes or ["placeholder"],
        "artifacts": artifacts
        or [
            {
                "timestamp": "2026-06-28T12:00:00Z",
                "layer": "mrms_reflectivity",
                "tile_mode": "placeholder",
                "render_status": "placeholder",
                "raw_kind": "demo_seeded_stub",
                "artifact_paths_found": ["data/processed/demo.png"],
                "missing_artifacts": [],
            }
        ],
        "json_path": "data/dev/mrms_visual_review_latest.json",
        "markdown_path": "data/dev/mrms_visual_review_latest.md",
        "verified_mrms": False,
        "local_visual_review_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def test_visual_review_comparison_shape(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    latest = _visual_report(created_at="2026-06-28T20:00:00Z")
    comparison = compare_visual_reviews(None, latest)
    for key in (
        "compared_at",
        "latest_created_at",
        "baseline_created_at",
        "artifact_count_change",
        "missing_artifact_count_change",
        "inspected_frame_count_change",
        "tile_modes_added",
        "tile_modes_removed",
        "render_status_changes",
        "raw_kind_changes",
        "overall_visual_review_diff_status",
        "improvements",
        "regressions",
        "unchanged_items",
        "verified_mrms",
        "local_visual_review_comparison_only",
    ):
        assert key in comparison
    assert comparison["verified_mrms"] is False


def test_visual_review_comparison_no_baseline(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    latest = _visual_report(created_at="2026-06-28T20:00:00Z")
    comparison = compare_visual_reviews(None, latest)
    assert comparison["overall_visual_review_diff_status"] == DIFF_NO_BASELINE


def test_visual_review_comparison_unchanged(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = _visual_report(created_at="2026-06-28T20:00:00Z")
    comparison = compare_visual_reviews(report, dict(report, created_at="2026-06-28T20:01:00Z"))
    assert comparison["overall_visual_review_diff_status"] == DIFF_UNCHANGED


def test_visual_review_comparison_improved(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    baseline = _visual_report(created_at="2026-06-28T19:00:00Z", artifact_count=1, missing_artifact_count=2)
    latest = _visual_report(
        created_at="2026-06-28T20:00:00Z",
        artifact_count=3,
        missing_artifact_count=0,
        tile_modes=["decoded_prototype"],
    )
    comparison = compare_visual_reviews(baseline, latest)
    assert comparison["overall_visual_review_diff_status"] == DIFF_IMPROVED
    assert "artifact_count" in comparison["improvements"]


def test_visual_review_comparison_worsened(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    baseline = _visual_report(created_at="2026-06-28T19:00:00Z", artifact_count=4, missing_artifact_count=0)
    latest = _visual_report(created_at="2026-06-28T20:00:00Z", artifact_count=1, missing_artifact_count=3)
    comparison = compare_visual_reviews(baseline, latest)
    assert comparison["overall_visual_review_diff_status"] == DIFF_WORSENED


def test_visual_review_comparison_mixed(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    baseline = _visual_report(
        created_at="2026-06-28T19:00:00Z",
        artifact_count=2,
        missing_artifact_count=1,
        artifacts=[
            {
                "timestamp": "2026-06-28T12:00:00Z",
                "render_status": "decoded_prototype",
                "raw_kind": "mrms_real_grib2",
            }
        ],
    )
    latest = _visual_report(
        created_at="2026-06-28T20:00:00Z",
        artifact_count=3,
        missing_artifact_count=2,
        artifacts=[
            {
                "timestamp": "2026-06-28T12:00:00Z",
                "render_status": "placeholder",
                "raw_kind": "demo_seeded_stub",
            }
        ],
    )
    comparison = compare_visual_reviews(baseline, latest)
    assert comparison["overall_visual_review_diff_status"] == DIFF_MIXED


def test_visual_review_comparison_history_bounded(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    latest = _visual_report(created_at="2026-06-28T20:00:00Z")
    save_visual_review_report(storage, latest)
    for _ in range(30):
        record_visual_review_comparison(storage, latest_report=latest)
    history_path = storage.normalize_path(COMPARISON_HISTORY_PATH)
    history = json.loads(storage.absolute_path(history_path).read_text(encoding="utf-8"))
    assert len(history) == 25


def test_stale_hint_when_no_visual_review(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    hint = build_visual_review_hint(storage)
    assert hint["visual_review_regeneration_recommended"] is True
    assert hint["stale_visual_review"] is True
    assert hint["reason"] == "no_visual_review"
    assert hint["verified_mrms"] is False


def test_stale_hint_when_evidence_newer(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(
        storage,
        _visual_report(created_at="2026-06-28T10:00:00Z"),
    )
    save_latest_validation_report(
        storage,
        {"ran_at": "2026-06-28T20:00:00Z", "verified_mrms": False},
    )
    hint = build_visual_review_hint(storage)
    assert hint["visual_review_regeneration_recommended"] is True
    assert hint["stale_visual_review"] is True
    assert hint["reason"] in (
        "evidence_newer_than_visual_review",
        "missing_artifacts_and_newer_proof_render_activity",
    )


def test_no_stale_hint_when_visual_review_current(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(
        storage,
        _visual_report(created_at="2026-06-28T20:00:00Z", missing_artifact_count=0),
    )
    save_latest_validation_report(
        storage,
        {"ran_at": "2026-06-28T19:00:00Z", "verified_mrms": False},
    )
    hint = build_visual_review_hint(storage)
    assert hint["visual_review_regeneration_recommended"] is False
    assert hint["stale_visual_review"] is False


def test_summary_includes_comparison_and_hint(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    record_visual_review_comparison(storage)
    summary = build_validation_summary(db_session, storage)
    assert summary["mrms_visual_review_comparison"]["available"] is True
    assert summary["mrms_visual_review_hint"]["verified_mrms"] is False


def test_comparison_endpoint_empty(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-visual-review/comparison")
    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_mrms"] is False
    assert payload["compact"]["available"] is False


def test_hint_endpoint_safe_empty(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-visual-review/hint")
    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_mrms"] is False
    assert payload["compact"]["visual_review_regeneration_recommended"] is True


def test_comparison_and_hint_do_not_clear_alerts(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(storage, {"status": ALERT_FAILED, "operator_attention_needed": True})
    before = load_validation_alert(storage)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    record_visual_review_comparison(storage)
    build_visual_review_hint(storage)
    after = load_validation_alert(storage)
    assert after.get("status") == before.get("status")


def test_comparison_and_hint_do_not_mutate_gates(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    before_prod = settings.enable_production_radar_tiles
    before_decoded = settings.enable_decoded_tiles
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    record_visual_review_comparison(storage)
    build_visual_review_hint(storage)
    assert settings.enable_production_radar_tiles == before_prod
    assert settings.enable_decoded_tiles == before_decoded


def test_comparison_hint_always_verified_mrms_false(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    comparison = record_visual_review_comparison(
        storage,
        latest_report=_visual_report(created_at="2026-06-28T20:00:00Z"),
    )
    hint = build_visual_review_hint(storage)
    compact = compact_visual_review_hint(storage)
    assert comparison["verified_mrms"] is False
    assert hint["verified_mrms"] is False
    assert compact["verified_mrms"] is False


def test_previous_snapshot_on_save(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    first = _visual_report(created_at="2026-06-28T19:00:00Z", artifact_count=1)
    second = _visual_report(created_at="2026-06-28T20:00:00Z", artifact_count=2)
    save_visual_review_report(storage, first)
    save_visual_review_report(storage, second)
    previous_path = storage.normalize_path(VISUAL_REVIEW_PREVIOUS_JSON)
    assert storage.path_exists(previous_path)
    previous = json.loads(storage.absolute_path(previous_path).read_text(encoding="utf-8"))
    assert previous["created_at"] == "2026-06-28T19:00:00Z"


def test_record_comparison_persists_latest(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    record_visual_review_comparison(storage)
    latest_path = storage.normalize_path(COMPARISON_LATEST_PATH)
    assert storage.path_exists(latest_path)
    loaded = load_latest_visual_review_comparison(storage)
    assert loaded is not None
    assert loaded["verified_mrms"] is False


def test_production_tile_serving_remains_gated(client, db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T11:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase57.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PLACEHOLDER,
        production_rendering=False,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()
    response = client.get("/tiles/mrms_reflectivity/2026-06-28T11:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"
