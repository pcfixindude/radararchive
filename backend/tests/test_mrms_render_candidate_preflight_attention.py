"""Tests for preflight operator attention resolution (Phase 101)."""

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
    ATTENTION_JSON,
    STATUS_BLOCKED,
    STATUS_RESOLVED,
    SUGGESTED_COMMAND,
    TYPE_HUMAN_JUDGMENT,
    compact_preflight_attention,
    gather_operator_attention_inventory,
    load_preflight_attention_report,
    resolve_preflight_operator_attention,
    save_preflight_attention_report,
)
from backend.app.services.mrms_render_candidate_validation_remediation import (
    REMEDIATION_STUB_DOCUMENTED,
    remediate_validation_failures,
    save_validation_remediation_report,
)
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert, save_validation_alert


def _use_test_storage(monkeypatch, storage):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "enable_decoded_tiles", False)


def test_inventory_identifies_validation_alert_attention(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(
        storage,
        {
            "status": ALERT_FAILED,
            "operator_attention_needed": True,
            "failure_count": 2,
            "verified_mrms": False,
        },
    )
    inventory = gather_operator_attention_inventory(storage)
    texts = [item["text"] for item in inventory]
    assert any("validation alert" in text.lower() for text in texts)
    blocking = [item for item in inventory if item.get("blocks_preflight")]
    assert blocking
    assert blocking[0]["resolution_type"] == TYPE_HUMAN_JUDGMENT


def test_resolve_keeps_human_judgment_open(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(
        storage,
        {
            "status": ALERT_FAILED,
            "operator_attention_needed": True,
            "failure_count": 2,
            "verified_mrms": False,
        },
    )
    report = save_preflight_attention_report(
        storage,
        resolve_preflight_operator_attention(storage, refresh=True),
    )
    assert report["resolution_status"] == STATUS_BLOCKED
    assert report["blocks_preflight"] is True
    assert report["validation_alert_unchanged"] is True
    assert load_validation_alert(storage).get("status") == ALERT_FAILED
    assert storage.absolute_path(ATTENTION_JSON).is_file()


def test_preflight_skips_operator_warn_when_attention_resolved(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    save_validation_alert(
        storage,
        {
            "status": ALERT_FAILED,
            "operator_attention_needed": True,
            "failure_count": 2,
            "verified_mrms": False,
        },
    )
    save_preflight_attention_report(
        storage,
        {
            **resolve_preflight_operator_attention(storage, refresh=False),
            "blocks_preflight": False,
            "resolution_status": STATUS_RESOLVED,
            "open_attention_items": [],
            "open_blocking_items": [],
        },
    )
    save_validation_remediation_report(
        storage,
        {
            **remediate_validation_failures(storage, refresh=False),
            "blocks_preflight": False,
            "stub_mode_documented": True,
            "remediation_status": REMEDIATION_STUB_DOCUMENTED,
        },
    )
    evidence = gather_preflight_evidence(storage)
    report = evaluate_render_candidate_preflight(evidence)
    operator_checks = [
        check for check in report["checks"] if check["id"] == "operator_review_status_clear"
    ]
    assert not operator_checks


def test_resolve_persists_report(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    report = save_preflight_attention_report(
        storage,
        resolve_preflight_operator_attention(storage, refresh=True),
    )
    loaded = load_preflight_attention_report(storage)
    assert loaded is not None
    assert loaded["resolution_status"] == report["resolution_status"]


def test_compact_before_resolve(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    compact = compact_preflight_attention(storage)
    assert compact["available"] is False
    assert compact["suggested_command"] == SUGGESTED_COMMAND


def test_preflight_still_needs_review_when_attention_blocks(storage, monkeypatch):
    _use_test_storage(monkeypatch, storage)
    from backend.tests.test_mrms_render_candidate_preflight import _seed_candidate_ready_chain

    _seed_candidate_ready_chain(storage, monkeypatch)
    save_validation_alert(
        storage,
        {
            "status": ALERT_FAILED,
            "operator_attention_needed": True,
            "failure_count": 2,
            "verified_mrms": False,
        },
    )
    save_preflight_attention_report(
        storage,
        resolve_preflight_operator_attention(storage, refresh=True),
    )
    report = generate_render_candidate_preflight(storage)
    assert report["preflight_level"] in {PREFLIGHT_NEEDS_REVIEW, PREFLIGHT_CANDIDATE_READY}
    if report["preflight_level"] == PREFLIGHT_NEEDS_REVIEW:
        assert any(
            "operator review" in warning.lower() or "wgrib2" in warning.lower()
            for warning in report.get("warnings") or []
        )
