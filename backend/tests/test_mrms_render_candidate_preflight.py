"""Tests for MRMS render candidate preflight (Phase 62)."""

from __future__ import annotations

import json
from typing import Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight import (
    PREFLIGHT_BLOCKED,
    PREFLIGHT_CANDIDATE_READY,
    PREFLIGHT_JSON,
    PREFLIGHT_MD,
    PREFLIGHT_NEEDS_REVIEW,
    build_preflight_markdown,
    build_render_candidate_preflight_payload,
    compact_render_candidate_preflight,
    evaluate_render_candidate_preflight,
    gather_preflight_evidence,
    generate_render_candidate_preflight,
    load_render_candidate_preflight,
)
from backend.app.services.mrms_visual_review import save_visual_review_report
from backend.app.services.mrms_visual_review_sample_readiness import (
    READINESS_CANDIDATE_READY,
    STATUS_ACCEPTABLE,
    build_sample_key,
    upsert_sample_annotation,
)
from backend.app.services.mrms_visual_review_sample_set import build_visual_review_sample_set
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))


def _visual_report(*, created_at: str, artifacts: Optional[list[dict]] = None) -> dict:
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
        }
    ]
    return {
        "created_at": created_at,
        "layers_inspected": ["mrms_reflectivity"],
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


def _seed_candidate_ready_chain(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)

    class _MockDecoder:
        any_decoder = True
        wgrib2 = True
        gdal = False

        def summary_message(self) -> str:
            return "wgrib2 available"

    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_preflight.detect_decoder_availability",
        _MockDecoder,
    )
    monkeypatch.setattr(
        "backend.app.services.mrms_visual_review_sample_set.compact_visual_review_hint",
        lambda _storage: {
            "stale_visual_review": False,
            "visual_review_regeneration_recommended": False,
        },
    )
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_preflight.compact_operator_review_status",
        lambda _storage: {"status_level": "ok", "status_reason": "ok"},
    )
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_preflight.compact_preflight_attention",
        lambda _storage: {"blocks_preflight": False, "resolution_status": "attention_resolved_for_preflight"},
    )
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_preflight.load_mrms_proof_report",
        lambda _storage: {"generated_at": "2026-06-28T20:00:00Z", "overall_status": "pass"},
    )
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_preflight.compact_proof_bundle_status",
        lambda _storage: {"available": True},
    )
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    sample_set = build_visual_review_sample_set(storage, limit=1)
    for entry in sample_set["entries"]:
        upsert_sample_annotation(
            storage,
            sample_key=build_sample_key(timestamp=entry["timestamp"], layer=entry["layer"]),
            status=STATUS_ACCEPTABLE,
            operator_notes="Acceptable for local drilldown.",
            reviewer_label="op1",
        )


