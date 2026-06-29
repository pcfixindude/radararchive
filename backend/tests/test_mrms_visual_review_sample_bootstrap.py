"""Tests for visual review sample set bootstrap (Phase 91)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight_attempt import ATTEMPT_BLOCKED_BY_READINESS
from backend.app.services.mrms_visual_review import save_visual_review_report
from backend.app.services.mrms_visual_review_sample_bootstrap import (
    BOOTSTRAP_JSON,
    BOOTSTRAP_READY_FOR_PREFLIGHT,
    BOOTSTRAP_STILL_BLOCKED,
    SUGGESTED_COMMAND,
    bootstrap_visual_sample_set,
    compact_visual_sample_bootstrap,
    ensure_sample_set,
    load_visual_sample_bootstrap_report,
    seed_bootstrap_annotations,
)
from backend.app.services.mrms_visual_review_sample_readiness import (
    READINESS_CANDIDATE_READY,
    STATUS_ACCEPTABLE,
    build_sample_key,
    compact_visual_review_sample_readiness,
    upsert_sample_annotation,
)
from backend.app.services.mrms_visual_review_sample_set import build_visual_review_sample_set
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary
from backend.tests.test_mrms_render_candidate_preflight import _seed_candidate_ready_chain
from backend.tests.test_mrms_render_candidate_preflight_attempt import _ready_review_chain_evidence


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def _visual_report(*, created_at: str = "2026-06-28T20:00:00Z", artifacts=None):
    default_artifacts = [
        {
            "timestamp": "2026-06-28T20:00:00Z",
            "layer": "reflectivity",
            "tile_mode": "placeholder",
            "render_status": "placeholder",
            "raw_kind": "placeholder",
            "artifact_paths_found": ["data/dev/sample.png"],
            "missing_artifacts": [],
        }
    ]
    return {
        "created_at": created_at,
        "layers_inspected": ["reflectivity"],
        "timestamps_inspected": [item["timestamp"] for item in (artifacts or default_artifacts)],
        "frame_count": len(artifacts or default_artifacts),
        "artifact_count": len(artifacts or default_artifacts),
        "missing_artifact_count": 0,
        "tile_modes_found": ["placeholder"],
        "artifacts": artifacts or default_artifacts,
        "json_path": "data/dev/mrms_visual_review_latest.json",
        "markdown_path": "data/dev/mrms_visual_review_latest.md",
        "verified_mrms": False,
        "local_visual_review_only": True,
    }


def _seed_visual_review(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(storage, _visual_report())


def test_ensure_sample_set_creates_when_missing(storage, monkeypatch):
    _seed_visual_review(storage, monkeypatch)
    result = ensure_sample_set(storage, limit=1)
    assert result["created"] is True
    assert result["entry_count"] == 1


def test_seed_bootstrap_annotations(storage, monkeypatch):
    _seed_visual_review(storage, monkeypatch)
    build_visual_review_sample_set(storage, limit=1)
    result = seed_bootstrap_annotations(storage)
    assert result["annotated"] == 1
    visual = compact_visual_review_sample_readiness(storage)
    assert visual["readiness_level"] == READINESS_CANDIDATE_READY


def test_bootstrap_reaches_candidate_ready(storage, monkeypatch):
    _seed_visual_review(storage, monkeypatch)
    report = bootstrap_visual_sample_set(storage)
    assert report["visual_readiness_level"] == READINESS_CANDIDATE_READY
    assert not report["visual_blockers"]


def test_bootstrap_blocked_without_visual_review(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = bootstrap_visual_sample_set(storage)
    assert report["bootstrap_status"] == BOOTSTRAP_STILL_BLOCKED
    assert report["visual_blockers"]
    assert report["preflight_not_run"] is True


def test_bootstrap_does_not_force_preflight_when_visual_blocked(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = bootstrap_visual_sample_set(storage)
    assert report["preflight_not_run"] is True
    assert report.get("preflight_attempt_status") in {ATTEMPT_BLOCKED_BY_READINESS, None}


def test_bootstrap_persists_report(storage, monkeypatch):
    _seed_visual_review(storage, monkeypatch)
    bootstrap_visual_sample_set(storage)
    assert storage.absolute_path(BOOTSTRAP_JSON).is_file()
    loaded = load_visual_sample_bootstrap_report(storage)
    assert loaded is not None
    assert loaded["visual_readiness_level"] == READINESS_CANDIDATE_READY


def test_bootstrap_skips_existing_annotations(storage, monkeypatch):
    _seed_visual_review(storage, monkeypatch)
    sample_set = build_visual_review_sample_set(storage, limit=1)
    entry = sample_set["entries"][0]
    upsert_sample_annotation(
        storage,
        sample_key=build_sample_key(timestamp=entry["timestamp"], layer=entry["layer"]),
        status=STATUS_ACCEPTABLE,
        operator_notes="Already reviewed.",
        reviewer_label="op1",
    )
    report = bootstrap_visual_sample_set(storage)
    assert report["annotations_seeded"] == 0


def test_bootstrap_ready_for_preflight_when_chain_ready(storage, monkeypatch, db_session):
    _seed_candidate_ready_chain(storage, monkeypatch)
    evidence = _ready_review_chain_evidence(storage, monkeypatch)
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_review_readiness.gather_review_chain_evidence",
        lambda _storage: evidence,
    )
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_preflight_attempt.gather_review_chain_evidence",
        lambda _storage: evidence,
    )
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_preflight.gather_preflight_evidence",
        lambda _storage: evidence,
    )
    report = bootstrap_visual_sample_set(storage)
    assert report["visual_readiness_level"] == READINESS_CANDIDATE_READY
    assert report["bootstrap_status"] in {
        BOOTSTRAP_READY_FOR_PREFLIGHT,
        "preflight_candidate_ready",
        "preflight_attempted",
    }


def test_summary_includes_sample_bootstrap(db_session, storage, monkeypatch):
    _seed_visual_review(storage, monkeypatch)
    bootstrap_visual_sample_set(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_visual_review_sample_bootstrap")
    assert compact is not None
    assert compact["candidate_ready_is_not_production_authorization"] is True


def test_sample_bootstrap_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-visual-review/sample-set/bootstrap")
    assert response.status_code == 200
    assert response.json()["verified_mrms"] is False


def test_sample_bootstrap_post_refresh(client, storage, monkeypatch):
    _seed_visual_review(storage, monkeypatch)
    response = client.post("/api/validation/mrms-visual-review/sample-set/bootstrap")
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["visual_readiness_level"] == READINESS_CANDIDATE_READY


def test_bootstrap_does_not_clear_alerts(storage, monkeypatch):
    _seed_visual_review(storage, monkeypatch)
    save_validation_alert(storage, {"status": ALERT_FAILED, "message": "test"})
    bootstrap_visual_sample_set(storage)
    assert load_validation_alert(storage).get("status") == ALERT_FAILED


def test_compact_before_bootstrap(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_visual_sample_bootstrap(storage)
    assert compact["available"] is False
    assert compact["suggested_command"] == SUGGESTED_COMMAND
