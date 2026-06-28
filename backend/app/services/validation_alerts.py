"""Local validation alert markers and grouped failure diagnostics (dev/prototype only)."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_failure_log import (
    load_all_validation_failures,
    load_recent_validation_failures,
)
from backend.app.services.validation_report_store import load_latest_scheduled_validation_report

VALIDATION_ALERT_PATH = "dev/validation_alert_latest.json"

ALERT_OK = "ok"
ALERT_WARNING = "warning"
ALERT_FAILED = "failed"

CAUSE_NO_NETWORK = "no_network"
CAUSE_DECODER_UNAVAILABLE = "decoder_unavailable"
CAUSE_NO_GRIB2_ARTIFACT = "no_grib2_artifact"
CAUSE_ZERO_TILES_WRITTEN = "zero_tiles_written"
CAUSE_PRODUCTION_FLAG_OFF = "production_flag_off"
CAUSE_CATALOG_GATE_MISSING = "catalog_gate_missing"
CAUSE_UNKNOWN = "unknown"

SUGGESTED_ACTIONS: dict[str, str] = {
    CAUSE_NO_NETWORK: "Check network connectivity; use stub mode offline or retry with --real when intentional.",
    CAUSE_DECODER_UNAVAILABLE: "Install optional decoder (wgrib2/GDAL/rasterio) or expect decode to be skipped in stub mode.",
    CAUSE_NO_GRIB2_ARTIFACT: "Download real .grib2.gz (MRMS_SOURCE_MODE=real) and run make decode-grib2.",
    CAUSE_ZERO_TILES_WRITTEN: "Ensure decode artifacts exist; lower zoom/count; prototype tiles may be zero in stub mode.",
    CAUSE_PRODUCTION_FLAG_OFF: "Production serving is off by default; set ENABLE_PRODUCTION_RADAR_TILES only when intentional.",
    CAUSE_CATALOG_GATE_MISSING: "Build production tiles and satisfy catalog gate before expecting production-prototype tiles.",
    CAUSE_UNKNOWN: "Review make validation-failures and docs/RUNBOOK_REAL_MRMS_VALIDATION.md.",
}


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _alert_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(VALIDATION_ALERT_PATH)


def classify_failure_cause(message: Optional[str]) -> str:
    """Map a failure/warning message to a coarse cause bucket."""
    if not message:
        return CAUSE_UNKNOWN
    text = message.lower()
    if any(token in text for token in ("network", "connection", "unreachable", "timeout", "503")):
        return CAUSE_NO_NETWORK
    if any(
        token in text
        for token in (
            "decoder",
            "wgrib2",
            "gdal",
            "rasterio",
            "no optional decoder",
            "decoder unavailable",
        )
    ):
        return CAUSE_DECODER_UNAVAILABLE
    if any(
        token in text
        for token in (
            "grib2",
            "inspectable",
            "no decode artifact",
            "not_decoded",
            "not real grib2",
            "no inspectable",
        )
    ):
        return CAUSE_NO_GRIB2_ARTIFACT
    if any(
        token in text
        for token in (
            "0 tiles",
            "zero tiles",
            "tiles_written=0",
            "write 0 tiles",
            "likely write 0 tiles",
        )
    ):
        return CAUSE_ZERO_TILES_WRITTEN
    if any(
        token in text
        for token in (
            "enable_production_radar_tiles",
            "production tile serving",
            "production rendering remains disabled",
            "production rendering enabled: false",
        )
    ):
        return CAUSE_PRODUCTION_FLAG_OFF
    if "catalog gate" in text or "catalog_gate" in text:
        return CAUSE_CATALOG_GATE_MISSING
    return CAUSE_UNKNOWN


def normalize_cause_message(message: Optional[str]) -> str:
    """Normalize message text for grouping repeated causes."""
    if not message:
        return "unknown"
    text = message.strip().lower()
    text = re.sub(r"\d+", "N", text)
    text = re.sub(r"\s+", " ", text)
    return text[:160]


def _entry_messages(entry: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    if entry.get("error_message"):
        messages.append(str(entry["error_message"]))
    for warning in entry.get("warnings") or []:
        messages.append(str(warning))
    for error in entry.get("errors") or []:
        messages.append(str(error))
    return messages


def group_validation_failures(
    entries: list[dict[str, Any]],
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Group failures by step and normalized cause."""
    buckets: dict[tuple[str, str, str], dict[str, Any]] = {}
    for entry in entries:
        step = str(entry.get("step") or entry.get("phase") or "unknown")
        for message in _entry_messages(entry):
            cause = classify_failure_cause(message)
            normalized = normalize_cause_message(message)
            key = (step, cause, normalized)
            bucket = buckets.get(key)
            logged_at = entry.get("logged_at")
            if bucket is None:
                buckets[key] = {
                    "step": step,
                    "cause": cause,
                    "message": message[:200],
                    "normalized_message": normalized,
                    "count": 1,
                    "latest_logged_at": logged_at,
                }
            else:
                bucket["count"] += 1
                if logged_at and (
                    not bucket.get("latest_logged_at")
                    or str(logged_at) > str(bucket["latest_logged_at"])
                ):
                    bucket["latest_logged_at"] = logged_at
    grouped = sorted(
        buckets.values(),
        key=lambda item: (item.get("latest_logged_at") or "", item.get("count", 0)),
        reverse=True,
    )
    return grouped[:limit]


