"""Tests for MRMS visual review sample annotations and readiness (Phase 61)."""

from __future__ import annotations

import json
from typing import Optional

from backend.app.config import settings
from backend.app.services.mrms_visual_review import save_visual_review_report
from backend.app.services.mrms_visual_review_sample_readiness import (
    ANNOTATIONS_JSON,
    READINESS_MD,
    READINESS_CANDIDATE_READY,
    READINESS_NEEDS_REVIEW,
    READINESS_NOT_READY,
    STATUS_ACCEPTABLE,
    STATUS_QUESTIONABLE,
    STATUS_REJECTED,
    STATUS_UNREVIEWED,
    SampleAnnotationValidationError,
    build_sample_key,
    build_visual_review_sample_readiness_payload,
    compute_readiness_summary,
    load_sample_annotations,
    refresh_visual_review_sample_readiness,
    upsert_sample_annotation,
)
from backend.app.services.mrms_visual_review_sample_set import (
    SAMPLE_SET_JSON,
    build_visual_review_sample_set,
    load_visual_review_sample_set,
)
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))


def _visual_report(
    *,
    created_at: str,
    artifacts: Optional[list[dict]] = None,
) -> dict:
    default_artifacts = [
        {
            "timestamp": "2026-06-28T12:00:00Z",
            "layer": "mrms_reflectivity",
            "tile_mode": "placeholder",
            "render_status": "placeholder",
            "raw_kind": "demo_seeded_stub",
            "artifact_paths_found": ["data/processed/demo-a.png"],
            "missing_artifacts": [],
            "stale_visual_review": False,
        },
        {
            "timestamp": "2026-06-28T12:05:00Z",
            "layer": "mrms_reflectivity",
            "tile_mode": "decoded_prototype",
            "render_status": "decoded_prototype",
            "raw_kind": "demo_seeded_stub",
            "artifact_paths_found": ["data/processed/demo-b.png"],
            "missing_artifacts": ["tile_cache"],
            "stale_visual_review": False,
        },
    ]
    return {
        "created_at": created_at,
        "layers_inspected": ["mrms_reflectivity"],
        "timestamps_inspected": [item["timestamp"] for item in (artifacts or default_artifacts)],
        "frame_count": len(artifacts or default_artifacts),
        "artifact_count": len(artifacts or default_artifacts),
        "missing_artifact_count": 1,
        "tile_modes_found": ["placeholder", "decoded_prototype"],
        "artifacts": artifacts or default_artifacts,
        "json_path": "data/dev/mrms_visual_review_latest.json",
        "markdown_path": "data/dev/mrms_visual_review_latest.md",
        "verified_mrms": False,
        "local_visual_review_only": True,
        "context": {"stale_visual_review": False},
    }


def _seed_sample_set(storage, monkeypatch, *, artifacts: Optional[list[dict]] = None) -> dict:
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z", artifacts=artifacts))
    return build_visual_review_sample_set(storage, limit=5)


def test_annotations_json_persistence(storage, monkeypatch):
    sample_set = _seed_sample_set(storage, monkeypatch)
    key = build_sample_key(
        timestamp=sample_set["entries"][0]["timestamp"],
        layer=sample_set["entries"][0]["layer"],
    )
    upsert_sample_annotation(
        storage,
        sample_key=key,
        status=STATUS_ACCEPTABLE,
        operator_notes="Looks fine for local drilldown.",
        reviewer_label="op1",
    )
    document = load_sample_annotations(storage)
    assert document is not None
    assert storage.absolute_path(ANNOTATIONS_JSON).is_file()
    assert document["annotations"][key]["status"] == STATUS_ACCEPTABLE
    assert document["verified_mrms"] is False
    assert document["local_advisory_only"] is True


def test_annotations_preserve_sample_set(storage, monkeypatch):
    sample_set = _seed_sample_set(storage, monkeypatch)
    before = json.loads(storage.absolute_path(SAMPLE_SET_JSON).read_text(encoding="utf-8"))
    key = build_sample_key(
        timestamp=before["entries"][0]["timestamp"],
        layer=before["entries"][0]["layer"],
    )
    upsert_sample_annotation(
        storage,
        sample_key=key,
        status=STATUS_ACCEPTABLE,
        operator_notes="Local note",
    )
    after = json.loads(storage.absolute_path(SAMPLE_SET_JSON).read_text(encoding="utf-8"))
    assert after["entry_count"] == before["entry_count"]
    assert after["entries"] == before["entries"]


def test_readiness_all_unreviewed(storage, monkeypatch):
    _seed_sample_set(storage, monkeypatch)
    readiness = compute_readiness_summary(storage)
    assert readiness["readiness_level"] == READINESS_NOT_READY
    assert readiness["readiness_reason"] == "missing_artifacts_present"
    assert readiness["unreviewed_samples"] == 2


