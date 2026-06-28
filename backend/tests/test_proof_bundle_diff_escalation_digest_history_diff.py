"""Tests for digest export history, diff metadata, and regeneration hints (Phase 40)."""

from __future__ import annotations

import json
from pathlib import Path

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
from backend.app.services.proof_bundle_diff_escalation import ESCALATION_URGENT
from backend.app.services.proof_bundle_diff_escalation_digest import (
    export_proof_bundle_diff_escalation_digest,
)
from backend.app.services.proof_bundle_diff_escalation_digest_diff import (
    DIGEST_DIFF_LATEST_PATH,
    build_digest_regeneration_hint,
    compare_digest_metadata,
    record_digest_diff_metadata,
)
from backend.app.services.proof_bundle_diff_escalation_digest_history import (
    DIGEST_HISTORY_PATH,
    MAX_DIGEST_HISTORY,
    build_digest_history_entry,
    load_digest_export_history,
    record_digest_export_history,
)
from backend.app.services.proof_bundle_diff_alert_history import (
    record_proof_bundle_diff_alert_history,
)
from backend.app.services.proof_bundle_diff_escalation_history import (
    ESCALATION_HISTORY_PATH,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _metadata(
    *,
    generated_at: str,
    level: str = "none",
    diff_status: str = "unchanged",
    urgent: int = 0,
    attention: int = 0,
    stale_ack: int = 0,
    streak: int = 0,
) -> dict:
    return {
        "generated_at": generated_at,
        "markdown_path": "data/dev/proof_bundle_diff_escalation_digest_latest.md",
        "json_path": "data/dev/proof_bundle_diff_escalation_digest_latest.json",
        "latest_escalation_level": level,
        "latest_diff_status": diff_status,
        "current_attention_or_urgent_streak": streak,
        "urgent_count": urgent,
        "attention_count": attention,
        "stale_acknowledgment_count": stale_ack,
        "metrics": {
            "urgent_count": urgent,
            "attention_count": attention,
            "stale_acknowledgment_count": stale_ack,
            "current_attention_or_urgent_streak": streak,
        },
        "verified_mrms": False,
    }


def test_digest_history_item_shape(storage):
    entry = build_digest_history_entry(_metadata(generated_at="2026-06-28T16:00:00Z"))
    assert entry["created_at"] == "2026-06-28T16:00:00Z"
    assert entry["digest_path"]
    assert entry["metadata_path"]
    assert entry["verified_mrms"] is False
    assert entry["local_digest_only"] is True
    assert entry["does_not_clear_alerts"] is True
    assert entry["does_not_enable_production"] is True


def test_bounded_digest_history_length(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    for index in range(MAX_DIGEST_HISTORY + 5):
        record_digest_export_history(
            storage,
            _metadata(generated_at=f"2026-06-28T16:{index:02d}:00Z"),
        )
    entries = load_digest_export_history(storage)
    assert len(entries) == MAX_DIGEST_HISTORY
    assert entries[0]["created_at"] == f"2026-06-28T16:{MAX_DIGEST_HISTORY + 4:02d}:00Z"


def test_digest_diff_no_baseline(storage):
    diff = compare_digest_metadata(None, _metadata(generated_at="2026-06-28T16:00:00Z"))
    assert diff["overall_digest_diff_status"] == DIFF_NO_BASELINE
    assert diff["verified_mrms"] is False


def test_digest_diff_unchanged(storage):
    baseline_entry = build_digest_history_entry(_metadata(generated_at="2026-06-28T16:00:00Z"))
    current = _metadata(generated_at="2026-06-28T16:01:00Z")
    diff = compare_digest_metadata(baseline_entry, current)
    assert diff["overall_digest_diff_status"] == DIFF_UNCHANGED


def test_digest_diff_worsened_classification(storage):
    baseline_entry = build_digest_history_entry(
        _metadata(generated_at="2026-06-28T16:00:00Z", level="watch", urgent=0)
    )
    current = _metadata(generated_at="2026-06-28T16:01:00Z", level=ESCALATION_URGENT, urgent=3)
    diff = compare_digest_metadata(baseline_entry, current)
    assert diff["overall_digest_diff_status"] == DIFF_WORSENED


def test_digest_diff_improved_classification(storage):
    baseline_entry = build_digest_history_entry(
        _metadata(generated_at="2026-06-28T16:00:00Z", level=ESCALATION_URGENT, urgent=3)
    )
    current = _metadata(generated_at="2026-06-28T16:01:00Z", level="none", urgent=0)
    diff = compare_digest_metadata(baseline_entry, current)
    assert diff["overall_digest_diff_status"] == DIFF_IMPROVED


def test_digest_diff_mixed_classification(storage):
    baseline_entry = build_digest_history_entry(
        _metadata(
            generated_at="2026-06-28T16:00:00Z",
            level="attention",
            urgent=1,
            diff_status=DIFF_WORSENED,
        )
    )
    current = _metadata(
        generated_at="2026-06-28T16:01:00Z",
        level="attention",
        urgent=2,
        diff_status=DIFF_IMPROVED,
    )
    diff = compare_digest_metadata(baseline_entry, current)
    assert diff["overall_digest_diff_status"] == DIFF_MIXED


def _fake_diff_report(*, status: str, bundle_id: str, checked_at: str) -> dict:
    return {
        "overall_diff_status": status,
        "checked_at": checked_at,
        "evidence_changes_count": 1,
        "current_bundle": {"bundle_id": bundle_id},
        "baseline_bundle": {"bundle_id": "base"},
        "verified_mrms": False,
        "operator_attention_needed": status in (DIFF_WORSENED, DIFF_MIXED),
    }


def test_regeneration_hint_urgent_missing_digest(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    for index, checked_at in enumerate(
        ["2026-06-28T16:12:00Z", "2026-06-28T16:13:00Z", "2026-06-28T16:14:00Z"]
    ):
        record_proof_bundle_diff_alert_history(
            storage,
            _fake_diff_report(status=DIFF_WORSENED, bundle_id=f"b{index}", checked_at=checked_at),
            skip_duplicate=False,
        )
    hint = build_digest_regeneration_hint(storage)
    assert hint["digest_regeneration_recommended"] is True
    assert hint["reason"] == "urgent_escalation_and_digest_missing"
    assert hint["suggested_command"] == "make scheduled-proof-bundle-digest"
    assert hint["verified_mrms"] is False


def test_regeneration_hint_digest_older_than_escalation(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    metadata = _metadata(generated_at="2026-06-28T16:00:00Z")
    record_digest_export_history(storage, metadata)
    digest_json = storage.absolute_path(
        storage.normalize_path("dev/proof_bundle_diff_escalation_digest_latest.json")
    )
    digest_json.parent.mkdir(parents=True, exist_ok=True)
    digest_json.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    history_path = storage.absolute_path(storage.normalize_path(ESCALATION_HISTORY_PATH))
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(
        json.dumps(
            [
                {
                    "created_at": "2026-06-28T16:30:00Z",
                    "escalation_level": "attention",
                    "reason": "test",
                    "latest_diff_status": DIFF_WORSENED,
                    "current_attention_streak": 2,
                    "acknowledgment_status": "none",
                    "stale_acknowledgment": False,
                    "verified_mrms": False,
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    hint = build_digest_regeneration_hint(storage)
    assert hint["digest_regeneration_recommended"] is True
    assert hint["reason"] == "digest_older_than_latest_escalation_snapshot"


def test_summary_includes_digest_history_diff_hint(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    export_proof_bundle_diff_escalation_digest(storage)
    summary = build_validation_summary(db_session, storage)
    assert summary["verified_mrms"] is False
    history = summary.get("proof_bundle_diff_escalation_digest_history")
    assert history is not None
    assert history.get("count", 0) >= 1
    diff = summary.get("proof_bundle_diff_escalation_digest_diff")
    assert diff is not None
    hint = summary.get("digest_regeneration_hint")
    assert hint is not None
    assert "digest_regeneration_recommended" in hint


def test_digest_history_endpoint_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/proof-bundle-diff-escalation-digest-history")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["count"] == 0


def test_digest_diff_endpoint_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/proof-bundle-diff-escalation-digest-diff")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["compact"]["available"] is False
    assert body["regeneration_hint"]["verified_mrms"] is False


def test_digest_export_records_history_and_diff(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    export_proof_bundle_diff_escalation_digest(storage)
    export_proof_bundle_diff_escalation_digest(storage)
    history = load_digest_export_history(storage)
    assert len(history) == 2
    diff_latest = storage.absolute_path(DIGEST_DIFF_LATEST_PATH)
    assert diff_latest.is_file()
    diff_body = json.loads(diff_latest.read_text(encoding="utf-8"))
    assert diff_body["overall_digest_diff_status"] == DIFF_UNCHANGED


def test_digest_history_does_not_clear_alerts(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record_digest_export_history(storage, _metadata(generated_at="2026-06-28T16:00:00Z"))
    record_digest_diff_metadata(
        storage,
        _metadata(generated_at="2026-06-28T16:01:00Z", level=ESCALATION_URGENT),
        baseline_history_entry=build_digest_history_entry(
            _metadata(generated_at="2026-06-28T16:00:00Z")
        ),
    )
    alert_before = load_validation_alert(storage)
    record_digest_export_history(storage, _metadata(generated_at="2026-06-28T16:02:00Z"))
    alert_after = load_validation_alert(storage)
    assert alert_before == alert_after or (alert_before is None and alert_after is None)


def test_digest_history_does_not_mutate_production_gates(
    client, db_session, storage, monkeypatch
):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T10:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase40.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=False,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    export_proof_bundle_diff_escalation_digest(storage)
    db_session.refresh(frame)
    assert frame.production_rendering is False

    response = client.get("/tiles/mrms_reflectivity/2026-06-28T10:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"


def test_runtime_digest_history_artifacts_gitignored():
    gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
    text = gitignore.read_text(encoding="utf-8")
    assert "proof_bundle_diff_escalation_digest_history.json" in text
    assert "proof_bundle_diff_escalation_digest_diff_latest.json" in text
    assert "proof_bundle_diff_escalation_digest_diff_history.json" in text
