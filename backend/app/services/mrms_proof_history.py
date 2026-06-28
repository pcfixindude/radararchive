"""Bounded MRMS proof / regression history for dev review API (read-only)."""

from __future__ import annotations

from typing import Any, Optional

from backend.app.services.mrms_proof_regression import (
    load_proof_regression_history,
    load_proof_regression_report,
)
from backend.app.services.mrms_proof_report import (
    MAX_PROOF_HISTORY,
    compact_mrms_proof_report,
    load_mrms_proof_history,
    load_mrms_proof_report,
)
from backend.app.services.mrms_signoff import load_signoffs
from backend.app.services.storage import LocalStorage

MAX_SIGNOFF_LIST = 25


def compact_proof_history_entry(entry: dict[str, Any]) -> dict[str, Any]:
    counts = entry.get("criteria_counts") or {}
    return {
        "generated_at": entry.get("generated_at"),
        "overall_status": entry.get("overall_status", "not_started"),
        "source_mode": entry.get("source_mode"),
        "frame_count": int(entry.get("frame_count", 0)),
        "criteria_counts": {
            "passed": int(counts.get("passed", 0)),
            "failed": int(counts.get("failed", 0)),
            "warning": int(counts.get("warning", 0)),
            "skipped": int(counts.get("skipped", 0)),
            "unknown": int(counts.get("unknown", 0)),
        },
        "operator_review_required": True,
        "verified_mrms": False,
        "proof_only": True,
        "prototype": True,
    }


def compact_regression_history_entry(entry: dict[str, Any]) -> dict[str, Any]:
    status = entry.get("regression_status", "inconclusive")
    count = int(entry.get("regression_count", 0))
    summary = f"{status}"
    if count:
        summary = f"{status} ({count} finding{'s' if count != 1 else ''})"
    return {
        "checked_at": entry.get("checked_at"),
        "regression_status": status,
        "regression_detected": bool(entry.get("regression_detected")),
        "regression_count": count,
        "summary": summary,
        "verified_mrms": False,
        "prototype": True,
    }


def compact_regression_report_entry(report: dict[str, Any]) -> dict[str, Any]:
    findings = report.get("findings") or []
    count = int(report.get("regression_count", len(findings)))
    status = report.get("regression_status", "inconclusive")
    summary = status
    if findings:
        summary = f"{status}: {findings[0].get('message', '')[:120]}"
    elif count:
        summary = f"{status} ({count} findings)"
    return {
        "checked_at": report.get("checked_at"),
        "regression_status": status,
        "regression_detected": bool(report.get("regression_detected")),
        "regression_count": count,
        "summary": summary,
        "current_overall_status": report.get("current_overall_status"),
        "previous_overall_status": report.get("previous_overall_status"),
        "verified_mrms": False,
        "prototype": True,
    }


def compact_signoff_item(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "signoff_id": entry.get("signoff_id"),
        "created_at": entry.get("created_at"),
        "operator_name": entry.get("operator_name"),
        "operator_initials": entry.get("operator_initials"),
        "operator": entry.get("operator_name") or entry.get("operator_initials"),
        "proof_report_timestamp": entry.get("proof_report_timestamp"),
        "frame_count_reviewed": entry.get("frame_count_reviewed", 0),
        "accepted_limitations": entry.get("accepted_limitations"),
        "verified_mrms": False,
        "does_not_set_verified_mrms": True,
        "local_signoff_only": True,
        "prototype": True,
    }


def build_proof_history_payload(storage: LocalStorage) -> dict[str, Any]:
    latest_raw = load_mrms_proof_report(storage)
    entries = [compact_proof_history_entry(item) for item in load_mrms_proof_history(storage)]
    return {
        "prototype": True,
        "verified_mrms": False,
        "proof_only": True,
        "operator_review_required": True,
        "count": len(entries),
        "max_entries": MAX_PROOF_HISTORY,
        "latest": compact_mrms_proof_report(latest_raw),
        "entries": entries,
    }


def build_regression_history_payload(storage: LocalStorage) -> dict[str, Any]:
    latest_raw = load_proof_regression_report(storage)
    entries = [
        compact_regression_history_entry(item) for item in load_proof_regression_history(storage)
    ]
    latest_compact = (
        compact_regression_report_entry(latest_raw) if latest_raw is not None else None
    )
    return {
        "prototype": True,
        "verified_mrms": False,
        "count": len(entries),
        "max_entries": 10,
        "latest": latest_compact,
        "entries": entries,
    }


def build_signoffs_list_payload(
    storage: LocalStorage,
    *,
    limit: Optional[int] = None,
) -> dict[str, Any]:
    bounded = limit if limit is not None else MAX_SIGNOFF_LIST
    bounded = max(1, min(bounded, MAX_SIGNOFF_LIST))
    all_entries = load_signoffs(storage)
    compact = [compact_signoff_item(item) for item in all_entries[:bounded]]
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_signoff_only": True,
        "does_not_set_verified_mrms": True,
        "count": len(all_entries),
        "entries": compact,
    }