def test_readiness_acceptable_clean_samples(storage, monkeypatch):
    artifacts = [
        {
            "timestamp": "2026-06-28T12:00:00Z",
            "layer": "mrms_reflectivity",
            "tile_mode": "placeholder",
            "render_status": "placeholder",
            "raw_kind": "demo_seeded_stub",
            "artifact_paths_found": ["data/processed/demo-a.png"],
            "missing_artifacts": [],
            "stale_visual_review": False,
        },
        {
            "timestamp": "2026-06-28T12:10:00Z",
            "layer": "mrms_reflectivity",
            "tile_mode": "production_gated",
            "render_status": "production_gated",
            "raw_kind": "demo_seeded_stub",
            "artifact_paths_found": ["data/processed/demo-c.png"],
            "missing_artifacts": [],
            "stale_visual_review": False,
        },
    ]
    sample_set = _seed_sample_set(storage, monkeypatch, artifacts=artifacts)
    for entry in sample_set["entries"]:
        upsert_sample_annotation(
            storage,
            sample_key=build_sample_key(timestamp=entry["timestamp"], layer=entry["layer"]),
            status=STATUS_ACCEPTABLE,
            operator_notes="Acceptable for local drilldown.",
            reviewer_label="op1",
        )
    readiness = compute_readiness_summary(storage)
    assert readiness["readiness_level"] == READINESS_CANDIDATE_READY
    assert readiness["acceptable_count"] == 2
    assert readiness["verified_mrms"] is False
    assert readiness["candidate_ready_is_not_production_authorization"] is True


def test_readiness_questionable_blocks_candidate_ready(storage, monkeypatch):
    sample_set = _seed_sample_set(
        storage,
        monkeypatch,
        artifacts=[
            {
                "timestamp": "2026-06-28T12:00:00Z",
                "layer": "mrms_reflectivity",
                "tile_mode": "placeholder",
                "render_status": "placeholder",
                "raw_kind": "demo_seeded_stub",
                "artifact_paths_found": ["data/processed/demo-a.png"],
                "missing_artifacts": [],
                "stale_visual_review": False,
            }
        ],
    )
    entry = sample_set["entries"][0]
    upsert_sample_annotation(
        storage,
        sample_key=build_sample_key(timestamp=entry["timestamp"], layer=entry["layer"]),
        status=STATUS_QUESTIONABLE,
        operator_notes="Needs another look.",
    )
    readiness = compute_readiness_summary(storage)
    assert readiness["readiness_level"] == READINESS_NEEDS_REVIEW
    assert readiness["questionable_count"] == 1


def test_readiness_rejected_is_not_ready(storage, monkeypatch):
    sample_set = _seed_sample_set(
        storage,
        monkeypatch,
        artifacts=[
            {
                "timestamp": "2026-06-28T12:00:00Z",
                "layer": "mrms_reflectivity",
                "tile_mode": "placeholder",
                "render_status": "placeholder",
                "raw_kind": "demo_seeded_stub",
                "artifact_paths_found": ["data/processed/demo-a.png"],
                "missing_artifacts": [],
                "stale_visual_review": False,
            }
        ],
    )
    entry = sample_set["entries"][0]
    upsert_sample_annotation(
        storage,
        sample_key=build_sample_key(timestamp=entry["timestamp"], layer=entry["layer"]),
        status=STATUS_REJECTED,
        operator_notes="Bad visual evidence.",
    )
    readiness = compute_readiness_summary(storage)
    assert readiness["readiness_level"] == READINESS_NOT_READY
    assert readiness["rejected_count"] == 1


def test_readiness_missing_artifact_blocks_candidate_ready(storage, monkeypatch):
    sample_set = _seed_sample_set(storage, monkeypatch)
    for entry in sample_set["entries"]:
        upsert_sample_annotation(
            storage,
            sample_key=build_sample_key(timestamp=entry["timestamp"], layer=entry["layer"]),
            status=STATUS_ACCEPTABLE,
            operator_notes="Marked acceptable despite context.",
        )
    readiness = compute_readiness_summary(storage)
    assert readiness["missing_artifact_samples"] >= 1
    assert readiness["readiness_level"] == READINESS_NOT_READY


