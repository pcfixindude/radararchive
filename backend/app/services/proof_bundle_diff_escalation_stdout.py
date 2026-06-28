"""Stdout-only urgent escalation notices — local terminal only, no external notifications."""

from __future__ import annotations

import json
import sys
from typing import Any, Optional

from backend.app.services.operator_guidance import RUNBOOK_PATH
from backend.app.services.proof_bundle_diff_escalation import ESCALATION_URGENT
from backend.app.services.storage import LocalStorage

STDOUT_LATEST_PATH = "dev/proof_bundle_diff_escalation_stdout_latest.json"
URGENT_NOTICE_HEADER = "URGENT LOCAL VALIDATION NOTICE"


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stdout_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(STDOUT_LATEST_PATH)


def _primary_runbook_reference(escalation: dict[str, Any]) -> tuple[str, str]:
    guidance_items = escalation.get("guidance_items") or []
    for item in guidance_items:
        path = str(item.get("path") or RUNBOOK_PATH)
        anchor = str(item.get("anchor") or "proof-bundle-diff-escalation-urgent")
        return path, anchor
    return RUNBOOK_PATH, "proof-bundle-diff-escalation-urgent"


def build_urgent_stdout_notice_record(
    escalation: dict[str, Any],
    *,
    production_rendering_enabled: bool,
    source: str,
) -> dict[str, Any]:
    runbook_path, runbook_anchor = _primary_runbook_reference(escalation)
    return {
        "triggered": True,
        "triggered_at": _utc_now(),
        "escalation_level": escalation.get("escalation_level"),
        "reason": escalation.get("reason", ""),
        "suggested_next_action": escalation.get("suggested_next_action", ""),
        "runbook_path": runbook_path,
        "runbook_anchor": runbook_anchor,
        "runbook_section": f"{runbook_path}#{runbook_anchor}",
        "source": source,
        "verified_mrms": False,
        "production_rendering_enabled": production_rendering_enabled,
        "local_stdout_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def _save_latest_stdout_notice(storage: LocalStorage, record: dict[str, Any]) -> str:
    repo_path = _stdout_repo_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(record, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return repo_path


def load_latest_stdout_notice(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_stdout_repo_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def compact_latest_stdout_notice(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_stdout_notice(storage)
    if latest is None:
        return {
            "available": False,
            "triggered": False,
            "verified_mrms": False,
            "local_stdout_only": True,
            "no_external_notifications": True,
            "prototype": True,
        }
    return {
        "available": True,
        "triggered": bool(latest.get("triggered")),
        "triggered_at": latest.get("triggered_at"),
        "escalation_level": latest.get("escalation_level"),
        "reason": latest.get("reason"),
        "runbook_section": latest.get("runbook_section"),
        "source": latest.get("source"),
        "verified_mrms": False,
        "local_stdout_only": True,
        "no_external_notifications": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def format_urgent_stdout_notice_lines(
    escalation: dict[str, Any],
    *,
    production_rendering_enabled: bool,
) -> list[str]:
    runbook_path, runbook_anchor = _primary_runbook_reference(escalation)
    production_line = (
        "Production rendering: ENABLED (ENABLE_PRODUCTION_RADAR_TILES=true) — "
        "still NOT verified MRMS."
        if production_rendering_enabled
        else "Production rendering: DISABLED (default) — does not enable production rendering."
    )
    return [
        "=" * 72,
        URGENT_NOTICE_HEADER,
        "=" * 72,
        f"Escalation level: {escalation.get('escalation_level')}",
        f"Reason: {escalation.get('reason', '')}",
        f"Suggested next action: {escalation.get('suggested_next_action', '')}",
        f"Runbook: {runbook_path} (section: {runbook_anchor})",
        "verified_mrms: false — this notice does NOT verify MRMS.",
        production_line,
        "This notice does NOT clear alerts or mutate catalog/render gates.",
        "Local terminal stdout only — no email, SMS, Slack, webhooks, or push notifications.",
        "=" * 72,
    ]


def print_urgent_stdout_notice(
    escalation: dict[str, Any],
    *,
    production_rendering_enabled: bool,
    source: str,
    storage: Optional[LocalStorage] = None,
    stream: Any = None,
) -> dict[str, Any]:
    """Print urgent notice to stdout and optionally persist latest notice metadata."""
    output = stream if stream is not None else sys.stdout
    for line in format_urgent_stdout_notice_lines(
        escalation,
        production_rendering_enabled=production_rendering_enabled,
    ):
        print(line, file=output)

    record = build_urgent_stdout_notice_record(
        escalation,
        production_rendering_enabled=production_rendering_enabled,
        source=source,
    )
    if storage is not None:
        _save_latest_stdout_notice(storage, record)
    return record


def maybe_trigger_urgent_stdout_notice(
    storage: LocalStorage,
    escalation: dict[str, Any],
    *,
    notify_stdout: bool,
    production_rendering_enabled: bool,
    source: str,
) -> Optional[dict[str, Any]]:
    if not notify_stdout:
        return None
    if escalation.get("escalation_level") != ESCALATION_URGENT:
        return None
    return print_urgent_stdout_notice(
        escalation,
        production_rendering_enabled=production_rendering_enabled,
        source=source,
        storage=storage,
    )
