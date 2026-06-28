"""Compare local MRMS proof bundles — does NOT verify MRMS or enable production."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_proof_bundle import (
    load_latest_proof_bundle_manifest,
    load_proof_bundle_index,
)
from backend.app.services.storage import LocalStorage

DIFF_LATEST_PATH = "dev/mrms_proof_bundle_diff_latest.json"
DIFF_HISTORY_PATH = "dev/mrms_proof_bundle_diff_history.json"
MAX_DIFF_HISTORY = 10

DIFF_NO_BASELINE = "no_baseline"
DIFF_UNCHANGED = "unchanged"
DIFF_IMPROVED = "improved"
DIFF_WORSENED = "worsened"
DIFF_MIXED = "mixed"
DIFF_UNKNOWN = "unknown"

DIFF_ATTENTION_STATUSES = frozenset({DIFF_WORSENED, DIFF_MIXED})

ALERT_RANK = {"ok": 0, "warning": 1, "failed": 2}
PROOF_RANK = {
    "passed": 4,
    "ready_for_operator_review": 3,
    "insufficient_evidence": 2,
    "failed": 1,
    "not_started": 0,
}


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json_file(path: Path) -> Optional[dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _bundle_dir_from_repo_path(storage: LocalStorage, bundle_folder: str) -> Path:
    rel = bundle_folder.removeprefix("data/").lstrip("/")
    return storage.absolute_path(rel)


def load_bundle_manifest(storage: LocalStorage, bundle_folder: str) -> Optional[dict[str, Any]]:
    bundle_dir = _bundle_dir_from_repo_path(storage, bundle_folder)
    return _load_json_file(bundle_dir / "manifest.json")


def _load_bundle_evidence(storage: LocalStorage, bundle_folder: str, evidence_rel: str) -> Optional[dict[str, Any]]:
    bundle_dir = _bundle_dir_from_repo_path(storage, bundle_folder)
    return _load_json_file(bundle_dir / evidence_rel)


def _bundle_ref(manifest: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if manifest is None:
        return None
    return {
        "bundle_id": manifest.get("bundle_id"),
        "created_at": manifest.get("created_at"),
        "bundle_folder": manifest.get("bundle_folder"),
        "archive_name": manifest.get("archive_name"),
        "file_count": manifest.get("file_count"),
    }


def _signoff_count(evidence: Optional[dict[str, Any]]) -> int:
    if evidence is None:
        return 0
    if "count" in evidence:
        return int(evidence.get("count", 0))
    if "entries" in evidence and isinstance(evidence["entries"], list):
        return len(evidence["entries"])
    if isinstance(evidence, list):
        return len(evidence)
    return 0


def _extract_signoff_evidence(storage: LocalStorage, bundle_folder: str) -> Optional[dict[str, Any]]:
    for rel in ("evidence/mrms_signoffs_compact.json", "evidence/mrms_signoffs.json"):
        data = _load_bundle_evidence(storage, bundle_folder, rel)
        if data is not None:
            return data
    return None


def _file_set_changes(
    baseline_files: set[str],
    current_files: set[str],
    baseline_missing: set[str],
    current_missing: set[str],
) -> dict[str, Any]:
    return {
        "files_added": sorted(current_files - baseline_files),
        "files_removed": sorted(baseline_files - current_files),
        "missing_added": sorted(current_missing - baseline_missing),
        "missing_removed": sorted(baseline_missing - current_missing),
    }


def _classify_overall_status(signals: list[int]) -> str:
    if not signals:
        return DIFF_UNKNOWN
    positives = sum(1 for value in signals if value > 0)
    negatives = sum(1 for value in signals if value < 0)
    if positives == 0 and negatives == 0:
        return DIFF_UNCHANGED
    if positives > 0 and negatives == 0:
        return DIFF_IMPROVED
    if negatives > 0 and positives == 0:
        return DIFF_WORSENED
    return DIFF_MIXED


def build_proof_bundle_diff_report(
    storage: LocalStorage,
    *,
    current_bundle_folder: Optional[str] = None,
    baseline_bundle_folder: Optional[str] = None,
) -> dict[str, Any]:
    """Compare two proof bundle manifests/evidence; persist latest diff report."""
    warnings: list[str] = []
    errors: list[str] = []

    if current_bundle_folder is None:
        latest = load_latest_proof_bundle_manifest(storage)
        current_bundle_folder = (latest or {}).get("bundle_folder")
        current_manifest = latest
    else:
        current_manifest = load_bundle_manifest(storage, current_bundle_folder)

    if baseline_bundle_folder is None:
        index = load_proof_bundle_index(storage)
        baseline_bundle_folder = None
        if len(index) >= 2:
            baseline_bundle_folder = index[1].get("bundle_folder")
        baseline_manifest = (
            load_bundle_manifest(storage, baseline_bundle_folder) if baseline_bundle_folder else None
        )
    else:
        baseline_manifest = load_bundle_manifest(storage, baseline_bundle_folder)

    if not current_bundle_folder or current_manifest is None:
        report = _base_diff_report(
            overall_diff_status=DIFF_UNKNOWN,
            current_manifest=current_manifest,
            baseline_manifest=baseline_manifest,
            warnings=["Current bundle manifest not found — run make mrms-proof-bundle first."],
        )
        return _persist_diff_report(storage, report)

    if not baseline_bundle_folder or baseline_manifest is None:
        report = _base_diff_report(
            overall_diff_status=DIFF_NO_BASELINE,
            current_manifest=current_manifest,
            baseline_manifest=None,
            warnings=[
                "No baseline bundle available — export at least two bundles "
                "(run make mrms-proof-bundle twice) before diffing."
            ],
        )
        return _persist_diff_report(storage, report)

    baseline_proof = _load_bundle_evidence(storage, baseline_bundle_folder, "evidence/mrms_proof_latest.json")
    current_proof = _load_bundle_evidence(storage, current_bundle_folder, "evidence/mrms_proof_latest.json")
    baseline_regression = _load_bundle_evidence(
        storage, baseline_bundle_folder, "evidence/mrms_proof_regression_latest.json"
    )
    current_regression = _load_bundle_evidence(
        storage, current_bundle_folder, "evidence/mrms_proof_regression_latest.json"
    )
    baseline_signoffs = _extract_signoff_evidence(storage, baseline_bundle_folder)
    current_signoffs = _extract_signoff_evidence(storage, current_bundle_folder)
    baseline_alert = _load_bundle_evidence(storage, baseline_bundle_folder, "evidence/validation_alert_latest.json")
    current_alert = _load_bundle_evidence(storage, current_bundle_folder, "evidence/validation_alert_latest.json")
    baseline_catalog = _load_bundle_evidence(storage, baseline_bundle_folder, "evidence/catalog_status.json")
    current_catalog = _load_bundle_evidence(storage, current_bundle_folder, "evidence/catalog_status.json")
    baseline_queue = _load_bundle_evidence(storage, baseline_bundle_folder, "evidence/render_queue_status.json")
    current_queue = _load_bundle_evidence(storage, current_bundle_folder, "evidence/render_queue_status.json")

    baseline_files = set(baseline_manifest.get("files_included") or [])
    current_files = set(current_manifest.get("files_included") or [])
    baseline_missing = set(baseline_manifest.get("files_missing") or [])
    current_missing = set(current_manifest.get("files_missing") or [])
    file_changes = _file_set_changes(baseline_files, current_files, baseline_missing, current_missing)

    baseline_status = (baseline_proof or {}).get("overall_status", "not_started")
    current_status = (current_proof or {}).get("overall_status", "not_started")
    proof_status_change = {
        "from": baseline_status,
        "to": current_status,
        "changed": baseline_status != current_status,
    }

    baseline_counts = (baseline_proof or {}).get("criteria_counts") or {}
    current_counts = (current_proof or {}).get("criteria_counts") or {}
    criteria_count_change = {
        "passed_delta": int(current_counts.get("passed", 0)) - int(baseline_counts.get("passed", 0)),
        "failed_delta": int(current_counts.get("failed", 0)) - int(baseline_counts.get("failed", 0)),
        "warning_delta": int(current_counts.get("warning", 0)) - int(baseline_counts.get("warning", 0)),
        "skipped_delta": int(current_counts.get("skipped", 0)) - int(baseline_counts.get("skipped", 0)),
        "baseline": baseline_counts,
        "current": current_counts,
    }

    baseline_regression_detected = bool((baseline_regression or {}).get("regression_detected"))
    current_regression_detected = bool((current_regression or {}).get("regression_detected"))
    regression_change = {
        "from_status": (baseline_regression or {}).get("regression_status"),
        "to_status": (current_regression or {}).get("regression_status"),
        "from_detected": baseline_regression_detected,
        "to_detected": current_regression_detected,
        "changed": baseline_regression_detected != current_regression_detected
        or (baseline_regression or {}).get("regression_status")
        != (current_regression or {}).get("regression_status"),
    }

    baseline_signoff_count = _signoff_count(baseline_signoffs)
    current_signoff_count = _signoff_count(current_signoffs)
    signoff_count_change = {
        "from": baseline_signoff_count,
        "to": current_signoff_count,
        "delta": current_signoff_count - baseline_signoff_count,
    }

    baseline_alert_status = (baseline_alert or {}).get("status", "ok")
    current_alert_status = (current_alert or {}).get("status", "ok")
    alert_status_change = {
        "from": baseline_alert_status,
        "to": current_alert_status,
        "changed": baseline_alert_status != current_alert_status,
    }

    catalog_change = {
        "total_frames_delta": int((current_catalog or {}).get("total_frames", 0))
        - int((baseline_catalog or {}).get("total_frames", 0)),
        "mrms_discovered_frames_delta": int((current_catalog or {}).get("mrms_discovered_frames", 0))
        - int((baseline_catalog or {}).get("mrms_discovered_frames", 0)),
    }

    queue_change = {
        "succeeded_delta": int((current_queue or {}).get("succeeded", 0))
        - int((baseline_queue or {}).get("succeeded", 0)),
        "failed_delta": int((current_queue or {}).get("failed", 0))
        - int((baseline_queue or {}).get("failed", 0)),
        "queued_delta": int((current_queue or {}).get("queued", 0))
        - int((baseline_queue or {}).get("queued", 0)),
    }

    signals: list[int] = []
    if baseline_proof and current_proof:
        signals.append(PROOF_RANK.get(current_status, 0) - PROOF_RANK.get(baseline_status, 0))
    else:
        warnings.append("Proof evidence missing in one or both bundles — proof status diff may be incomplete.")

    if baseline_proof and current_proof:
        signals.append(-criteria_count_change["failed_delta"])
        signals.append(criteria_count_change["passed_delta"])

    if baseline_regression and current_regression:
        if baseline_regression_detected and not current_regression_detected:
            signals.append(2)
        elif current_regression_detected and not baseline_regression_detected:
            signals.append(-2)

    if baseline_alert and current_alert:
        signals.append(ALERT_RANK.get(baseline_alert_status, 1) - ALERT_RANK.get(current_alert_status, 1))

    evidence_changes_count = sum(
        1
        for changed in (
            proof_status_change["changed"],
            regression_change["changed"],
            alert_status_change["changed"],
            signoff_count_change["delta"] != 0,
            catalog_change["total_frames_delta"] != 0,
            queue_change["succeeded_delta"] != 0,
            queue_change["failed_delta"] != 0,
            bool(file_changes["files_added"]),
            bool(file_changes["files_removed"]),
        )
        if changed
    )

    overall = _classify_overall_status(signals)
    if overall == DIFF_UNKNOWN and baseline_manifest and current_manifest:
        if evidence_changes_count == 0 and not file_changes["files_added"] and not file_changes["files_removed"]:
            overall = DIFF_UNCHANGED

    report = _base_diff_report(
        overall_diff_status=overall,
        current_manifest=current_manifest,
        baseline_manifest=baseline_manifest,
        warnings=warnings,
        errors=errors,
    )
    report.update(
        {
            "file_changes": file_changes,
            "proof_status_change": proof_status_change,
            "criteria_count_change": criteria_count_change,
            "regression_change": regression_change,
            "signoff_count_change": signoff_count_change,
            "alert_status_change": alert_status_change,
            "catalog_change": catalog_change,
            "queue_change": queue_change,
            "evidence_changes_count": evidence_changes_count,
        }
    )
    return _persist_diff_report(storage, report)


def _base_diff_report(
    *,
    overall_diff_status: str,
    current_manifest: Optional[dict[str, Any]],
    baseline_manifest: Optional[dict[str, Any]],
    warnings: Optional[list[str]] = None,
    errors: Optional[list[str]] = None,
) -> dict[str, Any]:
    return {
        "diff_id": str(uuid.uuid4()),
        "checked_at": _utc_now(),
        "overall_diff_status": overall_diff_status,
        "current_bundle": _bundle_ref(current_manifest),
        "baseline_bundle": _bundle_ref(baseline_manifest),
        "file_changes": {
            "files_added": [],
            "files_removed": [],
            "missing_added": [],
            "missing_removed": [],
        },
        "proof_status_change": {"from": None, "to": None, "changed": False},
        "criteria_count_change": {
            "passed_delta": 0,
            "failed_delta": 0,
            "warning_delta": 0,
            "skipped_delta": 0,
            "baseline": {},
            "current": {},
        },
        "regression_change": {
            "from_status": None,
            "to_status": None,
            "from_detected": False,
            "to_detected": False,
            "changed": False,
        },
        "signoff_count_change": {"from": 0, "to": 0, "delta": 0},
        "alert_status_change": {"from": None, "to": None, "changed": False},
        "catalog_change": {"total_frames_delta": 0, "mrms_discovered_frames_delta": 0},
        "queue_change": {"succeeded_delta": 0, "failed_delta": 0, "queued_delta": 0},
        "evidence_changes_count": 0,
        "warnings": warnings or [],
        "errors": errors or [],
        "verified_mrms": False,
        "proof_only": True,
        "local_diff_only": True,
        "does_not_enable_production": True,
        "production_rendering_enabled": settings.enable_production_radar_tiles,
        "placeholder_default": not settings.enable_production_radar_tiles
        and not settings.enable_decoded_tiles,
        "prototype": True,
    }


def _persist_diff_report(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
    latest_path = storage.normalize_path(DIFF_LATEST_PATH)
    storage.ensure_directories(latest_path.rsplit("/", 1)[0])
    storage.absolute_path(latest_path).write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    history_path = storage.normalize_path(DIFF_HISTORY_PATH)
    abs_history = storage.absolute_path(history_path)
    entries: list[dict[str, Any]] = []
    if abs_history.is_file():
        try:
            data = json.loads(abs_history.read_text(encoding="utf-8"))
            if isinstance(data, list):
                entries = data
        except (json.JSONDecodeError, OSError):
            entries = []
    entries.insert(0, compact_proof_bundle_diff(report))
    abs_history.write_text(
        json.dumps(entries[:MAX_DIFF_HISTORY], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


def load_latest_proof_bundle_diff(storage: LocalStorage) -> Optional[dict[str, Any]]:
    repo_path = storage.normalize_path(DIFF_LATEST_PATH)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return None
    try:
        return json.loads(abs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def compact_proof_bundle_diff(report: Optional[dict[str, Any]]) -> dict[str, Any]:
    if report is None:
        return {
            "available": False,
            "overall_diff_status": DIFF_UNKNOWN,
            "evidence_changes_count": 0,
            "verified_mrms": False,
            "local_diff_only": True,
            "proof_only": True,
            "does_not_enable_production": True,
            "prototype": True,
        }
    return {
        "available": True,
        "diff_id": report.get("diff_id"),
        "checked_at": report.get("checked_at"),
        "overall_diff_status": report.get("overall_diff_status", DIFF_UNKNOWN),
        "evidence_changes_count": int(report.get("evidence_changes_count", 0)),
        "current_bundle_id": (report.get("current_bundle") or {}).get("bundle_id"),
        "baseline_bundle_id": (report.get("baseline_bundle") or {}).get("bundle_id"),
        "verified_mrms": False,
        "local_diff_only": True,
        "proof_only": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def proof_bundle_diff_requires_attention(diff_status: Optional[str]) -> bool:
    return str(diff_status or "") in DIFF_ATTENTION_STATUSES


def compact_scheduled_proof_bundle(scheduled: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Compact proof bundle export/diff status from a scheduled validation report."""
    if scheduled is None:
        return None
    bundle = scheduled.get("mrms_proof_bundle")
    diff = scheduled.get("mrms_proof_bundle_diff")
    diff_status = (diff or {}).get("overall_diff_status")
    attention = proof_bundle_diff_requires_attention(diff_status)
    return {
        "bundle_exported": bundle is not None,
        "bundle_id": (bundle or {}).get("bundle_id"),
        "bundle_created_at": (bundle or {}).get("created_at"),
        "diff_ran": diff is not None,
        "diff_status": diff_status,
        "evidence_changes_count": int((diff or {}).get("evidence_changes_count", 0)),
        "operator_attention_needed": attention,
        "verified_mrms": False,
        "local_evidence_monitoring_only": True,
        "prototype": True,
    }


def compact_proof_bundle_diff_status(storage: LocalStorage) -> dict[str, Any]:
    report = load_latest_proof_bundle_diff(storage)
    status = compact_proof_bundle_diff(report)
    status["has_baseline"] = report is not None and report.get("overall_diff_status") != DIFF_NO_BASELINE
    return status