def test_readiness_stale_blocks_candidate_ready(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    monkeypatch.setattr(
        "backend.app.services.mrms_visual_review_sample_set.compact_visual_review_hint",
        lambda _storage: {
            "stale_visual_review": True,
            "visual_review_regeneration_recommended": True,
            "reason": "evidence_newer_than_visual_review",
        },
    )
    artifacts = [
        {
            "timestamp": "2026-06-28T12:00:00Z",
            "layer": "mrms_reflectivity",
            "tile_mode": "placeholder",
            "render_status": "placeholder",
            "raw_kind": "demo_seeded_stub",
            "artifact_paths_found": ["data/processed/demo-a.png"],
            "missing_artifacts": [],
            "stale_visual_review": True,
        }
    ]
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z", artifacts=artifacts))
    sample_set = build_visual_review_sample_set(storage, limit=1)
    entry = sample_set["entries"][0]
    upsert_sample_annotation(
        storage,
        sample_key=build_sample_key(timestamp=entry["timestamp"], layer=entry["layer"]),
        status=STATUS_ACCEPTABLE,
        operator_notes="Looks ok locally.",
    )
    readiness = compute_readiness_summary(storage)
    assert readiness["readiness_level"] == READINESS_NOT_READY
    assert readiness["stale_samples"] >= 1


def test_readiness_no_sample_set(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    readiness = compute_readiness_summary(storage)
    assert readiness["readiness_level"] == READINESS_NOT_READY
    assert readiness["readiness_reason"] == "no_sample_set"


def test_refresh_writes_readiness_markdown(storage, monkeypatch):
    _seed_sample_set(storage, monkeypatch)
    readiness = refresh_visual_review_sample_readiness(storage)
    assert storage.absolute_path(READINESS_MD).is_file()
    markdown = storage.absolute_path(READINESS_MD).read_text(encoding="utf-8")
    assert "NOT" in markdown
    assert "production authorization" in markdown
    assert readiness["markdown_path"].endswith("mrms_visual_review_sample_readiness.md")


def test_summary_includes_sample_readiness_compact(db_session, storage, monkeypatch):
    _seed_sample_set(storage, monkeypatch)
    refresh_visual_review_sample_readiness(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_visual_review_sample_readiness")
    assert compact is not None
    assert compact["verified_mrms"] is False
    assert compact["candidate_ready_is_not_production_authorization"] is True


def test_readiness_get_endpoint(client, storage, monkeypatch):
    _seed_sample_set(storage, monkeypatch)
    response = client.get("/api/validation/mrms-visual-review/sample-set/readiness")
    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_mrms"] is False
    assert payload["compact"]["readiness_level"] == READINESS_NOT_READY


def test_annotation_post_endpoint(client, storage, monkeypatch):
    sample_set = _seed_sample_set(
        storage,
        monkeypatch,
        artifacts=[
            {
                "timestamp": "2026-06-28T12:00:00Z",
                "layer": "mrms_reflectivity",
                "tile_mode": "placeholder",
                "render_status": "placeholder",
                "raw_kind": "demo_seeded_stub",
                "artifact_paths_found": ["data/processed/demo-a.png"],
                "missing_artifacts": [],
                "stale_visual_review": False,
            }
        ],
    )
    entry = sample_set["entries"][0]
    response = client.post(
        "/api/validation/mrms-visual-review/sample-set/annotations",
        json={
            "sample_key": build_sample_key(timestamp=entry["timestamp"], layer=entry["layer"]),
            "status": STATUS_ACCEPTABLE,
            "operator_notes": "Local acceptable.",
            "reviewer_label": "op1",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["does_not_clear_alerts"] is True
    assert payload["annotation"]["status"] == STATUS_ACCEPTABLE


def test_annotation_requires_sample_set(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.post(
        "/api/validation/mrms-visual-review/sample-set/annotations",
        json={"sample_key": "2026-06-28T12:00:00Z|mrms_reflectivity", "status": STATUS_ACCEPTABLE},
    )
    assert response.status_code == 422


def test_readiness_does_not_clear_alerts(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(storage, {"status": ALERT_FAILED, "reason": "proof_failed"})
    _seed_sample_set(storage, monkeypatch)
    refresh_visual_review_sample_readiness(storage)
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert.get("status") == ALERT_FAILED


def test_readiness_does_not_mutate_production_flags(storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    _seed_sample_set(storage, monkeypatch)
    payload = build_visual_review_sample_readiness_payload(storage)
    assert payload["verified_mrms"] is False
    assert settings.enable_production_radar_tiles is False


def test_invalid_annotation_status_raises(storage, monkeypatch):
    sample_set = _seed_sample_set(
        storage,
        monkeypatch,
        artifacts=[
            {
                "timestamp": "2026-06-28T12:00:00Z",
                "layer": "mrms_reflectivity",
                "tile_mode": "placeholder",
                "render_status": "placeholder",
                "raw_kind": "demo_seeded_stub",
                "artifact_paths_found": ["data/processed/demo-a.png"],
                "missing_artifacts": [],
                "stale_visual_review": False,
            }
        ],
    )
    entry = sample_set["entries"][0]
    try:
        upsert_sample_annotation(
            storage,
            sample_key=build_sample_key(timestamp=entry["timestamp"], layer=entry["layer"]),
            status="approved",
            operator_notes="nope",
        )
    except SampleAnnotationValidationError:
        pass
    else:
        raise AssertionError("expected SampleAnnotationValidationError")
