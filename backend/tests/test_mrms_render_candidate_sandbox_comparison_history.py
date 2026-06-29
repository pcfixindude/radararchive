"""Tests for MRMS render candidate sandbox comparison history (Phase 67)."""

from __future__ import annotations

import json

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox import generate_render_candidate_sandbox
from backend.app.services.mrms_render_candidate_sandbox_comparison_history import (
    COMPARISON_CHANGED,
    COMPARISON_HISTORY_JSON,
    COMPARISON_HISTORY_MD,
    COMPARISON_TYPE_CURRENT_VS_IMPORTED,
    COMPARISON_TYPE_EXPORT_VS_PREVIOUS,
    COMPARISON_UNCHANGED,
    HISTORY_BLOCKED,
    HISTORY_MISSING,
    HISTORY_READY,
    SCHEMA_VERSION,
    append_comparison_history_entry,
    build_comparison_history_entry,
    compact_comparison_history,
    evaluate_comparison_history_status,
    load_comparison_history,
    load_comparison_latest,
    record_export_comparison_history,
    record_import_comparison_history,
    refresh_comparison_history_report,
)
from backend.app.services.mrms_render_candidate_sandbox_import_export import (
    EXPORT_DIR,
    export_candidate_sandbox_manifest,
    import_candidate_sandbox_manifest,
)
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert
from backend.app.services.validation_dashboard import build_validation_summary


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def _seed_sandbox(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    generate_render_candidate_sandbox(storage)


def test_comparison_history_missing_when_empty(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    status = evaluate_comparison_history_status(storage)
    assert status["history_status"] == HISTORY_MISSING
    assert status["history_count"] == 0


def test_import_records_comparison_history(storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    history = load_comparison_history(storage)
    assert len(history) >= 1
    assert history[0]["comparison_type"] == COMPARISON_TYPE_CURRENT_VS_IMPORTED
    assert history[0]["schema_version"] == SCHEMA_VERSION
    assert history[0]["verified_mrms"] is False


def test_export_pair_records_comparison_history(storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    tokens = iter(["20260629T010000Z", "20260629T010001Z"])
    monkeypatch.setattr(
        "backend.app.services.mrms_render_candidate_sandbox_import_export._timestamp_token",
        lambda: next(tokens),
    )
    export_candidate_sandbox_manifest(storage)
    export_candidate_sandbox_manifest(storage)
    history = load_comparison_history(storage)
    types = {item["comparison_type"] for item in history}
    assert COMPARISON_TYPE_EXPORT_VS_PREVIOUS in types


def test_comparison_history_json_and_markdown_persistence(storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    refresh_comparison_history_report(storage)
    assert storage.absolute_path(COMPARISON_HISTORY_JSON).is_file()
    assert storage.absolute_path(COMPARISON_HISTORY_MD).is_file()
    latest = load_comparison_latest(storage)
    assert latest is not None
    markdown = storage.absolute_path(COMPARISON_HISTORY_MD).read_text(encoding="utf-8")
    assert "comparison history only" in markdown.lower()


def test_history_ready_after_entries(storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    status = evaluate_comparison_history_status(storage)
    assert status["history_status"] == HISTORY_READY
    assert status["history_count"] >= 1


def test_history_blocked_when_production_enabled(storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    monkeypatch.setattr(settings, "enable_production_radar_tiles", True)
    status = evaluate_comparison_history_status(storage)
    assert status["history_status"] == HISTORY_BLOCKED


def test_append_entry_classifies_unchanged(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    entry = build_comparison_history_entry(
        comparison_type=COMPARISON_TYPE_CURRENT_VS_IMPORTED,
        comparison={"changed_sandbox_status": False, "changed_blockers": [], "changed_warnings": []},
        comparison_status=COMPARISON_UNCHANGED,
        source_paths={"import_json_path": "data/dev/test.json"},
    )
    latest = append_comparison_history_entry(storage, entry)
    assert latest["comparison_status"] == COMPARISON_UNCHANGED


def test_append_entry_classifies_changed(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    entry = build_comparison_history_entry(
        comparison_type=COMPARISON_TYPE_CURRENT_VS_IMPORTED,
        comparison={"changed_sandbox_status": True, "changed_blockers": ["x"]},
        comparison_status=COMPARISON_CHANGED,
        source_paths={"import_json_path": "data/dev/test.json"},
    )
    latest = append_comparison_history_entry(storage, entry)
    assert latest["comparison_status"] == COMPARISON_CHANGED


def test_history_bounded(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    for idx in range(30):
        entry = build_comparison_history_entry(
            comparison_type=COMPARISON_TYPE_CURRENT_VS_IMPORTED,
            comparison={"changed_sandbox_status": bool(idx % 2)},
            comparison_status=COMPARISON_CHANGED,
            source_paths={"import_json_path": f"data/dev/test_{idx}.json"},
        )
        append_comparison_history_entry(storage, entry)
    history = load_comparison_history(storage, limit=50)
    assert len(history) <= 25


def test_record_import_comparison_history_helper(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    import_record = {
        "json_path": "data/dev/mrms_render_candidate_imports/imported.json",
        "imported_from": "data/dev/mrms_render_candidate_exports/export.json",
        "import_export_status": "imported",
        "comparison": {"changed_sandbox_status": False},
    }
    latest = record_import_comparison_history(storage, import_record)
    assert latest is not None
    assert latest["comparison_type"] == COMPARISON_TYPE_CURRENT_VS_IMPORTED


def test_safety_invariants(storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    compact = compact_comparison_history(storage)
    assert compact["verified_mrms"] is False
    assert compact["does_not_enable_production"] is True
    assert compact["does_not_download_or_decode"] is True
    assert compact["does_not_create_production_tiles"] is True
    assert compact["does_not_serve_production_tiles"] is True
    assert compact["does_not_clear_alerts"] is True
    assert compact["binary_artifacts_included"] is False


def test_comparison_history_does_not_clear_alerts(storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    save_validation_alert(storage, {"level": ALERT_FAILED, "reason": "test"})
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    alert = load_validation_alert(storage)
    assert alert is not None
    assert alert["level"] == ALERT_FAILED


def test_summary_includes_comparison_history_compact(db_session, storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    summary = build_validation_summary(db_session, storage)
    compact = summary["mrms_render_candidate_sandbox_comparison_history"]
    assert compact["history_status"] == HISTORY_READY
    assert compact["verified_mrms"] is False


def test_comparison_history_get_endpoint(client, storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    response = client.get("/api/validation/mrms-render-candidate/sandbox/import-export/comparison-history")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["compact"]["history_count"] >= 1


def test_comparison_history_post_endpoint(client, storage, monkeypatch):
    _seed_sandbox(storage, monkeypatch)
    export = export_candidate_sandbox_manifest(storage)
    import_candidate_sandbox_manifest(storage, source_json_path=export["json_path"])
    response = client.post("/api/validation/mrms-render-candidate/sandbox/import-export/comparison-history")
    assert response.status_code == 200
    assert storage.absolute_path(COMPARISON_HISTORY_MD).is_file()


def test_record_export_comparison_requires_two_exports(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    assert record_export_comparison_history(storage) is None
    sandbox_manifest = {"sandbox_status": "ready", "verified_mrms": False}
    path = storage.normalize_path(EXPORT_DIR, "candidate_sandbox_export_one.json")
    storage.ensure_directories(EXPORT_DIR)
    storage.absolute_path(path).write_text(
        json.dumps({"included_reports": [{"kind": "sandbox_manifest", "content": sandbox_manifest}]}),
        encoding="utf-8",
    )
    assert record_export_comparison_history(storage) is None
