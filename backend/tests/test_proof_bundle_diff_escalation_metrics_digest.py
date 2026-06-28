"""Tests for proof bundle diff escalation metrics and digest export (Phase 38)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
from backend.app.services.mrms_proof_bundle_diff import DIFF_UNCHANGED, DIFF_WORSENED
from backend.app.services.proof_bundle_diff_alert_history import record_proof_bundle_diff_alert_history
from backend.app.services.proof_bundle_diff_escalation import (
    ESCALATION_ATTENTION,
    ESCALATION_NONE,
    ESCALATION_URGENT,
    ESCALATION_WATCH,
    build_proof_bundle_diff_escalation,
)
from backend.app.services.proof_bundle_diff_escalation_digest import (
    DIGEST_JSON_PATH,
    DIGEST_MD_PATH,
    compact_proof_bundle_diff_escalation_digest,
    export_proof_bundle_diff_escalation_digest,
)
from backend.app.services.proof_bundle_diff_escalation_history import (
    record_proof_bundle_diff_escalation_history,
)
from backend.app.services.proof_bundle_diff_escalation_metrics import (
    build_proof_bundle_diff_escalation_metrics,
    compact_proof_bundle_diff_escalation_metrics,
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


def _seed_history_levels(
    storage: LocalStorage,
    levels: list[tuple[str, str, bool]],
) -> None:
    """Seed escalation history snapshots (level, created_at, stale_ack)."""
    for index, (level, created_at, stale) in enumerate(reversed(levels)):
        record_proof_bundle_diff_escalation_history(
            storage,
            {
                "escalation_level": level,
                "reason": f"reason-{level}-{index}",
                "latest_diff_status": DIFF_WORSENED if level != ESCALATION_NONE else DIFF_UNCHANGED,
                "current_attention_streak": 1 if level != ESCALATION_NONE else 0,
                "acknowledgment_status": "stale" if stale else "none",
                "stale_acknowledgment": stale,
                "suggested_next_action": "local review",
                "guidance_items": [],
            },
            source="test",
            run_id=f"run-{index}",
            skip_duplicate=False,
        )
        history_path = storage.absolute_path(
            storage.normalize_path("dev/proof_bundle_diff_escalation_history.json")
        )
        entries = json.loads(history_path.read_text(encoding="utf-8"))
        entries[0]["created_at"] = created_at
        history_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def test_escalation_metrics_shape(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history_levels(
        storage,
        [
            (ESCALATION_URGENT, "2026-06-28T16:10:00Z", False),
            (ESCALATION_ATTENTION, "2026-06-28T16:09:00Z", True),
            (ESCALATION_WATCH, "2026-06-28T16:08:00Z", False),
        ],
    )
    metrics = build_proof_bundle_diff_escalation_metrics(storage)
    assert metrics["total_snapshots"] == 3
    assert metrics["urgent_count"] == 1
    assert metrics["attention_count"] == 1
    assert metrics["watch_count"] == 1
    assert metrics["verified_mrms"] is False
    assert metrics["local_metrics_only"] is True
    assert metrics["does_not_clear_alerts"] is True


def test_empty_history_metrics(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    metrics = build_proof_bundle_diff_escalation_metrics(storage)
    assert metrics["total_snapshots"] == 0
    assert metrics["latest_level"] == ESCALATION_NONE
    assert metrics["current_urgent_streak"] == 0
    assert metrics["verified_mrms"] is False


def test_longest_urgent_streak(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history_levels(
        storage,
        [
            (ESCALATION_NONE, "2026-06-28T16:13:00Z", False),
            (ESCALATION_URGENT, "2026-06-28T16:12:00Z", False),
            (ESCALATION_URGENT, "2026-06-28T16:11:00Z", False),
            (ESCALATION_WATCH, "2026-06-28T16:10:00Z", False),
            (ESCALATION_URGENT, "2026-06-28T16:09:00Z", False),
        ],
    )
    metrics = build_proof_bundle_diff_escalation_metrics(storage)
    assert metrics["longest_urgent_streak"] == 2
    assert metrics["current_urgent_streak"] == 0


def test_current_attention_or_urgent_streak(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history_levels(
        storage,
        [
            (ESCALATION_ATTENTION, "2026-06-28T16:12:00Z", False),
            (ESCALATION_URGENT, "2026-06-28T16:11:00Z", False),
            (ESCALATION_NONE, "2026-06-28T16:10:00Z", False),
        ],
    )
    metrics = build_proof_bundle_diff_escalation_metrics(storage)
    assert metrics["current_attention_or_urgent_streak"] == 2
    assert metrics["longest_attention_or_urgent_streak"] == 2


def test_stale_acknowledgment_count(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history_levels(
        storage,
        [
            (ESCALATION_WATCH, "2026-06-28T16:10:00Z", True),
            (ESCALATION_ATTENTION, "2026-06-28T16:09:00Z", True),
            (ESCALATION_NONE, "2026-06-28T16:08:00Z", False),
        ],
    )
    metrics = build_proof_bundle_diff_escalation_metrics(storage)
    assert metrics["stale_acknowledgment_count"] == 2


def test_digest_markdown_contains_warnings(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history_levels(storage, [(ESCALATION_WATCH, "2026-06-28T16:10:00Z", False)])
    metadata = export_proof_bundle_diff_escalation_digest(storage)
    md_path = storage.absolute_path(DIGEST_MD_PATH)
    markdown = md_path.read_text(encoding="utf-8")
    assert "does **NOT** verify MRMS" in markdown
    assert "does not clear validation alerts" in markdown.lower() or "does not clear alerts" in markdown.lower()
    assert "no email" in markdown.lower()
    assert metadata["verified_mrms"] is False
    assert metadata["local_digest_only"] is True


def test_digest_metadata_shape(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    metadata = export_proof_bundle_diff_escalation_digest(storage)
    assert metadata["markdown_path"]
    assert metadata["json_path"]
    assert metadata["does_not_clear_alerts"] is True
    assert metadata["no_external_notifications"] is True
    json_path = storage.absolute_path(DIGEST_JSON_PATH)
    assert json_path.is_file()


def test_summary_includes_metrics_and_digest(db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_history_levels(storage, [(ESCALATION_WATCH, "2026-06-28T16:10:00Z", False)])
    export_proof_bundle_diff_escalation_digest(storage)
    summary = build_validation_summary(db_session, storage)
    metrics = summary.get("proof_bundle_diff_escalation_metrics")
    digest = summary.get("proof_bundle_diff_escalation_digest")
    assert metrics is not None
    assert metrics.get("total_snapshots") >= 1
    assert metrics.get("verified_mrms") is False
    assert digest is not None
    assert digest.get("available") is True
    assert digest.get("markdown_path")


def test_metrics_endpoint_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/proof-bundle-diff-escalation-metrics")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["metrics"]["total_snapshots"] == 0


def test_digest_endpoint_empty(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    md_path = storage.absolute_path(DIGEST_MD_PATH)
    json_path = storage.absolute_path(DIGEST_JSON_PATH)
    for path in (md_path, json_path):
        if path.is_file():
            path.unlink()
    response = client.get("/api/validation/proof-bundle-diff-escalation-digest")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["compact"]["available"] is False


def test_digest_does_not_clear_alerts(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_worsening_streak(storage)
    export_proof_bundle_diff_escalation_digest(storage)
    alert = build_validation_alert(
        storage,
        scheduled={
            "success": True,
            "exit_code": 0,
            "mrms_proof_bundle_diff": {"overall_diff_status": DIFF_WORSENED},
        },
    )
    assert alert["operator_attention_needed"] is True


def test_digest_does_not_mutate_gates(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    export_proof_bundle_diff_escalation_digest(storage)

    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-28T10:00:00Z",
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase38.grib2.gz"),
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


def test_gitignore_covers_digest_artifacts():
    gitignore = Path("/Users/irds/Projects/radararchive/.gitignore").read_text(encoding="utf-8")
    assert "proof_bundle_diff_escalation_digest_latest.md" in gitignore
    assert "proof_bundle_diff_escalation_digest_latest.json" in gitignore


def test_compact_metrics_from_urgent_history(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    _seed_worsening_streak(storage)
    escalation = build_proof_bundle_diff_escalation(storage)
    record_proof_bundle_diff_escalation_history(
        storage, escalation, source="urgent-test", skip_duplicate=False
    )
    compact = compact_proof_bundle_diff_escalation_metrics(storage)
    assert compact["available"] is True
    assert compact["urgent_count"] >= 1 or compact["latest_level"] == ESCALATION_URGENT


def test_compact_digest_unavailable(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    compact = compact_proof_bundle_diff_escalation_digest(storage)
    assert compact["available"] is False
    assert compact["verified_mrms"] is False
