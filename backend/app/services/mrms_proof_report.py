"""Draft verified-MRMS proof report automation (evidence gathering only).

Does NOT set verified_mrms=true. Operator review always required.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models import RadarFile
from backend.app.models.render_job import RenderJob
from backend.app.services.decoded_tile_cache import find_decode_artifact_for_frame
from backend.app.services.grib2_inspect_catalog import find_real_mrms_inspect_candidates
from backend.app.services.grib2_inspector import detect_decoder_availability, inspect_grib2_file
from backend.app.services.raw_file_classifier import (
    RAW_KIND_MRMS_REAL_GRIB2,
    classify_raw_file,
    is_placeholder_raw_kind,
    is_real_grib2_raw_kind,
)
from backend.app.services.render_metadata import DEFAULT_MRMS_BOUNDS, load_geo_metadata
from backend.app.services.render_status import classify_frame_render_status
from backend.app.services.storage import LocalStorage
from backend.app.services.tile_pyramid import build_production_tile_repo_path, validate_geo_metadata
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.sources.mrms import MRMS_CATALOG_SOURCE

MRMS_PROOF_LATEST_PATH = "dev/mrms_proof_latest.json"
MRMS_PROOF_HISTORY_PATH = "dev/mrms_proof_history.json"
MAX_PROOF_HISTORY = 10
DEFAULT_PROOF_FRAME_COUNT = 3
MAX_PROOF_FRAME_COUNT = 10
EXPECTED_PRODUCT_ID = "mrms_reflectivity"

STATUS_PASSED = "passed"
STATUS_FAILED = "failed"
STATUS_WARNING = "warning"
STATUS_SKIPPED = "skipped"
STATUS_UNKNOWN = "unknown"

OVERALL_NOT_STARTED = "not_started"
OVERALL_INSUFFICIENT = "insufficient_evidence"
OVERALL_FAILED = "failed"
OVERALL_READY_REVIEW = "ready_for_operator_review"

CRITERION_REAL_NOAA_SOURCE = "real_noaa_source"
CRITERION_DECODER_ARTIFACTS = "decoder_and_artifacts"
CRITERION_PRODUCT_TIME = "product_time_metadata"
CRITERION_GEOSPATIAL = "geospatial_correctness"
CRITERION_VISUAL_SANITY = "visual_sanity_checks"
CRITERION_TILE_OUTPUT = "tile_output_from_decoded"
CRITERION_PRODUCTION_PATH = "production_path_intentional"
CRITERION_MULTI_FRAME = "repeatable_multi_frame"
CRITERION_ALERT_HYGIENE = "failure_alert_hygiene"
CRITERION_OPERATOR_REVIEW = "operator_review"

ALL_CRITERION_IDS = [
    CRITERION_REAL_NOAA_SOURCE,
    CRITERION_DECODER_ARTIFACTS,
    CRITERION_PRODUCT_TIME,
    CRITERION_GEOSPATIAL,
    CRITERION_VISUAL_SANITY,
    CRITERION_TILE_OUTPUT,
    CRITERION_PRODUCTION_PATH,
    CRITERION_MULTI_FRAME,
    CRITERION_ALERT_HYGIENE,
    CRITERION_OPERATOR_REVIEW,
]

MANUAL_CRITERIA = frozenset({CRITERION_VISUAL_SANITY, CRITERION_OPERATOR_REVIEW})
CONUS_TOLERANCE_DEGREES = 5.0


@dataclass
class GeoSanityChecks:
    crs_present: bool = False
    bounds_valid: bool = False
    bounds_in_conus: bool = False
    grid_positive: bool = False
    transform_ok: bool = False
    tile_output_nonempty: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "crs_present": self.crs_present,
            "bounds_valid": self.bounds_valid,
            "bounds_in_conus_mrms_range": self.bounds_in_conus,
            "grid_positive": self.grid_positive,
            "transform_present_or_fallback": self.transform_ok,
            "tile_output_nonempty": self.tile_output_nonempty,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_proof_frame_count(requested: Optional[int]) -> int:
    if requested is None:
        return DEFAULT_PROOF_FRAME_COUNT
    return max(1, min(int(requested), MAX_PROOF_FRAME_COUNT))


def resolve_proof_source_mode(*, real: bool = False, explicit_mode: Optional[str] = None) -> str:
    if explicit_mode in ("stub", "real"):
        return explicit_mode
    if real:
        return "real"
    return "stub"


def bounds_inside_conus_mrms(bounds: list[float], *, tolerance: float = CONUS_TOLERANCE_DEGREES) -> bool:
    if len(bounds) != 4:
        return False
    west, south, east, north = bounds
    ref_w, ref_s, ref_e, ref_n = DEFAULT_MRMS_BOUNDS
    return (
        west >= ref_w - tolerance
        and south >= ref_s - tolerance
        and east <= ref_e + tolerance
        and north <= ref_n + tolerance
        and west < east
        and south < north
    )


def evaluate_geo_sanity(
    storage: LocalStorage,
    *,
    frame: RadarFile,
    geo_metadata: Optional[Any],
    tile_cache_path: Optional[str] = None,
) -> GeoSanityChecks:
    """Geo sanity helpers for proof reports (prototype, not geo-verified)."""
    result = GeoSanityChecks()

    if geo_metadata is None:
        result.errors.append("geo_metadata missing")
        return result

    result.crs_present = bool(geo_metadata.source_crs or geo_metadata.output_crs)
    result.grid_positive = geo_metadata.grid_width > 0 and geo_metadata.grid_height > 0

    validation = validate_geo_metadata(geo_metadata)
    result.bounds_valid = validation.valid and len(geo_metadata.bounds) == 4
    result.bounds_in_conus = bounds_inside_conus_mrms(list(geo_metadata.bounds))
    result.warnings.extend(validation.warnings)
    result.errors.extend(validation.errors)

    has_transform = geo_metadata.transform is not None and len(geo_metadata.transform or []) >= 6
    has_pixel_size = geo_metadata.pixel_size_x is not None and geo_metadata.pixel_size_y is not None
    result.transform_ok = has_transform or has_pixel_size or (
        result.bounds_valid and geo_metadata.source_crs in (None, "EPSG:4326", "WGS84")
    )

    if tile_cache_path and storage.path_exists(tile_cache_path):
        try:
            size = storage.absolute_path(tile_cache_path).stat().st_size
            result.tile_output_nonempty = size > 0
        except OSError:
            result.tile_output_nonempty = False
    else:
        prod_path = build_production_tile_repo_path(
            storage,
            frame.product_id,
            frame.timestamp,
            0,
            0,
            0,
        )
        if storage.path_exists(prod_path):
            try:
                result.tile_output_nonempty = storage.absolute_path(prod_path).stat().st_size > 0
            except OSError:
                result.tile_output_nonempty = False

    if not result.tile_output_nonempty:
        result.warnings.append("no non-empty tile PNG found at zoom 0/0/0")

    return result


def _criterion_record(
    criterion_id: str,
    status: str,
    *,
    message: str = "",
    details: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    return {
        "criterion_id": criterion_id,
        "status": status,
        "message": message,
        "details": details or {},
    }


def _merge_criterion_status(current: str, new: str) -> str:
    priority = {
        STATUS_FAILED: 0,
        STATUS_WARNING: 1,
        STATUS_UNKNOWN: 2,
        STATUS_SKIPPED: 3,
        STATUS_PASSED: 4,
    }
    return current if priority.get(current, 99) <= priority.get(new, 99) else new


def _find_latest_render_job(session: Session, *, layer: str, timestamp: str) -> Optional[RenderJob]:
    return (
        session.query(RenderJob)
        .filter(RenderJob.layer == layer, RenderJob.timestamp == timestamp)
        .order_by(RenderJob.id.desc())
        .first()
    )


def _compute_checksum(storage: LocalStorage, frame: RadarFile) -> Optional[str]:
    if frame.sha256:
        return frame.sha256
    if frame.raw_path and storage.path_exists(frame.raw_path):
        try:
            return storage.sha256(frame.raw_path)
        except OSError:
            return None
    return None


def _select_proof_frames(
    session: Session,
    storage: LocalStorage,
    *,
    count: int,
    source_mode: str,
) -> list[RadarFile]:
    if source_mode == "real":
        candidates = find_real_mrms_inspect_candidates(session, storage, limit=count)
        if not candidates:
            return []
        ids = [item.radar_file_id for item in candidates]
        rows = session.query(RadarFile).filter(RadarFile.id.in_(ids)).all()
        by_id = {row.id: row for row in rows}
        return [by_id[item.radar_file_id] for item in candidates if item.radar_file_id in by_id]

    rows = (
        session.query(RadarFile)
        .filter(RadarFile.raw_path.isnot(None))
        .order_by(RadarFile.timestamp.desc())
        .limit(count)
        .all()
    )
    return rows


def build_frame_proof_evidence(
    session: Session,
    storage: LocalStorage,
    frame: RadarFile,
) -> dict[str, Any]:
    """Collect per-frame evidence for proof evaluation."""
    raw_kind = frame.raw_kind or classify_raw_file(frame)
    decoder_availability = detect_decoder_availability()
    inspect_result = None
    if frame.raw_path and storage.path_exists(frame.raw_path):
        try:
            inspect_result = inspect_grib2_file(storage, frame.raw_path)
        except Exception as exc:  # noqa: BLE001 — proof report must not crash on inspect
            inspect_result = {"error": str(exc), "inspectable": False}

    artifact = find_decode_artifact_for_frame(storage, frame)
    geo = load_geo_metadata(storage, artifact.output_dir) if artifact else None
    render_info = classify_frame_render_status(storage, frame)
    render_job = _find_latest_render_job(
        session, layer=frame.product_id, timestamp=frame.timestamp
    )

    tile_cache_path = None
    if render_job and render_job.tiles_written > 0:
        tile_cache_path = build_production_tile_repo_path(
            storage, frame.product_id, frame.timestamp, 0, 0, 0
        )

    geo_sanity = evaluate_geo_sanity(
        storage,
        frame=frame,
        geo_metadata=geo,
        tile_cache_path=tile_cache_path,
    )

    checksum = _compute_checksum(storage, frame)
    file_size = frame.file_size_bytes
    if file_size is None and frame.raw_path and storage.path_exists(frame.raw_path):
        try:
            file_size = storage.absolute_path(frame.raw_path).stat().st_size
        except OSError:
            file_size = None

    inspect_dict: dict[str, Any] = {}
    if inspect_result is not None:
        if hasattr(inspect_result, "__dataclass_fields__"):
            inspect_dict = {
                "inspectable": inspect_result.inspectable,
                "raw_kind": inspect_result.raw_kind,
                "decoder_used": inspect_result.decoder_used,
                "has_grib_magic": inspect_result.has_grib_magic,
                "compressed_size_bytes": inspect_result.compressed_size_bytes,
                "error": inspect_result.error,
                "notes": inspect_result.notes[:5],
            }
        else:
            inspect_dict = dict(inspect_result)

    warnings: list[str] = []
    errors: list[str] = []
    if is_placeholder_raw_kind(raw_kind):
        warnings.append("stub/placeholder raw file — not real NOAA MRMS proof")
    if inspect_dict.get("error"):
        errors.append(str(inspect_dict["error"]))

    return {
        "radar_file_id": frame.id,
        "layer": frame.product_id,
        "timestamp": frame.timestamp,
        "source": frame.source,
        "source_url": frame.source_url,
        "source_provider": frame.source_provider,
        "raw_path": frame.raw_path,
        "raw_kind": raw_kind,
        "sha256": checksum,
        "file_size_bytes": file_size,
        "download_status": frame.download_status,
        "processed_status": frame.processed_status,
        "render_status": render_info.render_status,
        "production_rendering": frame.production_rendering,
        "decoder_available": decoder_availability.any_decoder,
        "decoder_summary": decoder_availability.summary_message(),
        "grib2_inspection": inspect_dict,
        "decode_artifact_path": artifact.output_dir if artifact else None,
        "decoder_used": artifact.decoder if artifact else None,
        "geo_metadata_path": render_info.render_metadata_path,
        "geo_metadata": geo.to_dict() if geo else None,
        "geo_sanity": geo_sanity.to_dict(),
        "render_job_id": render_job.id if render_job else None,
        "tiles_planned": render_job.progress_total if render_job else 0,
        "tiles_written": render_job.tiles_written if render_job else 0,
        "tiles_skipped": render_job.tiles_skipped if render_job else 0,
        "tile_cache_path": tile_cache_path,
        "warnings": warnings,
        "errors": errors,
    }


def evaluate_frame_criteria(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    """Evaluate per-frame criteria from collected evidence."""
    raw_kind = evidence.get("raw_kind", "")
    criteria: list[dict[str, Any]] = []

    # 1. Real NOAA source
    if not evidence.get("raw_path"):
        criteria.append(
            _criterion_record(CRITERION_REAL_NOAA_SOURCE, STATUS_SKIPPED, message="no raw_path")
        )
    elif is_real_grib2_raw_kind(raw_kind) and evidence.get("sha256"):
        status = STATUS_PASSED if evidence.get("source") == MRMS_CATALOG_SOURCE else STATUS_WARNING
        criteria.append(
            _criterion_record(
                CRITERION_REAL_NOAA_SOURCE,
                status,
                message="real .grib2.gz with checksum recorded",
                details={"source_url": evidence.get("source_url")},
            )
        )
    elif is_placeholder_raw_kind(raw_kind):
        criteria.append(
            _criterion_record(
                CRITERION_REAL_NOAA_SOURCE,
                STATUS_FAILED,
                message="stub/placeholder raw — not real NOAA MRMS",
            )
        )
    else:
        criteria.append(
            _criterion_record(
                CRITERION_REAL_NOAA_SOURCE,
                STATUS_UNKNOWN,
                message=f"unclassified raw_kind: {raw_kind}",
            )
        )

    # 2. Decoder and artifacts
    if evidence.get("decode_artifact_path") and evidence.get("geo_metadata_path"):
        criteria.append(
            _criterion_record(
                CRITERION_DECODER_ARTIFACTS,
                STATUS_PASSED,
                message="decode artifacts and geo_metadata present",
                details={"decoder_used": evidence.get("decoder_used")},
            )
        )
    elif evidence.get("decoder_available"):
        criteria.append(
            _criterion_record(
                CRITERION_DECODER_ARTIFACTS,
                STATUS_WARNING,
                message="decoder available but decode artifacts missing",
            )
        )
    else:
        criteria.append(
            _criterion_record(
                CRITERION_DECODER_ARTIFACTS,
                STATUS_FAILED,
                message="no decode artifacts; decoder may be unavailable",
            )
        )

    # 3. Product/time metadata
    if evidence.get("layer") == EXPECTED_PRODUCT_ID:
        geo = evidence.get("geo_metadata") or {}
        valid_ts = geo.get("valid_timestamp")
        frame_ts = evidence.get("timestamp")
        if valid_ts and frame_ts and valid_ts == frame_ts:
            criteria.append(
                _criterion_record(
                    CRITERION_PRODUCT_TIME,
                    STATUS_PASSED,
                    message="product and valid time match catalog",
                )
            )
        elif geo:
            criteria.append(
                _criterion_record(
                    CRITERION_PRODUCT_TIME,
                    STATUS_WARNING,
                    message="geo valid_timestamp missing or mismatched",
                    details={"valid_timestamp": valid_ts, "catalog_timestamp": frame_ts},
                )
            )
        else:
            criteria.append(
                _criterion_record(
                    CRITERION_PRODUCT_TIME,
                    STATUS_SKIPPED,
                    message="no geo_metadata for time confirmation",
                )
            )
    else:
        criteria.append(
            _criterion_record(
                CRITERION_PRODUCT_TIME,
                STATUS_FAILED,
                message=f"unexpected product_id: {evidence.get('layer')}",
            )
        )

    # 4. Geospatial correctness
    geo_sanity = evidence.get("geo_sanity") or {}
    if not evidence.get("geo_metadata"):
        criteria.append(
            _criterion_record(
                CRITERION_GEOSPATIAL,
                STATUS_SKIPPED,
                message="no geo_metadata to evaluate",
            )
        )
    elif geo_sanity.get("bounds_valid") and geo_sanity.get("grid_positive"):
        status = STATUS_PASSED if geo_sanity.get("bounds_in_conus_mrms_range") else STATUS_WARNING
        criteria.append(
            _criterion_record(
                CRITERION_GEOSPATIAL,
                status,
                message="geo sanity checks evaluated",
                details=geo_sanity,
            )
        )
    else:
        criteria.append(
            _criterion_record(
                CRITERION_GEOSPATIAL,
                STATUS_FAILED,
                message="geo sanity checks failed",
                details=geo_sanity,
            )
        )

    # 5. Visual sanity — manual only
    criteria.append(
        _criterion_record(
            CRITERION_VISUAL_SANITY,
            STATUS_SKIPPED,
            message="requires operator visual spot-check (not automated)",
        )
    )

    # 6. Tile output from decoded data
    tiles_written = int(evidence.get("tiles_written") or 0)
    tile_ok = bool(geo_sanity.get("tile_output_nonempty"))
    if tiles_written > 0 or tile_ok:
        criteria.append(
            _criterion_record(
                CRITERION_TILE_OUTPUT,
                STATUS_PASSED,
                message="tile output recorded",
                details={"tiles_written": tiles_written, "tile_cache_path": evidence.get("tile_cache_path")},
            )
        )
    elif evidence.get("decode_artifact_path"):
        criteria.append(
            _criterion_record(
                CRITERION_TILE_OUTPUT,
                STATUS_WARNING,
                message="decode artifacts exist but zero tiles written",
            )
        )
    else:
        criteria.append(
            _criterion_record(
                CRITERION_TILE_OUTPUT,
                STATUS_FAILED,
                message="no tiles from decoded data",
            )
        )

    # 7. Production path intentional
    if settings.enable_production_radar_tiles:
        gate_ok = bool(evidence.get("production_rendering")) and evidence.get("render_status") in (
            "production_rendered",
            "production_pending",
        )
        if gate_ok and tile_ok:
            criteria.append(
                _criterion_record(
                    CRITERION_PRODUCTION_PATH,
                    STATUS_PASSED,
                    message="production flag on with catalog gate and cached tile",
                )
            )
        else:
            criteria.append(
                _criterion_record(
                    CRITERION_PRODUCTION_PATH,
                    STATUS_WARNING,
                    message="production flag on but gate/tile incomplete",
                )
            )
    else:
        criteria.append(
            _criterion_record(
                CRITERION_PRODUCTION_PATH,
                STATUS_SKIPPED,
                message="ENABLE_PRODUCTION_RADAR_TILES=false (default) — intentional",
            )
        )

    # 8–10 are aggregate-only at frame level → skipped
    for cid in (CRITERION_MULTI_FRAME, CRITERION_ALERT_HYGIENE, CRITERION_OPERATOR_REVIEW):
        criteria.append(_criterion_record(cid, STATUS_SKIPPED, message="evaluated at report level"))

    return criteria


def _aggregate_frame_criteria(
    frame_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge per-frame criteria into report-level statuses."""
    per_id: dict[str, dict[str, Any]] = {}
    for frame in frame_results:
        for item in frame.get("criteria") or []:
            cid = item["criterion_id"]
            if cid in (CRITERION_MULTI_FRAME, CRITERION_ALERT_HYGIENE, CRITERION_OPERATOR_REVIEW):
                continue
            existing = per_id.get(cid)
            if existing is None:
                per_id[cid] = dict(item)
                existing = per_id[cid]
            else:
                existing["status"] = _merge_criterion_status(existing["status"], item["status"])
                if item.get("message"):
                    messages = existing.setdefault("frame_messages", [])
                    if item["message"] not in messages:
                        messages.append(item["message"])

    aggregated = [per_id[cid] for cid in ALL_CRITERION_IDS if cid in per_id]

    # Multi-frame
    frame_count = len(frame_results)
    real_frames = sum(
        1
        for fr in frame_results
        if is_real_grib2_raw_kind((fr.get("evidence") or {}).get("raw_kind", ""))
    )
    decoded_frames = sum(
        1 for fr in frame_results if (fr.get("evidence") or {}).get("decode_artifact_path")
    )
    if frame_count < DEFAULT_PROOF_FRAME_COUNT:
        multi_status = STATUS_FAILED if frame_count > 0 else STATUS_SKIPPED
        multi_msg = f"only {frame_count} frame(s) evaluated; need {DEFAULT_PROOF_FRAME_COUNT}+"
    elif decoded_frames >= DEFAULT_PROOF_FRAME_COUNT:
        multi_status = STATUS_PASSED
        multi_msg = f"{decoded_frames}/{frame_count} frames with decode artifacts"
    elif real_frames >= DEFAULT_PROOF_FRAME_COUNT:
        multi_status = STATUS_WARNING
        multi_msg = f"{real_frames} real frames but only {decoded_frames} decoded"
    else:
        multi_status = STATUS_FAILED
        multi_msg = "insufficient real/decoded frames across batch"

    aggregated.append(
        _criterion_record(
            CRITERION_MULTI_FRAME,
            multi_status,
            message=multi_msg,
            details={"frame_count": frame_count, "decoded_frames": decoded_frames, "real_frames": real_frames},
        )
    )

    return aggregated


