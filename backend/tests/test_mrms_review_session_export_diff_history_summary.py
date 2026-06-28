"""Tests for compact review session export diff history summary (Phase 48)."""

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
from backend.app.services.mrms_review_session_export_diff import (
    EXPORT_DIFF_HISTORY_PATH,
    compact_export_diff_history_entry,
    compact_review_session_export_diff_history_summary,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _diff_entry(*, compared_at: str, status: str, index: int = 0) -> dict:
    return {
        "compared_at": compared_at,
        "latest_export_created_at": compared_at,
        "baseline_export_created_at": "2026-06-28T15:00:00Z",
        "overall_export_diff_status": status,
        "latest_session_id": f"latest-{index}",
        "baseline_session_id": f"baseline-{index}",
        "session_changed": status != DIFF_UNCHANGED,
        "open_attention_count_change": {"baseline": index + 1, "latest": index},
        "comparison_status_change": {"baseline": DIFF_UNCHANGED, "latest": status},
        "escalation_level_change": {"baseline": "none", "latest": "watch"},
        "digest_regeneration_recommended_change": {"baseline": True, "latest": False},
        "improvements": ["open_attention_count"] if status == DIFF_IMPROVED else [],
        "regressions": ["open_attention_count"] if status == DIFF_WORSENED else [],
        "verified_mrms": False,
        "local_export_diff_only": True,
    }


def _seed_history(storage: LocalStorage, count: int) -> None:
    entries = [
        _diff_entry(
            compared_at=f"2026-06-28T16:{count - 1 - index:02d}:00Z",
            status=DIFF_UNCHANGED if index % 2 == 0 else DIFF_IMPROVED,
            index=index,
        )
        for index in range(count)
    ]
    repo_path = storage.normalize_path(EXPORT_DIFF_HISTORY_PATH)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(json.dumps(entries, indent=2), encoding="utf-8")


def test_compact_history_entry_shape(storage):
    entry = compact_export_diff_history_entry(
        _diff_entry(compared_at="2026-06-28T16:00:00Z", status=DIFF_WORSENED, index=1)
    )
    assert entry is not None
    assert entry["created_at"] == "2026-06-28T16:00:00Z"
    assert entry["overall_export_diff_status"] == DIFF_WORSENED
    assert entry["improvements_count"] == 0
    assert entry["regressions_count"] == 1
    assert entry["verified_mrms"] is False
    assert entry["local_export_diff_history_only"] is True


def test_summary_includes_compact_export_diff_history(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(storage, 3)
    summary = build_validation_summary(db_session, storage)
    history = summary.get("mrms_review_session_export_diff_history")
    assert history is not None
    assert history["count"] == 3
    assert history["latest_status"] is not None
    assert history["latest_created_at"] is not None
    assert len(history["recent"]) <= 5
    assert history["verified_mrms"] is False
    assert history["local_export_diff_history_only"] is True


def test_compact_history_missing_file(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    summary = compact_review_session_export_diff_history_summary(storage)
    assert summary["available"] is False
    assert summary["count"] == 0
    assert summary["recent"] == []
    assert summary["verified_mrms"] is False
    assert summary["does_not_clear_alerts"] is True
    assert summary["does_not_enable_production"] is True


def test_compact_history_limits_recent_to_five(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(storage, 8)
    summary = compact_review_session_export_diff_history_summary(storage)
    assert summary["count"] == 8
    assert len(summary["recent"]) == 5


def test_export_diff_history_endpoint_read_only(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history(storage, 2)
    response = client.get("/api/validation/review-sessions/export/diff/history")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["count"] == 2


def test_history_does_not_clear_alerts(storage, monkeypatch):
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
    _seed_history(storage, 2)
    compact_review_session_export_diff_history_summary(storage)
    alert_after = load_validation_alert(storage)
    if alert_before is not None:
        assert alert_after is not None
        assert alert_after.get("operator_attention_needed") == alert_before.get(
            "operator_attention_needed"
        )


def test_history_does_not_mutate_production_gates(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    radar = RadarFile(
        product_id="mrms",
        timestamp="2026-06-28T12:00:00Z",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
    )
    db_session.add(radar)
    db_session.commit()
    _seed_history(storage, 2)
    assert settings.enable_production_radar_tiles is False
    summary = build_validation_summary(db_session, storage)
    assert summary["verified_mrms"] is False
    assert summary["catalog"]["verified_mrms"] is False


def test_recorded_diff_appears_in_compact_history(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    entries = [
        _diff_entry(compared_at="2026-06-28T16:05:00Z", status=DIFF_MIXED, index=1),
        _diff_entry(compared_at="2026-06-28T16:04:00Z", status=DIFF_UNCHANGED, index=0),
    ]
    repo_path = storage.normalize_path(EXPORT_DIFF_HISTORY_PATH)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(json.dumps(entries, indent=2), encoding="utf-8")
    summary = compact_review_session_export_diff_history_summary(storage)
    assert summary["available"] is True
    assert summary["latest_status"] == DIFF_MIXED
