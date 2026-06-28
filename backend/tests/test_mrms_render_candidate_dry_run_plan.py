"""Tests for MRMS render candidate dry-run plan (Phase 63)."""

from __future__ import annotations

from typing import Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_dry_run_plan import (
    DRY_RUN_BLOCKED,
    DRY_RUN_NEEDS_REVIEW,
    DRY_RUN_PLAN_JSON,
    DRY_RUN_PLAN_MD,
    DRY_RUN_PLAN_READY,
    build_dry_run_plan_markdown,
    build_render_candidate_dry_run_plan_payload,
    compact_render_candidate_dry_run_plan,
    evaluate_dry_run_plan_status,
    gather_dry_run_context,
    generate_render_candidate_dry_run_plan,
    load_render_candidate_dry_run_plan,
)
from backend.app.services.mrms_render_candidate_preflight import (
    PREFLIGHT_BLOCKED,
    PREFLIGHT_CANDIDATE_READY,
    PREFLIGHT_NEEDS_REVIEW,
    generate_render_candidate_preflight,
)
from backend.app.services.mrms_visual_review import save_visual_review_report
from backend.app.services.mrms_visual_review_sample_readiness import (
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


def _seed_preflight_ready_chain(storage, monkeypatch):
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
    generate_render_candidate_preflight(storage)


def test_dry_run_plan_blocked_when_preflight_missing(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    context = gather_dry_run_context(storage)
    status = evaluate_dry_run_plan_status(context)
    assert status["plan_status"] == DRY_RUN_BLOCKED
    assert any("preflight" in item.lower() for item in status["blocking_items"])


def test_dry_run_plan_blocked_when_preflight_blocked(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    generate_render_candidate_preflight(storage)
    context = gather_dry_run_context(storage)
    status = evaluate_dry_run_plan_status(context)
    assert status["plan_status"] == DRY_RUN_BLOCKED


def test_dry_run_plan_needs_review_when_preflight_needs_review(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_preflight.load_mrms_proof_report",
        lambda _storage: None,
    )
    generate_render_candidate_preflight(storage)
    context = gather_dry_run_context(storage)
    status = evaluate_dry_run_plan_status(context)
    assert status["plan_status"] == DRY_RUN_NEEDS_REVIEW


def test_dry_run_plan_ready_when_preflight_candidate_ready(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    context = gather_dry_run_context(storage)
    status = evaluate_dry_run_plan_status(context)
    assert status["plan_status"] == DRY_RUN_PLAN_READY
    plan = generate_render_candidate_dry_run_plan(storage)
    assert plan["plan_status"] == DRY_RUN_PLAN_READY
    assert plan["verified_mrms"] is False
    assert plan["does_not_execute_candidate_steps"] is True


def test_dry_run_plan_blocked_if_production_enabled(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", True)
    context = gather_dry_run_context(storage)
    status = evaluate_dry_run_plan_status(context)
    assert status["plan_status"] == DRY_RUN_BLOCKED


def test_dry_run_plan_blocked_if_placeholder_default_not_preserved(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    monkeypatch.setattr(settings, "enable_decoded_tiles", True)
    context = gather_dry_run_context(storage)
    status = evaluate_dry_run_plan_status(context)
    assert status["plan_status"] == DRY_RUN_BLOCKED


def test_dry_run_plan_json_and_markdown_persistence(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    plan = generate_render_candidate_dry_run_plan(storage)
    assert storage.absolute_path(DRY_RUN_PLAN_JSON).is_file()
    assert storage.absolute_path(DRY_RUN_PLAN_MD).is_file()
    loaded = load_render_candidate_dry_run_plan(storage)
    assert loaded is not None
    assert loaded["plan_status"] == plan["plan_status"]
    markdown = storage.absolute_path(DRY_RUN_PLAN_MD).read_text(encoding="utf-8")
    assert "NOT run by this phase" in markdown
    assert "does **NOT** verify MRMS" in markdown


def test_dry_run_plan_markdown_contains_sections(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    plan = generate_render_candidate_dry_run_plan(storage)
    markdown = build_dry_run_plan_markdown(plan)
    assert "Prerequisites" in markdown
    assert "Stop conditions" in markdown
    assert "Rollback" in markdown
    assert "NOT run by this phase" in markdown


def test_summary_includes_dry_run_plan_compact(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_dry_run_plan(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary.get("mrms_render_candidate_dry_run_plan")
    assert compact is not None
    assert compact["verified_mrms"] is False
    assert compact["does_not_authorize_production_use"] is True


def test_dry_run_plan_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.get("/api/validation/mrms-render-candidate/dry-run-plan")
    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_mrms"] is False
    assert payload["compact"]["plan_status"] == DRY_RUN_BLOCKED


def test_dry_run_plan_post_endpoint_persists(client, storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    response = client.post("/api/validation/mrms-render-candidate/dry-run-plan")
    assert response.status_code == 200
    payload = response.json()
    assert payload["does_not_execute_candidate_steps"] is True
    assert payload["latest"]["plan_status"] == DRY_RUN_PLAN_READY


def test_dry_run_plan_does_not_clear_alerts(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(storage, {"status": ALERT_FAILED, "reason": "proof_failed"})
    generate_render_candidate_dry_run_plan(storage)
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert.get("status") == ALERT_FAILED


def test_dry_run_plan_does_not_mutate_production_flags(storage, monkeypatch):
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_dry_run_plan(storage)
    assert settings.enable_production_radar_tiles is False


def test_dry_run_plan_always_verified_mrms_false(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    plan = generate_render_candidate_dry_run_plan(storage)
    compact = compact_render_candidate_dry_run_plan(storage)
    payload = build_render_candidate_dry_run_plan_payload(storage)
    assert plan["verified_mrms"] is False
    assert compact["verified_mrms"] is False
    assert payload["verified_mrms"] is False


def test_required_docs_missing_blocks_plan(storage, monkeypatch, tmp_path):
    _seed_preflight_ready_chain(storage, monkeypatch)
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_dry_run_plan._project_root",
        lambda: tmp_path,
    )
    context = gather_dry_run_context(storage)
    status = evaluate_dry_run_plan_status(context)
    assert status["plan_status"] == DRY_RUN_BLOCKED
    assert any("required docs" in item.lower() for item in status["blocking_items"])
