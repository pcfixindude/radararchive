"""Local Markdown digest export for escalation history — not verified MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.proof_bundle_diff_acknowledgment import load_latest_diff_acknowledgment
from backend.app.services.proof_bundle_diff_escalation import (
    build_proof_bundle_diff_escalation,
)
from backend.app.services.proof_bundle_diff_escalation_history import (
    compact_escalation_history_entry,
    load_recent_proof_bundle_diff_escalation_history,
)
from backend.app.services.proof_bundle_diff_escalation_metrics import (
    build_proof_bundle_diff_escalation_metrics,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import load_validation_alert

DIGEST_MD_PATH = "dev/proof_bundle_diff_escalation_digest_latest.md"
DIGEST_JSON_PATH = "dev/proof_bundle_diff_escalation_digest_latest.json"


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _digest_md_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(DIGEST_MD_PATH)


def _digest_json_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(DIGEST_JSON_PATH)


def load_latest_escalation_digest_metadata(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_digest_json_repo_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _build_digest_markdown(
    *,
    generated_at: str,
    metrics: dict[str, Any],
    escalation: dict[str, Any],
    recent_snapshots: list[dict[str, Any]],
    latest_ack: Optional[dict[str, Any]],
    alert: Optional[dict[str, Any]],
    markdown_path: str,
) -> str:
    guidance_items = escalation.get("guidance_items") or []
    lines = [
        "# Proof Bundle Diff Escalation Digest (Local Review Only)",
        "",
        f"Generated at: {generated_at}",
        "",
        "> **WARNING:** This digest is local operator review evidence only.",
        "> It does **NOT** verify MRMS, enable production rendering, or clear validation alerts.",
        "> No email, SMS, Slack, webhooks, or push notifications are sent.",
        "",
        "## Latest escalation",
        "",
        f"- Level: `{escalation.get('escalation_level')}`",
        f"- Reason: {escalation.get('reason', '')}",
        f"- Latest diff status: {escalation.get('latest_diff_status')}",
        f"- Acknowledgment status: {escalation.get('acknowledgment_status')}",
        f"- Stale acknowledgment: {escalation.get('stale_acknowledgment')}",
        f"- Suggested next action: {escalation.get('suggested_next_action', '')}",
        "",
        "## Trend metrics",
        "",
        f"- Total snapshots: {metrics.get('total_snapshots', 0)}",
        f"- Urgent count: {metrics.get('urgent_count', 0)}",
        f"- Attention count: {metrics.get('attention_count', 0)}",
        f"- Watch count: {metrics.get('watch_count', 0)}",
        f"- None count: {metrics.get('none_count', 0)}",
        f"- Current urgent streak: {metrics.get('current_urgent_streak', 0)}",
        f"- Current attention/urgent streak: {metrics.get('current_attention_or_urgent_streak', 0)}",
        f"- Longest urgent streak: {metrics.get('longest_urgent_streak', 0)}",
        f"- Longest attention/urgent streak: {metrics.get('longest_attention_or_urgent_streak', 0)}",
        f"- First urgent at: {metrics.get('first_urgent_at') or '—'}",
        f"- Last urgent at: {metrics.get('last_urgent_at') or '—'}",
        f"- Stale acknowledgment snapshots: {metrics.get('stale_acknowledgment_count', 0)}",
        "",
        "## Recent escalation snapshots",
        "",
    ]
    if recent_snapshots:
        for entry in recent_snapshots:
            lines.append(
                f"- {entry.get('created_at')}: **{entry.get('escalation_level')}** "
                f"({entry.get('latest_diff_status')}) — {entry.get('reason', '')}"
            )
    else:
        lines.append("- No escalation history snapshots recorded yet.")
    lines.extend(
        [
            "",
            "## Latest acknowledgment",
            "",
        ]
    )
    if latest_ack:
        lines.append(
            f"- {latest_ack.get('created_at')}: {latest_ack.get('operator')} — "
            f"{latest_ack.get('note', '')}"
        )
    else:
        lines.append("- No local diff alert acknowledgment recorded.")
    lines.extend(["", "## Runbook / guidance", ""])
    if guidance_items:
        for item in guidance_items:
            anchor = item.get("anchor") or ""
            path = item.get("path") or ""
            label = item.get("section_label") or item.get("title") or ""
            suffix = f"#{anchor}" if anchor else ""
            lines.append(f"- {label}: `{path}{suffix}`")
    else:
        lines.append("- No escalation guidance items for current state.")
    lines.extend(["", "## Validation alert", ""])
    if alert:
        lines.append(f"- Status: `{alert.get('status')}`")
        lines.append(
            f"- Operator attention needed: {alert.get('operator_attention_needed', False)}"
        )
        lines.append(f"- Updated at: {alert.get('updated_at')}")
        if alert.get("suggested_next_action"):
            lines.append(f"- Suggested next action: {alert.get('suggested_next_action')}")
    else:
        lines.append("- No validation alert marker persisted.")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- `verified_mrms`: false",
            f"- Production rendering enabled: {settings.enable_production_radar_tiles}",
            "- Digest does not clear alerts or mutate catalog/render gates.",
            f"- Digest path: `{markdown_path}`",
            "",
        ]
    )
    return "\n".join(lines)


def export_proof_bundle_diff_escalation_digest(storage: LocalStorage) -> dict[str, Any]:
    """Write local Markdown digest and JSON metadata; return metadata record."""
    generated_at = _utc_now()
    metrics = build_proof_bundle_diff_escalation_metrics(storage)
    escalation = build_proof_bundle_diff_escalation(storage)
    recent = [
        compact_escalation_history_entry(item)
        for item in load_recent_proof_bundle_diff_escalation_history(storage, limit=10)
        if item
    ]
    latest_ack = load_latest_diff_acknowledgment(storage)
    alert = load_validation_alert(storage)

    md_repo = _digest_md_repo_path(storage)
    json_repo = _digest_json_repo_path(storage)
    storage.ensure_directories(md_repo.rsplit("/", 1)[0])
    md_abs = storage.absolute_path(md_repo)
    markdown = _build_digest_markdown(
        generated_at=generated_at,
        metrics=metrics,
        escalation=escalation,
        recent_snapshots=[item for item in recent if item],
        latest_ack=latest_ack,
        alert=alert,
        markdown_path=md_repo,
    )
    md_abs.write_text(markdown, encoding="utf-8")

    metadata = {
        "generated_at": generated_at,
        "markdown_path": md_repo,
        "json_path": json_repo,
        "latest_escalation_level": escalation.get("escalation_level"),
        "metrics": metrics,
        "snapshot_count": metrics.get("total_snapshots", 0),
        "urgent_count": metrics.get("urgent_count", 0),
        "attention_count": metrics.get("attention_count", 0),
        "verified_mrms": False,
        "local_digest_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }
    storage.absolute_path(json_repo).write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return metadata


def compact_proof_bundle_diff_escalation_digest(storage: LocalStorage) -> dict[str, Any]:
    metadata = load_latest_escalation_digest_metadata(storage)
    if metadata is None:
        return {
            "available": False,
            "verified_mrms": False,
            "local_digest_only": True,
            "does_not_clear_alerts": True,
            "does_not_enable_production": True,
            "no_external_notifications": True,
            "prototype": True,
        }
    return {
        "available": True,
        "generated_at": metadata.get("generated_at"),
        "markdown_path": metadata.get("markdown_path"),
        "json_path": metadata.get("json_path"),
        "latest_escalation_level": metadata.get("latest_escalation_level"),
        "snapshot_count": metadata.get("snapshot_count", 0),
        "urgent_count": metadata.get("urgent_count", 0),
        "attention_count": metadata.get("attention_count", 0),
        "verified_mrms": False,
        "local_digest_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def compact_scheduled_digest(scheduled: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Compact digest step status from the latest scheduled validation report."""
    if scheduled is None:
        return None
    return {
        "digest_requested": bool(scheduled.get("digest_requested")),
        "digest_generated": bool(scheduled.get("digest_generated")),
        "digest_path": scheduled.get("digest_path"),
        "digest_metadata_path": scheduled.get("digest_metadata_path"),
        "digest_reason": scheduled.get("digest_reason"),
        "digest_elapsed_seconds": scheduled.get("digest_elapsed_seconds"),
        "verified_mrms": False,
        "local_digest_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def build_proof_bundle_diff_escalation_digest_payload(storage: LocalStorage) -> dict[str, Any]:
    metadata = load_latest_escalation_digest_metadata(storage)
    md_repo = _digest_md_repo_path(storage)
    md_abs = storage.absolute_path(md_repo)
    markdown = None
    if md_abs.is_file():
        try:
            markdown = md_abs.read_text(encoding="utf-8")
        except OSError:
            markdown = None
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_digest_only": True,
        "does_not_clear_alerts": True,
        "digest": metadata,
        "markdown": markdown,
        "compact": compact_proof_bundle_diff_escalation_digest(storage),
    }
