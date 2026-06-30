"""Fast-track local MRMS render pipeline — prototype preview only, not verified MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.models import RadarFile
from backend.app.services.decoded_tile_cache import (
    find_decode_artifact_for_frame,
    load_decode_manifest,
    render_decoded_prototype_tile,
)
from backend.app.services.grib2_decoder import build_decode_output_dir, decode_grib2_file
from backend.app.services.grib2_inspect_catalog import find_real_mrms_inspect_candidates
from backend.app.services.grib2_inspector import detect_decoder_availability, inspect_grib2_file
from backend.app.services.raw_file_classifier import (
    RAW_KIND_MRMS_REAL_GRIB2,
    classify_raw_file,
    is_placeholder_raw_kind,
    is_real_grib2_raw_kind,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.color_scale import COLOR_SCALE_MODE
from backend.app.services.tile_preview import (
    TILE_MODE_LOCAL_RASTER,
    TILE_MODE_SINGLE_IMAGE,
    build_local_tile_preview,
    compact_tile_preview,
    render_color_preview_from_artifact,
)
from backend.app.services.tile_service import generate_placeholder_tile_png
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE

PIPELINE_JSON = "dev/mrms_local_render_pipeline_latest.json"
PIPELINE_MD = "dev/mrms_local_render_pipeline_latest.md"
PREVIEW_DIR = "dev/mrms_local_render_preview"

SUGGESTED_COMMAND = "make mrms-local-render-pipeline"

STATUS_PREVIEW_OK = "preview_ok"
STATUS_DECODE_OK = "decode_ok_no_preview"
STATUS_DECODER_MISSING = "decoder_missing"
STATUS_STUB_INPUT = "stub_input"
STATUS_INSPECT_FAILED = "inspect_failed"
STATUS_DECODE_FAILED = "decode_failed"
STATUS_NO_CANDIDATE = "no_candidate"
STATUS_PIPELINE_FAILED = "pipeline_failed"

STEP_SELECT = "select_candidate"
STEP_DECODER = "decoder_check"
STEP_INSPECT = "inspect"
STEP_DECODE = "decode"
STEP_RENDER = "render_preview"


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_render_pipeline_only": True,
        "advisory_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "enable_production_radar_tiles": settings.enable_production_radar_tiles,
        "does_not_download_or_decode_by_default": False,
        "does_not_serve_production_tiles": True,
        "does_not_claim_verified_mrms": True,
        "prototype": True,
    }


def _pipeline_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(PIPELINE_JSON)


def _pipeline_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(PIPELINE_MD)


def _preview_dir(storage: LocalStorage) -> str:
    return storage.normalize_path(PREVIEW_DIR)


def _preview_tile_path(storage: LocalStorage, *, z: int = 0, x: int = 0, y: int = 0) -> str:
    return storage.normalize_path(PREVIEW_DIR, f"preview_z{z}_x{x}_y{y}.png")


def select_pipeline_candidate(session: Session, storage: LocalStorage) -> Optional[dict[str, Any]]:
    """Pick latest real GRIB2 candidate, else latest MRMS catalog row with a local raw path."""
    real_candidates = find_real_mrms_inspect_candidates(session, storage, limit=1)
    if real_candidates:
        candidate = real_candidates[0]
        row = session.get(RadarFile, candidate.radar_file_id)
        return {
            "radar_file_id": candidate.radar_file_id,
            "timestamp": candidate.timestamp,
            "raw_path": candidate.raw_path,
            "raw_kind": candidate.raw_kind,
            "source": candidate.source,
            "selection": "real_grib2",
            "is_real_grib2": True,
            "is_placeholder": False,
            "layer": row.product_id if row else "mrms_reflectivity",
        }

    rows = (
        session.query(RadarFile)
        .filter(RadarFile.raw_path.isnot(None))
        .order_by(RadarFile.timestamp.desc())
        .all()
    )
    for row in rows:
        if not row.raw_path or not storage.path_exists(row.raw_path):
            continue
        raw_kind = row.raw_kind or classify_raw_file(row)
        return {
            "radar_file_id": row.id,
            "timestamp": row.timestamp,
            "raw_path": row.raw_path,
            "raw_kind": raw_kind,
            "source": row.source,
            "selection": "catalog_fallback",
            "is_real_grib2": is_real_grib2_raw_kind(raw_kind),
            "is_placeholder": is_placeholder_raw_kind(raw_kind),
            "layer": row.product_id or "mrms_reflectivity",
        }
    return None


def _decoder_summary(availability) -> dict[str, Any]:
    return {
        "any_decoder": availability.any_decoder,
        "wgrib2": availability.wgrib2,
        "wgrib2_path": availability.wgrib2_path,
        "gdal": availability.gdal,
        "rasterio": availability.rasterio,
        "pygrib": availability.pygrib,
        "cfgrib": availability.cfgrib,
        "summary_message": availability.summary_message(),
    }


def _next_retry_commands(
    *,
    pipeline_status: str,
    candidate: Optional[dict[str, Any]],
    decoder: dict[str, Any],
) -> list[str]:
    if pipeline_status == STATUS_PREVIEW_OK:
        return [
            SUGGESTED_COMMAND,
            "make decode-grib2 -- --latest-mrms",
            "make build-tile-cache",
        ]
    if pipeline_status == STATUS_DECODER_MISSING:
        return [
            "# install wgrib2 or rasterio/GDAL",
            "MRMS_SOURCE_MODE=real make download-mrms ARGS='--register-discovered --limit 1'",
            "make decode-grib2 ARGS='--latest-mrms'",
            SUGGESTED_COMMAND,
        ]
    if pipeline_status == STATUS_STUB_INPUT:
        return [
            "MRMS_SOURCE_MODE=real make download-mrms ARGS='--register-discovered --limit 1'",
            "make decode-grib2 ARGS='--latest-mrms'",
            SUGGESTED_COMMAND,
        ]
    if candidate and candidate.get("raw_path"):
        return [
            f"make decode-grib2 ARGS='--file {candidate['raw_path']}'",
            SUGGESTED_COMMAND,
        ]
    return [
        "MRMS_SOURCE_MODE=real make download-mrms ARGS='--register-discovered --limit 1'",
        SUGGESTED_COMMAND,
    ]


def _next_phase_recommendation(pipeline_status: str) -> str:
    if pipeline_status == STATUS_PREVIEW_OK:
        return "Phase 107 — time-synced playback and geo-accurate overlay"
    if pipeline_status == STATUS_DECODER_MISSING:
        return "Phase 105 — install rasterio via make install-decoders and rerun make decode-retry"
    if pipeline_status == STATUS_STUB_INPUT:
        return "Phase 105 — download real MRMS GRIB2 and rerun local render pipeline"
    if pipeline_status == STATUS_DECODE_FAILED:
        return "Phase 105 — fix decode failure for local render pipeline"
    return "Phase 105 — obtain decodable MRMS input for local render pipeline"


def run_local_render_pipeline(
    session: Session,
    storage: LocalStorage,
    *,
    z: int = 0,
    x: int = 0,
    y: int = 0,
) -> dict[str, Any]:
    """End-to-end local render attempt: candidate → inspect → decode → preview PNG."""
    if catalog_is_empty(session):
        seed_demo_catalog(session, storage=storage)

    steps: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []

    candidate = select_pipeline_candidate(session, storage)
    steps.append(
        {
            "step": STEP_SELECT,
            "status": "ok" if candidate else "failed",
            "candidate": candidate,
        }
    )
    if candidate is None:
        report = {
            "ran_at": _utc_now(),
            "pipeline_status": STATUS_NO_CANDIDATE,
            "candidate": None,
            "decoder": _decoder_summary(detect_decoder_availability()),
            "steps": steps,
            "errors": ["No catalog candidate with a local raw_path found."],
            "warnings": warnings,
            "preview_paths": [],
            "render_attempt_status": "not_started",
            "blocker": "no_candidate",
            "next_retry_commands": _next_retry_commands(
                pipeline_status=STATUS_NO_CANDIDATE,
                candidate=None,
                decoder={},
            ),
            "next_phase_recommendation": _next_phase_recommendation(STATUS_NO_CANDIDATE),
            "suggested_command": SUGGESTED_COMMAND,
            **_safety_fields(),
        }
        return save_local_render_pipeline_report(storage, report)

    availability = detect_decoder_availability()
    decoder = _decoder_summary(availability)
    steps.append({"step": STEP_DECODER, "status": "ok", "decoder": decoder})

    raw_path = candidate["raw_path"]
    inspect_result = inspect_grib2_file(storage, raw_path)
    steps.append(
        {
            "step": STEP_INSPECT,
            "status": "ok" if inspect_result.inspectable or inspect_result.file_exists else "skipped",
            "inspectable": inspect_result.inspectable,
            "raw_kind": inspect_result.raw_kind,
            "error": inspect_result.error,
        }
    )

    decode_result: Optional[dict[str, Any]] = None
    preview_paths: list[str] = []
    render_mode: Optional[str] = None
    pipeline_status = STATUS_PIPELINE_FAILED
    blocker: Optional[str] = None

    if candidate.get("is_placeholder") or not candidate.get("is_real_grib2"):
        pipeline_status = STATUS_STUB_INPUT
        blocker = "stub_or_non_grib2_input"
        warnings.append(
            "Selected input is stub/placeholder — decode skipped. Download a real .grib2.gz to render radar values."
        )
        png = generate_placeholder_tile_png(z=z, x=x, y=y)
        preview_path = _write_preview_png(storage, png, z=z, x=x, y=y)
        preview_paths.append(preview_path)
        render_mode = "placeholder_stub_input"
        steps.append(
            {
                "step": STEP_DECODE,
                "status": "skipped",
                "reason": "stub_or_non_grib2_input",
            }
        )
        steps.append(
            {
                "step": STEP_RENDER,
                "status": "ok",
                "render_mode": render_mode,
                "preview_path": preview_path,
            }
        )
    elif not availability.any_decoder:
        pipeline_status = STATUS_DECODER_MISSING
        blocker = "decoder_missing"
        warnings.append(decoder["summary_message"])
        png = generate_placeholder_tile_png(z=z, x=x, y=y)
        preview_path = _write_preview_png(storage, png, z=z, x=x, y=y)
        preview_paths.append(preview_path)
        render_mode = "placeholder_decoder_missing"
        steps.append(
            {
                "step": STEP_DECODE,
                "status": "skipped",
                "reason": "decoder_missing",
            }
        )
        steps.append(
            {
                "step": STEP_RENDER,
                "status": "ok",
                "render_mode": render_mode,
                "preview_path": preview_path,
                "note": "Placeholder preview only — install wgrib2 or rasterio to decode real GRIB2.",
            }
        )
    elif not inspect_result.inspectable:
        pipeline_status = STATUS_INSPECT_FAILED
        blocker = "not_inspectable"
        errors.append(inspect_result.error or f"File not inspectable: {raw_path}")
        steps.append({"step": STEP_DECODE, "status": "skipped", "reason": "not_inspectable"})
        steps.append({"step": STEP_RENDER, "status": "skipped"})
    else:
        decoded = decode_grib2_file(storage, raw_path)
        decode_result = {
            "success": decoded.success,
            "decoder_used": decoded.decoder_used,
            "decoder_unavailable": decoded.decoder_unavailable,
            "manifest_path": decoded.manifest_path,
            "raster_path": decoded.raster_path,
            "output_dir": decoded.output_dir,
            "error": decoded.error,
            "notes": decoded.notes,
        }
        steps.append(
            {
                "step": STEP_DECODE,
                "status": "ok" if decoded.success else "failed",
                "decode": decode_result,
            }
        )
        if decoded.error:
            errors.append(decoded.error)
        if not decoded.success:
            pipeline_status = STATUS_DECODE_FAILED
            blocker = "decode_failed"
            steps.append({"step": STEP_RENDER, "status": "skipped"})
        else:
            frame = session.get(RadarFile, candidate["radar_file_id"])
            artifact = None
            if frame is not None:
                artifact = find_decode_artifact_for_frame(storage, frame)
            if artifact is None and decoded.output_dir:
                artifact = load_decode_manifest(storage, decoded.output_dir)
            if artifact is None:
                pipeline_status = STATUS_DECODE_OK
                blocker = "decode_manifest_missing"
                warnings.append("Decode succeeded but manifest could not be loaded for preview render.")
                steps.append({"step": STEP_RENDER, "status": "skipped"})
            else:
                png_bytes = render_color_preview_from_artifact(storage, artifact, z=z, x=x, y=y)
                color_scale_mode = COLOR_SCALE_MODE
                tile_preview_result = None
                if png_bytes is None:
                    png_bytes = render_decoded_prototype_tile(
                        storage, artifact, z=z, x=x, y=y
                    )
                    color_scale_mode = "grayscale_fallback"
                if png_bytes is None:
                    pipeline_status = STATUS_DECODE_OK
                    blocker = "preview_render_failed"
                    errors.append("Decode artifact present but preview tile render returned None.")
                    steps.append({"step": STEP_RENDER, "status": "failed"})
                else:
                    preview_path = _write_preview_png(storage, png_bytes, z=z, x=x, y=y)
                    preview_paths.append(preview_path)
                    render_mode = "decoded_prototype"
                    pipeline_status = STATUS_PREVIEW_OK
                    blocker = None
                    tile_preview_result = build_local_tile_preview(storage, artifact, z_levels=[0, 1], xy_limit=2)
                    steps.append(
                        {
                            "step": STEP_RENDER,
                            "status": "ok",
                            "render_mode": render_mode,
                            "color_scale_mode": color_scale_mode,
                            "preview_path": preview_path,
                            "artifact_output_dir": artifact.output_dir,
                            "tile_preview": compact_tile_preview(tile_preview_result),
                        }
                    )

    render_attempt_status = (
        "preview_produced"
        if preview_paths and render_mode in {"decoded_prototype", "placeholder_stub_input", "placeholder_decoder_missing"}
        else "failed"
        if errors
        else "partial"
    )

    tile_preview_compact = None
    color_scale_mode = None
    tile_mode = TILE_MODE_SINGLE_IMAGE
    for step in steps:
        if step.get("step") == STEP_RENDER and step.get("tile_preview"):
            tile_preview_compact = step["tile_preview"]
            color_scale_mode = step.get("color_scale_mode")
            if tile_preview_compact.get("tile_mode") == TILE_MODE_LOCAL_RASTER:
                tile_mode = TILE_MODE_LOCAL_RASTER
        elif step.get("step") == STEP_RENDER and step.get("color_scale_mode"):
            color_scale_mode = step.get("color_scale_mode")

    report = {
        "ran_at": _utc_now(),
        "pipeline_status": pipeline_status,
        "candidate": candidate,
        "decoder": decoder,
        "inspect": {
            "inspectable": inspect_result.inspectable,
            "raw_kind": inspect_result.raw_kind,
            "error": inspect_result.error,
        },
        "decode": decode_result,
        "render_mode": render_mode,
        "color_scale_mode": color_scale_mode,
        "tile_mode": tile_mode,
        "tile_preview": tile_preview_compact,
        "render_attempt_status": render_attempt_status,
        "preview_paths": preview_paths,
        "preview_dir": _preview_dir(storage),
        "decode_output_dir": build_decode_output_dir(storage, raw_path) if raw_path else None,
        "steps": steps,
        "errors": errors,
        "warnings": warnings,
        "blocker": blocker,
        "produced_local_artifact": bool(preview_paths),
        "next_retry_commands": _next_retry_commands(
            pipeline_status=pipeline_status,
            candidate=candidate,
            decoder=decoder,
        ),
        "next_phase_recommendation": _next_phase_recommendation(pipeline_status),
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }
    return save_local_render_pipeline_report(storage, report)


def _write_preview_png(
    storage: LocalStorage,
    png_bytes: bytes,
    *,
    z: int,
    x: int,
    y: int,
) -> str:
    preview_path = _preview_tile_path(storage, z=z, x=x, y=y)
    storage.ensure_directories(_preview_dir(storage))
    storage.write_bytes(preview_path, png_bytes, overwrite=True)
    return preview_path


def build_pipeline_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Local MRMS render pipeline (Phase 103)",
        "",
        "> **WARNING:** Local fast-track prototype only — does **NOT** verify MRMS or enable production tiles.",
        "",
        f"- Ran at: {report.get('ran_at')}",
        f"- Pipeline status: **{report.get('pipeline_status')}**",
        f"- Render attempt: {report.get('render_attempt_status')}",
        f"- Produced local artifact: {report.get('produced_local_artifact')}",
        f"- Render mode: {report.get('render_mode') or '—'}",
        f"- Blocker: {report.get('blocker') or 'none'}",
        f"- Next phase: {report.get('next_phase_recommendation')}",
        "",
        "## Candidate",
        "",
    ]
    candidate = report.get("candidate") or {}
    if candidate:
        lines.append(f"- raw_path: `{candidate.get('raw_path')}`")
        lines.append(f"- raw_kind: {candidate.get('raw_kind')}")
        lines.append(f"- selection: {candidate.get('selection')}")
    else:
        lines.append("- none")
    lines.extend(["", "## Decoder", ""])
    decoder = report.get("decoder") or {}
    lines.append(f"- {decoder.get('summary_message')}")
    lines.extend(["", "## Preview outputs", ""])
    for path in report.get("preview_paths") or []:
        lines.append(f"- `{path}`")
    if not report.get("preview_paths"):
        lines.append("- none")
    if report.get("errors"):
        lines.extend(["", "## Errors", ""])
        for item in report["errors"]:
            lines.append(f"- {item}")
    if report.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        for item in report["warnings"]:
            lines.append(f"- {item}")
    lines.extend(["", "## Retry", ""])
    for cmd in report.get("next_retry_commands") or []:
        lines.append(f"- `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def save_local_render_pipeline_report(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
    json_path = _pipeline_json_path(storage)
    md_path = _pipeline_md_path(storage)
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
    storage.absolute_path(md_path).write_text(build_pipeline_markdown(report), encoding="utf-8")
    return report


def load_local_render_pipeline_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_pipeline_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def compact_local_render_pipeline(storage: LocalStorage) -> dict[str, Any]:
    latest = load_local_render_pipeline_report(storage)
    if latest is None:
        return {
            "available": False,
            "suggested_command": SUGGESTED_COMMAND,
            **_safety_fields(),
        }
    return {
        "available": True,
        "pipeline_status": latest.get("pipeline_status"),
        "render_attempt_status": latest.get("render_attempt_status"),
        "produced_local_artifact": bool(latest.get("produced_local_artifact")),
        "render_mode": latest.get("render_mode"),
        "blocker": latest.get("blocker"),
        "preview_paths": latest.get("preview_paths") or [],
        "candidate_raw_path": (latest.get("candidate") or {}).get("raw_path"),
        "next_retry_commands": latest.get("next_retry_commands") or [],
        "next_phase_recommendation": latest.get("next_phase_recommendation"),
        "ran_at": latest.get("ran_at"),
        "json_path": latest.get("json_path"),
        "markdown_path": latest.get("markdown_path"),
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }
