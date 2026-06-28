"""Local Markdown export for MRMS proof review sessions — does NOT verify MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.services.operator_guidance import build_open_attention_guidance
from backend.app.services.proof_bundle_diff_escalation_digest_diff import (
    build_digest_regeneration_hint,
)
from backend.app.services.mrms_review_session import load_review_sessions
from backend.app.services.mrms_review_session_compare import (
    load_latest_review_session_comparison,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.time_utils import parse_utc_iso

EXPORT_MD_PATH = "dev/mrms_review_session_export_latest.md"
EXPORT_JSON_PATH = "dev/mrms_review_session_export_latest.json"
EXPORT_HISTORY_PATH = "dev/mrms_review_session_export_history.json"
MAX_EXPORT_HISTORY = 25
SUGGESTED_EXPORT_COMMAND = "make mrms-review-session-export"


class ReviewSessionExportError(ValueError):
    """Raised when review session export cannot proceed."""


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _export_md_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(EXPORT_MD_PATH)


def _export_json_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(EXPORT_JSON_PATH)


def _export_history_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(EXPORT_HISTORY_PATH)


def _load_export_history(storage: LocalStorage) -> list[dict[str, Any]]:
    abs_path = storage.absolute_path(_export_history_repo_path(storage))
    if not abs_path.is_file():
        return []
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save_export_history(storage: LocalStorage, entries: list[dict[str, Any]]) -> None:
    repo_path = _export_history_repo_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(entries[:MAX_EXPORT_HISTORY], indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _is_older(left: Optional[str], right: Optional[str]) -> bool:
    if not left or not right:
        return False
    try:
        return parse_utc_iso(left) < parse_utc_iso(right)
    except ValueError:
        return False


def load_latest_review_session_export_metadata(
    storage: LocalStorage,
) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_export_json_repo_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _session_operator(session: dict[str, Any]) -> Optional[str]:
    return session.get("operator_name") or session.get("operator_initials")


def _format_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def _build_export_markdown(
    *,
    created_at: str,
    session: dict[str, Any],
    comparison: Optional[dict[str, Any]],
    guidance: list[dict[str, Any]],
    digest_hint: dict[str, Any],
    markdown_path: str,
) -> str:
    reviewed = session.get("checklist_items_reviewed") or []
    not_reviewed = session.get("checklist_items_not_reviewed") or []
    open_items = session.get("open_attention_items") or []

    lines = [
        "# MRMS Proof Review Session Export (Local Review Only)",
        "",
        f"Exported at: {created_at}",
        "",
        "> **WARNING:** This export is local operator review evidence only.",
        "> It does **NOT** verify MRMS, clear validation alerts, enable production rendering,",
        "> or send external notifications (email, SMS, Slack, webhooks, push).",
        "",
        "## Review session summary",
        "",
        f"- Session ID: `{session.get('session_id')}`",
        f"- Session created at: {session.get('created_at')}",
        f"- Operator: {_format_value(_session_operator(session))}",
        f"- Session notes: {_format_value(session.get('session_notes'))}",
        f"- Latest escalation level: {_format_value(session.get('latest_escalation_level'))}",
        f"- Open attention count: {int(session.get('open_attention_count', 0))}",
        f"- Checklist reviewed count: {len(reviewed)}",
        f"- Checklist not reviewed count: {len(not_reviewed)}",
        f"- Latest digest path: {_format_value(session.get('latest_digest_path'))}",
        f"- Latest operator handoff path: {_format_value(session.get('latest_operator_handoff_path'))}",
        f"- Latest proof bundle ID: {_format_value(session.get('latest_proof_bundle_id'))}",
        f"- Latest proof bundle path: {_format_value(session.get('latest_proof_bundle_path'))}",
        f"- Latest proof bundle diff status: {_format_value(session.get('latest_proof_bundle_diff_status'))}",
        f"- Latest proof report status: {_format_value(session.get('latest_proof_report_status'))}",
        f"- Latest acknowledgment ID: {_format_value(session.get('latest_acknowledgment_id'))}",
        f"- Latest acknowledgment at: {_format_value(session.get('latest_acknowledgment_at'))}",
        "",
        "## Open attention items",
        "",
    ]
    if open_items:
        for item in open_items:
            lines.append(f"- {item}")
    else:
        lines.append("- None recorded at session creation time.")

    lines.extend(["", "## Comparison vs previous session", ""])
    if comparison is None:
        lines.append("- No comparison metadata available.")
    else:
        lines.extend(
            [
                f"- Overall review diff status: `{comparison.get('overall_review_diff_status')}`",
                f"- Compared at: {comparison.get('compared_at')}",
                f"- Baseline session: {comparison.get('baseline_created_at')} — "
                f"{_format_value(comparison.get('baseline_operator'))}",
                f"- Latest session: {comparison.get('latest_created_at')} — "
                f"{_format_value(comparison.get('latest_operator'))}",
            ]
        )
        improvements = comparison.get("improvements") or []
        regressions = comparison.get("regressions") or []
        unchanged = comparison.get("unchanged_items") or []
        lines.append("")
        lines.append("### Improvements")
        if improvements:
            for item in improvements:
                lines.append(f"- {item}")
        else:
            lines.append("- None")
        lines.append("")
        lines.append("### Regressions")
        if regressions:
            for item in regressions:
                lines.append(f"- {item}")
        else:
            lines.append("- None")
        lines.append("")
        lines.append("### Unchanged items")
        if unchanged:
            for item in unchanged:
                lines.append(f"- {item}")
        else:
            lines.append("- None")

    lines.extend(["", "## Open attention guidance (runbook)", ""])
    if guidance:
        for item in guidance:
            lines.append(
                f"- **{item.get('title')}** — `{item.get('path')}` "
                f"(section: {item.get('section_label', '')}, anchor: {item.get('anchor', '')})"
            )
            if item.get("attention_item"):
                lines.append(f"  - Attention item: {item.get('attention_item')}")
            if item.get("suggested_action"):
                lines.append(f"  - Suggested action: {item.get('suggested_action')}")
    else:
        lines.append("- No open attention guidance items.")

    lines.extend(
        [
            "",
            "## Digest regeneration hint",
            "",
            f"- Digest regeneration recommended: "
            f"{_format_value(digest_hint.get('digest_regeneration_recommended'))}",
            f"- Reason: {_format_value(digest_hint.get('reason'))}",
            f"- Suggested command: {_format_value(digest_hint.get('suggested_command'))}",
            f"- Latest escalation level: {_format_value(digest_hint.get('latest_escalation_level'))}",
            f"- Latest digest at: {_format_value(digest_hint.get('latest_digest_at'))}",
            f"- Latest escalation snapshot at: "
            f"{_format_value(digest_hint.get('latest_escalation_snapshot_at'))}",
            "",
            "## Checklist detail",
            "",
            "### Reviewed",
        ]
    )
    if reviewed:
        for item in reviewed:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines.extend(["", "### Not reviewed"])
    if not_reviewed:
        for item in not_reviewed:
            lines.append(f"- {item}")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Safety reminders",
            "",
            "- Local review export only — not verified MRMS production output.",
            "- Does not clear validation alerts.",
            "- Does not enable production rendering.",
            "- Does not notify externally.",
            f"- Export path: `{markdown_path}`",
            "",
        ]
    )
    return "\n".join(lines)


def build_export_history_entry(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "created_at": metadata.get("created_at"),
        "export_path": metadata.get("export_path"),
        "metadata_path": metadata.get("metadata_path"),
        "session_id": metadata.get("session_id"),
        "operator": metadata.get("operator"),
        "comparison_status": metadata.get("comparison_status"),
        "open_attention_count": int(metadata.get("open_attention_count", 0)),
        "escalation_level": metadata.get("escalation_level"),
        "digest_regeneration_recommended": bool(metadata.get("digest_regeneration_recommended")),
        "proof_bundle_diff_status": metadata.get("proof_bundle_diff_status"),
        "acknowledgment_id": metadata.get("acknowledgment_id"),
        "verified_mrms": False,
        "local_export_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def export_latest_review_session(
    storage: LocalStorage,
    *,
    session: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Export latest review session to Markdown + JSON metadata; append bounded history."""
    entries = load_review_sessions(storage)
    latest = session if session is not None else (entries[0] if entries else None)
    if latest is None:
        raise ReviewSessionExportError("No review session available to export")

    created_at = _utc_now()
    md_repo = _export_md_repo_path(storage)
    json_repo = _export_json_repo_path(storage)
    storage.ensure_directories(md_repo.rsplit("/", 1)[0])

    comparison = load_latest_review_session_comparison(storage)
    open_items = latest.get("open_attention_items") or []
    guidance = latest.get("open_attention_guidance") or build_open_attention_guidance(open_items)
    digest_hint = build_digest_regeneration_hint(storage)

    markdown = _build_export_markdown(
        created_at=created_at,
        session=latest,
        comparison=comparison,
        guidance=guidance,
        digest_hint=digest_hint,
        markdown_path=md_repo,
    )
    storage.absolute_path(md_repo).write_text(markdown, encoding="utf-8")

    metadata: dict[str, Any] = {
        "created_at": created_at,
        "export_path": md_repo,
        "metadata_path": json_repo,
        "session_id": latest.get("session_id"),
        "session_created_at": latest.get("created_at"),
        "operator": _session_operator(latest),
        "comparison_status": (comparison or {}).get("overall_review_diff_status"),
        "comparison_compared_at": (comparison or {}).get("compared_at"),
        "open_attention_count": int(latest.get("open_attention_count", 0)),
        "escalation_level": latest.get("latest_escalation_level"),
        "digest_regeneration_recommended": bool(digest_hint.get("digest_regeneration_recommended")),
        "proof_bundle_diff_status": latest.get("latest_proof_bundle_diff_status"),
        "acknowledgment_id": latest.get("latest_acknowledgment_id"),
        "verified_mrms": False,
        "local_export_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }
    storage.absolute_path(json_repo).write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    from backend.app.services.mrms_review_session_export_diff import record_export_diff_metadata

    history = _load_export_history(storage)
    baseline_entry = history[0] if history else None
    history_entry = build_export_history_entry(metadata)
    history.insert(0, history_entry)
    _save_export_history(storage, history)
    record_export_diff_metadata(storage, history_entry, baseline_history_entry=baseline_entry)
    return metadata


def try_export_after_review_session_create(
    storage: LocalStorage,
    record: dict[str, Any],
) -> dict[str, Any]:
    """Export Markdown for a newly created session; never rolls back the session."""
    base: dict[str, Any] = {
        "export_after_create_requested": True,
        "export_generated": False,
        "export_path": None,
        "export_metadata_path": None,
        "export_error": None,
        "verified_mrms": False,
        "local_export_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }
    try:
        metadata = export_latest_review_session(storage, session=record)
        return {
            **base,
            "export_generated": True,
            "export_path": metadata.get("export_path"),
            "export_metadata_path": metadata.get("metadata_path"),
            "export_compact": compact_review_session_export_summary(storage),
        }
    except Exception as exc:
        return {**base, "export_error": str(exc)}


def compact_review_session_export_summary(storage: LocalStorage) -> dict[str, Any]:
    metadata = load_latest_review_session_export_metadata(storage)
    history = _load_export_history(storage)
    empty = {
        "available": False,
        "created_at": None,
        "export_path": None,
        "metadata_path": None,
        "session_id": None,
        "operator": None,
        "comparison_status": None,
        "open_attention_count": 0,
        "history_count": len(history),
        "verified_mrms": False,
        "local_export_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }
    if metadata is None:
        return empty
    return {
        "available": True,
        "created_at": metadata.get("created_at"),
        "export_path": metadata.get("export_path"),
        "metadata_path": metadata.get("metadata_path"),
        "session_id": metadata.get("session_id"),
        "operator": metadata.get("operator"),
        "comparison_status": metadata.get("comparison_status"),
        "open_attention_count": int(metadata.get("open_attention_count", 0)),
        "history_count": len(history),
        "verified_mrms": False,
        "local_export_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def build_review_export_regeneration_hint(storage: LocalStorage) -> dict[str, Any]:
    """Suggest when operator should re-export review session summary (local review only)."""
    export = load_latest_review_session_export_metadata(storage)
    sessions = load_review_sessions(storage)
    latest_session = sessions[0] if sessions else None
    comparison = load_latest_review_session_comparison(storage)
    digest_hint = build_digest_regeneration_hint(storage)

    recommended = False
    reason: Optional[str] = None

    if latest_session is None:
        reason = "no_review_session"
    elif export is None:
        recommended = True
        reason = "review_export_missing"
    elif export.get("session_id") != latest_session.get("session_id"):
        recommended = True
        reason = "latest_review_session_newer_than_export"
    elif comparison and export.get("comparison_compared_at") != comparison.get("compared_at"):
        recommended = True
        reason = "latest_comparison_newer_than_export"
    elif _is_older(export.get("created_at"), latest_session.get("created_at")):
        recommended = True
        reason = "latest_review_session_newer_than_export"
    elif comparison and _is_older(export.get("created_at"), comparison.get("compared_at")):
        recommended = True
        reason = "latest_comparison_newer_than_export"
    elif digest_hint.get("digest_regeneration_recommended"):
        recommended = True
        reason = f"digest_regeneration_recommended_{digest_hint.get('reason') or 'unknown'}"

    return {
        "review_export_regeneration_recommended": recommended,
        "reason": reason,
        "suggested_command": SUGGESTED_EXPORT_COMMAND if recommended else None,
        "latest_export_at": (export or {}).get("created_at"),
        "latest_session_at": (latest_session or {}).get("created_at"),
        "latest_comparison_at": (comparison or {}).get("compared_at"),
        "digest_regeneration_recommended": bool(digest_hint.get("digest_regeneration_recommended")),
        "digest_regeneration_reason": digest_hint.get("reason"),
        "verified_mrms": False,
        "local_export_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def compact_scheduled_review_export(
    scheduled: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    """Compact review export step status from the latest scheduled validation report."""
    if scheduled is None:
        return None
    return {
        "review_export_requested": bool(scheduled.get("review_export_requested")),
        "review_export_generated": bool(scheduled.get("review_export_generated")),
        "review_export_path": scheduled.get("review_export_path"),
        "review_export_metadata_path": scheduled.get("review_export_metadata_path"),
        "review_export_reason": scheduled.get("review_export_reason"),
        "review_export_elapsed_seconds": scheduled.get("review_export_elapsed_seconds"),
        "verified_mrms": False,
        "local_export_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def build_review_session_export_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_review_session_export_metadata(storage)
    history = _load_export_history(storage)[:MAX_EXPORT_HISTORY]
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_export_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "latest": latest,
        "count": len(history),
        "max_entries": MAX_EXPORT_HISTORY,
        "entries": history,
        "compact": compact_review_session_export_summary(storage),
        "regeneration_hint": build_review_export_regeneration_hint(storage),
    }
