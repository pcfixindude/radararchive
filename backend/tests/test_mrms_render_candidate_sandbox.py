"""Tests for MRMS render candidate artifact sandbox (Phase 65)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox import (
    EXPECTED_SUBDIRS,
    MANIFEST_JSON,
    REPORT_MD,
    SANDBOX_BLOCKED,
    SANDBOX_MISSING,
    SANDBOX_NEEDS_CLEANUP,
    SANDBOX_NEEDS_SETUP,
    SANDBOX_READY,
    SANDBOX_ROOT_REL,
    build_render_candidate_sandbox_payload,
    build_sandbox_report_markdown,
    compact_render_candidate_sandbox,
    evaluate_sandbox_status,
    gather_sandbox_context,
    generate_render_candidate_sandbox,
    load_sandbox_manifest,
    validate_sandbox_path_safety,
)
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def test_sandbox_missing_status_before_layout(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    context = gather_sandbox_context(storage)
    status = evaluate_sandbox_status(context)
    assert status["sandbox_status"] == SANDBOX_MISSING


def test_sandbox_layout_creation_under_data_dev(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    manifest = generate_render_candidate_sandbox(storage)
    root_abs = storage.absolute_path(manifest["sandbox_root"])
    assert str(root_abs).endswith("dev/mrms_render_candidate_sandbox")
    for subdir in EXPECTED_SUBDIRS:
        assert storage.absolute_path(
            storage.normalize_path(SANDBOX_ROOT_REL, subdir)
        ).is_dir()
    assert manifest["sandbox_status"] == SANDBOX_READY


def test_sandbox_needs_setup_when_subdirectory_missing(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)
    missing = storage.absolute_path(storage.normalize_path(SANDBOX_ROOT_REL, "scratch"))
    missing.rmdir()
    context = gather_sandbox_context(storage)
    status = evaluate_sandbox_status(context)
    assert status["sandbox_status"] == SANDBOX_NEEDS_SETUP
    assert "scratch" in (context.get("missing_subdirectories") or [])


def test_sandbox_needs_cleanup_report_only_candidates(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)
    scratch = storage.absolute_path(storage.normalize_path(SANDBOX_ROOT_REL, "scratch", "temp.bin"))
    scratch.write_bytes(b"demo")
    context = gather_sandbox_context(storage)
    status = evaluate_sandbox_status(context)
    assert status["sandbox_status"] == SANDBOX_NEEDS_CLEANUP
    assert context["cleanup_candidates"]
    assert context["cleanup_candidates"][0]["action"] == "report_only"


def test_sandbox_ready_when_directories_exist(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    manifest = generate_render_candidate_sandbox(storage)
    assert manifest["sandbox_status"] == SANDBOX_READY
    assert manifest["delete_performed"] is False


def test_sandbox_manifest_and_markdown_persistence(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    manifest = generate_render_candidate_sandbox(storage)
    assert storage.absolute_path(MANIFEST_JSON).is_file()
    assert storage.absolute_path(REPORT_MD).is_file()
    loaded = load_sandbox_manifest(storage)
    assert loaded is not None
    assert loaded["sandbox_status"] == manifest["sandbox_status"]
    markdown = storage.absolute_path(REPORT_MD).read_text(encoding="utf-8")
    assert "local candidate artifact sandbox only" in markdown.lower()
    assert "report-only" in markdown.lower()


def test_sandbox_markdown_contains_sections(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    manifest = generate_render_candidate_sandbox(storage)
    markdown = build_sandbox_report_markdown(manifest)
    assert "Expected subdirectories" in markdown
    assert "Isolation status" in markdown
    assert "Cleanup candidates" in markdown


def test_sandbox_blocked_when_path_escapes_data_dev(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_sandbox._sandbox_root_normalized",
        lambda _storage: "raw/unsafe_sandbox",
    )
    safety = validate_sandbox_path_safety(storage)
    assert safety["under_data_dev"] is False
    context = gather_sandbox_context(storage)
    status = evaluate_sandbox_status(context)
    assert status["sandbox_status"] == SANDBOX_BLOCKED


def test_sandbox_blocked_when_overlaps_production_tile_paths(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_sandbox._sandbox_root_normalized",
        lambda storage: storage.normalize_path("tiles", "production", "candidate"),
    )
    safety = validate_sandbox_path_safety(storage)
    assert safety["overlaps_production_tile_paths"] is True
    context = gather_sandbox_context(storage)
    status = evaluate_sandbox_status(context)
    assert status["sandbox_status"] == SANDBOX_BLOCKED


def test_sandbox_blocked_if_verified_mrms_unexpectedly_true(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)

    def _unsafe_safety():
        return {
            "verified_mrms": True,
            "enable_production_radar_tiles": False,
            "enable_decoded_tiles": False,
            "placeholder_default": True,
            "production_tile_serving_enabled": False,
        }

    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_sandbox._current_safety_state",
        _unsafe_safety,
    )
    context = gather_sandbox_context(storage)
    status = evaluate_sandbox_status(context)
    assert status["sandbox_status"] == SANDBOX_BLOCKED


def test_sandbox_blocked_if_production_rendering_enabled(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)
    monkeypatch.setattr(settings, "enable_production_radar_tiles", True)
    context = gather_sandbox_context(storage)
    status = evaluate_sandbox_status(context)
    assert status["sandbox_status"] == SANDBOX_BLOCKED


def test_sandbox_blocked_if_placeholder_default_not_preserved(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)
    monkeypatch.setattr(settings, "enable_decoded_tiles", True)
    context = gather_sandbox_context(storage)
    status = evaluate_sandbox_status(context)
    assert status["sandbox_status"] == SANDBOX_BLOCKED


def test_sandbox_blocked_on_unsafe_symlinks(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_sandbox._detect_unsafe_symlinks",
        lambda _path: ["sandbox root is a symlink: /tmp/evil"],
    )
    context = gather_sandbox_context(storage)
    status = evaluate_sandbox_status(context)
    assert status["sandbox_status"] == SANDBOX_BLOCKED


def test_sandbox_no_deletion_by_default(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)
    scratch = storage.absolute_path(storage.normalize_path(SANDBOX_ROOT_REL, "scratch", "keep.bin"))
    scratch.write_bytes(b"keep")
    manifest = generate_render_candidate_sandbox(storage, confirm_delete_requested=True)
    assert manifest["delete_performed"] is False
    assert scratch.is_file()


def test_sandbox_does_not_clear_alerts(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(storage, {"level": ALERT_FAILED, "reason": "test"})
    generate_render_candidate_sandbox(storage)
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert["level"] == ALERT_FAILED


def test_sandbox_does_not_mutate_production_flags(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)
    assert settings.enable_production_radar_tiles is False
    assert settings.enable_decoded_tiles is False


def test_sandbox_always_verified_mrms_false(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    manifest = generate_render_candidate_sandbox(storage)
    payload = build_render_candidate_sandbox_payload(storage)
    assert manifest["verified_mrms"] is False
    assert payload["verified_mrms"] is False
    assert payload["compact"]["verified_mrms"] is False


def test_sandbox_safety_invariants(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    manifest = generate_render_candidate_sandbox(storage)
    compact = compact_render_candidate_sandbox(storage)
    for payload in (manifest, compact):
        assert payload["verified_mrms"] is False
        assert payload["does_not_enable_production"] is True
        assert payload["does_not_download_or_decode"] is True
        assert payload["does_not_create_production_tiles"] is True
        assert payload["does_not_serve_production_tiles"] is True
        assert payload["does_not_delete_by_default"] is True
        assert payload["does_not_clear_alerts"] is True
        assert payload["does_not_authorize_production_use"] is True


def test_summary_includes_sandbox_compact(db_session, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary["mrms_render_candidate_sandbox"]
    assert compact["sandbox_status"] == SANDBOX_READY
    assert compact["verified_mrms"] is False


def test_sandbox_get_endpoint(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)
    response = client.get("/api/validation/mrms-render-candidate/sandbox")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["compact"]["sandbox_status"] == SANDBOX_READY


def test_sandbox_post_endpoint_persists(client, storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    response = client.post("/api/validation/mrms-render-candidate/sandbox")
    assert response.status_code == 200
    assert storage.absolute_path(MANIFEST_JSON).is_file()
