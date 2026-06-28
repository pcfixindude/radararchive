"""Tests for local MRMS proof review session comparison (Phase 42)."""

from __future__ import annotations

from pathlib import Path

import pytest

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
from backend.app.services.mrms_review_session_compare import (
    MAX_COMPARISON_HISTORY,
    compare_review_sessions,
    record_review_session_comparison,
)
from backend.app.services.operator_guidance import build_open_attention_guidance
from backend.app.services.proof_bundle_diff_escalation import ESCALATION_URGENT, ESCALATION_WATCH
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _session(
    *,
    session_id: str,
    created_at: str,
    operator: str = "OP",
    escalation_level: str = "none",
    open_attention_count: int = 0,
    checklist_reviewed: int = 0,
    checklist_not_reviewed: int = 5,
    diff_status: str = "unchanged",
    proof_status: str = "ready_for_operator_review",
    ack_id: str | None = None,
) -> dict:
    reviewed = [f"item-{index}" for index in range(checklist_reviewed)]
    not_reviewed = [f"nr-{index}" for index in range(checklist_not_reviewed)]
    return {
        "session_id": session_id,
        "created_at": created_at,
        "operator_initials": operator,
        "latest_escalation_level": escalation_level,
        "open_attention_count": open_attention_count,
        "checklist_items_reviewed": reviewed,
        "checklist_items_not_reviewed": not_reviewed,
        "latest_proof_bundle_diff_status": diff_status,
        "latest_proof_report_status": proof_status,
        "latest_acknowledgment_id": ack_id,
        "latest_acknowledgment_at": created_at if ack_id else None,
        "latest_digest_path": f"data/dev/digest-{session_id}.md",
        "latest_operator_handoff_path": f"data/dev/handoff-{session_id}.md",
    }


def test_comparison_shape_no_baseline():
    latest = _session(session_id="latest", created_at="2026-06-28T12:00:00Z")
    comparison = compare_review_sessions(None, latest)
    assert comparison["overall_review_diff_status"] == DIFF_NO_BASELINE
    assert comparison["latest_session_id"] == "latest"
    assert comparison["baseline_session_id"] is None
    assert comparison["verified_mrms"] is False
    assert comparison["local_comparison_only"] is True
    assert comparison["does_not_clear_alerts"] is True
    assert comparison["does_not_enable_production"] is True


def test_comparison_unchanged():
    baseline = _session(
        session_id="base",
        created_at="2026-06-28T11:00:00Z",
        open_attention_count=2,
        checklist_reviewed=1,
        checklist_not_reviewed=4,
    )
    latest = _session(
        session_id="latest",
        created_at="2026-06-28T12:00:00Z",
        open_attention_count=2,
        checklist_reviewed=1,
        checklist_not_reviewed=4,
        diff_status="unchanged",
    )
    latest["latest_digest_path"] = baseline["latest_digest_path"]
    latest["latest_operator_handoff_path"] = baseline["latest_operator_handoff_path"]
    comparison = compare_review_sessions(baseline, latest)
    assert comparison["overall_review_diff_status"] == DIFF_UNCHANGED
    assert "open_attention_count" in comparison["unchanged_items"]


def test_comparison_improved():
    baseline = _session(
        session_id="base",
        created_at="2026-06-28T11:00:00Z",
        escalation_level=ESCALATION_URGENT,
        open_attention_count=5,
        checklist_reviewed=0,
        checklist_not_reviewed=5,
        diff_status=DIFF_WORSENED,
        proof_status="failed",
    )
    latest = _session(
        session_id="latest",
        created_at="2026-06-28T12:00:00Z",
        escalation_level=ESCALATION_WATCH,
        open_attention_count=1,
        checklist_reviewed=3,
        checklist_not_reviewed=2,
        diff_status=DIFF_IMPROVED,
        proof_status="ready_for_operator_review",
        ack_id="ack-new",
    )
    comparison = compare_review_sessions(baseline, latest)
    assert comparison["overall_review_diff_status"] == DIFF_IMPROVED
    assert "open_attention_count" in comparison["improvements"]
    assert "escalation_level" in comparison["improvements"]


def test_comparison_worsened():
    baseline = _session(
        session_id="base",
        created_at="2026-06-28T11:00:00Z",
        escalation_level=ESCALATION_WATCH,
        open_attention_count=1,
        checklist_reviewed=3,
        checklist_not_reviewed=2,
        diff_status=DIFF_IMPROVED,
        proof_status="ready_for_operator_review",
        ack_id="ack-old",
    )
    latest = _session(
        session_id="latest",
        created_at="2026-06-28T12:00:00Z",
        escalation_level=ESCALATION_URGENT,
        open_attention_count=4,
        checklist_reviewed=0,
        checklist_not_reviewed=5,
        diff_status=DIFF_WORSENED,
        proof_status="failed",
        ack_id=None,
    )
    comparison = compare_review_sessions(baseline, latest)
    assert comparison["overall_review_diff_status"] == DIFF_WORSENED
    assert "open_attention_count" in comparison["regressions"]


