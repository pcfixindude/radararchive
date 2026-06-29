"""MRMS render candidate sandbox comparison acknowledgment status history — local advisory only."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status import (
    ROLLUP_BLOCKED,
    ROLLUP_CURRENT,
    ROLLUP_MISSING,
    ROLLUP_NEEDS_ACKNOWLEDGMENT,
    ROLLUP_NOT_NEEDED,
    ROLLUP_STALE,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_trend_hint import SCHEMA_VERSION
from backend.app.services.storage import LocalStorage

ACK_STATUS_HISTORY_JSON = (
    "dev/mrms_render_candidate_sandbox_comparison_acknowledgment_status_history.json"
)
ACK_STATUS_HISTORY_MD = (
    "dev/mrms_render_candidate_sandbox_comparison_acknowledgment_status_history.md"
)

MAX_ACK_STATUS_HISTORY = 25
SUGGESTED_COMMAND = "make mrms-render-candidate-sandbox-comparison-acknowledgment-status-history"

COVERAGE_UNCHANGED = "unchanged"
COVERAGE_IMPROVED = "improved"
COVERAGE_WORSENED = "worsened"
COVERAGE_MIXED = "mixed"
COVERAGE_NO_BASELINE = "no_baseline"

NEXT_PHASE_RECOMMENDATION = (
    "Phase 79 — Gated candidate sandbox comparison acknowledgment status trend review acknowledgment status "
    "trend review acknowledgment status history (local bounded history of status rollups without production "
    "authorization)"
)

ROLLUP_COVERAGE_RANK = {
    ROLLUP_BLOCKED: 0,
    ROLLUP_MISSING: 1,
    ROLLUP_NEEDS_ACKNOWLEDGMENT: 2,
    ROLLUP_STALE: 3,
    ROLLUP_NOT_NEEDED: 4,
    ROLLUP_CURRENT: 5,
}


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_status_history_only": True,
        "advisory_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "does_not_download_or_decode": True,
        "does_not_create_production_tiles": True,
        "does_not_serve_production_tiles": True,
        "does_not_delete_by_default": True,
        "binary_artifacts_included": False,
        "no_external_notifications": True,
        "does_not_authorize_production_use": True,
        "prototype": True,
    }


def _history_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(ACK_STATUS_HISTORY_JSON)


def _history_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(ACK_STATUS_HISTORY_MD)


def load_ack_status_history(
    storage: LocalStorage,
    *,
    limit: int = MAX_ACK_STATUS_HISTORY,
) -> list[dict[str, Any]]:
    bounded = max(1, min(limit, MAX_ACK_STATUS_HISTORY))
    abs_path = storage.absolute_path(_history_json_path(storage))
    if not abs_path.is_file():
        return []
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)][:bounded]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save_ack_status_history(storage: LocalStorage, entries: list[dict[str, Any]]) -> None:
    repo_path = _history_json_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(entries[:MAX_ACK_STATUS_HISTORY], indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _coverage_change_for_rollup(
    baseline_rollup: Optional[str],
    latest_rollup: Optional[str],
) -> str:
    if not baseline_rollup:
        return COVERAGE_NO_BASELINE
    if baseline_rollup == latest_rollup:
        return COVERAGE_UNCHANGED
    base_rank = ROLLUP_COVERAGE_RANK.get(str(baseline_rollup), 0)
    latest_rank = ROLLUP_COVERAGE_RANK.get(str(latest_rollup), 0)
    if latest_rank > base_rank:
        return COVERAGE_IMPROVED
    if latest_rank < base_rank:
        return COVERAGE_WORSENED
    return COVERAGE_MIXED


def build_ack_status_history_entry(
    status: dict[str, Any],
    *,
    previous_entry: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    baseline_rollup = (previous_entry or {}).get("rollup_status")
    baseline_ack = (previous_entry or {}).get("acknowledgment_status")
    latest_rollup = status.get("rollup_status")
    latest_ack = status.get("acknowledgment_status")
    return {
        "recorded_at": status.get("generated_at") or _utc_now(),
        "rollup_status": latest_rollup,
        "acknowledgment_status": latest_ack,
        "status_reason": status.get("status_reason"),
        "stale_acknowledgment": bool(status.get("stale_acknowledgment")),
        "trend": status.get("trend"),
        "hint_status": status.get("hint_status"),
        "trend_review_recommended": bool(status.get("trend_review_recommended")),
        "acknowledgment_count": status.get("acknowledgment_count"),
        "rollup_status_change": {
            "baseline": baseline_rollup,
            "latest": latest_rollup,
        },
        "acknowledgment_status_change": {
            "baseline": baseline_ack,
            "latest": latest_ack,
        },
        "coverage_change": _coverage_change_for_rollup(baseline_rollup, latest_rollup),
        "schema_version": status.get("schema_version") or SCHEMA_VERSION,
        **_safety_fields(),
    }


def append_ack_status_history_entry(storage: LocalStorage, status: dict[str, Any]) -> dict[str, Any]:
    history = load_ack_status_history(storage, limit=MAX_ACK_STATUS_HISTORY)
    previous = history[0] if history else None
    entry = build_ack_status_history_entry(status, previous_entry=previous)
    history.insert(0, entry)
    _save_ack_status_history(storage, history)
    return entry


def build_ack_status_history_markdown(
    history: list[dict[str, Any]],
    latest: dict[str, Any],
) -> str:
    lines = [
        "# MRMS Render Candidate Sandbox Comparison Acknowledgment Status History",
        "",
        f"Generated at: {_utc_now()}",
        "",
        "> **WARNING:** Local acknowledgment status history only. Advisory metadata — does **NOT** "
        "verify MRMS, enable production rendering, download/decode/render, create or serve production "
        "tiles, clear alerts, or authorize production use.",
        "",
        f"- History count: {latest.get('history_count', len(history))}",
        f"- Latest rollup status: {latest.get('latest_rollup_status')}",
        f"- Latest coverage change: {latest.get('latest_coverage_change')}",
        "",
        "## Recent entries",
        "",
    ]
    if not history:
        lines.append("- None")
    else:
        for item in history[:10]:
            lines.append(
                f"- {item.get('recorded_at')} — rollup={item.get('rollup_status')} "
                f"ack={item.get('acknowledgment_status')} "
                f"coverage={item.get('coverage_change')}"
            )
    return "\n".join(lines) + "\n"


def refresh_ack_status_history_report(storage: LocalStorage) -> dict[str, Any]:
    history = load_ack_status_history(storage, limit=MAX_ACK_STATUS_HISTORY)
    latest_entry = history[0] if history else None
    body = {
        "generated_at": _utc_now(),
        "history_count": len(history),
        "latest_rollup_status": (latest_entry or {}).get("rollup_status"),
        "latest_acknowledgment_status": (latest_entry or {}).get("acknowledgment_status"),
        "latest_coverage_change": (latest_entry or {}).get("coverage_change"),
        "latest_entry": latest_entry,
        "recent_entries": history[:10],
        "schema_version": SCHEMA_VERSION,
        "json_path": _history_json_path(storage),
        "markdown_path": _history_md_path(storage),
        "suggested_command": SUGGESTED_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }
    storage.ensure_directories(_history_json_path(storage).rsplit("/", 1)[0])
    storage.absolute_path(_history_md_path(storage)).write_text(
        build_ack_status_history_markdown(history, body),
        encoding="utf-8",
    )
    return body


def compact_ack_status_history(storage: LocalStorage) -> dict[str, Any]:
    history = load_ack_status_history(storage, limit=10)
    latest_entry = history[0] if history else None
    return {
        "available": bool(history),
        "history_count": len(load_ack_status_history(storage)),
        "latest_rollup_status": (latest_entry or {}).get("rollup_status"),
        "latest_acknowledgment_status": (latest_entry or {}).get("acknowledgment_status"),
        "latest_coverage_change": (latest_entry or {}).get("coverage_change"),
        "latest_recorded_at": (latest_entry or {}).get("recorded_at"),
        "recent_entries": [
            {
                "recorded_at": item.get("recorded_at"),
                "rollup_status": item.get("rollup_status"),
                "acknowledgment_status": item.get("acknowledgment_status"),
                "coverage_change": item.get("coverage_change"),
                "stale_acknowledgment": item.get("stale_acknowledgment"),
            }
            for item in history[:5]
        ],
        "json_path": _history_json_path(storage),
        "markdown_path": _history_md_path(storage),
        "suggested_command": SUGGESTED_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_ack_status_history_payload(storage: LocalStorage) -> dict[str, Any]:
    history = load_ack_status_history(storage)
    body = refresh_ack_status_history_report(storage) if history else {
        "generated_at": _utc_now(),
        "history_count": 0,
        "latest_rollup_status": None,
        "latest_acknowledgment_status": None,
        "latest_coverage_change": None,
        "latest_entry": None,
        "recent_entries": [],
        "schema_version": SCHEMA_VERSION,
        "json_path": _history_json_path(storage),
        "markdown_path": _history_md_path(storage),
        "suggested_command": SUGGESTED_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }
    return {
        **_safety_fields(),
        "latest": body,
        "compact": compact_ack_status_history(storage),
        "entries": history,
        "count": len(history),
        "max_entries": MAX_ACK_STATUS_HISTORY,
    }