def _evaluate_alert_hygiene(storage: LocalStorage) -> dict[str, Any]:
    alert = load_validation_alert(storage)
    if alert is None:
        return _criterion_record(
            CRITERION_ALERT_HYGIENE,
            STATUS_UNKNOWN,
            message="no validation alert marker yet",
        )
    status = alert.get("status", "ok")
    if status == "failed":
        return _criterion_record(
            CRITERION_ALERT_HYGIENE,
            STATUS_FAILED,
            message="validation alert status failed",
            details={"failure_count": alert.get("failure_count"), "warning_count": alert.get("warning_count")},
        )
    if status == "warning":
        return _criterion_record(
            CRITERION_ALERT_HYGIENE,
            STATUS_WARNING,
            message="validation alert has warnings",
            details={"warning_count": alert.get("warning_count")},
        )
    return _criterion_record(
        CRITERION_ALERT_HYGIENE,
        STATUS_PASSED,
        message="validation alert status ok",
    )


def _evaluate_operator_review() -> dict[str, Any]:
    return _criterion_record(
        CRITERION_OPERATOR_REVIEW,
        STATUS_SKIPPED,
        message="operator sign-off required — use docs/MRMS_OPERATOR_SIGNOFF_TEMPLATE.md",
        details={"signing_does_not_set_verified_mrms": True},
    )


