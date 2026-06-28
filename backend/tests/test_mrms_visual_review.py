"""Tests for MRMS visual review artifacts (Phase 56)."""

from __future__ import annotations

import json

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import (
    PROCESSED_STATUS_PLACEHOLDER_FOR_REAL_RAW,
    PROCESSED_STATUS_PLACEHOLDER_PROCESSED,
    RENDER_STATUS_PLACEHOLDER,
    RENDER_STATUS_PRODUCTION_RENDERED,
)
from backend.app.services.mrms_visual_review import (
    MAX_VISUAL_REVIEW_HISTORY,
    TILE_MODE_DECODED_PROTOTYPE,
    TILE_MODE_PLACEHOLDER,
    TILE_MODE_PLACEHOLDER_FOR_REAL_RAW,
    TILE_MODE_PRODUCTION_GATED,
    TILE_MODE_PRODUCTION_RENDERED_CACHE,
    VISUAL_REVIEW_HISTORY,
    VISUAL_REVIEW_LATEST_JSON,
    VISUAL_REVIEW_LATEST_MD,
    build_visual_review_report,
    classify_visual_tile_mode,
    compact_mrms_visual_review,
    generate_mrms_visual_review,
    load_latest_visual_review,
    load_visual_review_history,
    save_visual_review_report,
)
from backend.app.services.tile_pyramid import build_production_tile_repo_path
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))


def test_visual_review_report_shape(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T12:00:00Z",
        processed_status=PROCESSED_STATUS_PLACEHOLDER_PROCESSED,
        render_status=RENDER_STATUS_PLACEHOLDER,
        production_rendering=False,
        source="demo",
    )
    db_session.add(frame)
    db_session.commit()

    report = build_visual_review_report(db_session, storage)
    for key in (
        "created_at",
        "layers_inspected",
        "timestamps_inspected",
        "artifact_count",
        "missing_artifact_count",
        "tile_modes_found",
        "artifacts",
        "json_path",
        "markdown_path",
        "verified_mrms",
        "local_visual_review_only",
        "does_not_clear_alerts",
        "does_not_enable_production",
    ):
        assert key in report
    assert report["verified_mrms"] is False
    assert report["local_visual_review_only"] is True


def test_visual_review_empty_catalog_safe(tmp_path, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    from backend.app.database import configure_test_database, reset_engine

    session_factory = configure_test_database(tmp_path / "empty_visual_review.sqlite")
    session = session_factory()
    try:
        report = build_visual_review_report(session, storage)
        assert report["frame_count"] == 0
        assert report["artifact_count"] == 0
        assert report["artifacts"] == []
        compact = compact_mrms_visual_review(storage)
        assert compact["available"] is False
        assert compact["verified_mrms"] is False
    finally:
        session.close()
        reset_engine()


def test_visual_review_markdown_contains_safety_warnings(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = generate_mrms_visual_review(db_session, storage)
    md_path = storage.absolute_path(report["markdown_path"])
    markdown = md_path.read_text(encoding="utf-8")
    assert "WARNING" in markdown
    assert "does **NOT** verify MRMS" in markdown
    assert "does not execute commands" in markdown.lower() or "Copy suggested commands manually" in markdown


def test_classify_placeholder_tile_mode():
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T12:00:00Z",
        processed_status=PROCESSED_STATUS_PLACEHOLDER_PROCESSED,
        render_status=RENDER_STATUS_PLACEHOLDER,
        production_rendering=False,
        source="demo",
    )
    mode = classify_visual_tile_mode(
        frame=frame,
        has_decode_artifact=False,
        has_decoded_tile=False,
        has_production_tile=False,
        has_processed_path=True,
    )
    assert mode == TILE_MODE_PLACEHOLDER


def test_classify_placeholder_for_real_raw():
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T12:00:00Z",
        processed_status=PROCESSED_STATUS_PLACEHOLDER_FOR_REAL_RAW,
        render_status=RENDER_STATUS_PLACEHOLDER,
        production_rendering=False,
        source="demo",
    )
    mode = classify_visual_tile_mode(
        frame=frame,
        has_decode_artifact=False,
        has_decoded_tile=False,
        has_production_tile=False,
        has_processed_path=True,
    )
    assert mode == TILE_MODE_PLACEHOLDER_FOR_REAL_RAW


