"""Local candidate trend-hint review chain digest — does NOT clear alerts or verify MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint import (
    SCHEMA_VERSION,
)
from backend.app.services.mrms_render_candidate_trend_hint_ack_status import (
    ROLLUP_BLOCKED,
    ROLLUP_CURRENT,
    ROLLUP_MISSING,
    ROLLUP_NEEDS_ACKNOWLEDGMENT,
    ROLLUP_NOT_NEEDED,
    ROLLUP_STALE,
    SUGGESTED_COMMAND as SUGGESTED_STATUS_COMMAND,
    build_trend_hint_ack_status,
    load_trend_hint_ack_status,
)
from backend.app.services.mrms_render_candidate_trend_hint_ack_status_history import (
    COVERAGE_IMPROVED,
    COVERAGE_WORSENED,
    SUGGESTED_COMMAND as SUGGESTED_HISTORY_COMMAND,
    load_trend_hint_ack_status_history,
)
from backend.app.services.storage import LocalStorage

DIGEST_JSON = "dev/mrms_render_candidate_trend_hint_review_digest.json"
DIGEST_MD = "dev/mrms_render_candidate_trend_hint_review_digest.md"

SUGGESTED_COMMAND = "make mrms-render-candidate-trend-hint-review-digest"

DIGEST_MISSING = "missing"
DIGEST_BLOCKED = "blocked"
DIGEST_NEEDS_ATTENTION = "needs_attention"
DIGEST_STABLE = "stable"
DIGEST_CURRENT = "current"

NEXT_PHASE_RECOMMENDATION = (
    "Phase 90 — bootstrap sandbox comparison trend-hint chain "
    "(seed comparison history and refresh candidate trend hints)"
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_digest_only": True,
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


def _current_safety_state() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "enable_production_radar_tiles": settings.enable_production_radar_tiles,
        "enable_decoded_tiles": settings.enable_decoded_tiles,
        "placeholder_default": not settings.enable_production_radar_tiles
        and not settings.enable_decoded_tiles,
        "production_tile_serving_enabled": settings.enable_production_radar_tiles,
    }


def _digest_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(DIGEST_JSON)


def _digest_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(DIGEST_MD)


def _history_metrics(history: list[dict[str, Any]]) -> dict[str, int]:
    worsened = sum(1 for item in history if item.get("coverage_change") == COVERAGE_WORSENED)
    improved = sum(1 for item in history if item.get("coverage_change") == COVERAGE_IMPROVED)
    return {
        "worsened_count": worsened,
        "improved_count": improved,
    }


def _digest_status_for_status_and_history(
    *,
    status: dict[str, Any],
    history: list[dict[str, Any]],
) -> tuple[str, str]:
    rollup = status.get("rollup_status")
    blockers = list(status.get("blockers") or [])
    if blockers or rollup == ROLLUP_BLOCKED:
        return DIGEST_BLOCKED, "safety_gate_failure"
    if rollup == ROLLUP_MISSING:
        return DIGEST_MISSING, "rollup_missing"
    if not history:
        return DIGEST_MISSING, "history_missing"
    if rollup in {ROLLUP_NEEDS_ACKNOWLEDGMENT, ROLLUP_STALE}:
        return DIGEST_NEEDS_ATTENTION, "rollup_needs_review"
    latest_coverage = history[0].get("coverage_change")
    if latest_coverage == COVERAGE_WORSENED:
        return DIGEST_NEEDS_ATTENTION, "coverage_worsened"
    if rollup == ROLLUP_CURRENT:
        return DIGEST_CURRENT, "rollup_current"
    if rollup == ROLLUP_NOT_NEEDED:
        return DIGEST_STABLE, "rollup_stable"
    return DIGEST_NEEDS_ATTENTION, "rollup_uncertain"


def _suggested_action_for_digest(
    *,
    digest_status: str,
    status: dict[str, Any],
) -> str:
    if digest_status == DIGEST_BLOCKED:
        return "Resolve blocked trend-hint acknowledgment safety gates before relying on review digest."
    if digest_status == DIGEST_MISSING:
        return (
            "Refresh trend-hint acknowledgment status rollup to seed history, then regenerate review digest "
            "(local monitoring only)."
        )
    if digest_status == DIGEST_NEEDS_ATTENTION:
        if status.get("rollup_status") == ROLLUP_STALE:
            return (
                "Re-review updated candidate trend hints and record a fresh acknowledgment, then refresh "
                "status rollup and digest (does not verify MRMS or clear alerts)."
            )
        return (
            "Record local trend-hint review acknowledgment after reviewing candidate trend hints, then "
            "refresh status rollup and digest (does not verify MRMS or clear alerts)."
        )
    if digest_status == DIGEST_STABLE:
        return "Candidate trend-hint review chain stable — ongoing local monitoring only."
    return "Trend-hint review chain digest current for latest rollup and history snapshot."


def build_trend_hint_review_digest(storage: LocalStorage) -> dict[str, Any]:
    status = build_trend_hint_ack_status(storage)
    history = load_trend_hint_ack_status_history(storage)
    metrics = _history_metrics(history)
    digest_status, digest_reason = _digest_status_for_status_and_history(status=status, history=history)

    suggested_command = None
    if digest_status in {DIGEST_MISSING, DIGEST_NEEDS_ATTENTION}:
        suggested_command = status.get("suggested_command") or SUGGESTED_STATUS_COMMAND
    elif digest_status == DIGEST_BLOCKED:
        suggested_command = SUGGESTED_STATUS_COMMAND

    latest_history = history[0] if history else None
    return {
        "generated_at": _utc_now(),
        "schema_version": SCHEMA_VERSION,
        "digest_status": digest_status,
        "digest_reason": digest_reason,
        "rollup_status": status.get("rollup_status"),
        "acknowledgment_status": status.get("acknowledgment_status"),
        "status_reason": status.get("status_reason"),
        "stale_acknowledgment": bool(status.get("stale_acknowledgment")),
        "trend": status.get("trend"),
        "hint_status": status.get("hint_status"),
        "trend_review_recommended": bool(status.get("trend_review_recommended")),
        "history_count": len(history),
        "latest_coverage_change": (latest_history or {}).get("coverage_change"),
        "latest_history_recorded_at": (latest_history or {}).get("recorded_at"),
        "worsened_count": metrics["worsened_count"],
        "improved_count": metrics["improved_count"],
        "recent_history_entries": [
            {
                "recorded_at": item.get("recorded_at"),
                "rollup_status": item.get("rollup_status"),
                "acknowledgment_status": item.get("acknowledgment_status"),
                "coverage_change": item.get("coverage_change"),
            }
            for item in history[:5]
        ],
        "blockers": list(status.get("blockers") or []),
        "warnings": list(status.get("warnings") or []),
        "safety_state": _current_safety_state(),
        "suggested_action": _suggested_action_for_digest(digest_status=digest_status, status=status),
        "suggested_command": suggested_command,
        "suggested_status_command": SUGGESTED_STATUS_COMMAND,
        "suggested_history_command": SUGGESTED_HISTORY_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_trend_hint_review_digest_markdown(digest: dict[str, Any]) -> str:
    lines = [
        "# Candidate Trend-Hint Review Chain Digest",
        "",
        f"Generated at: {digest.get('generated_at')}",
        "",
        "> **WARNING:** Local trend-hint review chain digest only. Advisory metadata — does **NOT** "
        "verify MRMS, enable production rendering, download/decode/render, create or serve production "
        "tiles, clear alerts, or authorize production use.",
        "",
        f"- Digest status: **{digest.get('digest_status')}**",
        f"- Reason: {digest.get('digest_reason')}",
        "",
        "## Current rollup",
        "",
        f"- Rollup status: {digest.get('rollup_status')}",
        f"- Acknowledgment status: {digest.get('acknowledgment_status')}",
        f"- Trend: {digest.get('trend')}",
        f"- Hint status: {digest.get('hint_status')}",
        f"- Review recommended: {digest.get('trend_review_recommended')}",
        f"- Stale acknowledgment: {digest.get('stale_acknowledgment')}",
        "",
        "## History summary",
        "",
        f"- History count: {digest.get('history_count')}",
        f"- Latest coverage change: {digest.get('latest_coverage_change') or '—'}",
        f"- Worsened entries: {digest.get('worsened_count')}",
        f"- Improved entries: {digest.get('improved_count')}",
        "",
        "## Recent history",
        "",
    ]
    recent = digest.get("recent_history_entries") or []
    if not recent:
        lines.append("- None")
    else:
        for item in recent:
            lines.append(
                f"- {item.get('recorded_at')} — rollup={item.get('rollup_status')} "
                f"ack={item.get('acknowledgment_status')} coverage={item.get('coverage_change')}"
            )
    lines.extend(
        [
            "",
            "## Suggested action",
            "",
            digest.get("suggested_action") or "—",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def save_trend_hint_review_digest(storage: LocalStorage, digest: dict[str, Any]) -> dict[str, Any]:
    from backend.app.services.mrms_render_candidate_trend_hint_review_digest_history import (
        append_trend_hint_review_digest_history_entry,
        refresh_trend_hint_review_digest_history_report,
    )

    json_path = _digest_json_path(storage)
    md_path = _digest_md_path(storage)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    digest = {
        **digest,
        "json_path": json_path,
        "markdown_path": md_path,
        "suggested_command": digest.get("suggested_command") or SUGGESTED_COMMAND,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(digest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(
        build_trend_hint_review_digest_markdown(digest),
        encoding="utf-8",
    )
    append_trend_hint_review_digest_history_entry(storage, digest)
    refresh_trend_hint_review_digest_history_report(storage)
    return digest


def load_trend_hint_review_digest(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_digest_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def refresh_trend_hint_review_digest(storage: LocalStorage) -> dict[str, Any]:
    digest = build_trend_hint_review_digest(storage)
    return save_trend_hint_review_digest(storage, digest)


def compact_trend_hint_review_digest(storage: LocalStorage) -> dict[str, Any]:
    latest = load_trend_hint_review_digest(storage)
    if latest is None:
        latest = build_trend_hint_review_digest(storage)
    return {
        "available": load_trend_hint_review_digest(storage) is not None,
        "digest_status": latest.get("digest_status"),
        "digest_reason": latest.get("digest_reason"),
        "rollup_status": latest.get("rollup_status"),
        "acknowledgment_status": latest.get("acknowledgment_status"),
        "history_count": latest.get("history_count"),
        "latest_coverage_change": latest.get("latest_coverage_change"),
        "worsened_count": latest.get("worsened_count"),
        "improved_count": latest.get("improved_count"),
        "trend_review_recommended": bool(latest.get("trend_review_recommended")),
        "stale_acknowledgment": bool(latest.get("stale_acknowledgment")),
        "blockers": latest.get("blockers") or [],
        "warnings": latest.get("warnings") or [],
        "suggested_action": latest.get("suggested_action"),
        "suggested_command": latest.get("suggested_command") or SUGGESTED_COMMAND,
        "schema_version": latest.get("schema_version") or SCHEMA_VERSION,
        "json_path": _digest_json_path(storage),
        "markdown_path": _digest_md_path(storage),
        "next_phase_recommendation": latest.get("next_phase_recommendation") or NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_trend_hint_review_digest_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_trend_hint_review_digest(storage)
    if latest is None:
        latest = build_trend_hint_review_digest(storage)
    return {
        **_safety_fields(),
        "latest": latest,
        "compact": compact_trend_hint_review_digest(storage),
    }
