"""Decode retry — check decoders, decode latest MRMS, rerun local render pipeline."""

from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.services.decoder_setup import (
    SUGGESTED_DECODE_RETRY_COMMAND,
    SUGGESTED_INSTALL_COMMAND,
    decoder_availability_dict,
    gather_decoder_setup_status,
)
from backend.app.services.grib2_decoder import Grib2DecodeResult, decode_grib2_file
from backend.app.services.grib2_inspect_catalog import find_real_mrms_inspect_candidates
from backend.app.services.grib2_inspector import detect_decoder_availability
from backend.app.services.mrms_local_render_pipeline import (
    STATUS_DECODER_MISSING,
    STATUS_PREVIEW_OK,
    run_local_render_pipeline,
)
from backend.app.services.storage import LocalStorage

RETRY_JSON = "dev/decode_retry_latest.json"
RETRY_MD = "dev/decode_retry_latest.md"


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_decode_retry_only": True,
        "does_not_enable_production": True,
        "does_not_claim_verified_mrms": True,
        "prototype": True,
    }


def _decode_result_dict(result: Grib2DecodeResult) -> dict[str, Any]:
    return {
        "raw_path": result.raw_path,
        "raw_kind": result.raw_kind,
        "success": result.success,
        "decoder_unavailable": result.decoder_unavailable,
        "decoder_used": result.decoder_used,
        "output_dir": result.output_dir,
        "manifest_path": result.manifest_path,
        "raster_path": result.raster_path,
        "width": result.width,
        "height": result.height,
        "error": result.error,
        "notes": result.notes,
    }


def _next_phase_recommendation(
    *,
    decode_success: bool,
    pipeline_status: Optional[str],
    render_mode: Optional[str],
) -> str:
    if decode_success and pipeline_status == STATUS_PREVIEW_OK and render_mode == "decoded_prototype":
        return "Phase 105 — wire decoded preview into map overlay (color scale / georef / tile slice)"
    if pipeline_status == STATUS_DECODER_MISSING:
        return "Phase 105 — install rasterio via make install-decoders and rerun make decode-retry"
    if not decode_success:
        return "Phase 105 — fix decode failure (see decode_retry report stderr/error)"
    return "Phase 105 — improve decoded preview rendering (color scale / georef)"


