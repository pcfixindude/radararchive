"""Tests for review session export diff trend regeneration hints (Phase 47)."""

from __future__ import annotations

import json

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_IMPROVED,
    DIFF_MIXED,
    DIFF_UNCHANGED,
    DIFF_WORSENED,
)
from backend.app.services.mrms_review_session import create_review_session_record
from backend.app.services.mrms_review_session_export import export_latest_review_session
from backend.app.services.mrms_review_session_export_diff import (
    EXPORT_DIFF_HISTORY_PATH,
    EXPORT_DIFF_LATEST_PATH,
    record_export_diff_metadata,
)
from backend.app.services.mrms_review_session_export_diff_trend_hint import (
    SUGGESTED_EXPORT_COMMAND,
    SUGGESTED_SCHEDULED_REVIEW_EXPORT_COMMAND,
    SUGGESTED_SESSION_EXPORT_COMMAND,
    build_review_session_export_diff_trend_hint,
)
from backend.app.services.mrms_review_session_export_diff_trends import TREND_STABLE
from backend.app.services.scheduled_validation import run_scheduled_validation
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _diff_entry(*, compared_at: str, status: str) -> dict:
    return {
        "compared_at": compared_at,
        "latest_export_created_at": compared_at,
        "baseline_export_created_at": "2026-06-28T15:00:00Z",
        "overall_export_diff_status": status,
        "session_changed": status != DIFF_UNCHANGED,
        "verified_mrms": False,
        "local_export_diff_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def _seed_diff_history(storage: LocalStorage, statuses: list[str]) -> None:
    total = len(statuses)
    entries = [
        _diff_entry(
            compared_at=f"2026-06-28T16:{total - 1 - index:02d}:00Z",
            status=status,
        )
        for index, status in enumerate(statuses)
    ]
    repo_path = storage.normalize_path(EXPORT_DIFF_HISTORY_PATH)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(json.dumps(entries, indent=2), encoding="utf-8")
    if entries:
        latest_repo = storage.normalize_path(EXPORT_DIFF_LATEST_PATH)
        storage.absolute_path(latest_repo).write_text(json.dumps(entries[0], indent=2), encoding="utf-8")


def test_trend_hint_shape(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_WORSENED, DIFF_UNCHANGED])
    hint = build_review_session_export_diff_trend_hint(storage)
    assert "review_trend_regeneration_recommended" in hint
    assert "suggested_command" in hint
    assert "trend" in hint
    assert "latest_export_diff_status" in hint
    assert hint["verified_mrms"] is False
    assert hint["local_hint_only"] is True
    assert hint["does_not_clear_alerts"] is True
    assert hint["does_not_enable_production"] is True


def test_no_data_hint_behavior(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    hint = build_review_session_export_diff_trend_hint(storage)
    assert hint["review_trend_regeneration_recommended"] is False
    assert hint["reason"] == "no_export_diff_trend_data"
    assert hint["suggested_command"] is None


def test_worsening_trend_recommends_regeneration(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_WORSENED, DIFF_WORSENED, DIFF_UNCHANGED])
    hint = build_review_session_export_diff_trend_hint(storage)
    assert hint["review_trend_regeneration_recommended"] is True
    assert hint["reason"] == "export_diff_trend_worsening"
    assert hint["suggested_command"] == SUGGESTED_SESSION_EXPORT_COMMAND


def test_mixed_trend_streak_recommends_regeneration(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_MIXED, DIFF_MIXED, DIFF_UNCHANGED])
    hint = build_review_session_export_diff_trend_hint(storage)
    assert hint["review_trend_regeneration_recommended"] is True
    assert hint["reason"] == "export_diff_trend_mixed_streak"


def test_latest_export_diff_worsened_recommends(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_UNCHANGED, DIFF_UNCHANGED])
    latest_repo = storage.normalize_path(EXPORT_DIFF_LATEST_PATH)
    latest = json.loads(storage.absolute_path(latest_repo).read_text(encoding="utf-8"))
    latest["overall_export_diff_status"] = DIFF_WORSENED
    storage.absolute_path(latest_repo).write_text(json.dumps(latest, indent=2), encoding="utf-8")
    hint = build_review_session_export_diff_trend_hint(storage)
    assert hint["review_trend_regeneration_recommended"] is True
    assert hint["reason"] == "latest_export_diff_worsened"


def test_session_newer_than_export_recommends(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_UNCHANGED, DIFF_UNCHANGED])
    first = create_review_session_record(
        storage,
        operator_initials="OLD",
        session_notes="older",
        accepted_limitations=True,
    )
    export_latest_review_session(storage, session=first)
    create_review_session_record(
        storage,
        operator_initials="NEW",
        session_notes="newer session",
        accepted_limitations=True,
    )
    hint = build_review_session_export_diff_trend_hint(storage)
    assert hint["review_trend_regeneration_recommended"] is True
    assert hint["reason"] == "latest_review_session_newer_than_export"
    assert hint["export_is_stale"] is True
    assert hint["suggested_command"] == SUGGESTED_EXPORT_COMMAND


