"""Tests for validation remediation (Phase 102)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight import (
    PREFLIGHT_CANDIDATE_READY,
    PREFLIGHT_NEEDS_REVIEW,
    evaluate_render_candidate_preflight,
    gather_preflight_evidence,
    generate_render_candidate_preflight,
)
from backend.app.services.mrms_render_candidate_preflight_attention import (
    resolve_preflight_operator_attention,
    save_preflight_attention_report,
)
from backend.app.services.mrms_render_candidate_validation_remediation import (
    CLASS_STUB_EXPECTED,
    REMEDIATION_JSON,
    REMEDIATION_STUB_DOCUMENTED,
    SUGGESTED_COMMAND,
    analyze_proof_report_failures,
    analyze_validation_alert_failures,
    compact_validation_remediation,
    load_validation_remediation_report,
    remediate_validation_failures,
    save_validation_remediation_report,
    stub_mode_documented_for_preflight,
)
from backend.app.services.operator_review_status import STATUS_OK, STATUS_URGENT, build_operator_review_status
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def _stub_alert(storage):
    save_validation_alert(
        storage,
        {
            "status": ALERT_FAILED,
            "operator_attention_needed": True,
            "failure_count": 100,
            "warning_count": 0,
            "verified_mrms": False,
            "grouped_failure_causes": [
                {
                    "step": "batch_validation",
                    "cause": "no_grib2_artifact",
                    "message": "Stub/offline mode: stub downloads are not real GRIB2",
                    "count": 10,
                },
                {
                    "step": "queue_benchmark",
                    "cause": "unknown",
                    "message": "Queue benchmark is experimental prototype tooling",
                    "count": 5,
                },
            ],
        },
    )


def _stub_proof(storage):
    path = storage.normalize_path("dev/mrms_proof_latest.json")
    storage.ensure_directories(path.rsplit("/", 1)[0])
    storage.absolute_path(path).write_text(
        """
        {
          "overall_status": "failed",
          "aggregate_criteria": [
            {"criterion_id": "real_noaa_source", "status": "failed", "message": "stub placeholder"},
            {"criterion_id": "decoder_and_artifacts", "status": "failed", "message": "no decode artifacts"},
            {"criterion_id": "failure_alert_hygiene", "status": "failed", "message": "validation alert status failed"}
          ]
        }
        """,
        encoding="utf-8",
    )


def test_analyze_stub_failures(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    _stub_alert(storage)
    validation = analyze_validation_alert_failures(storage)
    assert validation
    assert all(item["failure_class"] == CLASS_STUB_EXPECTED for item in validation)


def test_remediate_documents_stub_without_clearing_alert(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    _stub_alert(storage)
    _stub_proof(storage)
    report = save_validation_remediation_report(
        storage,
        remediate_validation_failures(storage, refresh=True),
    )
    assert report["remediation_status"] == REMEDIATION_STUB_DOCUMENTED
    assert report["blocks_preflight"] is False
    assert report["validation_alert_unchanged"] is True
    assert load_validation_alert(storage).get("status") == ALERT_FAILED
    assert storage.absolute_path(REMEDIATION_JSON).is_file()


def test_operator_status_improves_after_stub_remediation(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    _stub_alert(storage)
    _stub_proof(storage)
    before = build_operator_review_status(storage)
    assert before["status_level"] == STATUS_URGENT
    save_validation_remediation_report(
        storage,
        remediate_validation_failures(storage, refresh=True),
    )
    after = build_operator_review_status(storage)
    assert after["status_level"] == STATUS_OK
    assert after["status_reason"] == "stub_mode_validation_documented"


def test_attention_and_preflight_after_remediation(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    _stub_alert(storage)
    _stub_proof(storage)
    from backend.tests.test_mrms_render_candidate_preflight import _seed_candidate_ready_chain

    _seed_candidate_ready_chain(storage, monkeypatch)
    save_validation_remediation_report(
        storage,
        remediate_validation_failures(storage, refresh=True),
    )
    attention = save_preflight_attention_report(
        storage,
        resolve_preflight_operator_attention(storage, refresh=True),
    )
    assert attention["blocks_preflight"] is False
    assert stub_mode_documented_for_preflight(storage)
    report = generate_render_candidate_preflight(storage)
    assert report["preflight_level"] == PREFLIGHT_CANDIDATE_READY


def test_compact_before_remediation(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_validation_remediation(storage)
    assert compact["available"] is False
    assert compact["suggested_command"] == SUGGESTED_COMMAND


def test_stub_documented_requires_saved_report(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    _stub_alert(storage)
    _stub_proof(storage)
    assert stub_mode_documented_for_preflight(storage) is False
    save_validation_remediation_report(
        storage,
        remediate_validation_failures(storage, refresh=True),
    )
    assert stub_mode_documented_for_preflight(storage) is True