def test_comparison_mixed():
    baseline = _session(
        session_id="base",
        created_at="2026-06-28T11:00:00Z",
        escalation_level=ESCALATION_WATCH,
        open_attention_count=4,
        checklist_reviewed=0,
        diff_status=DIFF_IMPROVED,
        proof_status="ready_for_operator_review",
    )
    latest = _session(
        session_id="latest",
        created_at="2026-06-28T12:00:00Z",
        escalation_level=ESCALATION_URGENT,
        open_attention_count=1,
        checklist_reviewed=0,
        diff_status=DIFF_WORSENED,
        proof_status="ready_for_operator_review",
    )
    comparison = compare_review_sessions(baseline, latest)
    assert comparison["overall_review_diff_status"] == DIFF_MIXED
    assert "open_attention_count" in comparison["improvements"]
    assert "escalation_level" in comparison["regressions"]


def test_open_attention_guidance_mapping():
    items = [
        "Validation alert: operator attention needed",
        "Proof bundle diff attention: worsened",
        "Escalation level: urgent — streak",
        "Digest regeneration recommended: stale digest",
        "Diff alert acknowledgment is stale relative to latest alerts",
    ]
    guidance = build_open_attention_guidance(items)
    assert len(guidance) >= 4
    assert all(item["verified_mrms"] is False for item in guidance)
    assert all(item["path"].startswith("docs/") for item in guidance)
    assert all(item.get("suggested_action") for item in guidance)
    assert all(item.get("attention_item") for item in guidance)


def test_comparison_history_bounded(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    for index in range(MAX_COMPARISON_HISTORY + 3):
        record_review_session_comparison(
            storage,
            baseline_session=_session(
                session_id=f"b{index}",
                created_at=f"2026-06-28T10:{index:02d}:00Z",
            ),
            latest_session=_session(
                session_id=f"l{index}",
                created_at=f"2026-06-28T11:{index:02d}:00Z",
            ),
        )
    history_path = storage.absolute_path("dev/mrms_review_session_comparison_history.json")
    history = __import__("json").loads(history_path.read_text(encoding="utf-8"))
    assert len(history) == MAX_COMPARISON_HISTORY


def test_summary_includes_comparison_and_guidance(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    create_review_session_record(
        storage,
        operator_initials="BASE",
        session_notes="baseline session",
        accepted_limitations=True,
    )
    create_review_session_record(
        storage,
        operator_initials="LATEST",
        session_notes="latest session",
        accepted_limitations=True,
    )
    summary = build_validation_summary(db_session, storage)
    session = summary.get("mrms_review_session")
    assert session is not None
    assert session["comparison"] is not None
    assert session["comparison"]["available"] is True
    assert session["comparison"]["verified_mrms"] is False
    assert isinstance(session.get("open_attention_guidance"), list)


def test_comparison_endpoints_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/review-sessions/comparison")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["local_comparison_only"] is True
    assert body["compact"]["available"] is False

    history_response = client.get("/api/validation/review-sessions/comparison/history")
    assert history_response.status_code == 200
    history_body = history_response.json()
    assert history_body["count"] == 0


def test_comparison_does_not_clear_alerts(storage, monkeypatch):
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
    alert_before = load_validation_alert(storage)
    record_review_session_comparison(
        storage,
        baseline_session=_session(session_id="b", created_at="2026-06-28T11:00:00Z"),
        latest_session=_session(session_id="l", created_at="2026-06-28T12:00:00Z"),
    )
    alert_after = load_validation_alert(storage)
    if alert_before is not None:
        assert alert_after is not None
        assert alert_after.get("operator_attention_needed") == alert_before.get(
            "operator_attention_needed"
        )


def test_comparison_does_not_mutate_production_gates(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T11:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase42.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=False,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    record_review_session_comparison(
        storage,
        baseline_session=_session(session_id="b", created_at="2026-06-28T11:00:00Z"),
        latest_session=_session(session_id="l", created_at="2026-06-28T12:00:00Z"),
    )
    db_session.refresh(frame)
    assert frame.production_rendering is False

    response = client.get("/tiles/mrms_reflectivity/2026-06-28T11:00:00Z/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"


def test_review_session_includes_open_attention_guidance(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    record = create_review_session_record(
        storage,
        operator_initials="OP",
        session_notes="guidance test",
        accepted_limitations=True,
    )
    assert isinstance(record.get("open_attention_guidance"), list)


def test_runtime_comparison_artifacts_gitignored():
    gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
    text = gitignore.read_text(encoding="utf-8")
    assert "mrms_review_session_comparison_latest.json" in text
    assert "mrms_review_session_comparison_history.json" in text


def test_comparison_always_verified_mrms_false(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    comparison = record_review_session_comparison(
        storage,
        baseline_session=_session(session_id="b", created_at="2026-06-28T11:00:00Z"),
        latest_session=_session(session_id="l", created_at="2026-06-28T12:00:00Z"),
    )
    assert comparison["verified_mrms"] is False
    assert comparison["does_not_clear_alerts"] is True
