"""Validation/proof failure remediation for render-candidate preflight — does NOT verify MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_proof_report import (
    CRITERION_ALERT_HYGIENE,
    CRITERION_DECODER_ARTIFACTS,
    CRITERION_MULTI_FRAME,
    CRITERION_PRODUCTION_PATH,
    CRITERION_REAL_NOAA_SOURCE,
    CRITERION_TILE_OUTPUT,
    load_mrms_proof_report,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import (
    ALERT_FAILED,
    CAUSE_DECODER_UNAVAILABLE,
    CAUSE_NO_GRIB2_ARTIFACT,
    CAUSE_NO_NETWORK,
    CAUSE_PRODUCTION_FLAG_OFF,
    CAUSE_UNKNOWN,
    CAUSE_ZERO_TILES_WRITTEN,
    classify_failure_cause,
    group_validation_failures,
    load_validation_alert,
)
from backend.app.services.validation_failure_log import load_recent_validation_failures

REMEDIATION_JSON = "dev/mrms_render_candidate_validation_remediation_latest.json"
REMEDIATION_MD = "dev/mrms_render_candidate_validation_remediation_latest.md"

SUGGESTED_COMMAND = "make mrms-remediate-validation"

REMEDIATION_STUB_DOCUMENTED = "stub_mode_documented"
REMEDIATION_REAL_REMAIN = "real_failures_remain"
REMEDIATION_PARTIAL = "partial_stub_documented"
REMEDIATION_NO_DATA = "no_validation_data"

CLASS_STUB_EXPECTED = "expected_stub_mode"
CLASS_TOOLING = "tooling_warning"
CLASS_STALE = "stale_runtime_artifact"
CLASS_REAL = "real_validation_failure"
CLASS_MISSING = "missing_generated_evidence"

STUB_EXPECTED_CAUSES = frozenset(
    {
        CAUSE_NO_NETWORK,
        CAUSE_NO_GRIB2_ARTIFACT,
        CAUSE_DECODER_UNAVAILABLE,
        CAUSE_PRODUCTION_FLAG_OFF,
        CAUSE_ZERO_TILES_WRITTEN,
    }
)

STUB_EXPECTED_PROOF_CRITERIA = frozenset(
    {
        CRITERION_REAL_NOAA_SOURCE,
        CRITERION_DECODER_ARTIFACTS,
        CRITERION_TILE_OUTPUT,
        CRITERION_MULTI_FRAME,
        CRITERION_ALERT_HYGIENE,
        CRITERION_PRODUCTION_PATH,
    }
)

STUB_MESSAGE_MARKERS = (
    "stub",
    "offline",
    "placeholder",
    "not verified",
    "experimental prototype",
    "queue benchmark",
    "production tile serving remains disabled",
    "enable_production_radar_tiles=false",
    "not real grib",
    "no optional decoder",
    "intentional",
    "real mode:",
    "mrms_source_mode=real",
    "validate-real-mrms",
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_validation_remediation_only": True,
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
        "stub_documented_is_not_verified_mrms": True,
        "prototype": True,
    }


def _remediation_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(REMEDIATION_JSON)


def _remediation_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(REMEDIATION_MD)


def _message_is_stub_expected(message: str) -> bool:
    lowered = message.lower()
    return any(marker in lowered for marker in STUB_MESSAGE_MARKERS)


def _classify_grouped_failure(entry: dict[str, Any]) -> str:
    cause = str(entry.get("cause") or CAUSE_UNKNOWN)
    message = str(entry.get("message") or "")
    if cause in STUB_EXPECTED_CAUSES:
        return CLASS_STUB_EXPECTED
    if cause == CAUSE_UNKNOWN and _message_is_stub_expected(message):
        return CLASS_STUB_EXPECTED
    if "decoder" in message.lower() or "wgrib2" in message.lower() or "gdal" in message.lower():
        return CLASS_TOOLING
    return CLASS_REAL


def analyze_validation_alert_failures(storage: LocalStorage) -> list[dict[str, Any]]:
    alert = load_validation_alert(storage) or {}
    grouped = alert.get("grouped_failure_causes") or []
    if not grouped:
        recent = load_recent_validation_failures(storage, limit=50)
        grouped = group_validation_failures(recent, limit=10)

    sources: list[dict[str, Any]] = []
    for entry in grouped:
        failure_class = _classify_grouped_failure(entry)
        sources.append(
            {
                "source": "validation_alert",
                "step": entry.get("step"),
                "cause": entry.get("cause"),
                "message": entry.get("message"),
                "count": entry.get("count"),
                "failure_class": failure_class,
                "blocks_preflight": failure_class == CLASS_REAL,
                "operator_action": (
                    "Expected stub/placeholder limitation — documented for preflight only; "
                    "does not verify MRMS or clear alerts."
                    if failure_class == CLASS_STUB_EXPECTED
                    else "Review make validation-failures and address real validation failures."
                ),
            }
        )
    if alert.get("status") == ALERT_FAILED and not sources:
        sources.append(
            {
                "source": "validation_alert",
                "step": "alert_status",
                "cause": "alert_failed",
                "message": f"validation alert status failed (failure_count={alert.get('failure_count')})",
                "count": alert.get("failure_count"),
                "failure_class": CLASS_STUB_EXPECTED
                if not settings.enable_production_radar_tiles
                else CLASS_REAL,
                "blocks_preflight": settings.enable_production_radar_tiles,
                "operator_action": (
                    "Stub-mode validation failures expected with placeholder tiles — "
                    "run make mrms-remediate-validation to document for preflight."
                ),
            }
        )
    return sources


def analyze_proof_report_failures(storage: LocalStorage) -> list[dict[str, Any]]:
    proof = load_mrms_proof_report(storage)
    if not proof:
        return [
            {
                "source": "proof_report",
                "criterion_id": "proof_report",
                "message": "MRMS proof report not found",
                "failure_class": CLASS_MISSING,
                "blocks_preflight": True,
                "operator_action": "Run make mrms-proof-report to generate local proof evidence.",
            }
        ]

    sources: list[dict[str, Any]] = []
    for criterion in proof.get("aggregate_criteria") or []:
        if criterion.get("status") != "failed":
            continue
        criterion_id = str(criterion.get("criterion_id") or "")
        message = str(criterion.get("message") or "")
        frame_messages = " ".join(criterion.get("frame_messages") or []).lower()

        if criterion_id in STUB_EXPECTED_PROOF_CRITERIA or _message_is_stub_expected(
            f"{message} {frame_messages}"
        ):
            failure_class = CLASS_STUB_EXPECTED
            blocks = False
            action = (
                "Expected stub/placeholder proof limitation — documented for preflight only; "
                "does not verify MRMS."
            )
        elif criterion_id == CRITERION_ALERT_HYGIENE:
            failure_class = CLASS_STUB_EXPECTED
            blocks = False
            action = (
                "Proof alert hygiene reflects validation alert — remediate via validation stub "
                "documentation; does not clear alerts."
            )
        else:
            failure_class = CLASS_REAL
            blocks = True
            action = "Review proof criteria and run make mrms-proof-report after fixes."

        sources.append(
            {
                "source": "proof_report",
                "criterion_id": criterion_id,
                "message": message,
                "failure_class": failure_class,
                "blocks_preflight": blocks,
                "operator_action": action,
            }
        )

    overall = proof.get("overall_status")
    if overall == "failed" and not sources:
        sources.append(
            {
                "source": "proof_report",
                "criterion_id": "overall_status",
                "message": "proof report overall_status failed",
                "failure_class": CLASS_STUB_EXPECTED
                if not settings.enable_production_radar_tiles
                else CLASS_REAL,
                "blocks_preflight": settings.enable_production_radar_tiles,
                "operator_action": "Run make mrms-proof-report and review aggregate criteria.",
            }
        )
    return sources


def _summarize_remediation(
    validation_sources: list[dict[str, Any]],
    proof_sources: list[dict[str, Any]],
) -> tuple[str, bool, list[str]]:
    all_sources = validation_sources + proof_sources
    if not all_sources:
        return REMEDIATION_NO_DATA, True, []

    blocking = [item for item in all_sources if item.get("blocks_preflight")]
    real = [item for item in all_sources if item.get("failure_class") == CLASS_REAL]
    stub = [item for item in all_sources if item.get("failure_class") == CLASS_STUB_EXPECTED]

    if real:
        return REMEDIATION_REAL_REMAIN, True, [item.get("message", "") for item in real]
    if blocking:
        return REMEDIATION_PARTIAL, True, [item.get("message", "") for item in blocking]
    if stub:
        return REMEDIATION_STUB_DOCUMENTED, False, []
    return REMEDIATION_PARTIAL, True, [item.get("message", "") for item in all_sources]


def remediate_validation_failures(
    storage: LocalStorage,
    *,
    refresh: bool = False,
) -> dict[str, Any]:
    alert_before = load_validation_alert(storage) or {}
    validation_sources = analyze_validation_alert_failures(storage)
    proof_sources = analyze_proof_report_failures(storage)

    remediation_status, blocks_preflight, remaining = _summarize_remediation(
        validation_sources, proof_sources
    )

    refresh_steps: list[dict[str, Any]] = []
    if refresh:
        refresh_steps.append(
            {
                "action": "analyze_validation_alert",
                "alert_status": alert_before.get("status"),
                "grouped_cause_count": len(validation_sources),
            }
        )
        refresh_steps.append(
            {
                "action": "analyze_proof_report",
                "proof_overall_status": (load_mrms_proof_report(storage) or {}).get(
                    "overall_status"
                ),
                "failed_criteria_count": len(proof_sources),
            }
        )
        if remediation_status == REMEDIATION_STUB_DOCUMENTED:
            refresh_steps.append(
                {
                    "action": "document_stub_mode_for_preflight",
                    "note": (
                        "All validation/proof failures classified as expected stub-mode limitations. "
                        "Alert status unchanged; not verified MRMS."
                    ),
                }
            )

    operator_status_impact = "unchanged"
    if remediation_status == REMEDIATION_STUB_DOCUMENTED:
        operator_status_impact = "validation_alert_failed_may_downgrade_for_preflight"

    return {
        "remediated_at": _utc_now(),
        "remediation_status": remediation_status,
        "blocks_preflight": blocks_preflight,
        "validation_alert_status": alert_before.get("status"),
        "validation_alert_unchanged": True,
        "validation_failure_sources": validation_sources,
        "proof_failure_sources": proof_sources,
        "remaining_real_failures": remaining,
        "stub_mode_documented": remediation_status == REMEDIATION_STUB_DOCUMENTED,
        "refresh_steps": refresh_steps,
        "operator_status_impact": operator_status_impact,
        "next_operator_step": _next_operator_step(remediation_status, remaining),
        "next_phase_recommendation": _next_phase(remediation_status),
        "retry_commands": _retry_commands(remediation_status),
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }


def _next_operator_step(remediation_status: str, remaining: list[str]) -> str:
    if remediation_status == REMEDIATION_STUB_DOCUMENTED:
        return (
            "Stub-mode validation/proof failures documented for preflight — "
            "re-run preflight attention and milestone audit."
        )
    if remaining:
        return f"Resolve real validation/proof failure: {remaining[0]}"
    return "Review validation failures and proof report before preflight."


def _next_phase(remediation_status: str) -> str:
    if remediation_status == REMEDIATION_STUB_DOCUMENTED:
        return "Phase 103 — continue gated dry-run plan review (preflight may be ready)"
    return "Phase 103 — resolve remaining real validation/proof failures for preflight"


def _retry_commands(remediation_status: str) -> list[str]:
    commands = [
        "make mrms-remediate-validation --refresh",
        "make mrms-resolve-preflight-attention --refresh",
        "make operator-review-status --refresh",
        "make mrms-render-candidate-preflight --refresh",
        "make mrms-readiness-milestone-audit --refresh",
    ]
    if remediation_status != REMEDIATION_STUB_DOCUMENTED:
        commands.insert(1, "make validation-failures")
        commands.insert(2, "make mrms-proof-report")
    return commands


def stub_mode_documented_for_preflight(storage: LocalStorage) -> bool:
    latest = load_validation_remediation_report(storage)
    return bool(latest and latest.get("stub_mode_documented"))


def proof_stub_documented_for_preflight(storage: LocalStorage) -> bool:
    latest = load_validation_remediation_report(storage)
    if not latest or not latest.get("stub_mode_documented"):
        return False
    proof_sources = latest.get("proof_failure_sources") or []
    return all(not item.get("blocks_preflight") for item in proof_sources)


def build_remediation_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Validation remediation for render-candidate preflight (Phase 102)",
        "",
        "> **WARNING:** Local advisory only — does **NOT** verify MRMS or clear validation alerts.",
        "",
        f"- Remediated at: {report.get('remediated_at')}",
        f"- Remediation status: **{report.get('remediation_status')}**",
        f"- Blocks preflight: {report.get('blocks_preflight')}",
        f"- Validation alert status (unchanged): {report.get('validation_alert_status')}",
        f"- Stub mode documented: {report.get('stub_mode_documented')}",
        f"- Next operator step: {report.get('next_operator_step')}",
        "",
        "## Validation failure sources",
        "",
    ]
    for item in report.get("validation_failure_sources") or []:
        lines.append(
            f"- [{item.get('failure_class')}] {item.get('message')} "
            f"(blocks_preflight={item.get('blocks_preflight')})"
        )
    lines.extend(["", "## Proof failure sources", ""])
    for item in report.get("proof_failure_sources") or []:
        lines.append(
            f"- [{item.get('failure_class')}] {item.get('criterion_id')}: {item.get('message')} "
            f"(blocks_preflight={item.get('blocks_preflight')})"
        )
    lines.extend(["", "## Retry commands", ""])
    for cmd in report.get("retry_commands") or []:
        lines.append(f"- `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def save_validation_remediation_report(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
    json_path = _remediation_json_path(storage)
    md_path = _remediation_md_path(storage)
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
    storage.absolute_path(md_path).write_text(build_remediation_markdown(report), encoding="utf-8")
    return report


def load_validation_remediation_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_remediation_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def compact_validation_remediation(storage: LocalStorage) -> dict[str, Any]:
    latest = load_validation_remediation_report(storage)
    if latest is None:
        validation_sources = analyze_validation_alert_failures(storage)
        proof_sources = analyze_proof_report_failures(storage)
        status, blocks, remaining = _summarize_remediation(validation_sources, proof_sources)
        return {
            "available": False,
            "remediation_status": status,
            "blocks_preflight": blocks,
            "stub_mode_documented": status == REMEDIATION_STUB_DOCUMENTED,
            "validation_alert_status": (load_validation_alert(storage) or {}).get("status"),
            "remaining_real_failures": remaining,
            "suggested_command": SUGGESTED_COMMAND,
            **_safety_fields(),
        }
    return {
        "available": True,
        "remediation_status": latest.get("remediation_status"),
        "blocks_preflight": bool(latest.get("blocks_preflight")),
        "stub_mode_documented": bool(latest.get("stub_mode_documented")),
        "validation_alert_status": latest.get("validation_alert_status"),
        "validation_alert_unchanged": bool(latest.get("validation_alert_unchanged")),
        "remaining_real_failures": latest.get("remaining_real_failures") or [],
        "next_operator_step": latest.get("next_operator_step"),
        "next_phase_recommendation": latest.get("next_phase_recommendation"),
        "retry_commands": latest.get("retry_commands") or [],
        "remediated_at": latest.get("remediated_at"),
        "json_path": latest.get("json_path"),
        "markdown_path": latest.get("markdown_path"),
        "suggested_command": latest.get("suggested_command") or SUGGESTED_COMMAND,
        **_safety_fields(),
    }


def build_validation_remediation_payload(storage: LocalStorage) -> dict[str, Any]:
    return {
        **_safety_fields(),
        "latest": load_validation_remediation_report(storage),
        "compact": compact_validation_remediation(storage),
    }
