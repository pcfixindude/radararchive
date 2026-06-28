"""Tests for proof bundle diff alert history timeline (Phase 34)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_MIXED,
    DIFF_UNCHANGED,
    DIFF_WORSENED,
    build_proof_bundle_diff_report,
)
from backend.app.services.proof_bundle_diff_alert_history import (
    ALERT_HISTORY_PATH,
    MAX_ALERT_HISTORY,
    build_alert_history_entry,
    build_proof_bundle_diff_alert_history_payload,
    compact_latest_proof_bundle_diff_alert,
    load_latest_proof_bundle_diff_alert_history,
    load_proof_bundle_diff_alert_history,
    record_proof_bundle_diff_alert_history,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_dashboard import build_validation_summary


def _fake_diff_report(
    *,
    status: str,
    bundle_id: str = "cur",
    baseline_id: str = "base",
    changes: int = 1,
) -> dict:
    return {
        "overall_diff_status": status,
        "checked_at": "2026-06-28T16:00:00Z",
        "evidence_changes_count": changes,
        "current_bundle": {"bundle_id": bundle_id},
        "baseline_bundle": {"bundle_id": baseline_id},
        "verified_mrms": False,
    }


def test_alert_history_entry_shape(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    entry = build_alert_history_entry(_fake_diff_report(status=DIFF_WORSENED))
    assert entry["diff_status"] == DIFF_WORSENED
    assert entry["operator_attention_needed"] is True
    assert entry["guidance_cause"] == "proof_bundle_diff_worsened"
    assert entry["bundle_id"] == "cur"
    assert entry["baseline_bundle_id"] == "base"
    assert entry["verified_mrms"] is False
    assert entry["local_history_only"] is True
    assert entry["suggested_next_action"]


def test_record_worsened_and_mixed(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record_proof_bundle_diff_alert_history(storage, _fake_diff_report(status=DIFF_WORSENED))
    record_proof_bundle_diff_alert_history(
        storage, _fake_diff_report(status=DIFF_MIXED, bundle_id="cur2", changes=2)
    )
    entries = load_proof_bundle_diff_alert_history(storage)
    assert len(entries) == 2
    assert entries[0]["diff_status"] == DIFF_MIXED
    assert entries[1]["diff_status"] == DIFF_WORSENED
    assert entries[0]["guidance_cause"] == "proof_bundle_diff_mixed"


def test_bounded_history_length(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    for index in range(MAX_ALERT_HISTORY + 5):
        record_proof_bundle_diff_alert_history(
            storage,
            _fake_diff_report(status=DIFF_UNCHANGED, bundle_id=f"b{index}", changes=index),
        )
    entries = load_proof_bundle_diff_alert_history(storage)
    assert len(entries) == MAX_ALERT_HISTORY


def test_latest_entry_retrieval(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record_proof_bundle_diff_alert_history(storage, _fake_diff_report(status=DIFF_WORSENED))
    latest = load_latest_proof_bundle_diff_alert_history(storage)
    assert latest is not None
    assert latest["diff_status"] == DIFF_WORSENED


def test_duplicate_entry_skipped(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    report = _fake_diff_report(status=DIFF_WORSENED)
    first = record_proof_bundle_diff_alert_history(storage, report)
    second = record_proof_bundle_diff_alert_history(storage, report)
    assert first is not None
    assert second is None
    assert len(load_proof_bundle_diff_alert_history(storage)) == 1


def test_diff_report_hook_records_history(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    bundle_dir = storage.absolute_path("dev/proof_bundles/history_hook_base")
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "manifest.json").write_text(
        json.dumps(
            {
                "bundle_id": "base",
                "bundle_folder": "data/dev/proof_bundles/history_hook_base",
                "files_included": [],
                "files_missing": [],
            }
        ),
        encoding="utf-8",
    )
    current_dir = storage.absolute_path("dev/proof_bundles/history_hook_cur")
    current_dir.mkdir(parents=True, exist_ok=True)
    (current_dir / "manifest.json").write_text(
        json.dumps(
            {
                "bundle_id": "cur",
                "bundle_folder": "data/dev/proof_bundles/history_hook_cur",
                "files_included": ["evidence/mrms_proof_latest.json"],
                "files_missing": [],
            }
        ),
        encoding="utf-8",
    )
    evidence_dir = current_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "mrms_proof_latest.json").write_text(
        json.dumps({"overall_status": "failed", "criteria_counts": {"failed": 2}}),
        encoding="utf-8",
    )

    build_proof_bundle_diff_report(
        storage,
        current_bundle_folder="data/dev/proof_bundles/history_hook_cur",
        baseline_bundle_folder="data/dev/proof_bundles/history_hook_base",
    )
    entries = load_proof_bundle_diff_alert_history(storage)
    assert len(entries) >= 1
    assert entries[0]["verified_mrms"] is False


def test_summary_includes_diff_alert_timeline(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record_proof_bundle_diff_alert_history(storage, _fake_diff_report(status=DIFF_WORSENED))
    summary = build_validation_summary(db_session, storage)
    assert summary["verified_mrms"] is False
    alert_compact = summary.get("proof_bundle_diff_alert")
    assert alert_compact is not None
    assert alert_compact["available"] is True
    assert alert_compact["diff_status"] == DIFF_WORSENED
    history = summary.get("proof_bundle_diff_alert_history") or []
    assert len(history) >= 1
    alert = summary.get("validation_alert")
    assert alert is not None
    assert alert.get("proof_bundle_diff_alert_history_count", 0) >= 1


def test_endpoint_returns_empty_when_missing(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    history_path = storage.absolute_path(ALERT_HISTORY_PATH)
    if history_path.is_file():
        history_path.unlink()
    response = client.get("/api/validation/proof-bundle-diff-alert-history")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["count"] == 0
    assert body["entries"] == []


def test_history_does_not_mutate_gates(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    record_proof_bundle_diff_alert_history(storage, _fake_diff_report(status=DIFF_WORSENED))

    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T09:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase34.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=False,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    db_session.refresh(frame)
    assert frame.production_rendering is False

    response = client.get("/tiles/mrms_reflectivity/2026-06-28T09:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"


def test_payload_builder(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record_proof_bundle_diff_alert_history(storage, _fake_diff_report(status=DIFF_WORSENED))
    payload = build_proof_bundle_diff_alert_history_payload(storage, limit=5)
    assert payload["count"] == 1
    assert payload["latest"]["diff_status"] == DIFF_WORSENED
    assert payload["verified_mrms"] is False


def test_compact_latest_when_empty(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    compact = compact_latest_proof_bundle_diff_alert(storage)
    assert compact["available"] is False
    assert compact["verified_mrms"] is False


def test_gitignore_covers_diff_alert_history():
    gitignore = Path("/Users/irds/Projects/radararchive/.gitignore").read_text(encoding="utf-8")
    assert "proof_bundle_diff_alert_history.json" in gitignore
