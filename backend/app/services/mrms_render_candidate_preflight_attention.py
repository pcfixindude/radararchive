"""Resolve operator review attention items for render-candidate preflight — does NOT verify MRMS."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from backend.app.services.mrms_review_session import (
    _build_open_attention_items,
    create_review_session_record,
)
from backend.app.services.operator_review_status import (
    STATUS_ATTENTION,
    STATUS_URGENT,
    build_operator_review_status,
)
from backend.app.services.proof_bundle_diff_acknowledgment import create_diff_acknowledgment
from backend.app.services.proof_bundle_diff_escalation import build_proof_bundle_diff_escalation
from backend.app.services.proof_bundle_diff_escalation_digest import (
    export_proof_bundle_diff_escalation_digest,
)
from backend.app.services.proof_bundle_diff_escalation_digest_diff import (
    build_digest_regeneration_hint,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import ALERT_FAILED, load_validation_alert

ATTENTION_JSON = "dev/mrms_render_candidate_preflight_attention_latest.json"
ATTENTION_MD = "dev/mrms_render_candidate_preflight_attention_latest.md"

SUGGESTED_COMMAND = "make mrms-resolve-preflight-attention"

RESOLUTION_OPEN = "open"
RESOLUTION_CLEARED = "cleared"
RESOLUTION_ACKNOWLEDGED = "acknowledged_for_preflight"

STATUS_BLOCKED = "attention_blocked"
STATUS_PARTIAL = "attention_partial"
STATUS_RESOLVED = "attention_resolved_for_preflight"

TYPE_ADVISORY_ACK = "advisory_ack"
TYPE_VISUAL_REFRESH = "visual_refresh"
TYPE_DIGEST_REFRESH = "digest_refresh"
TYPE_DIFF_ACK = "diff_ack"
TYPE_REVIEW_SESSION = "review_session"
TYPE_STALE_ARTIFACT = "stale_runtime_refresh"
TYPE_TOOLING = "tooling_warning"
TYPE_HUMAN_JUDGMENT = "human_judgment"


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_preflight_attention_only": True,
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
        "preflight_attention_is_not_production_authorization": True,
        "prototype": True,
    }


def _attention_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(ATTENTION_JSON)


def _attention_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(ATTENTION_MD)


def _normalize_item_key(text: str) -> str:
    lowered = text.lower().strip()
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    return lowered.strip("_")[:80] or "attention_item"


def _classify_attention_item(text: str) -> tuple[str, bool, str]:
    """Return resolution_type, blocks_preflight, operator_action."""
    lowered = text.lower()
    if "validation alert" in lowered and "operator attention" in lowered:
        return (
            TYPE_HUMAN_JUDGMENT,
            True,
            "Review `make validation-failures` and scheduled validation output; "
            "address real failures or document stub-mode limitations — does not clear alerts.",
        )
    if "proof report" in lowered and "failed" in lowered:
        return (
            TYPE_HUMAN_JUDGMENT,
            True,
            "Run `make mrms-proof-report` and review proof criteria; "
            "failed proof is not verified MRMS.",
        )
    if "proof regression" in lowered:
        return (
            TYPE_HUMAN_JUDGMENT,
            True,
            "Run `make mrms-proof-regression` and compare proof history before preflight.",
        )
    if "digest regeneration" in lowered:
        return (
            TYPE_DIGEST_REFRESH,
            False,
            "Run `make scheduled-proof-bundle-digest` or `make scheduled-proof-bundle-review-export`.",
        )
    if "stale" in lowered and "acknowledgment" in lowered:
        return (
            TYPE_DIFF_ACK,
            False,
            "Run `make proof-bundle-diff-acknowledge` with operator note after re-review.",
        )
    if "escalation level" in lowered:
        return (
            TYPE_HUMAN_JUDGMENT,
            True,
            "Review proof bundle diff escalation guidance and runbook escalation section.",
        )
    if "proof bundle diff status" in lowered:
        return (
            TYPE_ADVISORY_ACK,
            False,
            "Review proof bundle diff and acknowledge locally if reviewed — does not clear alerts.",
        )
    if "wgrib2" in lowered or "gdal" in lowered or "tooling" in lowered:
        return (
            TYPE_TOOLING,
            False,
            "Install wgrib2/GDAL locally or document tooling waiver for future real render path.",
        )
    return (
        TYPE_HUMAN_JUDGMENT,
        True,
        "Review item manually and follow runbook guidance before render-candidate preflight.",
    )


def _status_reason_items(status: dict[str, Any]) -> list[str]:
    items: list[str] = []
    reason = status.get("status_reason")
    if reason == "validation_alert_failed":
        items.append("Operator review status: validation alert failed")
    elif reason == "digest_regeneration_recommended":
        items.append(
            f"Digest regeneration recommended: {status.get('visual_review_hint_reason') or 'see runbook'}"
        )
    elif reason == "visual_review_regeneration_recommended":
        items.append(
            f"Visual review regeneration recommended: {status.get('visual_review_hint_reason') or 'see runbook'}"
        )
    elif reason == "open_review_attention_items":
        items.append("Operator review status: open review attention items")
    elif reason in {STATUS_ATTENTION, STATUS_URGENT}:
        items.append(f"Operator review status: {reason}")
    return items


def gather_operator_attention_inventory(storage: LocalStorage) -> list[dict[str, Any]]:
    status = build_operator_review_status(storage)
    seen: set[str] = set()
    inventory: list[dict[str, Any]] = []

    def add_item(text: str, *, source: str) -> None:
        key = _normalize_item_key(text)
        if key in seen:
            return
        seen.add(key)
        resolution_type, blocks_preflight, operator_action = _classify_attention_item(text)
        inventory.append(
            {
                "item_id": key,
                "text": text,
                "source": source,
                "resolution_type": resolution_type,
                "blocks_preflight": blocks_preflight,
                "status": RESOLUTION_OPEN,
                "operator_action": operator_action,
                "attempted_commands": [],
                "cleared_at": None,
                "notes": None,
            }
        )

    for item in _build_open_attention_items(storage):
        add_item(str(item), source="open_attention_items")
    for item in _status_reason_items(status):
        add_item(str(item), source="operator_review_status")

    if status.get("digest_regeneration_recommended"):
        add_item("Digest regeneration recommended (operator status)", source="operator_status_flag")
    if status.get("visual_review_regeneration_recommended"):
        add_item(
            "Visual review regeneration recommended (operator status)",
            source="operator_status_flag",
        )

    return inventory


def _try_clear_item(
    storage: LocalStorage,
    item: dict[str, Any],
    *,
    operator_initials: str = "PREFLIGHT",
) -> dict[str, Any]:
    """Attempt safe local advisory resolution; never clears validation alerts."""
    resolution_type = item.get("resolution_type")
    attempted: list[str] = []
    updated = dict(item)

    if resolution_type == TYPE_DIFF_ACK:
        escalation = build_proof_bundle_diff_escalation(storage)
        if escalation.get("stale_acknowledgment"):
            attempted.append("proof-bundle-diff-acknowledge")
            create_diff_acknowledgment(
                storage,
                operator_initials=operator_initials,
                note=(
                    "Preflight attention resolution — stale diff acknowledgment reviewed locally; "
                    "does not clear alerts or verify MRMS."
                ),
            )
            updated["status"] = RESOLUTION_CLEARED
            updated["notes"] = "Stale diff acknowledgment recorded locally."
        return {**updated, "attempted_commands": attempted}

    if resolution_type == TYPE_DIGEST_REFRESH:
        hint = build_digest_regeneration_hint(storage)
        if hint.get("digest_regeneration_recommended"):
            attempted.append("scheduled-proof-bundle-digest")
            export_proof_bundle_diff_escalation_digest(storage)
            updated["status"] = RESOLUTION_CLEARED
            updated["notes"] = "Digest refreshed from existing escalation evidence."
        return {**updated, "attempted_commands": attempted}

    if resolution_type == TYPE_ADVISORY_ACK:
        attempted.append("preflight-attention-advisory-ack")
        updated["status"] = RESOLUTION_ACKNOWLEDGED
        updated["notes"] = (
            "Acknowledged for render-candidate preflight path only — does not clear alerts."
        )
        return {**updated, "attempted_commands": attempted}

    if resolution_type == TYPE_REVIEW_SESSION:
        attempted.append("mrms-review-session")
        create_review_session_record(
            storage,
            operator_initials=operator_initials,
            session_notes="Preflight attention resolution review (local advisory only).",
            accepted_limitations=True,
        )
        updated["status"] = RESOLUTION_CLEARED
        updated["notes"] = "New local review session recorded."
        return {**updated, "attempted_commands": attempted}

    return updated


def resolve_preflight_operator_attention(
    storage: LocalStorage,
    *,
    refresh: bool = False,
    operator_initials: str = "PREFLIGHT",
) -> dict[str, Any]:
    inventory_before = gather_operator_attention_inventory(storage)
    status_before = build_operator_review_status(storage)
    alert_before = load_validation_alert(storage) or {}

    inventory = [dict(item) for item in inventory_before]
    refresh_steps: list[dict[str, Any]] = []

    if refresh:
        for index, item in enumerate(inventory):
            if item.get("resolution_type") == TYPE_HUMAN_JUDGMENT:
                continue
            if item.get("resolution_type") == TYPE_TOOLING:
                item["status"] = RESOLUTION_ACKNOWLEDGED
                item["notes"] = "Tooling warning documented for preflight — install optional decoder when needed."
                item["attempted_commands"] = ["document-tooling-waiver"]
                inventory[index] = item
                refresh_steps.append(
                    {"item_id": item["item_id"], "action": "acknowledged_tooling_warning"}
                )
                continue
            updated = _try_clear_item(storage, item, operator_initials=operator_initials)
            if updated.get("status") != RESOLUTION_OPEN:
                refresh_steps.append(
                    {
                        "item_id": updated["item_id"],
                        "action": updated.get("status"),
                        "attempted_commands": updated.get("attempted_commands") or [],
                    }
                )
            inventory[index] = updated

        remaining_open = _build_open_attention_items(storage)
        refresh_steps.append(
            {
                "action": "rebuild_open_attention_items",
                "remaining_count": len(remaining_open),
                "remaining_items": remaining_open,
            }
        )

    open_blocking = [
        item
        for item in inventory
        if item.get("status") == RESOLUTION_OPEN and item.get("blocks_preflight")
    ]
    open_non_blocking = [
        item
        for item in inventory
        if item.get("status") == RESOLUTION_OPEN and not item.get("blocks_preflight")
    ]
    cleared = [item for item in inventory if item.get("status") == RESOLUTION_CLEARED]
    acknowledged = [item for item in inventory if item.get("status") == RESOLUTION_ACKNOWLEDGED]

    if not inventory:
        resolution_status = STATUS_RESOLVED
    elif open_blocking:
        resolution_status = STATUS_BLOCKED
    elif open_non_blocking:
        resolution_status = STATUS_PARTIAL
    else:
        resolution_status = STATUS_RESOLVED

    blocks_preflight = bool(open_blocking)
    status_after = build_operator_review_status(storage)
    alert_after = load_validation_alert(storage) or {}

    next_phase = _next_phase_recommendation(
        blocks_preflight=blocks_preflight,
        open_blocking=open_blocking,
        status_after=status_after,
    )

    return {
        "resolved_at": _utc_now(),
        "resolution_status": resolution_status,
        "blocks_preflight": blocks_preflight,
        "open_attention_items": inventory,
        "open_blocking_items": open_blocking,
        "open_non_blocking_items": open_non_blocking,
        "cleared_items": cleared,
        "acknowledged_items": acknowledged,
        "remaining_open_attention_items": _build_open_attention_items(storage),
        "operator_review_status_before": {
            "status_level": status_before.get("status_level"),
            "status_reason": status_before.get("status_reason"),
            "open_attention_count": status_before.get("open_attention_count"),
        },
        "operator_review_status_after": {
            "status_level": status_after.get("status_level"),
            "status_reason": status_after.get("status_reason"),
            "open_attention_count": status_after.get("open_attention_count"),
        },
        "validation_alert_unchanged": alert_before.get("status") == alert_after.get("status"),
        "alert_status": alert_after.get("status"),
        "refresh_steps": refresh_steps,
        "next_operator_step": _next_operator_step(blocks_preflight, open_blocking),
        "next_phase_recommendation": next_phase,
        "retry_commands": _retry_commands(blocks_preflight, open_blocking),
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }


def _next_operator_step(blocks_preflight: bool, open_blocking: list[dict[str, Any]]) -> str:
    if not blocks_preflight:
        return "Operator attention items resolved for preflight — re-run preflight and milestone audit."
    primary = open_blocking[0] if open_blocking else None
    if primary:
        return f"Resolve blocking attention item: {primary.get('text')} — {primary.get('operator_action')}"
    return "Review remaining operator attention items before render-candidate preflight."


def _retry_commands(blocks_preflight: bool, open_blocking: list[dict[str, Any]]) -> list[str]:
    commands = [
        "make operator-review-status --refresh",
        "make mrms-render-candidate-preflight --refresh",
        "make mrms-resolve-preflight-blockers --refresh",
        "make mrms-readiness-milestone-audit --refresh",
    ]
    if blocks_preflight and open_blocking:
        item = open_blocking[0]
        if "proof report" in str(item.get("text", "")).lower():
            commands.insert(0, "make mrms-proof-report")
        elif "validation alert" in str(item.get("text", "")).lower():
            commands.insert(0, "make validation-failures")
    return commands


def _next_phase_recommendation(
    *,
    blocks_preflight: bool,
    open_blocking: list[dict[str, Any]],
    status_after: dict[str, Any],
) -> str:
    if not blocks_preflight:
        return "Phase 102 — continue gated dry-run plan review (preflight attention resolved)"

    if open_blocking:
        text = str(open_blocking[0].get("text", "")).lower()
        if "proof report" in text:
            return "Phase 102 — remediate proof report failures for preflight"
        if "validation alert" in text:
            return "Phase 102 — remediate validation alert failures for preflight"
    if status_after.get("status_level") in {STATUS_ATTENTION, STATUS_URGENT}:
        return "Phase 102 — resolve remaining operator attention items for preflight"
    return "Phase 102 — resolve remaining operator attention items for preflight"


def build_attention_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MRMS render candidate preflight attention (Phase 101)",
        "",
        "> **WARNING:** Local advisory only — does **NOT** verify MRMS, clear alerts, "
        "or enable production rendering.",
        "",
        f"- Resolved at: {report.get('resolved_at')}",
        f"- Resolution status: **{report.get('resolution_status')}**",
        f"- Blocks preflight: {report.get('blocks_preflight')}",
        f"- Alert unchanged: {report.get('validation_alert_unchanged')}",
        f"- Next operator step: {report.get('next_operator_step')}",
        f"- Next phase: {report.get('next_phase_recommendation')}",
        "",
        "## Attention items",
        "",
    ]
    for item in report.get("open_attention_items") or []:
        lines.append(
            f"- [{item.get('status')}] {item.get('text')} "
            f"({item.get('resolution_type')}, blocks_preflight={item.get('blocks_preflight')})"
        )
        if item.get("operator_action"):
            lines.append(f"  - Action: {item.get('operator_action')}")
    lines.extend(["", "## Retry commands", ""])
    for cmd in report.get("retry_commands") or []:
        lines.append(f"- `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def save_preflight_attention_report(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
    json_path = _attention_json_path(storage)
    md_path = _attention_md_path(storage)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    report = {
        **report,
        "json_path": json_path,
        "markdown_path": md_path,
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(build_attention_markdown(report), encoding="utf-8")
    return report


def load_preflight_attention_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_attention_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def compact_preflight_attention(storage: LocalStorage) -> dict[str, Any]:
    latest = load_preflight_attention_report(storage)
    if latest is None:
        inventory = gather_operator_attention_inventory(storage)
        open_blocking = [item for item in inventory if item.get("blocks_preflight")]
        return {
            "available": False,
            "resolution_status": STATUS_BLOCKED if open_blocking else STATUS_RESOLVED,
            "blocks_preflight": bool(open_blocking),
            "open_attention_count": len(inventory),
            "open_blocking_count": len(open_blocking),
            "open_attention_items": inventory,
            "remaining_open_attention_items": _build_open_attention_items(storage),
            "suggested_command": SUGGESTED_COMMAND,
            **_safety_fields(),
        }
    return {
        "available": True,
        "resolution_status": latest.get("resolution_status"),
        "blocks_preflight": bool(latest.get("blocks_preflight")),
        "open_attention_count": len(latest.get("open_attention_items") or []),
        "open_blocking_count": len(latest.get("open_blocking_items") or []),
        "open_blocking_items": latest.get("open_blocking_items") or [],
        "remaining_open_attention_items": latest.get("remaining_open_attention_items") or [],
        "next_operator_step": latest.get("next_operator_step"),
        "next_phase_recommendation": latest.get("next_phase_recommendation"),
        "retry_commands": latest.get("retry_commands") or [],
        "resolved_at": latest.get("resolved_at"),
        "json_path": latest.get("json_path"),
        "markdown_path": latest.get("markdown_path"),
        "suggested_command": latest.get("suggested_command") or SUGGESTED_COMMAND,
        **_safety_fields(),
    }


def build_preflight_attention_payload(storage: LocalStorage) -> dict[str, Any]:
    return {
        **_safety_fields(),
        "latest": load_preflight_attention_report(storage),
        "compact": compact_preflight_attention(storage),
    }
