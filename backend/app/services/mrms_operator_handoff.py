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
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_failure_log import load_recent_validation_failures
from backend.app.services.validation_report_store import load_latest_scheduled_validation_report

HANDOFF_MD_PATH = "dev/mrms_operator_handoff_latest.md"
HANDOFF_JSON_PATH = "dev/mrms_operator_handoff_latest.json"


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def generate_operator_handoff(session: Session, storage: LocalStorage) -> dict[str, Any]:
    """Write local operator handoff Markdown + JSON metadata; return record."""
    created_at = _utc_now()
    bundle = load_latest_proof_bundle_manifest(storage)
    proof = load_mrms_proof_report(storage)
    regression = load_proof_regression_report(storage)
    signoff = compact_signoff_summary(storage)
    alert = load_validation_alert(storage)
    scheduled = load_latest_scheduled_validation_report(storage)
    catalog = build_catalog_status(session)
    queue = get_queue_summary(session)
    failures = load_recent_validation_failures(storage, limit=10)
    diff = load_latest_proof_bundle_diff(storage)

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
            "## Operator review questions",
            "",
        ]
    )
    for index, question in enumerate(questions, start=1):
        md_lines.append(f"{index}. [ ] {question}")

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


def compact_operator_handoff_status(storage: LocalStorage) -> dict[str, Any]:
    record = load_latest_operator_handoff(storage)
    if record is None:
        return {
            "available": False,
            "verified_mrms": False,
            "local_handoff_only": True,
            "does_not_enable_production": True,
            "prototype": True,
        }
    return {
        "available": True,
        "created_at": record.get("created_at"),
        "markdown_path": record.get("markdown_path"),
        "json_path": record.get("json_path"),
        "question_count": int(record.get("question_count", 0)),
        "diff_status": record.get("diff_status"),
        "verified_mrms": False,
        "local_handoff_only": True,
        "does_not_enable_production": True,
        "prototype": True,
    }