def test_digest_regeneration_recommends_scheduled_export(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_UNCHANGED, DIFF_UNCHANGED])

    def _digest_hint(_storage):
        return {
            "digest_regeneration_recommended": True,
            "reason": "test_digest_stale",
            "verified_mrms": False,
        }

    monkeypatch.setattr(
        "backend.app.services.mrms_review_session_export_diff_trend_hint.build_digest_regeneration_hint",
        _digest_hint,
    )
    hint = build_review_session_export_diff_trend_hint(storage)
    assert hint["review_trend_regeneration_recommended"] is True
    assert hint["reason"].startswith("digest_regeneration_recommended")
    assert hint["suggested_command"] == SUGGESTED_SCHEDULED_REVIEW_EXPORT_COMMAND


def test_stable_trend_does_not_recommend(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record = create_review_session_record(
        storage,
        operator_initials="ST",
        session_notes="stable",
        accepted_limitations=True,
    )
    export_latest_review_session(storage, session=record)
    _seed_diff_history(storage, [DIFF_UNCHANGED, DIFF_UNCHANGED, DIFF_UNCHANGED])
  # refresh latest diff to unchanged after export
    record_export_diff_metadata(
        storage,
        _diff_entry(compared_at="2026-06-28T16:10:00Z", status=DIFF_UNCHANGED),
        baseline_history_entry=_diff_entry(
            compared_at="2026-06-28T16:09:00Z", status=DIFF_UNCHANGED
        ),
    )
    hint = build_review_session_export_diff_trend_hint(storage)
    assert hint["trend"] == TREND_STABLE
    assert hint["review_trend_regeneration_recommended"] is False


def test_summary_includes_trend_hint(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_WORSENED, DIFF_WORSENED])
    summary = build_validation_summary(db_session, storage)
    hint = summary.get("mrms_review_session_export_diff_trend_hint")
    assert hint is not None
    assert hint["review_trend_regeneration_recommended"] is True
    assert hint["verified_mrms"] is False


def test_trend_hint_endpoint_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/review-sessions/export/diff/trend-hint")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["local_hint_only"] is True
    assert body["hint"]["review_trend_regeneration_recommended"] is False


def test_scheduled_validation_includes_hint_when_review_export_requested(
    db_session, storage, monkeypatch
):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    from backend.app.services.mrms_batch_validation import BatchValidationReport
    from backend.app.services.render_queue_benchmark import RenderQueueBenchmarkReport

    create_review_session_record(
        storage,
        operator_initials="SCH",
        session_notes="scheduled hint",
        accepted_limitations=True,
    )
    _seed_diff_history(storage, [DIFF_WORSENED, DIFF_WORSENED])
    report = run_scheduled_validation(
        db_session,
        storage,
        batch_fn=lambda *_a, **_k: BatchValidationReport(source_mode="stub", effective_frame_count=1),
        queue_benchmark_fn=lambda *_a, **_k: RenderQueueBenchmarkReport(
            source_mode="stub", jobs_succeeded=1
        ),
        review_export_requested=True,
        persist=False,
    )
    assert report.review_export_trend_hint is not None
    assert report.review_export_trend_hint["verified_mrms"] is False
    body = report.to_dict()
    assert body["review_export_trend_hint"]["review_trend_regeneration_recommended"] is True


def test_hint_always_verified_mrms_false(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_MIXED])
    hint = build_review_session_export_diff_trend_hint(storage)
    assert hint["verified_mrms"] is False


def test_hint_does_not_clear_alerts(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
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
    alert_before = load_validation_alert(storage)
    _seed_diff_history(storage, [DIFF_WORSENED, DIFF_WORSENED])
    build_review_session_export_diff_trend_hint(storage)
    alert_after = load_validation_alert(storage)
    if alert_before is not None:
        assert alert_after is not None
        assert alert_after.get("operator_attention_needed") == alert_before.get(
            "operator_attention_needed"
        )


def test_hint_does_not_mutate_production_gates(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    radar = RadarFile(
        product_id="mrms",
        timestamp="2026-06-28T12:00:00Z",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
    )
    db_session.add(radar)
    db_session.commit()
    _seed_diff_history(storage, [DIFF_WORSENED])
    build_review_session_export_diff_trend_hint(storage)
    assert settings.enable_production_radar_tiles is False
    summary = build_validation_summary(db_session, storage)
    assert summary["verified_mrms"] is False
    assert summary["catalog"]["verified_mrms"] is False


def test_latest_export_diff_mixed_recommends(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_IMPROVED, DIFF_IMPROVED])
    latest_repo = storage.normalize_path(EXPORT_DIFF_LATEST_PATH)
    latest = json.loads(storage.absolute_path(latest_repo).read_text(encoding="utf-8"))
    latest["overall_export_diff_status"] = DIFF_MIXED
    storage.absolute_path(latest_repo).write_text(json.dumps(latest, indent=2), encoding="utf-8")
    hint = build_review_session_export_diff_trend_hint(storage)
    assert hint["review_trend_regeneration_recommended"] is True
    assert hint["reason"] == "latest_export_diff_mixed"