def test_classify_production_gated_and_cache(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    timestamp = "2026-06-28T12:00:00Z"
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        processed_status=PROCESSED_STATUS_PLACEHOLDER_PROCESSED,
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=True,
        source="demo",
    )
    db_session.add(frame)
    db_session.commit()

    gated = classify_visual_tile_mode(
        frame=frame,
        has_decode_artifact=False,
        has_decoded_tile=False,
        has_production_tile=False,
        has_processed_path=False,
    )
    assert gated == TILE_MODE_PRODUCTION_GATED

    prod_path = build_production_tile_repo_path(storage, "mrms_reflectivity", timestamp, 0, 0, 0)
    storage.ensure_directories(prod_path.rsplit("/", 1)[0])
    storage.write_bytes(prod_path, b"\x89PNG\r\n\x1a\n")

    cached = classify_visual_tile_mode(
        frame=frame,
        has_decode_artifact=False,
        has_decoded_tile=False,
        has_production_tile=True,
        has_processed_path=False,
    )
    assert cached == TILE_MODE_PRODUCTION_RENDERED_CACHE


def test_visual_review_history_bounded(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    for _ in range(MAX_VISUAL_REVIEW_HISTORY + 3):
        generate_mrms_visual_review(db_session, storage)
    history = load_visual_review_history(storage)
    assert len(history) == MAX_VISUAL_REVIEW_HISTORY


def test_summary_includes_compact_visual_review(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_mrms_visual_review(db_session, storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_visual_review")
    assert compact is not None
    assert compact["available"] is True
    assert compact["verified_mrms"] is False


def test_visual_review_endpoint_empty(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-visual-review")
    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_mrms"] is False
    assert payload["compact"]["available"] is False
    assert payload["latest"] is None


def test_visual_review_endpoint_with_report(client, db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_mrms_visual_review(db_session, storage)
    response = client.get("/api/validation/mrms-visual-review")
    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_mrms"] is False
    assert payload["compact"]["available"] is True
    assert payload["latest"] is not None


def test_visual_review_history_endpoint(client, db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_mrms_visual_review(db_session, storage)
    response = client.get("/api/validation/mrms-visual-review/history")
    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_mrms"] is False
    assert payload["count"] >= 1


def test_visual_review_does_not_clear_alerts(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(
        storage,
        {
            "status": ALERT_FAILED,
            "operator_attention_needed": True,
            "verified_mrms": False,
        },
    )
    before = load_validation_alert(storage)
    generate_mrms_visual_review(db_session, storage)
    after = load_validation_alert(storage)
    assert after is not None
    assert after.get("status") == before.get("status")


def test_visual_review_does_not_mutate_production_flags(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    before_prod = settings.enable_production_radar_tiles
    before_decoded = settings.enable_decoded_tiles
    generate_mrms_visual_review(db_session, storage)
    assert settings.enable_production_radar_tiles == before_prod
    assert settings.enable_decoded_tiles == before_decoded


def test_visual_review_always_verified_mrms_false(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = generate_mrms_visual_review(db_session, storage)
    assert report["verified_mrms"] is False
    latest = load_latest_visual_review(storage)
    assert latest is not None
    assert latest["verified_mrms"] is False
    history = load_visual_review_history(storage)
    assert all(entry.get("verified_mrms") is False for entry in history)


def test_production_tile_serving_remains_gated(client, db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T11:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase56.grib2.gz"),
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


def test_save_visual_review_writes_expected_paths(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = build_visual_review_report(db_session, storage)
    save_visual_review_report(storage, report)
    json_repo = storage.normalize_path(VISUAL_REVIEW_LATEST_JSON)
    md_repo = storage.normalize_path(VISUAL_REVIEW_LATEST_MD)
    history_repo = storage.normalize_path(VISUAL_REVIEW_HISTORY)
    assert storage.path_exists(json_repo)
    assert storage.path_exists(md_repo)
    assert storage.path_exists(history_repo)
    saved = json.loads(storage.absolute_path(json_repo).read_text(encoding="utf-8"))
    assert saved["verified_mrms"] is False