def _count_criteria_statuses(criteria: list[dict[str, Any]]) -> dict[str, int]:
    counts = {STATUS_PASSED: 0, STATUS_FAILED: 0, STATUS_WARNING: 0, STATUS_SKIPPED: 0, STATUS_UNKNOWN: 0}
    for item in criteria:
        status = item.get("status", STATUS_UNKNOWN)
        counts[status] = counts.get(status, 0) + 1
    return counts


def resolve_overall_proof_status(
    *,
    frame_count: int,
    aggregate_criteria: list[dict[str, Any]],
) -> str:
    if frame_count == 0:
        return OVERALL_INSUFFICIENT

    counts = _count_criteria_statuses(aggregate_criteria)
    if counts.get(STATUS_FAILED, 0) > 0:
        return OVERALL_FAILED

    automated = [c for c in aggregate_criteria if c["criterion_id"] not in MANUAL_CRITERIA]
    if not automated:
        return OVERALL_INSUFFICIENT

    skipped_unknown = sum(
        1 for c in automated if c.get("status") in (STATUS_SKIPPED, STATUS_UNKNOWN)
    )
    if skipped_unknown >= len(automated) - 1:
        return OVERALL_INSUFFICIENT

    passed = counts.get(STATUS_PASSED, 0)
    if passed >= 4 and counts.get(STATUS_FAILED, 0) == 0:
        return OVERALL_READY_REVIEW

    return OVERALL_INSUFFICIENT


