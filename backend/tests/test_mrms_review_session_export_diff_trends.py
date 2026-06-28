"""Tests for review session export diff trends (Phase 46)."""

from __future__ import annotations

import json

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_IMPROVED,
    DIFF_MIXED,
    DIFF_NO_BASELINE,
    DIFF_UNCHANGED,
    DIFF_WORSENED,
)
from backend.app.services.mrms_review_session import create_review_session_record
from backend.app.services.mrms_review_session_export_diff import EXPORT_DIFF_HISTORY_PATH
from backend.app.services.mrms_review_session_export_diff_trends import (
    TREND_IMPROVING,
    TREND_MIXED,
    TREND_NO_DATA,
    TREND_STABLE,
    TREND_WORSENING,
    build_review_session_export_diff_trend,
    compact_review_session_export_diff_trend,
)
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
    """Seed history where statuses[0] is the latest (newest) entry."""
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


def test_export_diff_trend_shape(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_WORSENED, DIFF_UNCHANGED])
    trend = build_review_session_export_diff_trend(storage)
    assert trend["latest_status"] == DIFF_WORSENED
    assert trend["total_diffs"] == 2
    assert "current_worsened_streak" in trend
    assert "current_mixed_or_worsened_streak" in trend
    assert "longest_worsened_streak" in trend
    assert "longest_mixed_or_worsened_streak" in trend
    assert trend["verified_mrms"] is False
    assert trend["local_trend_only"] is True
    assert trend["does_not_clear_alerts"] is True
    assert trend["does_not_enable_production"] is True


def test_no_data_trend(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    trend = build_review_session_export_diff_trend(storage)
    assert trend["trend"] == TREND_NO_DATA
    assert trend["total_diffs"] == 0
    assert trend["history_count"] == 0


def test_stable_trend(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_UNCHANGED, DIFF_UNCHANGED, DIFF_UNCHANGED])
    trend = build_review_session_export_diff_trend(storage)
    assert trend["trend"] == TREND_STABLE
    assert trend["unchanged_count"] >= 2


def test_improving_trend(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_IMPROVED, DIFF_IMPROVED, DIFF_WORSENED])
    trend = build_review_session_export_diff_trend(storage)
    assert trend["trend"] == TREND_IMPROVING
    assert trend["improved_count"] >= 2
    assert trend["last_improved_at"] is not None


def test_worsening_trend(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_WORSENED, DIFF_WORSENED, DIFF_UNCHANGED])
    trend = build_review_session_export_diff_trend(storage)
    assert trend["trend"] == TREND_WORSENING
    assert trend["worsened_count"] >= 2
    assert trend["last_worsened_at"] is not None


def test_mixed_trend(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_MIXED, DIFF_MIXED, DIFF_UNCHANGED])
    trend = build_review_session_export_diff_trend(storage)
    assert trend["trend"] == TREND_MIXED
    assert trend["mixed_count"] >= 2
    assert trend["last_mixed_at"] is not None


def test_current_worsened_streak(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_WORSENED, DIFF_WORSENED, DIFF_IMPROVED])
    trend = build_review_session_export_diff_trend(storage)
    assert trend["current_worsened_streak"] >= 2


def test_current_mixed_or_worsened_streak(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_MIXED, DIFF_WORSENED, DIFF_IMPROVED])
    trend = build_review_session_export_diff_trend(storage)
    assert trend["current_mixed_or_worsened_streak"] >= 2


def test_last_worsened_improved_timestamps(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_IMPROVED, DIFF_WORSENED, DIFF_UNCHANGED])
    trend = build_review_session_export_diff_trend(storage)
    assert trend["last_worsened_at"] == "2026-06-28T16:01:00Z"
    assert trend["last_improved_at"] == "2026-06-28T16:02:00Z"


def test_summary_includes_export_diff_trend(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_IMPROVED, DIFF_WORSENED])
    summary = build_validation_summary(db_session, storage)
    trend = summary.get("mrms_review_session_export_diff_trend")
    assert trend is not None
    assert trend["available"] is True
    assert trend["verified_mrms"] is False
    assert trend["local_trend_only"] is True


def test_trend_endpoint_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/review-sessions/export/diff/trend")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["local_trend_only"] is True
    assert body["trend"]["trend"] == TREND_NO_DATA
    assert body["trend"]["available"] is False


def test_trend_always_verified_mrms_false(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_UNCHANGED])
    trend = compact_review_session_export_diff_trend(storage)
    assert trend["verified_mrms"] is False


def test_trend_does_not_clear_alerts(storage, monkeypatch):
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
    _seed_diff_history(storage, [DIFF_WORSENED, DIFF_MIXED])
    build_review_session_export_diff_trend(storage)
    alert_after = load_validation_alert(storage)
    if alert_before is not None:
        assert alert_after is not None
        assert alert_after.get("operator_attention_needed") == alert_before.get(
            "operator_attention_needed"
        )


def test_trend_does_not_mutate_production_gates(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    radar = RadarFile(
        product_id="mrms",
        timestamp="2026-06-28T12:00:00Z",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
    )
    db_session.add(radar)
    db_session.commit()
    _seed_diff_history(storage, [DIFF_WORSENED, DIFF_IMPROVED])
    assert settings.enable_production_radar_tiles is False
    summary = build_validation_summary(db_session, storage)
    assert summary["verified_mrms"] is False
    assert summary["catalog"]["verified_mrms"] is False


def test_no_baseline_count(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_diff_history(storage, [DIFF_UNCHANGED, DIFF_NO_BASELINE])
    trend = build_review_session_export_diff_trend(storage)
    assert trend["no_baseline_count"] == 1
