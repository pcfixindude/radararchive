"""Generate local operator handoff checklist — does NOT verify MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.catalog_status import build_catalog_status
from backend.app.services.mrms_proof_bundle import load_latest_proof_bundle_manifest
from backend.app.services.mrms_proof_bundle_diff import load_latest_proof_bundle_diff
from backend.app.services.mrms_proof_regression import load_proof_regression_report
from backend.app.services.mrms_proof_report import load_mrms_proof_report
from backend.app.services.mrms_signoff import compact_signoff_summary, load_signoffs
from backend.app.services.render_queue import get_queue_summary
from backend.app.services.storage import LocalStorage
from backend.app.services.operator_guidance import build_operator_guidance
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_failure_log import load_recent_validation_failures
from backend.app.services.validation_report_store import load_latest_scheduled_validation_report

HANDOFF_MD_PATH = "dev/mrms_operator_handoff_latest.md"
HANDOFF_JSON_PATH = "dev/mrms_operator_handoff_latest.json"

REVIEW_CHECKLIST_ITEMS = [
    "Review latest proof bundle",
    "Review proof bundle diff",
    "Review escalation metrics",
    "Review recent failures",
    "Confirm decoder status",
    "Confirm tiles were actually written if applicable",
    "Confirm production remains disabled unless intentionally testing",
    "Confirm verified_mrms remains false",
    "Record local acknowledgment or sign-off if appropriate",
]


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def generate_operator_handoff(
    session: Session,
    storage: LocalStorage,
    *,
    diff_report: Optional[dict[str, Any]] = None,
    trigger_reason: Optional[str] = None,
    auto_generated: bool = False,
    include_escalation_review: bool = False,
    scheduled_context: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Write local operator handoff Markdown + JSON metadata; return record."""
    created_at = _utc_now()
    bundle = load_latest_proof_bundle_manifest(storage)
    proof = load_mrms_proof_report(storage)
    regression = load_proof_regression_report(storage)
    signoff = compact_signoff_summary(storage)
    alert = load_validation_alert(storage)
    scheduled = scheduled_context or load_latest_scheduled_validation_report(storage)
    catalog = build_catalog_status(session)
    queue = get_queue_summary(session)
    failures = load_recent_validation_failures(storage, limit=10)
    diff = diff_report if diff_report is not None else load_latest_proof_bundle_diff(storage)

    escalation_metrics: Optional[dict[str, Any]] = None
    escalation_current: Optional[dict[str, Any]] = None
    latest_ack: Optional[dict[str, Any]] = None
    digest_metadata: Optional[dict[str, Any]] = None
    if include_escalation_review:
        from backend.app.services.proof_bundle_diff_acknowledgment import (
            load_latest_diff_acknowledgment,
        )
        from backend.app.services.proof_bundle_diff_escalation import (
            build_proof_bundle_diff_escalation,
        )
        from backend.app.services.proof_bundle_diff_escalation_digest import (
            load_latest_escalation_digest_metadata,
        )
        from backend.app.services.proof_bundle_diff_escalation_metrics import (
            build_proof_bundle_diff_escalation_metrics,
        )
        from backend.app.services.grib2_inspector import detect_decoder_availability

        escalation_metrics = build_proof_bundle_diff_escalation_metrics(storage)
        escalation_current = build_proof_bundle_diff_escalation(storage)
        latest_ack = load_latest_diff_acknowledgment(storage)
        digest_metadata = load_latest_escalation_digest_metadata(storage)
        decoder_available = detect_decoder_availability()
    else:
        decoder_available = None

    guidance_items: list[dict[str, Any]] = []
    if alert and alert.get("operator_attention_needed"):
        guidance_items = build_operator_guidance(alert)
    elif auto_generated and diff:
        guidance_items = build_operator_guidance(
            {
                "operator_attention_needed": True,
                "proof_bundle_diff_attention": True,
                "proof_bundle_diff_status": diff.get("overall_diff_status"),
                "grouped_failure_causes": [],
            }
        )

    questions = [
        "Did you review the latest proof report JSON and criteria counts?",
        "Are proof regressions acknowledged or resolved with new evidence?",
        "Is the validation alert status acceptable for this review window?",
        "Are known prototype limitations documented in sign-off or notes?",
        "Is production rendering flag state intentional (expected disabled by default)?",
        "Were recent validation failures reviewed and triaged?",
    ]

    md_lines = [
        "# MRMS Operator Handoff Checklist (Local Review Only)",
        "",
        "> **This checklist is supporting review evidence only.**",
        "> It does **NOT** verify MRMS production output.",
        "> `verified_mrms` remains **false**.",
        "> Generating this checklist does **NOT** enable production rendering.",
        "",
        f"Generated at (UTC): {created_at}",
    ]
    if auto_generated:
        md_lines.extend(
            [
                "",
                "## Auto-generation (scheduled handoff)",
                "",
                f"- Trigger: {_format_value(trigger_reason)}",
                "- Source: scheduled validation with `--handoff` or `--digest` (local operator workflow only)",
                "- Does **not** verify MRMS or enable production rendering",
                "- Does **not** send external notifications",
            ]
        )
    md_lines.extend(
        [
        "",
        "## Latest proof bundle",
        "",
        f"- Bundle ID: {_format_value((bundle or {}).get('bundle_id'))}",
        f"- Created at: {_format_value((bundle or {}).get('created_at'))}",
        f"- Folder: {_format_value((bundle or {}).get('bundle_folder'))}",
        f"- ZIP: {_format_value((bundle or {}).get('zip_path'))}",
        f"- File count: {_format_value((bundle or {}).get('file_count'))}",
        "",
        "## Latest proof report",
        "",
        f"- Overall status: {_format_value((proof or {}).get('overall_status'))}",
        f"- Frame count: {_format_value((proof or {}).get('frame_count'))}",
        f"- Generated at: {_format_value((proof or {}).get('generated_at'))}",
        f"- verified_mrms: false",
        "",
        "## Latest proof regression",
        "",
        f"- Regression status: {_format_value((regression or {}).get('regression_status'))}",
        f"- Regression detected: {_format_value((regression or {}).get('regression_detected'))}",
        f"- Checked at: {_format_value((regression or {}).get('checked_at'))}",
        "",
        "## Latest sign-off",
        "",
        f"- Sign-off count: {_format_value(signoff.get('signoff_count'))}",
        f"- Latest sign-off at: {_format_value(signoff.get('latest_signoff_at'))}",
        f"- Latest operator: {_format_value(signoff.get('latest_operator'))}",
        f"- Proof regression still active: {_format_value(signoff.get('proof_regression_still_active'))}",
        "",
        "## Latest validation alert",
        "",
        f"- Alert status: {_format_value((alert or {}).get('status'))}",
        f"- Operator attention needed: {_format_value((alert or {}).get('operator_attention_needed'))}",
        f"- Failure count: {_format_value((alert or {}).get('failure_count'))}",
        f"- Warning count: {_format_value((alert or {}).get('warning_count'))}",
        "",
        "## Latest scheduled validation",
        "",
        f"- Ran at: {_format_value((scheduled or {}).get('ran_at'))}",
        f"- Success: {_format_value((scheduled or {}).get('success'))}",
        f"- Exit code: {_format_value((scheduled or {}).get('exit_code'))}",
        "",
        "## Latest catalog status",
        "",
        f"- Total frames: {_format_value(catalog.get('total_frames'))}",
        f"- MRMS discovered frames: {_format_value(catalog.get('mrms_discovered_frames'))}",
        f"- Latest timestamp: {_format_value(catalog.get('latest_timestamp'))}",
        "",
        "## Latest render queue",
        "",
        f"- Queued: {_format_value(queue.queued)}",
        f"- Running: {_format_value(queue.running)}",
        f"- Succeeded: {_format_value(queue.succeeded)}",
        f"- Failed: {_format_value(queue.failed)}",
        "",
        "## Recent validation failures (up to 10)",
        "",
        ]
    )
    if failures:
        for item in failures:
            md_lines.append(
                f"- {item.get('logged_at', '—')}: {item.get('phase', '—')}"
                f"{('/' + item.get('step')) if item.get('step') else ''} — {item.get('error_message', 'warning')}"
            )
    else:
        md_lines.append("- None logged")

    md_lines.extend(
        [
            "",
            "## Latest proof bundle diff",
            "",
            f"- Overall diff status: {_format_value((diff or {}).get('overall_diff_status'))}",
            f"- Evidence changes count: {_format_value((diff or {}).get('evidence_changes_count'))}",
            f"- Checked at: {_format_value((diff or {}).get('checked_at'))}",
            "",
        ]
    )
    evidence_changes = (diff or {}).get("evidence_changes") or []
    if evidence_changes:
        md_lines.append("### Evidence changes (latest diff)")
        md_lines.append("")
        for change in evidence_changes[:10]:
            md_lines.append(
                f"- {change.get('field', '—')}: {change.get('baseline_value', '—')} → "
                f"{change.get('current_value', '—')} ({change.get('direction', '—')})"
            )
        md_lines.append("")

    if include_escalation_review and escalation_metrics is not None:
        md_lines.extend(
            [
                "## Escalation metrics (local review only)",
                "",
                f"- Total snapshots: {_format_value(escalation_metrics.get('total_snapshots'))}",
                f"- Urgent count: {_format_value(escalation_metrics.get('urgent_count'))}",
                f"- Attention count: {_format_value(escalation_metrics.get('attention_count'))}",
                f"- Watch count: {_format_value(escalation_metrics.get('watch_count'))}",
                f"- Current urgent streak: {_format_value(escalation_metrics.get('current_urgent_streak'))}",
                f"- Current attention/urgent streak: "
                f"{_format_value(escalation_metrics.get('current_attention_or_urgent_streak'))}",
                f"- Longest urgent streak: {_format_value(escalation_metrics.get('longest_urgent_streak'))}",
                f"- Stale acknowledgment snapshots: "
                f"{_format_value(escalation_metrics.get('stale_acknowledgment_count'))}",
                "",
            ]
        )
        if digest_metadata:
            md_lines.extend(
                [
                    "## Escalation digest export",
                    "",
                    f"- Generated at: {_format_value(digest_metadata.get('generated_at'))}",
                    f"- Markdown path: `{digest_metadata.get('markdown_path', '—')}`",
                    f"- Metadata path: `{digest_metadata.get('json_path', '—')}`",
                    "> Local digest only — not a notification system; does not verify MRMS.",
                    "",
                ]
            )
        if escalation_current:
            md_lines.extend(
                [
                    "## Current escalation status",
                    "",
                    f"- Level: {_format_value(escalation_current.get('escalation_level'))}",
                    f"- Acknowledgment status: {_format_value(escalation_current.get('acknowledgment_status'))}",
                    f"- Stale acknowledgment: {_format_value(escalation_current.get('stale_acknowledgment'))}",
                    "",
                ]
            )
        if latest_ack:
            md_lines.extend(
                [
                    "## Latest diff alert acknowledgment",
                    "",
                    f"- Created at: {_format_value(latest_ack.get('created_at'))}",
                    f"- Operator: {_format_value(latest_ack.get('operator'))}",
                    f"- Note: {_format_value(latest_ack.get('note'))}",
                    "> Acknowledgment does not clear alerts or verify MRMS.",
                    "",
                ]
            )
        else:
            md_lines.extend(
                [
                    "## Latest diff alert acknowledgment",
                    "",
                    "- No local acknowledgment recorded yet.",
                    "",
                ]
            )
        batch_ctx = (scheduled or {}).get("batch_validation") or {}
        queue_ctx = (scheduled or {}).get("queue_benchmark") or {}
        md_lines.extend(
            [
                "## Decoder and tile write status",
                "",
                f"- Decoder available: {_format_value(decoder_available.any_decoder if decoder_available is not None else None)}",
                f"- Batch tiles written: {_format_value(batch_ctx.get('tiles_written', 0))}",
                f"- Queue benchmark tiles written: {_format_value(queue_ctx.get('total_tiles_written', 0))}",
                f"- Production rendering enabled: {_format_value(settings.enable_production_radar_tiles)}",
                "",
            ]
        )

    if guidance_items:
        md_lines.extend(
            [
                "## Runbook guidance references",
                "",
                "> Review aids only — not verification or production promotion.",
                "",
            ]
        )
        for item in guidance_items:
            anchor = item.get("anchor") or ""
            section = item.get("section_label") or item.get("title")
            md_lines.append(f"- **{item.get('title')}** — `{item.get('path')}` — section: {section}")
            if anchor:
                md_lines.append(f"  - Anchor: `{anchor}`")
            if item.get("suggested_action"):
                md_lines.append(f"  - Suggested action: {item.get('suggested_action')}")
        md_lines.append("")

    md_lines.extend(
        [
            "## Operator review questions",
            "",
        ]
    )
    for index, question in enumerate(questions, start=1):
        md_lines.append(f"{index}. [ ] {question}")

    if include_escalation_review:
        md_lines.extend(
            [
                "",
                "## Operator review checklist (Phase 39)",
                "",
                "> Local checklist only — does not verify MRMS, clear alerts, or enable production.",
                "",
            ]
        )
        for index, item in enumerate(REVIEW_CHECKLIST_ITEMS, start=1):
            md_lines.append(f"{index}. [ ] {item}")

    md_lines.extend(
        [
            "",
            "## Explicit attestation",
            "",
            "- [ ] I understand this handoff checklist does **not** certify verified MRMS.",
            "- [ ] I confirm `verified_mrms` must remain **false** until a future explicit launch review.",
            "",
            "## Related commands",
            "",
            "```bash",
            "make mrms-proof-bundle",
            "make mrms-proof-bundle-diff",
            "make mrms-operator-handoff",
            "make proof-bundle-diff-escalation-metrics",
            "make proof-bundle-diff-escalation-digest",
            "make scheduled-proof-bundle-digest",
            "make mrms-signoff",
            "```",
        ]
    )

    markdown = "\n".join(md_lines) + "\n"
    md_repo = storage.normalize_path(HANDOFF_MD_PATH)
    storage.ensure_directories(md_repo.rsplit("/", 1)[0])
    md_abs = storage.absolute_path(md_repo)
    md_abs.write_text(markdown, encoding="utf-8")

    record: dict[str, Any] = {
        "created_at": created_at,
        "markdown_path": md_repo,
        "question_count": len(questions),
        "recent_failures_count": len(failures),
        "proof_bundle_id": (bundle or {}).get("bundle_id"),
        "proof_status": (proof or {}).get("overall_status"),
        "regression_status": (regression or {}).get("regression_status"),
        "signoff_count": signoff.get("signoff_count", 0),
        "alert_status": (alert or {}).get("status"),
        "scheduled_success": (scheduled or {}).get("success"),
        "catalog_total_frames": catalog.get("total_frames"),
        "queue_succeeded": queue.succeeded,
        "diff_status": (diff or {}).get("overall_diff_status"),
        "auto_generated": auto_generated,
        "trigger_reason": trigger_reason,
        "guidance_item_count": len(guidance_items),
        "include_escalation_review": include_escalation_review,
        "digest_path": (digest_metadata or {}).get("markdown_path"),
        "digest_metadata_path": (digest_metadata or {}).get("json_path"),
        "acknowledgment_status": (escalation_current or {}).get("acknowledgment_status")
        if escalation_current
        else None,
        "stale_acknowledgment": (escalation_current or {}).get("stale_acknowledgment")
        if escalation_current
        else None,
        "escalation_level": (escalation_current or {}).get("escalation_level")
        if escalation_current
        else None,
        "review_checklist_count": len(REVIEW_CHECKLIST_ITEMS) if include_escalation_review else 0,
        "verified_mrms": False,
        "local_handoff_only": True,
        "does_not_enable_production": True,
        "production_rendering_enabled": settings.enable_production_radar_tiles,
        "placeholder_default": not settings.enable_production_radar_tiles
        and not settings.enable_decoded_tiles,
        "prototype": True,
    }

    json_repo = storage.normalize_path(HANDOFF_JSON_PATH)
    storage.absolute_path(json_repo).write_text(
        json.dumps(record, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    record["json_path"] = json_repo
    return record


def load_latest_operator_handoff(storage: LocalStorage) -> Optional[dict[str, Any]]:
    repo_path = storage.normalize_path(HANDOFF_JSON_PATH)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return None
    try:
        return json.loads(abs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def compact_operator_handoff_status(
    storage: LocalStorage,
    scheduled: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    record = load_latest_operator_handoff(storage)
    if record is None and scheduled is None:
        return {
            "available": False,
            "verified_mrms": False,
            "local_handoff_only": True,
            "does_not_enable_production": True,
            "prototype": True,
        }
    base: dict[str, Any] = {
        "available": record is not None,
        "created_at": (record or {}).get("created_at"),
        "markdown_path": (record or {}).get("markdown_path"),
        "json_path": (record or {}).get("json_path"),
        "question_count": int((record or {}).get("question_count", 0)),
        "diff_status": (record or {}).get("diff_status"),
        "auto_generated": bool((record or {}).get("auto_generated")),
        "trigger_reason": (record or {}).get("trigger_reason"),
        "include_escalation_review": bool((record or {}).get("include_escalation_review")),
        "digest_path": (record or {}).get("digest_path"),
        "digest_metadata_path": (record or {}).get("digest_metadata_path"),
        "acknowledgment_status": (record or {}).get("acknowledgment_status"),
        "stale_acknowledgment": (record or {}).get("stale_acknowledgment"),
        "escalation_level": (record or {}).get("escalation_level"),
        "review_checklist_count": int((record or {}).get("review_checklist_count", 0)),
        "verified_mrms": False,
        "local_handoff_only": True,
        "does_not_enable_production": True,
        "prototype": True,
    }
    if scheduled:
        base.update(
            {
                "handoff_requested": bool(scheduled.get("handoff_requested")),
                "handoff_generated": bool(scheduled.get("handoff_generated")),
                "handoff_reason": scheduled.get("handoff_reason"),
                "scheduled_handoff_path": scheduled.get("handoff_path"),
                "diff_status_that_triggered_handoff": scheduled.get(
                    "diff_status_that_triggered_handoff"
                ),
            }
        )
    return base
