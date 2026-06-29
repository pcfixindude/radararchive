"""Tests for MRMS render candidate sandbox manifest import/export (Phase 66)."""

from __future__ import annotations

import json

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox import generate_render_candidate_sandbox
from backend.app.services.mrms_render_candidate_sandbox_import_export import (
    EXPORT_DIR,
    IMPORT_DIR,
    SCHEMA_VERSION,
    STATUS_BLOCKED,
    STATUS_EXPORT_READY,
    STATUS_IMPORTED,
    STATUS_INVALID,
    STATUS_MISSING,
    build_export_manifest,
    build_export_markdown,
    build_render_candidate_sandbox_import_export_payload,
    compact_render_candidate_sandbox_import_export,
    compare_sandbox_manifests,
    export_candidate_sandbox_manifest,
    gather_export_inputs,
    import_candidate_sandbox_manifest,
    validate_import_manifest,
)
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def _seed_sandbox_reports(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)


def test_export_generation_with_full_sandbox_manifest(storage, monkeypatch):
    _seed_sandbox_reports(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    assert export["schema_version"] == SCHEMA_VERSION
    assert export["import_export_status"] == STATUS_EXPORT_READY
    assert export["binary_artifacts_included"] is False
    assert export["verified_mrms"] is False
    assert any(report["kind"] == "sandbox_manifest" for report in export["included_reports"])
    assert storage.absolute_path(export["json_path"]).is_file()
    assert storage.absolute_path(export["markdown_path"]).is_file()


def test_export_generation_with_optional_upstream_missing(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    sandbox_manifest = {
        "sandbox_status": "ready",
        "blocking_items": [],
        "warnings": [],
        "safety_gates": [],
        "verified_mrms": False,
    }
    path = storage.normalize_path("dev/mrms_render_candidate_sandbox_manifest.json")
    storage.ensure_directories(path.rsplit("/", 1)[0])
    storage.absolute_path(path).write_text(json.dumps(sandbox_manifest), encoding="utf-8")
    export = build_export_manifest(storage)
    assert export["import_export_status"] == STATUS_EXPORT_READY
    assert export["missing_inputs"]
    assert export["included_reports"]


def test_export_missing_all_inputs_status(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    export = build_export_manifest(storage)
    assert export["import_export_status"] == STATUS_MISSING
    assert not export["included_reports"]


def test_exported_schema_version_and_safety_metadata(storage, monkeypatch):
    _seed_sandbox_reports(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    assert export["schema_version"] == SCHEMA_VERSION
    assert export["safety_state"]["verified_mrms"] is False
    assert export["does_not_download_or_decode"] is True
    markdown = build_export_markdown(export)
    assert "Schema version" in markdown
    assert "NOT** verify MRMS" in markdown


def test_import_validation_of_valid_export(storage, monkeypatch):
    _seed_sandbox_reports(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    imported = import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    assert imported["import_export_status"] == STATUS_IMPORTED
    assert imported["validation"]["valid"] is True
    assert imported["comparison"]["advisory_only"] is True
    assert storage.absolute_path(imported["json_path"]).is_file()


def test_import_blocked_when_manifest_claims_verified_mrms(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    bad = {
        "schema_version": SCHEMA_VERSION,
        "verified_mrms": True,
        "included_reports": [{"path": "dev/mrms_render_candidate_sandbox_manifest.json", "kind": "sandbox_manifest"}],
    }
    path = storage.normalize_path(EXPORT_DIR, "candidate_sandbox_export_bad.json")
    storage.ensure_directories(EXPORT_DIR)
    storage.absolute_path(path).write_text(json.dumps(bad), encoding="utf-8")
    validation = validate_import_manifest(bad)
    assert validation["import_status"] == STATUS_BLOCKED
    imported = import_candidate_sandbox_manifest(storage, source_json_path=path)
    assert imported["import_export_status"] == STATUS_BLOCKED


def test_import_blocked_when_production_rendering_enabled(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    bad = {
        "schema_version": SCHEMA_VERSION,
        "safety_state": {"enable_production_radar_tiles": True},
        "included_reports": [{"path": "dev/mrms_render_candidate_sandbox_manifest.json", "kind": "sandbox_manifest"}],
    }
    validation = validate_import_manifest(bad)
    assert validation["import_status"] == STATUS_BLOCKED


def test_import_blocked_when_paths_escape_data_dev(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    bad = {
        "schema_version": SCHEMA_VERSION,
        "included_reports": [{"path": "raw/outside.json", "kind": "sandbox_manifest"}],
    }
    validation = validate_import_manifest(bad)
    assert validation["import_status"] == STATUS_BLOCKED


def test_import_blocked_when_production_tile_paths_referenced(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    bad = {
        "schema_version": SCHEMA_VERSION,
        "included_reports": [{"path": "dev/tiles/production/candidate.json", "kind": "sandbox_manifest"}],
    }
    validation = validate_import_manifest(bad)
    assert validation["import_status"] == STATUS_BLOCKED


def test_import_blocked_on_path_traversal(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    bad = {
        "schema_version": SCHEMA_VERSION,
        "included_reports": [{"path": "dev/../secrets.json", "kind": "sandbox_manifest"}],
    }
    validation = validate_import_manifest(bad)
    assert validation["import_status"] == STATUS_BLOCKED


def test_import_blocked_on_unsupported_schema_version(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    bad = {
        "schema_version": "99.0",
        "included_reports": [{"path": "dev/mrms_render_candidate_sandbox_manifest.json", "kind": "sandbox_manifest"}],
    }
    validation = validate_import_manifest(bad)
    assert validation["import_status"] == STATUS_BLOCKED


def test_import_blocked_on_binary_artifacts_flag(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    bad = {
        "schema_version": SCHEMA_VERSION,
        "binary_artifacts_included": True,
        "included_reports": [{"path": "dev/mrms_render_candidate_sandbox_manifest.json", "kind": "sandbox_manifest"}],
    }
    validation = validate_import_manifest(bad)
    assert validation["import_status"] == STATUS_BLOCKED


def test_compare_manifests_reports_changes(storage, monkeypatch):
    current = {
        "sandbox_status": "ready",
        "blocking_items": ["a"],
        "warnings": [],
        "safety_gates": [{"passed": True}],
        "subdirectory_scans": [{"name": "scratch", "file_count": 0, "total_bytes": 0}],
        "created_at": "2026-06-28T20:00:00Z",
    }
    imported = {
        "sandbox_status": "needs_cleanup",
        "blocking_items": ["b"],
        "warnings": ["warn"],
        "safety_gates": [{"passed": False}],
        "subdirectory_scans": [{"name": "scratch", "file_count": 2, "total_bytes": 10}],
        "created_at": "2026-06-28T21:00:00Z",
        "source": "archive",
    }
    comparison = compare_sandbox_manifests(current, imported)
    assert comparison["changed_sandbox_status"] is True
    assert comparison["changed_safety_gate_summary"] is True
    assert comparison["changed_file_counts"]


def test_no_binary_artifact_inclusion_by_default(storage, monkeypatch):
    _seed_sandbox_reports(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    payload = json.dumps(export)
    assert "base64" not in payload.lower()
    assert export["binary_artifacts_included"] is False


def test_json_persistence_under_data_dev(storage, monkeypatch):
    _seed_sandbox_reports(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    imported = import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    assert export["json_path"].startswith("data/dev/")
    assert imported["json_path"].startswith("data/dev/")
    assert storage.absolute_path(IMPORT_DIR).is_dir()


def test_sandbox_import_export_does_not_clear_alerts(storage, monkeypatch):
    _seed_sandbox_reports(storage, monkeypatch)
    save_validation_alert(storage, {"level": ALERT_FAILED, "reason": "test"})
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert["level"] == ALERT_FAILED


def test_sandbox_import_export_does_not_mutate_production_flags(storage, monkeypatch):
    _seed_sandbox_reports(storage, monkeypatch)
    export_candidate_sandbox_manifest(storage)
    assert settings.enable_production_radar_tiles is False
    assert settings.enable_decoded_tiles is False


def test_sandbox_import_export_safety_invariants(storage, monkeypatch):
    _seed_sandbox_reports(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    compact = compact_render_candidate_sandbox_import_export(storage)
    for payload in (export, compact):
        assert payload["verified_mrms"] is False
        assert payload["does_not_enable_production"] is True
        assert payload["does_not_download_or_decode"] is True
        assert payload["does_not_create_production_tiles"] is True
        assert payload["does_not_serve_production_tiles"] is True
        assert payload["does_not_clear_alerts"] is True
        assert payload["does_not_authorize_production_use"] is True


def test_summary_includes_import_export_compact(db_session, storage, monkeypatch):
    _seed_sandbox_reports(storage, monkeypatch)
    export_candidate_sandbox_manifest(storage)
    summary = build_validation_summary(db_session, storage)
    compact = summary["mrms_render_candidate_sandbox_import_export"]
    assert compact["schema_version"] == SCHEMA_VERSION
    assert compact["verified_mrms"] is False


def test_import_export_get_endpoint(client, storage, monkeypatch):
    _seed_sandbox_reports(storage, monkeypatch)
    export_candidate_sandbox_manifest(storage)
    response = client.get("/api/validation/mrms-render-candidate/sandbox/import-export")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["compact"]["schema_version"] == SCHEMA_VERSION


def test_import_export_export_post_endpoint(client, storage, monkeypatch):
    _seed_sandbox_reports(storage, monkeypatch)
    response = client.post("/api/validation/mrms-render-candidate/sandbox/import-export/export")
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["latest_export_json_path"]


def test_import_export_import_post_endpoint(client, storage, monkeypatch):
    _seed_sandbox_reports(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    response = client.post(
        "/api/validation/mrms-render-candidate/sandbox/import-export/import",
        json={"import_json_path": export["json_path"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["compact"]["import_export_status"] == STATUS_IMPORTED


def test_gather_export_inputs_lists_missing(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    inputs = gather_export_inputs(storage)
    assert inputs["missing_inputs"]
    assert not inputs["included_reports"]


def test_invalid_import_status_for_non_blocked_validation_issue(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    bad = {
        "schema_version": SCHEMA_VERSION,
        "included_reports": [],
    }
    validation = validate_import_manifest(bad)
    assert validation["import_status"] == STATUS_INVALID