def run_decode_retry(session: Session, storage: LocalStorage) -> dict[str, Any]:
    """Check decoders, decode latest MRMS candidate, rerun local render pipeline."""
    setup = gather_decoder_setup_status()
    decoder = setup["decoder"]
    errors: list[str] = []
    warnings: list[str] = []
    decode_report: Optional[dict[str, Any]] = None
    pipeline_report: Optional[dict[str, Any]] = None
    candidate_raw_path: Optional[str] = None

    if not decoder.get("any_decoder"):
        errors.append(decoder.get("summary_message") or "No decoder available.")
        warnings.append(f"Run `{SUGGESTED_INSTALL_COMMAND}` then retry.")
        report = {
            "ran_at": _utc_now(),
            "decode_retry_status": "decoder_missing",
            "decoder": decoder,
            "decode": None,
            "pipeline": None,
            "decode_success": False,
            "pipeline_status": STATUS_DECODER_MISSING,
            "render_mode": None,
            "produced_decoded_preview": False,
            "preview_paths": [],
            "errors": errors,
            "warnings": warnings,
            "blocker": "decoder_missing",
            "next_retry_commands": [SUGGESTED_INSTALL_COMMAND, SUGGESTED_DECODE_RETRY_COMMAND],
            "next_phase_recommendation": _next_phase_recommendation(
                decode_success=False,
                pipeline_status=STATUS_DECODER_MISSING,
                render_mode=None,
            ),
            "suggested_command": SUGGESTED_DECODE_RETRY_COMMAND,
            **_safety_fields(),
        }
        return save_decode_retry_report(storage, report)

    candidates = find_real_mrms_inspect_candidates(session, storage, limit=1)
    if not candidates:
        errors.append("No real MRMS .grib2.gz candidate in catalog.")
        report = {
            "ran_at": _utc_now(),
            "decode_retry_status": "no_candidate",
            "decoder": decoder,
            "decode": None,
            "pipeline": None,
            "decode_success": False,
            "pipeline_status": None,
            "render_mode": None,
            "produced_decoded_preview": False,
            "preview_paths": [],
            "errors": errors,
            "warnings": warnings,
            "blocker": "no_candidate",
            "next_retry_commands": [
                "MRMS_SOURCE_MODE=real make download-mrms ARGS='--register-discovered --limit 1'",
                SUGGESTED_DECODE_RETRY_COMMAND,
            ],
            "next_phase_recommendation": "Phase 105 — download real MRMS GRIB2 and rerun decode-retry",
            "suggested_command": SUGGESTED_DECODE_RETRY_COMMAND,
            **_safety_fields(),
        }
        return save_decode_retry_report(storage, report)

    candidate = candidates[0]
    candidate_raw_path = candidate.raw_path
    decode_result = decode_grib2_file(storage, candidate.raw_path)
    decode_report = _decode_result_dict(decode_result)
    if decode_result.error:
        errors.append(decode_result.error)
    if not decode_result.success:
        report = {
            "ran_at": _utc_now(),
            "decode_retry_status": "decode_failed",
            "decoder": decoder,
            "candidate": {
                "radar_file_id": candidate.radar_file_id,
                "timestamp": candidate.timestamp,
                "raw_path": candidate.raw_path,
            },
            "decode": decode_report,
            "pipeline": None,
            "decode_success": False,
            "pipeline_status": None,
            "render_mode": None,
            "produced_decoded_preview": False,
            "preview_paths": [],
            "errors": errors,
            "warnings": warnings,
            "blocker": "decode_failed",
            "next_retry_commands": [
                f'make decode-grib2 ARGS="--file {candidate.raw_path}"',
                SUGGESTED_DECODE_RETRY_COMMAND,
            ],
            "next_phase_recommendation": _next_phase_recommendation(
                decode_success=False,
                pipeline_status=None,
                render_mode=None,
            ),
            "suggested_command": SUGGESTED_DECODE_RETRY_COMMAND,
            **_safety_fields(),
        }
        return save_decode_retry_report(storage, report)

    pipeline_report = run_local_render_pipeline(session, storage)
    pipeline_status = pipeline_report.get("pipeline_status")
    render_mode = pipeline_report.get("render_mode")
    produced = bool(
        pipeline_report.get("produced_local_artifact")
        and render_mode == "decoded_prototype"
    )

    report = {
        "ran_at": _utc_now(),
        "decode_retry_status": "preview_ok" if produced else "pipeline_partial",
        "decoder": decoder,
        "candidate": {
            "radar_file_id": candidate.radar_file_id,
            "timestamp": candidate.timestamp,
            "raw_path": candidate.raw_path,
        },
        "decode": decode_report,
        "pipeline": {
            "pipeline_status": pipeline_status,
            "render_mode": render_mode,
            "render_attempt_status": pipeline_report.get("render_attempt_status"),
            "preview_paths": pipeline_report.get("preview_paths") or [],
            "blocker": pipeline_report.get("blocker"),
        },
        "decode_success": True,
        "pipeline_status": pipeline_status,
        "render_mode": render_mode,
        "produced_decoded_preview": produced,
        "preview_paths": pipeline_report.get("preview_paths") or [],
        "candidate_raw_path": candidate_raw_path,
        "errors": errors,
        "warnings": warnings,
        "blocker": pipeline_report.get("blocker"),
        "next_retry_commands": pipeline_report.get("next_retry_commands") or [SUGGESTED_DECODE_RETRY_COMMAND],
        "next_phase_recommendation": _next_phase_recommendation(
            decode_success=True,
            pipeline_status=pipeline_status,
            render_mode=render_mode,
        ),
        "suggested_command": SUGGESTED_DECODE_RETRY_COMMAND,
        **_safety_fields(),
    }
    return save_decode_retry_report(storage, report)


def build_retry_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Decode retry (local dev)",
        "",
        "> **WARNING:** Local prototype only — NOT verified MRMS production rendering.",
        "",
        f"- Ran at: {report.get('ran_at')}",
        f"- Status: **{report.get('decode_retry_status')}**",
        f"- Decode success: {report.get('decode_success')}",
        f"- Pipeline status: {report.get('pipeline_status')}",
        f"- Render mode: {report.get('render_mode')}",
        f"- Produced decoded preview: {report.get('produced_decoded_preview')}",
        f"- Blocker: {report.get('blocker') or 'none'}",
        f"- Next phase: {report.get('next_phase_recommendation')}",
        "",
        "## Decoder",
        "",
    ]
    decoder = report.get("decoder") or {}
    lines.append(f"- {decoder.get('summary_message')}")
    lines.append(f"- preferred: {decoder.get('preferred_decode_path')}")
    decode = report.get("decode")
    if decode:
        lines.extend(["", "## Decode", ""])
        lines.append(f"- success: {decode.get('success')}")
        lines.append(f"- decoder_used: {decode.get('decoder_used')}")
        lines.append(f"- grid: {decode.get('width')} x {decode.get('height')}")
        lines.append(f"- output_dir: `{decode.get('output_dir')}`")
        if decode.get("error"):
            lines.append(f"- error: {decode['error']}")
    lines.extend(["", "## Preview outputs", ""])
    for path in report.get("preview_paths") or []:
        lines.append(f"- `{path}`")
    if report.get("errors"):
        lines.extend(["", "## Errors", ""])
        for item in report["errors"]:
            lines.append(f"- {item}")
    lines.extend(["", "## Retry", ""])
    for cmd in report.get("next_retry_commands") or []:
        lines.append(f"- `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def save_decode_retry_report(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
    json_path = storage.normalize_path(RETRY_JSON)
    md_path = storage.normalize_path(RETRY_MD)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    report = {
        **report,
        "json_path": json_path,
        "markdown_path": md_path,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(build_retry_markdown(report), encoding="utf-8")
    return report