def _count_warning_vs_failure_entries(entries: list[dict[str, Any]]) -> tuple[int, int]:
    failure_count = 0
    warning_count = 0
    for entry in entries:
        has_error = bool(entry.get("error_message") or entry.get("errors"))
        has_warning = bool(entry.get("warnings"))
        if has_error:
            failure_count += 1
        elif has_warning:
            warning_count += 1
    return failure_count, warning_count


def _resolve_alert_status(
    *,
    scheduled: Optional[dict[str, Any]],
    failure_count: int,
    warning_count: int,
) -> str:
    if scheduled is not None:
        if not scheduled.get("success", True) or scheduled.get("exit_code", 0) != 0:
            return ALERT_FAILED
        steps = scheduled.get("steps") or []
        if any(step.get("status") == "failed" for step in steps):
            return ALERT_FAILED
        if scheduled.get("errors"):
            return ALERT_FAILED
    if failure_count > 0:
        return ALERT_FAILED
    if warning_count > 0:
        return ALERT_WARNING
    if scheduled is not None:
        steps = scheduled.get("steps") or []
        if any(step.get("status") == "warning" for step in steps):
            return ALERT_WARNING
        if scheduled.get("warnings"):
            return ALERT_WARNING
    return ALERT_OK


def _suggested_action(grouped_causes: list[dict[str, Any]], status: str) -> str:
    if status == ALERT_OK:
        return "No operator attention needed; continue stub validation or run real smoke test when ready."
    if not grouped_causes:
        return SUGGESTED_ACTIONS[CAUSE_UNKNOWN]
    top_cause = grouped_causes[0].get("cause", CAUSE_UNKNOWN)
    return SUGGESTED_ACTIONS.get(str(top_cause), SUGGESTED_ACTIONS[CAUSE_UNKNOWN])


def build_validation_alert(
    storage: LocalStorage,
    *,
    scheduled: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build alert summary from failure log and latest scheduled run."""
    all_failures = load_all_validation_failures(storage)
    recent = load_recent_validation_failures(storage, limit=25)
    scheduled = scheduled if scheduled is not None else load_latest_scheduled_validation_report(storage)

    log_failure_count, log_warning_count = _count_warning_vs_failure_entries(all_failures)
    grouped = group_validation_failures(all_failures)
    status = _resolve_alert_status(
        scheduled=scheduled,
        failure_count=log_failure_count,
        warning_count=log_warning_count,
    )

    latest_run_at = None
    if scheduled:
        latest_run_at = scheduled.get("ran_at")
    elif recent:
        latest_run_at = recent[0].get("logged_at")

    return {
        "status": status,
        "latest_run_at": latest_run_at,
        "updated_at": _utc_now(),
        "failure_count": log_failure_count,
        "warning_count": log_warning_count,
        "total_logged": len(all_failures),
        "grouped_failure_causes": grouped,
        "suggested_next_action": _suggested_action(grouped, status),
        "operator_attention_needed": status in (ALERT_WARNING, ALERT_FAILED),
        "production_rendering_enabled": settings.enable_production_radar_tiles,
        "verified_mrms": False,
        "prototype": True,
    }


def save_validation_alert(storage: LocalStorage, alert: dict[str, Any]) -> str:
    record = dict(alert)
    record.setdefault("updated_at", _utc_now())
    record.setdefault("verified_mrms", False)
    record.setdefault("prototype", True)
    repo_path = _alert_repo_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(record, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return repo_path


def load_validation_alert(storage: LocalStorage) -> Optional[dict[str, Any]]:
    repo_path = _alert_repo_path(storage)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return None
    try:
        return json.loads(abs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def refresh_validation_alert(
    storage: LocalStorage,
    *,
    scheduled: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Rebuild and persist latest validation alert marker."""
    alert = build_validation_alert(storage, scheduled=scheduled)
    save_validation_alert(storage, alert)
    return alert


def compact_validation_alert(alert: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if alert is None:
        return None
    grouped = alert.get("grouped_failure_causes") or []
    return {
        "status": alert.get("status", ALERT_OK),
        "latest_run_at": alert.get("latest_run_at"),
        "updated_at": alert.get("updated_at"),
        "failure_count": alert.get("failure_count", 0),
        "warning_count": alert.get("warning_count", 0),
        "operator_attention_needed": alert.get("operator_attention_needed", False),
        "suggested_next_action": alert.get("suggested_next_action"),
        "grouped_failure_causes": grouped[:5],
        "verified_mrms": False,
        "prototype": True,
    }
