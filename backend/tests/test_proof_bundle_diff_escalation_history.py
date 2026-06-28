"""Tests for proof bundle diff escalation history and stdout notices (Phase 37)."""

from __future__ import annotations

import io
import json
from pathlib import Path

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_proof_bundle_diff import DIFF_UNCHANGED, DIFF_WORSENED
from backend.app.services.proof_bundle_diff_alert_history import record_proof_bundle_diff_alert_history
from backend.app.services.proof_bundle_diff_escalation import (
    ESCALATION_NONE,
    ESCALATION_URGENT,
    build_proof_bundle_diff_escalation,
)
from backend.app.services.proof_bundle_diff_escalation_history import (
    ESCALATION_HISTORY_PATH,
    MAX_ESCALATION_HISTORY,
    compact_proof_bundle_diff_escalation_history_summary,
    count_proof_bundle_diff_escalation_history,
    load_latest_proof_bundle_diff_escalation_history,
    record_escalation_from_storage,
    record_proof_bundle_diff_escalation_history,
)
from backend.app.services.proof_bundle_diff_escalation_stdout import (
    STDOUT_LATEST_PATH,
    URGENT_NOTICE_HEADER,
    format_urgent_stdout_notice_lines,
    maybe_trigger_urgent_stdout_notice,
    print_urgent_stdout_notice,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import build_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _fake_diff_report(*, status: str, bundle_id: str, checked_at: str) -> dict:
    return {
        "overall_diff_status": status,
        "checked_at": checked_at,
        "evidence_changes_count": 1,
        "current_bundle": {"bundle_id": bundle_id},
        "baseline_bundle": {"bundle_id": "base"},
        "verified_mrms": False,
    }


def _seed_worsening_streak(storage: LocalStorage) -> None:
    entries = [
        (DIFF_WORSENED, "2026-06-28T16:14:00Z"),
        (DIFF_WORSENED, "2026-06-28T16:13:00Z"),
        (DIFF_WORSENED, "2026-06-28T16:12:00Z"),
        (DIFF_UNCHANGED, "2026-06-28T16:11:00Z"),
    ]
    for index, (status, checked_at) in enumerate(reversed(entries)):
        record_proof_bundle_diff_alert_history(
            storage,
            _fake_diff_report(status=status, bundle_id=f"b{index}", checked_at=checked_at),
            skip_duplicate=False,
        )


def test_escalation_history_entry_shape(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    escalation = build_proof_bundle_diff_escalation(storage)
    entry = record_proof_bundle_diff_escalation_history(
        storage,
        escalation,
        source="test",
        run_id="run-1",
    )
    assert entry is not None
    assert entry["verified_mrms"] is False
    assert entry["local_history_only"] is True
    assert entry["does_not_clear_alerts"] is True
    assert entry["does_not_enable_production"] is True
    assert "guidance_item_count" in entry
    assert entry["created_at"]


def test_escalation_history_bounded_length(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    base = build_proof_bundle_diff_escalation(storage)
    for index in range(MAX_ESCALATION_HISTORY + 5):
        escalation = {**base, "reason": f"reason-{index}"}
        record_proof_bundle_diff_escalation_history(
            storage,
            escalation,
            source="test",
            run_id=f"run-{index}",
            skip_duplicate=False,
        )
    assert count_proof_bundle_diff_escalation_history(storage) == MAX_ESCALATION_HISTORY


def test_latest_escalation_history_entry(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    first = build_proof_bundle_diff_escalation(storage)
    second = {**first, "reason": "second snapshot reason"}
    record_proof_bundle_diff_escalation_history(
        storage, first, source="first", run_id="run-a", skip_duplicate=False
    )
    record_proof_bundle_diff_escalation_history(
        storage, second, source="second", run_id="run-b", skip_duplicate=False
    )
    latest = load_latest_proof_bundle_diff_escalation_history(storage)
    assert latest is not None
    assert latest.get("source") == "second"


def test_duplicate_escalation_history_skipped(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record_escalation_from_storage(storage, source="test", run_id="same-run")
    record_escalation_from_storage(storage, source="test", run_id="same-run")
    assert count_proof_bundle_diff_escalation_history(storage) == 1


def test_urgent_snapshot_recording(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_worsening_streak(storage)
    entry = record_escalation_from_storage(storage, source="urgent-test")
    assert entry is not None
    assert entry["escalation_level"] == ESCALATION_URGENT


def test_empty_escalation_history_endpoint(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    history_path = storage.absolute_path(ESCALATION_HISTORY_PATH)
    if history_path.is_file():
        history_path.unlink()
    response = client.get("/api/validation/proof-bundle-diff-escalation-history")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["count"] == 0
    assert body["entries"] == []


def test_stdout_notice_only_for_urgent(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    escalation = build_proof_bundle_diff_escalation(storage)
    assert escalation["escalation_level"] == ESCALATION_NONE
    assert (
        maybe_trigger_urgent_stdout_notice(
            storage,
            escalation,
            notify_stdout=True,
            production_rendering_enabled=False,
            source="test",
        )
        is None
    )


def test_stdout_notice_includes_non_verification_warnings(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_worsening_streak(storage)
    escalation = build_proof_bundle_diff_escalation(storage)
    assert escalation["escalation_level"] == ESCALATION_URGENT
    lines = format_urgent_stdout_notice_lines(
        escalation,
        production_rendering_enabled=False,
    )
    joined = "\n".join(lines)
    assert URGENT_NOTICE_HEADER in joined
    assert "verified_mrms: false" in joined
    assert "does NOT clear alerts" in joined
    assert "no email" in joined.lower()


def test_stdout_notice_print_and_persist(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_worsening_streak(storage)
    escalation = build_proof_bundle_diff_escalation(storage)
    buffer = io.StringIO()
    record = print_urgent_stdout_notice(
        escalation,
        production_rendering_enabled=False,
        source="test",
        storage=storage,
        stream=buffer,
    )
    assert record["verified_mrms"] is False
    assert record["local_stdout_only"] is True
    assert URGENT_NOTICE_HEADER in buffer.getvalue()
    latest_path = storage.absolute_path(STDOUT_LATEST_PATH)
    assert latest_path.is_file()
    saved = json.loads(latest_path.read_text(encoding="utf-8"))
    assert saved["triggered"] is True


def test_summary_includes_escalation_history(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record_escalation_from_storage(storage, source="summary-test")
    summary = build_validation_summary(db_session, storage)
    history = summary.get("proof_bundle_diff_escalation_history")
    assert history is not None
    assert history.get("count") >= 1
    assert history.get("verified_mrms") is False
    assert history.get("does_not_clear_alerts") is True


def test_alert_includes_escalation_history_fields(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record_escalation_from_storage(storage, source="alert-test")
    alert = build_validation_alert(storage)
    assert alert.get("proof_bundle_diff_escalation_history_count", 0) >= 1
    assert alert.get("latest_proof_bundle_diff_escalation_snapshot_at")
    assert alert.get("verified_mrms") is False


def test_stdout_hook_does_not_clear_alerts(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_worsening_streak(storage)
    escalation = build_proof_bundle_diff_escalation(storage)
    maybe_trigger_urgent_stdout_notice(
        storage,
        escalation,
        notify_stdout=True,
        production_rendering_enabled=False,
        source="test",
    )
    alert = build_validation_alert(
        storage,
        scheduled={
            "success": True,
            "exit_code": 0,
            "mrms_proof_bundle_diff": {"overall_diff_status": DIFF_WORSENED},
        },
    )
    assert alert["operator_attention_needed"] is True


def test_stdout_hook_does_not_mutate_gates(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    _seed_worsening_streak(storage)
    escalation = build_proof_bundle_diff_escalation(storage)
    maybe_trigger_urgent_stdout_notice(
        storage,
        escalation,
        notify_stdout=True,
        production_rendering_enabled=False,
        source="test",
    )

    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T10:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase37.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=False,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()
    db_session.refresh(frame)
    assert frame.production_rendering is False

    response = client.get("/tiles/mrms_reflectivity/2026-06-28T10:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"


def test_gitignore_covers_escalation_history_artifacts():
    gitignore = Path("/Users/irds/Projects/radararchive/.gitignore").read_text(encoding="utf-8")
    assert "proof_bundle_diff_escalation_history.json" in gitignore
    assert "proof_bundle_diff_escalation_stdout_latest.json" in gitignore


def test_compact_history_summary_stdout_flags(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_worsening_streak(storage)
    escalation = build_proof_bundle_diff_escalation(storage)
    print_urgent_stdout_notice(
        escalation,
        production_rendering_enabled=False,
        source="test",
        storage=storage,
        stream=io.StringIO(),
    )
    summary = compact_proof_bundle_diff_escalation_history_summary(storage)
    assert summary["urgent_stdout_notice_triggered"] is True
    assert summary["urgent_stdout_notice_at"] is not None
