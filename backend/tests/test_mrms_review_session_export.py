"""Tests for local MRMS proof review session Markdown export (Phase 43)."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_review_session import create_review_session_record
from backend.app.services.mrms_review_session_compare import record_review_session_comparison
from backend.app.services.mrms_review_session_export import (
    MAX_EXPORT_HISTORY,
    ReviewSessionExportError,
    build_review_export_regeneration_hint,
    export_latest_review_session,
    load_latest_review_session_export_metadata,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def test_export_metadata_shape(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="export shape test",
        accepted_limitations=True,
    )
    metadata = export_latest_review_session(storage)
    assert metadata["created_at"]
    assert metadata["export_path"]
    assert metadata["metadata_path"]
    assert metadata["session_id"]
    assert metadata["operator"] == "OP"
    assert metadata["verified_mrms"] is False
    assert metadata["local_export_only"] is True
    assert metadata["does_not_clear_alerts"] is True
    assert metadata["does_not_enable_production"] is True


def test_markdown_contains_session_summary(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="MD",
        session_notes="markdown session notes",
        accepted_limitations=True,
    )
    export_latest_review_session(storage)
    md_path = storage.absolute_path("dev/mrms_review_session_export_latest.md")
    text = md_path.read_text(encoding="utf-8")
    assert "Review session summary" in text
    assert "markdown session notes" in text
    assert "MD" in text
    assert "Open attention count" in text


def test_markdown_contains_comparison_summary(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="B",
        session_notes="baseline",
        accepted_limitations=True,
    )
    create_review_session_record(
        storage,
        operator_initials="L",
        session_notes="latest",
        accepted_limitations=True,
    )
    record_review_session_comparison(storage)
    export_latest_review_session(storage)
    text = storage.absolute_path("dev/mrms_review_session_export_latest.md").read_text(
        encoding="utf-8"
    )
    assert "Comparison vs previous session" in text
    assert "Overall review diff status" in text
    assert "Improvements" in text
    assert "Regressions" in text


def test_markdown_contains_open_attention_guidance(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    import json

    from backend.app.services.mrms_proof_bundle_diff import DIFF_WORSENED
    from backend.app.services.proof_bundle_diff_alert_history import (
        record_proof_bundle_diff_alert_history,
    )
    from backend.app.services.validation_alerts import refresh_validation_alert

    diff_path = storage.absolute_path("dev/mrms_proof_bundle_diff_latest.json")
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    diff_path.write_text(
        json.dumps(
            {
                "overall_diff_status": DIFF_WORSENED,
                "checked_at": "2026-06-28T16:12:00Z",
                "verified_mrms": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    record_proof_bundle_diff_alert_history(
        storage,
        {
            "overall_diff_status": DIFF_WORSENED,
            "checked_at": "2026-06-28T16:12:00Z",
            "evidence_changes_count": 1,
            "current_bundle": {"bundle_id": "b1"},
            "baseline_bundle": {"bundle_id": "base"},
            "verified_mrms": False,
            "operator_attention_needed": True,
        },
        skip_duplicate=False,
    )
    refresh_validation_alert(storage)
    create_review_session_record(
        storage,
        operator_initials="G",
        session_notes="guidance export",
        accepted_limitations=True,
    )
    export_latest_review_session(storage)
    text = storage.absolute_path("dev/mrms_review_session_export_latest.md").read_text(
        encoding="utf-8"
    )
    assert "Open attention guidance" in text
    assert "RUNBOOK_REAL_MRMS_VALIDATION.md" in text


def test_markdown_contains_safety_warnings(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="W",
        session_notes="warnings",
        accepted_limitations=True,
    )
    export_latest_review_session(storage)
    text = storage.absolute_path("dev/mrms_review_session_export_latest.md").read_text(
        encoding="utf-8"
    )
    assert "**NOT** verify MRMS" in text or "not verified MRMS" in text
    assert "Does not clear validation alerts" in text
    assert "Does not enable production rendering" in text
    assert "Does not notify externally" in text
    assert "local review export only" in text.lower() or "Local review export only" in text


def test_no_session_export_raises(storage):
    with pytest.raises(ReviewSessionExportError):
        export_latest_review_session(storage)


def test_bounded_export_history(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    for index in range(MAX_EXPORT_HISTORY + 3):
        create_review_session_record(
            storage,
            operator_initials=f"O{index}",
            session_notes=f"export {index}",
            accepted_limitations=True,
        )
        export_latest_review_session(storage)
    history_path = storage.absolute_path("dev/mrms_review_session_export_history.json")
    history = __import__("json").loads(history_path.read_text(encoding="utf-8"))
    assert len(history) == MAX_EXPORT_HISTORY


def test_regeneration_hint_when_export_missing(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="hint missing export",
        accepted_limitations=True,
    )
    hint = build_review_export_regeneration_hint(storage)
    assert hint["review_export_regeneration_recommended"] is True
    assert hint["reason"] == "review_export_missing"
    assert hint["suggested_command"] == "make mrms-review-session-export"
    assert hint["verified_mrms"] is False


def test_regeneration_hint_when_session_newer_than_export(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="OLD",
        session_notes="older session",
        accepted_limitations=True,
    )
    export_latest_review_session(storage)
    create_review_session_record(
        storage,
        operator_initials="NEW",
        session_notes="newer session",
        accepted_limitations=True,
    )
    hint = build_review_export_regeneration_hint(storage)
    assert hint["review_export_regeneration_recommended"] is True
    assert hint["reason"] == "latest_review_session_newer_than_export"


def test_regeneration_hint_when_comparison_newer_than_export(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="B",
        session_notes="baseline",
        accepted_limitations=True,
    )
    create_review_session_record(
        storage,
        operator_initials="L",
        session_notes="latest",
        accepted_limitations=True,
    )
    export_latest_review_session(storage)
    create_review_session_record(
        storage,
        operator_initials="NEW",
        session_notes="triggers new comparison",
        accepted_limitations=True,
    )
    hint = build_review_export_regeneration_hint(storage)
    assert hint["review_export_regeneration_recommended"] is True
    assert hint["reason"] in (
        "latest_review_session_newer_than_export",
        "latest_comparison_newer_than_export",
    )


def test_summary_includes_export_and_hint(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="SUM",
        session_notes="summary export",
        accepted_limitations=True,
    )
    export_latest_review_session(storage)
    summary = build_validation_summary(db_session, storage)
    export_compact = summary.get("mrms_review_session_export")
    hint = summary.get("review_export_regeneration_hint")
    assert export_compact is not None
    assert export_compact["available"] is True
    assert export_compact["verified_mrms"] is False
    assert hint is not None
    assert hint["verified_mrms"] is False


def test_export_endpoints_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/review-sessions/export")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["local_export_only"] is True
    assert body["compact"]["available"] is False

    history_response = client.get("/api/validation/review-sessions/export/history")
    assert history_response.status_code == 200
    assert history_response.json()["count"] == 0


def test_export_does_not_clear_alerts(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    from backend.app.services.mrms_proof_bundle_diff import DIFF_WORSENED
    from backend.app.services.proof_bundle_diff_alert_history import (
        record_proof_bundle_diff_alert_history,
    )

    record_proof_bundle_diff_alert_history(
        storage,
        {
            "overall_diff_status": DIFF_WORSENED,
            "checked_at": "2026-06-28T16:12:00Z",
            "evidence_changes_count": 1,
            "current_bundle": {"bundle_id": "b1"},
            "baseline_bundle": {"bundle_id": "base"},
            "verified_mrms": False,
            "operator_attention_needed": True,
        },
        skip_duplicate=False,
    )
    create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="alert test",
        accepted_limitations=True,
    )
    alert_before = load_validation_alert(storage)
    export_latest_review_session(storage)
    alert_after = load_validation_alert(storage)
    if alert_before is not None:
        assert alert_after is not None
        assert alert_after.get("operator_attention_needed") == alert_before.get(
            "operator_attention_needed"
        )


def test_export_does_not_mutate_production_gates(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T11:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase43.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=False,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="gate test",
        accepted_limitations=True,
    )
    export_latest_review_session(storage)
    db_session.refresh(frame)
    assert frame.production_rendering is False

    response = client.get("/tiles/mrms_reflectivity/2026-06-28T11:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"


def test_runtime_export_artifacts_gitignored():
    gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
    text = gitignore.read_text(encoding="utf-8")
    assert "mrms_review_session_export_latest.md" in text
    assert "mrms_review_session_export_latest.json" in text
    assert "mrms_review_session_export_history.json" in text


def test_export_always_verified_mrms_false(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="verified false",
        accepted_limitations=True,
    )
    metadata = export_latest_review_session(storage)
    assert metadata["verified_mrms"] is False
    loaded = load_latest_review_session_export_metadata(storage)
    assert loaded is not None
    assert loaded["verified_mrms"] is False
