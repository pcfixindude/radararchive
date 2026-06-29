"""Local candidate trend-hint review digest history — does NOT clear alerts or verify MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint import (
    SCHEMA_VERSION,
)
from backend.app.services.mrms_render_candidate_trend_hint_review_digest import (
    DIGEST_BLOCKED,
    DIGEST_CURRENT,
    DIGEST_MISSING,
    DIGEST_NEEDS_ATTENTION,
    DIGEST_STABLE,
)
from backend.app.services.storage import LocalStorage

HISTORY_JSON = "dev/mrms_render_candidate_trend_hint_review_digest_history.json"
HISTORY_MD = "dev/mrms_render_candidate_trend_hint_review_digest_history.md"

MAX_HISTORY_ENTRIES = 25
SUGGESTED_COMMAND = "make mrms-render-candidate-trend-hint-review-digest-history"

COVERAGE_UNCHANGED = "unchanged"
COVERAGE_IMPROVED = "improved"
COVERAGE_WORSENED = "worsened"
COVERAGE_MIXED = "mixed"
COVERAGE_NO_BASELINE = "no_baseline"

NEXT_PHASE_RECOMMENDATION = (
    "Phase 87 — candidate trend-hint review digest regeneration hint "
    "(local hint when digest diff suggests refresh without production authorization)"
)

DIGEST_COVERAGE_RANK = {
    DIGEST_BLOCKED: 0,
    DIGEST_MISSING: 1,
    DIGEST_NEEDS_ATTENTION: 2,
    DIGEST_STABLE: 3,
    DIGEST_CURRENT: 4,
}


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_digest_history_only": True,
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
    return storage.normalize_path(HISTORY_JSON)


def _history_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(HISTORY_MD)


def load_trend_hint_review_digest_history(
    storage: LocalStorage,
    *,
    limit: int = MAX_HISTORY_ENTRIES,
) -> list[dict[str, Any]]:
    bounded = max(1, min(limit, MAX_HISTORY_ENTRIES))
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


def _save_trend_hint_review_digest_history(storage: LocalStorage, entries: list[dict[str, Any]]) -> None:
    repo_path = _history_json_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(entries[:MAX_HISTORY_ENTRIES], indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _coverage_change_for_digest(
    baseline_digest: Optional[str],
    latest_digest: Optional[str],
) -> str:
    if not baseline_digest:
        return COVERAGE_NO_BASELINE
    if baseline_digest == latest_digest:
        return COVERAGE_UNCHANGED
    base_rank = DIGEST_COVERAGE_RANK.get(str(baseline_digest), 0)
    latest_rank = DIGEST_COVERAGE_RANK.get(str(latest_digest), 0)
    if latest_rank > base_rank:
        return COVERAGE_IMPROVED
    if latest_rank < base_rank:
        return COVERAGE_WORSENED
    return COVERAGE_MIXED


def build_trend_hint_review_digest_history_entry(
    digest: dict[str, Any],
    *,
    previous_entry: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    baseline_digest = (previous_entry or {}).get("digest_status")
    baseline_rollup = (previous_entry or {}).get("rollup_status")
    latest_digest = digest.get("digest_status")
    latest_rollup = digest.get("rollup_status")
    return {
        "recorded_at": digest.get("generated_at") or _utc_now(),
        "digest_status": latest_digest,
        "digest_reason": digest.get("digest_reason"),
        "rollup_status": latest_rollup,
        "acknowledgment_status": digest.get("acknowledgment_status"),
        "history_count": digest.get("history_count"),
        "latest_coverage_change": digest.get("latest_coverage_change"),
        "digest_status_change": {
            "baseline": baseline_digest,
            "latest": latest_digest,
        },
        "rollup_status_change": {
            "baseline": baseline_rollup,
            "latest": latest_rollup,
        },
        "coverage_change": _coverage_change_for_digest(baseline_digest, latest_digest),
        "schema_version": digest.get("schema_version") or SCHEMA_VERSION,
        **_safety_fields(),
    }


def append_trend_hint_review_digest_history_entry(
    storage: LocalStorage,
    digest: dict[str, Any],
) -> dict[str, Any]:
    history = load_trend_hint_review_digest_history(storage, limit=MAX_HISTORY_ENTRIES)
    previous = history[0] if history else None
    entry = build_trend_hint_review_digest_history_entry(digest, previous_entry=previous)
    history.insert(0, entry)
    _save_trend_hint_review_digest_history(storage, history)
    from backend.app.services.mrms_render_candidate_trend_hint_review_digest_diff import (
        record_trend_hint_review_digest_diff,
    )

    record_trend_hint_review_digest_diff(
        storage,
        current_entry=entry,
        baseline_entry=previous,
    )
    return entry


def build_trend_hint_review_digest_history_markdown(
    history: list[dict[str, Any]],
    latest: dict[str, Any],
) -> str:
    lines = [
        "# Candidate Trend-Hint Review Digest History",
        "",
        f"Generated at: {_utc_now()}",
        "",
        "> **WARNING:** Local trend-hint review digest history only. Advisory metadata — does **NOT** "
        "verify MRMS, enable production rendering, download/decode/render, create or serve production "
        "tiles, clear alerts, or authorize production use.",
        "",
        f"- History count: {latest.get('history_count', len(history))}",
        f"- Latest digest status: {latest.get('latest_digest_status')}",
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
                f"- {item.get('recorded_at')} — digest={item.get('digest_status')} "
                f"rollup={item.get('rollup_status')} coverage={item.get('coverage_change')}"
            )
    return "\n".join(lines) + "\n"


def refresh_trend_hint_review_digest_history_report(storage: LocalStorage) -> dict[str, Any]:
    history = load_trend_hint_review_digest_history(storage, limit=MAX_HISTORY_ENTRIES)
    latest_entry = history[0] if history else None
    body = {
        "generated_at": _utc_now(),
        "history_count": len(history),
        "latest_digest_status": (latest_entry or {}).get("digest_status"),
        "latest_rollup_status": (latest_entry or {}).get("rollup_status"),
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
        build_trend_hint_review_digest_history_markdown(history, body),
        encoding="utf-8",
    )
    return body


def compact_trend_hint_review_digest_history(storage: LocalStorage) -> dict[str, Any]:
    history = load_trend_hint_review_digest_history(storage, limit=10)
    latest_entry = history[0] if history else None
    return {
        "available": bool(history),
        "history_count": len(load_trend_hint_review_digest_history(storage)),
        "latest_digest_status": (latest_entry or {}).get("digest_status"),
        "latest_rollup_status": (latest_entry or {}).get("rollup_status"),
        "latest_coverage_change": (latest_entry or {}).get("coverage_change"),
        "latest_recorded_at": (latest_entry or {}).get("recorded_at"),
        "recent_entries": [
            {
                "recorded_at": item.get("recorded_at"),
                "digest_status": item.get("digest_status"),
                "rollup_status": item.get("rollup_status"),
                "coverage_change": item.get("coverage_change"),
            }
            for item in history[:5]
        ],
        "json_path": _history_json_path(storage),
        "markdown_path": _history_md_path(storage),
        "suggested_command": SUGGESTED_COMMAND,
        "next_phase_recommendation": NEXT_PHASE_RECOMMENDATION,
        **_safety_fields(),
    }


def build_trend_hint_review_digest_history_payload(storage: LocalStorage) -> dict[str, Any]:
    history = load_trend_hint_review_digest_history(storage)
    body = (
        refresh_trend_hint_review_digest_history_report(storage)
        if history
        else {
            "generated_at": _utc_now(),
            "history_count": 0,
            "latest_digest_status": None,
            "latest_rollup_status": None,
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
    )
    return {
        **_safety_fields(),
        "latest": body,
        "compact": compact_trend_hint_review_digest_history(storage),
        "entries": history,
        "count": len(history),
        "max_entries": MAX_HISTORY_ENTRIES,
    }
