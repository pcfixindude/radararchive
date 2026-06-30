"""MRMS render candidate preflight — local advisory checklist only, not verified MRMS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.grib2_inspector import detect_decoder_availability
from backend.app.services.mrms_proof_report import load_mrms_proof_report
from backend.app.services.mrms_visual_review import compact_mrms_visual_review
from backend.app.services.mrms_visual_review_hint import compact_visual_review_hint
from backend.app.services.mrms_visual_review_sample_readiness import (
    READINESS_CANDIDATE_READY,
    STATUS_QUESTIONABLE,
    STATUS_REJECTED,
    STATUS_UNREVIEWED,
    ISSUE_MISSING_ARTIFACT,
    ISSUE_NEEDS_FOLLOWUP,
    ISSUE_STALE,
    ISSUE_SUSPICIOUS_VISUAL,
    compute_readiness_summary,
)
from backend.app.services.mrms_visual_review_sample_set import compact_visual_review_sample_set
from backend.app.services.mrms_proof_bundle import compact_proof_bundle_status
from backend.app.services.mrms_proof_report import compact_mrms_proof_report
from backend.app.services.operator_guidance import RUNBOOK_PATH, VERIFIED_CRITERIA_PATH
from backend.app.services.operator_review_status import compact_operator_review_status
from backend.app.services.mrms_render_candidate_preflight_attention import (
    compact_preflight_attention,
)
from backend.app.services.storage import LocalStorage

PREFLIGHT_JSON = "dev/mrms_render_candidate_preflight.json"
PREFLIGHT_MD = "dev/mrms_render_candidate_preflight.md"

SUGGESTED_PREFLIGHT_COMMAND = "make mrms-render-candidate-preflight"

PREFLIGHT_BLOCKED = "blocked"
PREFLIGHT_NEEDS_REVIEW = "needs_review"
PREFLIGHT_CANDIDATE_READY = "candidate_preflight_ready"

REQUIRED_DOC_PATHS = (
    RUNBOOK_PATH,
    VERIFIED_CRITERIA_PATH,
    "docs/GRIB2_DECODE.md",
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _preflight_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(PREFLIGHT_JSON)


def _preflight_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(PREFLIGHT_MD)


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_advisory_preflight_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "does_not_download_or_decode": True,
        "does_not_create_production_tiles": True,
        "no_external_notifications": True,
        "candidate_preflight_ready_is_not_production_authorization": True,
        "prototype": True,
    }


def _check_item(
    *,
    check_id: str,
    passed: bool,
    message: str,
    severity: str = "block",
    evidence: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "passed": passed,
        "severity": severity,
        "message": message,
        "evidence": evidence or {},
    }


def _required_docs_status() -> list[dict[str, Any]]:
    root = _project_root()
    items: list[dict[str, Any]] = []
    for relative_path in REQUIRED_DOC_PATHS:
        abs_path = root / relative_path
        items.append(
            {
                "path": relative_path,
                "available": abs_path.is_file(),
            }
        )
    return items


def gather_preflight_evidence(storage: LocalStorage) -> dict[str, Any]:
    decoder = detect_decoder_availability()
    proof = load_mrms_proof_report(storage)
    proof_compact = compact_mrms_proof_report(proof) or {}
    if isinstance(proof_compact, dict):
        proof_compact = {
            **proof_compact,
            "available": proof is not None and bool(proof.get("generated_at")),
        }
    sample_readiness = compute_readiness_summary(storage)
    return {
        "safety_flags": {
            "verified_mrms": False,
            "enable_production_radar_tiles": settings.enable_production_radar_tiles,
            "enable_decoded_tiles": settings.enable_decoded_tiles,
            "placeholder_default": not settings.enable_production_radar_tiles
            and not settings.enable_decoded_tiles,
        },
        "visual_review": compact_mrms_visual_review(storage),
        "visual_review_hint": compact_visual_review_hint(storage),
        "sample_set": compact_visual_review_sample_set(storage),
        "sample_readiness": sample_readiness,
        "operator_review_status": compact_operator_review_status(storage),
        "preflight_attention": compact_preflight_attention(storage),
        "mrms_proof": proof_compact,
        "proof_bundle": compact_proof_bundle_status(storage),
        "decoder_availability": {
            "any_decoder": decoder.any_decoder,
            "wgrib2": decoder.wgrib2,
            "gdal": decoder.gdal,
            "summary_message": decoder.summary_message(),
        },
        "required_docs": _required_docs_status(),
    }


def evaluate_render_candidate_preflight(
    evidence: dict[str, Any],
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blocking_items: list[str] = []
    warnings: list[str] = []

    safety = evidence.get("safety_flags") or {}
    visual_review = evidence.get("visual_review") or {}
    sample_set = evidence.get("sample_set") or {}
    sample_readiness = evidence.get("sample_readiness") or {}
    required_docs = evidence.get("required_docs") or []

    checks.append(
        _check_item(
            check_id="verified_mrms_false",
            passed=not bool(safety.get("verified_mrms")),
            message="verified_mrms must remain false",
            evidence={"verified_mrms": safety.get("verified_mrms")},
        )
    )
    checks.append(
        _check_item(
            check_id="production_rendering_disabled",
            passed=not bool(safety.get("enable_production_radar_tiles")),
            message="production rendering gate must remain disabled",
            evidence={"enable_production_radar_tiles": safety.get("enable_production_radar_tiles")},
        )
    )
    checks.append(
        _check_item(
            check_id="placeholder_default_preserved",
            passed=bool(safety.get("placeholder_default")),
            message="placeholder-first default must be preserved (decoded/production tiles off)",
            evidence={
                "placeholder_default": safety.get("placeholder_default"),
                "enable_decoded_tiles": safety.get("enable_decoded_tiles"),
            },
        )
    )
    checks.append(
        _check_item(
            check_id="visual_review_available",
            passed=bool(visual_review.get("available")),
            message="latest visual review manifest is required",
            evidence={"available": visual_review.get("available")},
        )
    )
    checks.append(
        _check_item(
            check_id="sample_set_available",
            passed=bool(sample_set.get("available")) and int(sample_set.get("entry_count") or 0) > 0,
            message="visual review sample set with entries is required",
            evidence={
                "available": sample_set.get("available"),
                "entry_count": sample_set.get("entry_count"),
            },
        )
    )
    readiness_level = sample_readiness.get("readiness_level")
    checks.append(
        _check_item(
            check_id="sample_readiness_present",
            passed=bool(readiness_level),
            message="sample-set readiness summary is required",
            evidence={"readiness_level": readiness_level},
        )
    )
    checks.append(
        _check_item(
            check_id="sample_readiness_candidate_ready",
            passed=readiness_level == READINESS_CANDIDATE_READY,
            message="sample-set readiness must be candidate_ready",
            evidence={"readiness_level": readiness_level},
        )
    )

    entry_summaries = sample_readiness.get("entry_summaries") or []
    sample_issue_messages: list[str] = []
    for entry in entry_summaries:
        status = str(entry.get("status") or STATUS_UNREVIEWED)
        tags = set(entry.get("issue_tags") or [])
        sample_key = entry.get("sample_key") or entry.get("timestamp")
        if status in {STATUS_REJECTED, STATUS_QUESTIONABLE, STATUS_UNREVIEWED}:
            sample_issue_messages.append(f"{sample_key}: status={status}")
        if entry.get("missing_artifacts"):
            sample_issue_messages.append(f"{sample_key}: missing_artifacts")
        if entry.get("stale_visual_review"):
            sample_issue_messages.append(f"{sample_key}: stale_visual_review")
        for tag in (ISSUE_SUSPICIOUS_VISUAL, ISSUE_NEEDS_FOLLOWUP, ISSUE_MISSING_ARTIFACT, ISSUE_STALE):
            if tag in tags:
                sample_issue_messages.append(f"{sample_key}: tag={tag}")

    checks.append(
        _check_item(
            check_id="sample_review_issues_clear",
            passed=not sample_issue_messages,
            message="sample review must have no rejected/questionable/unreviewed/stale/missing/suspicious/follow-up items",
            evidence={"issues": sample_issue_messages},
        )
    )

    missing_docs = [item["path"] for item in required_docs if not item.get("available")]
    checks.append(
        _check_item(
            check_id="required_docs_present",
            passed=not missing_docs,
            message="required local docs/checklists must be present",
            evidence={"missing_docs": missing_docs, "required_docs": required_docs},
        )
    )

    proof = evidence.get("mrms_proof") or {}
    if not proof.get("available"):
        checks.append(
            _check_item(
                check_id="mrms_proof_available",
                passed=False,
                message="MRMS proof report not found — review recommended before render candidate path",
                severity="warn",
            )
        )
    proof_bundle = evidence.get("proof_bundle") or {}
    if not proof_bundle.get("available"):
        checks.append(
            _check_item(
                check_id="proof_bundle_available",
                passed=False,
                message="proof bundle manifest not found — export recommended for evidence review",
                severity="warn",
            )
        )

    decoder = evidence.get("decoder_availability") or {}
    if not decoder.get("any_decoder"):
        checks.append(
            _check_item(
                check_id="decoder_tools_detected",
                passed=False,
                message="no local wgrib2/GDAL detected — future real render path may need tooling",
                severity="warn",
                evidence=decoder,
            )
        )

    operator_status = evidence.get("operator_review_status") or {}
    preflight_attention = evidence.get("preflight_attention") or {}
    operator_attention_blocks = bool(preflight_attention.get("blocks_preflight", True))
    if (
        operator_status.get("status_level") in {"attention", "urgent"}
        and operator_attention_blocks
    ):
        checks.append(
            _check_item(
                check_id="operator_review_status_clear",
                passed=False,
                message="operator review status indicates open attention items",
                severity="warn",
                evidence={
                    "status_level": operator_status.get("status_level"),
                    "status_reason": operator_status.get("status_reason"),
                    "blocks_preflight": operator_attention_blocks,
                    "open_blocking_count": preflight_attention.get("open_blocking_count"),
                },
            )
        )

    visual_hint = evidence.get("visual_review_hint") or {}
    if visual_hint.get("visual_review_regeneration_recommended"):
        checks.append(
            _check_item(
                check_id="visual_review_current",
                passed=False,
                message="visual review regeneration recommended — refresh evidence before render candidate path",
                severity="warn",
                evidence={"reason": visual_hint.get("reason")},
            )
        )

    for check in checks:
        if check["passed"]:
            continue
        if check["severity"] == "block":
            blocking_items.append(check["message"])
        else:
            warnings.append(check["message"])

    if any(not check["passed"] and check["severity"] == "block" for check in checks):
        level = PREFLIGHT_BLOCKED
        reason = "blocking_items_present"
    elif any(not check["passed"] and check["severity"] == "warn" for check in checks):
        level = PREFLIGHT_NEEDS_REVIEW
        reason = "warnings_present"
    else:
        level = PREFLIGHT_CANDIDATE_READY
        reason = "all_preflight_checks_passed"

    return {
        "computed_at": _utc_now(),
        "preflight_level": level,
        "preflight_reason": reason,
        "blocking_items": blocking_items,
        "warnings": warnings,
        "checks": checks,
        "evidence": evidence,
        "json_path": None,
        "markdown_path": None,
        "suggested_command": SUGGESTED_PREFLIGHT_COMMAND,
        **_safety_fields(),
    }


def build_preflight_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MRMS Render Candidate Preflight (Local Advisory Only)",
        "",
        f"Computed at: {report.get('computed_at') or _utc_now()}",
        "",
        "> **WARNING:** This preflight is local operator guidance only.",
        "> `candidate_preflight_ready` is **NOT** verified MRMS and is **NOT** production authorization.",
        "> It does **NOT** clear validation alerts, enable production rendering, download/decode MRMS,",
        "> or create production tiles.",
        "",
        "## Result",
        "",
        f"- Advisory preflight level: **{report.get('preflight_level')}**",
        f"- Reason: {report.get('preflight_reason')}",
        "",
        "## Blocking items",
        "",
    ]
    blocking = report.get("blocking_items") or []
    if blocking:
        lines.extend(f"- {item}" for item in blocking)
    else:
        lines.append("- None")

    lines.extend(["", "## Warnings", ""])
    warnings = report.get("warnings") or []
    if warnings:
        lines.extend(f"- {item}" for item in warnings)
    else:
        lines.append("- None")

    evidence = report.get("evidence") or {}
    sample_readiness = evidence.get("sample_readiness") or {}
    lines.extend(
        [
            "",
            "## Evidence summary",
            "",
            f"- Visual review available: {((evidence.get('visual_review') or {}).get('available'))}",
            f"- Sample set entries: {(evidence.get('sample_set') or {}).get('entry_count', 0)}",
            f"- Sample readiness level: {sample_readiness.get('readiness_level')}",
            f"- Production rendering enabled: {(evidence.get('safety_flags') or {}).get('enable_production_radar_tiles')}",
            f"- Placeholder default preserved: {(evidence.get('safety_flags') or {}).get('placeholder_default')}",
            "",
            "## Suggested local command",
            "",
            f"```bash\n{report.get('suggested_command') or SUGGESTED_PREFLIGHT_COMMAND}\n```",
        ]
    )
    return "\n".join(lines) + "\n"


def save_render_candidate_preflight(
    storage: LocalStorage,
    report: dict[str, Any],
) -> dict[str, Any]:
    json_path = _preflight_json_path(storage)
    md_path = _preflight_md_path(storage)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    report = {
        **report,
        "json_path": json_path,
        "markdown_path": md_path,
        "suggested_command": SUGGESTED_PREFLIGHT_COMMAND,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(
        build_preflight_markdown(report),
        encoding="utf-8",
    )
    return report


def load_render_candidate_preflight(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_preflight_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def generate_render_candidate_preflight(storage: LocalStorage) -> dict[str, Any]:
    evidence = gather_preflight_evidence(storage)
    report = evaluate_render_candidate_preflight(evidence)
    return save_render_candidate_preflight(storage, report)


def compact_render_candidate_preflight(storage: LocalStorage) -> dict[str, Any]:
    latest = load_render_candidate_preflight(storage)
    if latest is None:
        evidence = gather_preflight_evidence(storage)
        evaluated = evaluate_render_candidate_preflight(evidence)
        return {
            "available": False,
            "preflight_level": evaluated.get("preflight_level"),
            "preflight_reason": evaluated.get("preflight_reason"),
            "blocking_items": evaluated.get("blocking_items") or [],
            "warnings": evaluated.get("warnings") or [],
            "computed_at": evaluated.get("computed_at"),
            "json_path": _preflight_json_path(storage),
            "markdown_path": _preflight_md_path(storage),
            "suggested_command": SUGGESTED_PREFLIGHT_COMMAND,
            "evidence_found": {
                "visual_review": bool((evidence.get("visual_review") or {}).get("available")),
                "sample_set": bool((evidence.get("sample_set") or {}).get("available")),
                "sample_readiness": bool((evidence.get("sample_readiness") or {}).get("readiness_level")),
                "required_docs": all(item.get("available") for item in evidence.get("required_docs") or []),
            },
            **_safety_fields(),
        }
    evidence = latest.get("evidence") or {}
    return {
        "available": True,
        "preflight_level": latest.get("preflight_level"),
        "preflight_reason": latest.get("preflight_reason"),
        "blocking_items": latest.get("blocking_items") or [],
        "warnings": latest.get("warnings") or [],
        "computed_at": latest.get("computed_at"),
        "json_path": latest.get("json_path") or _preflight_json_path(storage),
        "markdown_path": latest.get("markdown_path") or _preflight_md_path(storage),
        "suggested_command": latest.get("suggested_command") or SUGGESTED_PREFLIGHT_COMMAND,
        "evidence_found": {
            "visual_review": bool((evidence.get("visual_review") or {}).get("available")),
            "sample_set": bool((evidence.get("sample_set") or {}).get("available")),
            "sample_readiness": bool((evidence.get("sample_readiness") or {}).get("readiness_level")),
            "required_docs": all(item.get("available") for item in evidence.get("required_docs") or []),
        },
        **_safety_fields(),
    }


def build_render_candidate_preflight_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_render_candidate_preflight(storage)
    if latest is None:
        evidence = gather_preflight_evidence(storage)
        evaluated = evaluate_render_candidate_preflight(evidence)
    else:
        evaluated = latest
    return {
        **_safety_fields(),
        "latest": evaluated,
        "compact": compact_render_candidate_preflight(storage),
    }