def generate_mrms_proof_report(
    session: Session,
    storage: LocalStorage,
    *,
    count: Optional[int] = None,
    source_mode: str = "stub",
) -> dict[str, Any]:
    """Build multi-frame proof report from catalog evidence (no network by default)."""
    effective_count = resolve_proof_frame_count(count)
    frames = _select_proof_frames(session, storage, count=effective_count, source_mode=source_mode)

    frame_results: list[dict[str, Any]] = []
    for frame in frames:
        evidence = build_frame_proof_evidence(session, storage, frame)
        criteria = evaluate_frame_criteria(evidence)
        frame_results.append(
            {
                "radar_file_id": frame.id,
                "timestamp": frame.timestamp,
                "layer": frame.product_id,
                "evidence": evidence,
                "criteria": criteria,
            }
        )

    aggregate = _aggregate_frame_criteria(frame_results)
    aggregate.append(_evaluate_alert_hygiene(storage))
    aggregate.append(_evaluate_operator_review())

    criteria_counts = _count_criteria_statuses(aggregate)
    overall = resolve_overall_proof_status(
        frame_count=len(frame_results),
        aggregate_criteria=aggregate,
    )

    warnings: list[str] = [
        "Proof report is draft evidence gathering — NOT verified MRMS.",
        "verified_mrms remains false; operator_review_required is always true.",
    ]
    if source_mode == "stub":
        warnings.append("Stub mode: evaluating local catalog only; real NOAA proof requires --real.")
    if not settings.enable_production_radar_tiles:
        warnings.append("Production rendering disabled by default (expected).")

    return {
        "generated_at": _utc_now(),
        "source_mode": source_mode,
        "requested_frame_count": effective_count,
        "frame_count": len(frame_results),
        "overall_status": overall,
        "criteria_counts": criteria_counts,
        "aggregate_criteria": aggregate,
        "frames": frame_results,
        "production_rendering_enabled": settings.enable_production_radar_tiles,
        "decoder_available": detect_decoder_availability().any_decoder,
        "warnings": warnings,
        "errors": [],
        "verified_mrms": False,
        "proof_only": True,
        "operator_review_required": True,
        "prototype": True,
        "signoff_template_path": "docs/MRMS_OPERATOR_SIGNOFF_TEMPLATE.md",
    }