def test_preflight_blocked_without_visual_evidence(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    evidence = gather_preflight_evidence(storage)
    report = evaluate_render_candidate_preflight(evidence)
    assert report["preflight_level"] == PREFLIGHT_BLOCKED
    assert any("visual review" in item.lower() for item in report["blocking_items"])


def test_preflight_blocked_when_sample_readiness_missing(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    evidence = gather_preflight_evidence(storage)
    report = evaluate_render_candidate_preflight(evidence)
    assert report["preflight_level"] == PREFLIGHT_BLOCKED
    assert any("sample set" in item.lower() for item in report["blocking_items"])


def test_preflight_blocked_when_sample_readiness_not_candidate_ready(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    build_visual_review_sample_set(storage, limit=1)
    evidence = gather_preflight_evidence(storage)
    report = evaluate_render_candidate_preflight(evidence)
    assert report["preflight_level"] == PREFLIGHT_BLOCKED
    assert any("candidate_ready" in item for item in report["blocking_items"])


def test_preflight_candidate_ready_when_evidence_complete(storage, monkeypatch):
    _seed_candidate_ready_chain(storage, monkeypatch)
    evidence = gather_preflight_evidence(storage)
    report = evaluate_render_candidate_preflight(evidence)
    assert report["preflight_level"] == PREFLIGHT_CANDIDATE_READY
    assert evidence["sample_readiness"]["readiness_level"] == READINESS_CANDIDATE_READY
    assert report["verified_mrms"] is False
    assert report["candidate_preflight_ready_is_not_production_authorization"] is True


def test_preflight_blocked_if_verified_mrms_unexpectedly_true(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    evidence = gather_preflight_evidence(storage)
    evidence["safety_flags"]["verified_mrms"] = True
    report = evaluate_render_candidate_preflight(evidence)
    assert report["preflight_level"] == PREFLIGHT_BLOCKED
    assert any("verified_mrms" in item for item in report["blocking_items"])


def test_preflight_blocked_if_production_rendering_enabled(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", True)
    evidence = gather_preflight_evidence(storage)
    report = evaluate_render_candidate_preflight(evidence)
    assert report["preflight_level"] == PREFLIGHT_BLOCKED
    assert any("production rendering" in item.lower() for item in report["blocking_items"])


def test_preflight_blocked_if_placeholder_default_not_preserved(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    monkeypatch.setattr(settings, "enable_decoded_tiles", True)
    evidence = gather_preflight_evidence(storage)
    report = evaluate_render_candidate_preflight(evidence)
    assert report["preflight_level"] == PREFLIGHT_BLOCKED
    assert any("placeholder" in item.lower() for item in report["blocking_items"])


def test_preflight_json_and_markdown_persistence(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = generate_render_candidate_preflight(storage)
    assert storage.absolute_path(PREFLIGHT_JSON).is_file()
    assert storage.absolute_path(PREFLIGHT_MD).is_file()
    loaded = load_render_candidate_preflight(storage)
    assert loaded is not None
    assert loaded["preflight_level"] == report["preflight_level"]
    markdown = storage.absolute_path(PREFLIGHT_MD).read_text(encoding="utf-8")
    assert "NOT" in markdown
    assert "production authorization" in markdown


def test_preflight_markdown_contains_blocking_and_warnings(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = evaluate_render_candidate_preflight(gather_preflight_evidence(storage))
    markdown = build_preflight_markdown(report)
    assert "Blocking items" in markdown
    assert "Warnings" in markdown


def test_summary_includes_preflight_compact(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_preflight(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_render_candidate_preflight")
    assert compact is not None
    assert compact["verified_mrms"] is False
    assert compact["candidate_preflight_ready_is_not_production_authorization"] is True


def test_preflight_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-render-candidate/preflight")
    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_mrms"] is False
    assert payload["compact"]["preflight_level"] == PREFLIGHT_BLOCKED


def test_preflight_post_endpoint_persists(client, storage, monkeypatch):
    _seed_candidate_ready_chain(storage, monkeypatch)
    response = client.post("/api/validation/mrms-render-candidate/preflight")
    assert response.status_code == 200
    payload = response.json()
    assert payload["does_not_clear_alerts"] is True
    assert payload["latest"]["preflight_level"] in {
        PREFLIGHT_CANDIDATE_READY,
        PREFLIGHT_NEEDS_REVIEW,
    }


def test_preflight_does_not_clear_alerts(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(storage, {"status": ALERT_FAILED, "reason": "proof_failed"})
    generate_render_candidate_preflight(storage)
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert.get("status") == ALERT_FAILED


def test_preflight_does_not_mutate_production_flags(storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_preflight(storage)
    assert settings.enable_production_radar_tiles is False


def test_preflight_always_verified_mrms_false(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = generate_render_candidate_preflight(storage)
    compact = compact_render_candidate_preflight(storage)
    payload = build_render_candidate_preflight_payload(storage)
    assert report["verified_mrms"] is False
    assert compact["verified_mrms"] is False
    assert payload["verified_mrms"] is False


def test_preflight_needs_review_when_warnings_present(storage, monkeypatch):
    _seed_candidate_ready_chain(storage, monkeypatch)
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_preflight.load_mrms_proof_report",
        lambda _storage: None,
    )
    evidence = gather_preflight_evidence(storage)
    report = evaluate_render_candidate_preflight(evidence)
    assert report["preflight_level"] == PREFLIGHT_NEEDS_REVIEW
    assert any("proof report" in item.lower() for item in report["warnings"])
