"""Tests for MRMS render candidate command scaffold (Phase 64)."""

from __future__ import annotations

from typing import Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_dry_run_plan import (
    DRY_RUN_BLOCKED,
    DRY_RUN_PLAN_READY,
    generate_render_candidate_dry_run_plan,
)
from backend.app.services.mrms_render_candidate_preflight import (
    PREFLIGHT_BLOCKED,
    generate_render_candidate_preflight,
)
from backend.app.services.mrms_render_candidate_scaffold import (
    SCAFFOLD_BLOCKED,
    SCAFFOLD_READY,
    SCAFFOLD_JSON,
    SCAFFOLD_MD,
    build_scaffold_markdown,
    build_render_candidate_scaffold_payload,
    compact_render_candidate_scaffold,
    evaluate_scaffold_status,
    gather_scaffold_context,
    generate_render_candidate_scaffold,
    load_render_candidate_scaffold,
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


def _seed_scaffold_ready_chain(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    generate_render_candidate_dry_run_plan(storage)


def test_scaffold_blocked_when_preflight_missing(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    context = gather_scaffold_context(storage)
    status = evaluate_scaffold_status(context)
    assert status["scaffold_status"] == SCAFFOLD_BLOCKED
    assert any("preflight" in item.lower() for item in status["blocking_items"])


def test_scaffold_blocked_when_dry_run_plan_missing(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    context = gather_scaffold_context(storage)
    status = evaluate_scaffold_status(context)
    assert status["scaffold_status"] == SCAFFOLD_BLOCKED
    assert any("dry-run plan" in item.lower() for item in status["blocking_items"])


def test_scaffold_blocked_when_preflight_blocked(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_visual_review_report(storage, _visual_report(created_at="2026-06-28T20:00:00Z"))
    generate_render_candidate_preflight(storage)
    context = gather_scaffold_context(storage)
    status = evaluate_scaffold_status(context)
    assert status["scaffold_status"] == SCAFFOLD_BLOCKED


def test_scaffold_blocked_when_dry_run_plan_blocked(storage, monkeypatch):
    _seed_preflight_ready_chain(storage, monkeypatch)
    generate_render_candidate_dry_run_plan(storage)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", True)
    context = gather_scaffold_context(storage)
    status = evaluate_scaffold_status(context)
    assert status["scaffold_status"] == SCAFFOLD_BLOCKED


def test_scaffold_ready_when_prerequisites_acceptable(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    context = gather_scaffold_context(storage)
    status = evaluate_scaffold_status(context)
    assert status["scaffold_status"] == SCAFFOLD_READY
    scaffold = generate_render_candidate_scaffold(storage)
    assert scaffold["scaffold_status"] == SCAFFOLD_READY
    assert scaffold["verified_mrms"] is False
    assert scaffold["does_not_execute_by_default"] is True
    assert scaffold["execute_performed"] is False


def test_scaffold_blocked_if_verified_mrms_unexpectedly_true(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)

    def _unsafe_safety():
        return {
            "verified_mrms": True,
            "enable_production_radar_tiles": False,
            "enable_decoded_tiles": False,
            "placeholder_default": True,
            "production_tile_serving_enabled": False,
        }

    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_scaffold._current_safety_state",
        _unsafe_safety,
    )
    context = gather_scaffold_context(storage)
    status = evaluate_scaffold_status(context)
    assert status["scaffold_status"] == SCAFFOLD_BLOCKED


def test_scaffold_blocked_if_production_rendering_enabled(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", True)
    context = gather_scaffold_context(storage)
    status = evaluate_scaffold_status(context)
    assert status["scaffold_status"] == SCAFFOLD_BLOCKED


def test_scaffold_blocked_if_placeholder_default_not_preserved(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    monkeypatch.setattr(settings, "enable_decoded_tiles", True)
    context = gather_scaffold_context(storage)
    status = evaluate_scaffold_status(context)
    assert status["scaffold_status"] == SCAFFOLD_BLOCKED


def test_scaffold_json_and_markdown_persistence(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    scaffold = generate_render_candidate_scaffold(storage)
    assert storage.absolute_path(SCAFFOLD_JSON).is_file()
    assert storage.absolute_path(SCAFFOLD_MD).is_file()
    loaded = load_render_candidate_scaffold(storage)
    assert loaded is not None
    assert loaded["scaffold_status"] == scaffold["scaffold_status"]
    markdown = storage.absolute_path(SCAFFOLD_MD).read_text(encoding="utf-8")
    assert "disabled-by-default" in markdown.lower()
    assert "does **NOT** verify MRMS" in markdown


def test_scaffold_markdown_contains_sections(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    scaffold = generate_render_candidate_scaffold(storage)
    markdown = build_scaffold_markdown(scaffold)
    assert "Safety gates" in markdown
    assert "Future candidate commands" in markdown
    assert "NOT executed by default" in markdown


def test_summary_includes_scaffold_compact(db_session, storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    generate_render_candidate_scaffold(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary["mrms_render_candidate_scaffold"]
    assert compact["scaffold_status"] == SCAFFOLD_READY
    assert compact["verified_mrms"] is False


def test_scaffold_get_endpoint(client, storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    generate_render_candidate_scaffold(storage)
    response = client.get("/api/validation/mrms-render-candidate/scaffold")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["compact"]["scaffold_status"] == SCAFFOLD_READY


def test_scaffold_post_endpoint_persists(client, storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    response = client.post("/api/validation/mrms-render-candidate/scaffold")
    assert response.status_code == 200
    assert storage.absolute_path(SCAFFOLD_JSON).is_file()


def test_scaffold_does_not_clear_alerts(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    save_validation_alert(storage, {"level": ALERT_FAILED, "reason": "test"})
    generate_render_candidate_scaffold(storage)
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert["level"] == ALERT_FAILED


def test_scaffold_does_not_mutate_production_flags(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    generate_render_candidate_scaffold(storage)
    assert settings.enable_production_radar_tiles is False
    assert settings.enable_decoded_tiles is False


def test_scaffold_always_verified_mrms_false(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    scaffold = generate_render_candidate_scaffold(storage)
    payload = build_render_candidate_scaffold_payload(storage)
    assert scaffold["verified_mrms"] is False
    assert payload["verified_mrms"] is False
    assert payload["compact"]["verified_mrms"] is False


def test_scaffold_execute_requested_still_no_side_effects(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    scaffold = generate_render_candidate_scaffold(storage, execute_requested=True)
    assert scaffold["execute_performed"] is False
    assert scaffold["does_not_download_or_decode"] is True
    assert scaffold["does_not_create_production_tiles"] is True


def test_scaffold_safety_invariants(storage, monkeypatch):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    scaffold = generate_render_candidate_scaffold(storage)
    compact = compact_render_candidate_scaffold(storage)
    for payload in (scaffold, compact):
        assert payload["verified_mrms"] is False
        assert payload["does_not_enable_production"] is True
        assert payload["does_not_download_or_decode"] is True
        assert payload["does_not_create_production_tiles"] is True
        assert payload["does_not_serve_production_tiles"] is True
        assert payload["does_not_clear_alerts"] is True
        assert payload["does_not_authorize_production_use"] is True


def test_required_docs_missing_blocks_scaffold(storage, monkeypatch, tmp_path):
    _seed_scaffold_ready_chain(storage, monkeypatch)
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_scaffold._project_root",
        lambda: tmp_path,
    )
    context = gather_scaffold_context(storage)
    status = evaluate_scaffold_status(context)
    assert status["scaffold_status"] == SCAFFOLD_BLOCKED