def save_mrms_proof_report(storage: LocalStorage, report: dict[str, Any]) -> str:
    record = dict(report)
    record.setdefault("generated_at", _utc_now())
    record.setdefault("verified_mrms", False)
    record.setdefault("proof_only", True)
    record.setdefault("operator_review_required", True)
    repo_path = storage.normalize_path(MRMS_PROOF_LATEST_PATH)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(record, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _append_proof_history(storage, record)
    return repo_path


def load_mrms_proof_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    repo_path = storage.normalize_path(MRMS_PROOF_LATEST_PATH)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return None
    try:
        return json.loads(abs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def load_mrms_proof_history(storage: LocalStorage) -> list[dict[str, Any]]:
    repo_path = storage.normalize_path(MRMS_PROOF_HISTORY_PATH)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return []
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _append_proof_history(storage: LocalStorage, record: dict[str, Any]) -> None:
    history = load_mrms_proof_history(storage)
    compact = {
        "generated_at": record.get("generated_at"),
        "source_mode": record.get("source_mode"),
        "overall_status": record.get("overall_status"),
        "frame_count": record.get("frame_count"),
        "criteria_counts": record.get("criteria_counts"),
        "verified_mrms": False,
        "proof_only": True,
        "operator_review_required": True,
        "prototype": True,
    }
    history.insert(0, compact)
    history = history[:MAX_PROOF_HISTORY]
    repo_path = storage.normalize_path(MRMS_PROOF_HISTORY_PATH)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(history, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def compact_mrms_proof_report(report: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if report is None:
        return {
            "overall_status": OVERALL_NOT_STARTED,
            "frame_count": 0,
            "criteria_counts": {},
            "operator_review_required": True,
            "proof_only": True,
            "verified_mrms": False,
            "prototype": True,
            "generated_at": None,
        }
    return {
        "generated_at": report.get("generated_at"),
        "overall_status": report.get("overall_status", OVERALL_INSUFFICIENT),
        "source_mode": report.get("source_mode"),
        "frame_count": report.get("frame_count", 0),
        "criteria_counts": report.get("criteria_counts", {}),
        "operator_review_required": True,
        "proof_only": True,
        "verified_mrms": False,
        "prototype": True,
    }


def write_operator_signoff_template_copy(storage: LocalStorage) -> str:
    """Copy sign-off template reference into data/dev for operator convenience."""
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[3]
    source = project_root / "docs" / "MRMS_OPERATOR_SIGNOFF_TEMPLATE.md"
    target_repo = storage.normalize_path("dev/mrms_operator_signoff_template.md")
    storage.ensure_directories("dev")
    if source.is_file():
        storage.absolute_path(target_repo).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        storage.write_text(
            target_repo,
            "# Operator sign-off\n\nTemplate missing from docs/. See docs/MRMS_OPERATOR_SIGNOFF_TEMPLATE.md\n",
        )
    return target_repo
