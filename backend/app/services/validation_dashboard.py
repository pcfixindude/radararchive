"""Dev validation dashboard summary — prototype only, not verified MRMS."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.catalog_status import build_catalog_status
from backend.app.services.grib2_inspector import detect_decoder_availability
from backend.app.services.mrms_operator_handoff import (
    compact_operator_handoff_status,
    load_latest_operator_handoff,
)
from backend.app.services.operator_guidance import compact_operator_guidance
from backend.app.services.mrms_visual_review import (
    compact_mrms_visual_review,
    compact_scheduled_visual_review,
)
from backend.app.services.mrms_visual_review_compare import compact_visual_review_comparison_summary
from backend.app.services.mrms_visual_review_hint import compact_visual_review_hint
from backend.app.services.mrms_visual_review_sample_set import compact_visual_review_sample_set
from backend.app.services.mrms_visual_review_sample_readiness import (
    compact_visual_review_sample_readiness,
)
from backend.app.services.mrms_render_candidate_preflight import (
    compact_render_candidate_preflight,
)
from backend.app.services.mrms_render_candidate_dry_run_plan import (
    compact_render_candidate_dry_run_plan,
)
from backend.app.services.mrms_render_candidate_scaffold import (
    compact_render_candidate_scaffold,
)
from backend.app.services.mrms_render_candidate_sandbox import (
    compact_render_candidate_sandbox,
)
from backend.app.services.mrms_render_candidate_sandbox_import_export import (
    compact_render_candidate_sandbox_import_export,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_history import (
    compact_comparison_history,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_trend_hint import (
    compact_sandbox_comparison_trend_hint,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_review_acknowledgment import (
    compact_sandbox_comparison_review_acknowledgment_summary,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status import (
    compact_sandbox_comparison_acknowledgment_status,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_history import (
    compact_ack_status_history,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint import (
    compact_ack_status_trend_hint,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment import (
    compact_ack_status_trend_review_acknowledgment_summary,
)
from backend.app.services.mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status import (
    compact_ack_status_trend_review_acknowledgment_status,
)
from backend.app.services.operator_review_status import (
    compact_operator_review_status,
    compact_scheduled_operator_status,
)
from backend.app.services.operator_workflow_presets import compact_operator_workflow_presets
from backend.app.services.proof_bundle_diff_acknowledgment import (
    compact_diff_acknowledgment_summary,
    load_diff_acknowledgments,
)
from backend.app.services.proof_bundle_diff_alert_trends import (
    compact_proof_bundle_diff_alert_trend,
)
from backend.app.services.proof_bundle_diff_escalation import (
    compact_proof_bundle_diff_escalation,
)
from backend.app.services.proof_bundle_diff_escalation_history import (
    compact_proof_bundle_diff_escalation_history_summary,
    load_recent_proof_bundle_diff_escalation_history,
)
from backend.app.services.proof_bundle_diff_escalation_metrics import (
    compact_proof_bundle_diff_escalation_metrics,
)
from backend.app.services.proof_bundle_diff_escalation_digest import (
    compact_proof_bundle_diff_escalation_digest,
    compact_scheduled_digest,
)
from backend.app.services.proof_bundle_diff_escalation_digest_diff import (
    build_digest_regeneration_hint,
    compact_digest_diff_summary,
    load_latest_digest_diff_metadata,
)
from backend.app.services.proof_bundle_diff_escalation_digest_history import (
    compact_digest_history_summary,
    load_recent_digest_export_history,
)
from backend.app.services.proof_bundle_diff_alert_history import (
    compact_latest_proof_bundle_diff_alert,
    load_recent_proof_bundle_diff_alert_history,
)
from backend.app.services.mrms_proof_bundle import (
    compact_proof_bundle_status,
    load_latest_proof_bundle_manifest,
    RUNBOOK_LINK_METADATA,
)
from backend.app.services.mrms_proof_bundle_diff import (
    compact_proof_bundle_diff_status,
    compact_scheduled_proof_bundle,
    load_latest_proof_bundle_diff,
)
from backend.app.services.mrms_proof_regression import compact_proof_regression, load_proof_regression_report
from backend.app.services.mrms_proof_report import compact_mrms_proof_report, load_mrms_proof_report
from backend.app.services.mrms_signoff import compact_signoff_summary, load_signoffs
from backend.app.services.mrms_review_session import (
    compact_latest_review_session_summary,
    build_review_sessions_payload,
)
from backend.app.services.mrms_review_session_export import (
    build_review_export_regeneration_hint,
    compact_review_session_export_summary,
    compact_scheduled_review_export,
)
from backend.app.services.mrms_review_session_export_diff import (
    compact_review_session_export_diff_summary,
    compact_review_session_export_diff_history_summary,
)
from backend.app.services.mrms_review_session_export_diff_trends import (
    compact_review_session_export_diff_trend,
)
from backend.app.services.mrms_review_session_export_diff_trend_hint import (
    build_review_session_export_diff_trend_hint,
    compact_review_session_export_diff_trend_hint,
)
from backend.app.services.render_queue import get_queue_summary
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import (
    compact_validation_alert,
    load_validation_alert,
    refresh_validation_alert,
)
from backend.app.services.validation_failure_log import (
    compact_failure,
    count_validation_failures,
    load_recent_validation_failures,
)
from backend.app.services.validation_report_store import (
    load_latest_benchmark_report,
    load_latest_queue_benchmark_report,
    load_latest_scheduled_validation_report,
    load_latest_validation_report,
    load_queue_benchmark_history,
    load_validation_history,
)


def build_validation_summary(session: Session, storage: LocalStorage) -> dict[str, Any]:
    """Compact dashboard summary for dev UI and GET /api/validation/summary."""
    availability = detect_decoder_availability()
    queue = get_queue_summary(session)
    validation = load_latest_validation_report(storage)
    benchmark = load_latest_benchmark_report(storage)
    queue_benchmark = load_latest_queue_benchmark_report(storage)
    history = load_validation_history(storage)
    queue_benchmark_history = load_queue_benchmark_history(storage)
    scheduled = load_latest_scheduled_validation_report(storage)
    recent_failures = load_recent_validation_failures(storage, limit=5)
    alert = load_validation_alert(storage)
    if alert is None:
        alert = refresh_validation_alert(storage, scheduled=scheduled)
    proof = load_mrms_proof_report(storage)
    regression = load_proof_regression_report(storage)
    signoff_summary = compact_signoff_summary(storage)
    catalog = build_catalog_status(session)

    return {
        "prototype": True,
        "verified_mrms": False,
        "production_rendering_enabled": settings.enable_production_radar_tiles,
        "placeholder_default": not settings.enable_production_radar_tiles
        and not settings.enable_decoded_tiles,
        "decoder_available": availability.any_decoder,
        "decoder_summary": availability.summary_message(),
        "stale_running_job_seconds": settings.stale_running_job_seconds,
        "validation_available": validation is not None,
        "validation": _compact_validation(validation),
        "frame_summaries": _compact_frame_summaries(validation),
        "benchmark_available": benchmark is not None,
        "benchmark": _compact_benchmark(benchmark),
        "queue_benchmark_available": queue_benchmark is not None,
        "queue_benchmark": _compact_queue_benchmark(queue_benchmark),
        "render_queue": queue.to_dict(),
        "validation_history_count": len(history),
        "validation_history": history[:5],
        "queue_benchmark_history_count": len(queue_benchmark_history),
        "scheduled_validation_available": scheduled is not None,
        "scheduled_validation": _compact_scheduled_validation(scheduled),
        "scheduled_proof_bundle": compact_scheduled_proof_bundle(scheduled),
        "scheduled_digest": compact_scheduled_digest(scheduled),
        "scheduled_review_export": compact_scheduled_review_export(scheduled),
        "scheduled_visual_review": compact_scheduled_visual_review(scheduled),
        "validation_failures_count": count_validation_failures(storage),
        "validation_failures_recent": [compact_failure(item) for item in recent_failures],
        "validation_alert": compact_validation_alert(alert),
        "grouped_failure_causes": (alert or {}).get("grouped_failure_causes", [])[:5],
        "mrms_proof": compact_mrms_proof_report(proof),
        "mrms_proof_available": proof is not None,
        "mrms_proof_regression": compact_proof_regression(regression),
        "mrms_proof_regression_available": regression is not None,
        "mrms_signoff": signoff_summary,
        "mrms_proof_bundle": compact_proof_bundle_status(storage),
        "mrms_proof_bundle_diff": compact_proof_bundle_diff_status(storage),
        "operator_handoff": compact_operator_handoff_status(storage, scheduled=scheduled),
        "operator_guidance": compact_operator_guidance(alert),
        "proof_bundle_diff_alert": compact_latest_proof_bundle_diff_alert(storage),
        "proof_bundle_diff_alert_history": load_recent_proof_bundle_diff_alert_history(
            storage, limit=5
        ),
        "proof_bundle_diff_alert_trend": compact_proof_bundle_diff_alert_trend(storage),
        "proof_bundle_diff_acknowledgment": compact_diff_acknowledgment_summary(storage),
        "proof_bundle_diff_escalation": compact_proof_bundle_diff_escalation(storage),
        "proof_bundle_diff_escalation_history": compact_proof_bundle_diff_escalation_history_summary(
            storage
        ),
        "proof_bundle_diff_escalation_metrics": compact_proof_bundle_diff_escalation_metrics(
            storage
        ),
        "proof_bundle_diff_escalation_digest": compact_proof_bundle_diff_escalation_digest(storage),
        "proof_bundle_diff_escalation_digest_history": compact_digest_history_summary(storage),
        "proof_bundle_diff_escalation_digest_diff": compact_digest_diff_summary(storage),
        "digest_regeneration_hint": build_digest_regeneration_hint(storage),
        "mrms_review_session": compact_latest_review_session_summary(storage),
        "mrms_review_session_export": compact_review_session_export_summary(storage),
        "mrms_review_session_export_diff": compact_review_session_export_diff_summary(storage),
        "mrms_review_session_export_diff_history": compact_review_session_export_diff_history_summary(
            storage
        ),
        "mrms_review_session_export_diff_trend": compact_review_session_export_diff_trend(storage),
        "mrms_review_session_export_diff_trend_hint": compact_review_session_export_diff_trend_hint(
            storage
        ),
        "review_export_regeneration_hint": build_review_export_regeneration_hint(storage),
        "operator_review_status": compact_operator_review_status(storage),
        "operator_workflow_presets": compact_operator_workflow_presets(storage),
        "mrms_visual_review": compact_mrms_visual_review(storage),
        "mrms_visual_review_comparison": compact_visual_review_comparison_summary(storage),
        "mrms_visual_review_hint": compact_visual_review_hint(storage),
        "mrms_visual_review_sample_set": compact_visual_review_sample_set(storage),
        "mrms_visual_review_sample_readiness": compact_visual_review_sample_readiness(storage),
        "mrms_render_candidate_preflight": compact_render_candidate_preflight(storage),
        "mrms_render_candidate_dry_run_plan": compact_render_candidate_dry_run_plan(storage),
        "mrms_render_candidate_scaffold": compact_render_candidate_scaffold(storage),
        "mrms_render_candidate_sandbox": compact_render_candidate_sandbox(storage),
        "mrms_render_candidate_sandbox_import_export": compact_render_candidate_sandbox_import_export(
            storage
        ),
        "mrms_render_candidate_sandbox_comparison_history": compact_comparison_history(storage),
        "mrms_render_candidate_sandbox_comparison_trend_hint": compact_sandbox_comparison_trend_hint(
            storage
        ),
        "mrms_render_candidate_sandbox_comparison_review_acknowledgment": (
            compact_sandbox_comparison_review_acknowledgment_summary(storage)
        ),
        "mrms_render_candidate_sandbox_comparison_acknowledgment_status": (
            compact_sandbox_comparison_acknowledgment_status(storage)
        ),
        "mrms_render_candidate_sandbox_comparison_acknowledgment_status_history": (
            compact_ack_status_history(storage)
        ),
        "mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint": (
            compact_ack_status_trend_hint(storage)
        ),
        "mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment": (
            compact_ack_status_trend_review_acknowledgment_summary(storage)
        ),
        "mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status": (
            compact_ack_status_trend_review_acknowledgment_status(storage)
        ),
        "scheduled_operator_status": compact_scheduled_operator_status(scheduled),
        "runbook_references": RUNBOOK_LINK_METADATA,
        "catalog": catalog,
    }


def build_validation_latest(storage: LocalStorage) -> dict[str, Any]:
    """Full latest persisted reports for GET /api/validation/latest."""
    return {
        "prototype": True,
        "verified_mrms": False,
        "production_rendering_enabled": settings.enable_production_radar_tiles,
        "validation": load_latest_validation_report(storage),
        "benchmark": load_latest_benchmark_report(storage),
        "queue_benchmark": load_latest_queue_benchmark_report(storage),
        "scheduled_validation": load_latest_scheduled_validation_report(storage),
        "validation_alert": load_validation_alert(storage),
        "mrms_proof": load_mrms_proof_report(storage),
        "mrms_proof_regression": load_proof_regression_report(storage),
        "mrms_signoffs": load_signoffs(storage)[:10],
        "mrms_proof_bundle": load_latest_proof_bundle_manifest(storage),
        "mrms_proof_bundle_diff": load_latest_proof_bundle_diff(storage),
        "operator_handoff": load_latest_operator_handoff(storage),
        "proof_bundle_diff_alert_history": load_recent_proof_bundle_diff_alert_history(
            storage, limit=25
        ),
        "proof_bundle_diff_alert_trend": compact_proof_bundle_diff_alert_trend(storage),
        "proof_bundle_diff_acknowledgments": load_diff_acknowledgments(storage)[:25],
        "proof_bundle_diff_escalation": compact_proof_bundle_diff_escalation(storage),
        "proof_bundle_diff_escalation_history": load_recent_proof_bundle_diff_escalation_history(
            storage, limit=25
        ),
        "proof_bundle_diff_escalation_metrics": compact_proof_bundle_diff_escalation_metrics(
            storage
        ),
        "proof_bundle_diff_escalation_digest": compact_proof_bundle_diff_escalation_digest(storage),
        "proof_bundle_diff_escalation_digest_history": load_recent_digest_export_history(
            storage, limit=25
        ),
        "proof_bundle_diff_escalation_digest_diff": load_latest_digest_diff_metadata(storage),
        "digest_regeneration_hint": build_digest_regeneration_hint(storage),
        "operator_review_status": compact_operator_review_status(storage),
        "operator_workflow_presets": compact_operator_workflow_presets(storage),
        "mrms_review_sessions": build_review_sessions_payload(storage, limit=10).get("entries", []),
    }


def _compact_validation(validation: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if validation is None:
        return None
    tile_cache = validation.get("tile_cache") or {}
    return {
        "validated_at": validation.get("validated_at"),
        "source_mode": validation.get("source_mode"),
        "batch": validation.get("batch", False),
        "requested_frame_count": validation.get("requested_frame_count"),
        "effective_frame_count": validation.get("effective_frame_count"),
        "discovered_count": validation.get("discovered_count", 0),
        "downloaded_count": validation.get("downloaded_count", 0),
        "inspected_count": validation.get("inspected_count", 0),
        "decoded_count": validation.get("decoded_count", 0),
        "render_jobs_enqueued": validation.get("render_jobs_enqueued", 0),
        "worker_jobs_processed": validation.get("worker_jobs_processed", 0),
        "tiles_planned": validation.get("tiles_planned", 0),
        "tiles_written": validation.get("tiles_written", tile_cache.get("tiles_written", 0)),
        "tiles_skipped": validation.get("tiles_skipped", tile_cache.get("tiles_skipped", 0)),
        "output_bytes": validation.get("output_bytes", tile_cache.get("output_bytes", 0)),
        "elapsed_seconds": validation.get("elapsed_seconds"),
        "decoder_available": validation.get("decoder_available", False),
        "tile_cache": tile_cache,
        "warnings": validation.get("warnings", [])[:5],
        "errors": validation.get("errors", [])[:5],
        "verified_mrms": False,
        "prototype": True,
    }


def _compact_benchmark(benchmark: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if benchmark is None:
        return None
    return {
        "benchmarked_at": benchmark.get("benchmarked_at"),
        "source_mode": benchmark.get("source_mode"),
        "stage_timings": benchmark.get("stage_timings", []),
        "min_zoom": benchmark.get("min_zoom"),
        "max_zoom": benchmark.get("max_zoom"),
        "tiles_planned": benchmark.get("tiles_planned", 0),
        "tiles_written": benchmark.get("tiles_written", 0),
        "tiles_skipped": benchmark.get("tiles_skipped", 0),
        "output_bytes": benchmark.get("output_bytes", 0),
        "tile_build_elapsed_seconds": benchmark.get("tile_build_elapsed_seconds", 0.0),
        "decoder_used": benchmark.get("decoder_used"),
        "warnings": benchmark.get("warnings", [])[:5],
        "errors": benchmark.get("errors", [])[:5],
        "verified_mrms": False,
        "prototype": True,
    }


def _compact_queue_benchmark(
    queue_benchmark: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    if queue_benchmark is None:
        return None
    job_summaries = queue_benchmark.get("job_summaries", [])
    compact_jobs = [
        {
            "timestamp": item.get("timestamp"),
            "radar_file_id": item.get("radar_file_id"),
            "job_id": item.get("job_id"),
            "status": item.get("status"),
            "decode_status": item.get("decode_status"),
            "min_zoom": item.get("min_zoom"),
            "max_zoom": item.get("max_zoom"),
            "tiles_planned": item.get("tiles_planned", item.get("progress_total", 0)),
            "tiles_written": item.get("tiles_written", 0),
            "tiles_skipped": item.get("tiles_skipped", 0),
            "output_bytes": item.get("output_bytes", 0),
            "elapsed_seconds": item.get("elapsed_seconds"),
            "warnings": (item.get("warnings") or [])[:2],
            "errors": (item.get("errors") or [])[:2],
        }
        for item in job_summaries[:5]
    ]
    return {
        "benchmarked_at": queue_benchmark.get("benchmarked_at"),
        "source_mode": queue_benchmark.get("source_mode"),
        "effective_count": queue_benchmark.get("effective_count"),
        "min_zoom": queue_benchmark.get("min_zoom"),
        "max_zoom": queue_benchmark.get("max_zoom"),
        "dry_run": queue_benchmark.get("dry_run", False),
        "jobs_enqueued": queue_benchmark.get("jobs_enqueued", 0),
        "jobs_processed": queue_benchmark.get("jobs_processed", 0),
        "jobs_succeeded": queue_benchmark.get("jobs_succeeded", 0),
        "jobs_failed": queue_benchmark.get("jobs_failed", 0),
        "total_tiles_written": queue_benchmark.get("total_tiles_written", 0),
        "total_tiles_skipped": queue_benchmark.get("total_tiles_skipped", 0),
        "total_output_bytes": queue_benchmark.get("total_output_bytes", 0),
        "total_elapsed_seconds": queue_benchmark.get("total_elapsed_seconds"),
        "job_summaries": compact_jobs,
        "warnings": queue_benchmark.get("warnings", [])[:5],
        "errors": queue_benchmark.get("errors", [])[:5],
        "verified_mrms": False,
        "prototype": True,
    }


def _compact_frame_summaries(validation: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    if validation is None:
        return []
    summaries = validation.get("frame_summaries") or []
    return [
        {
            "timestamp": item.get("timestamp"),
            "radar_file_id": item.get("radar_file_id"),
            "decode_status": item.get("decode_status"),
            "render_job_id": item.get("render_job_id"),
            "min_zoom": item.get("min_zoom"),
            "max_zoom": item.get("max_zoom"),
            "tiles_planned": item.get("tiles_planned", 0),
            "tiles_written": item.get("tiles_written", 0),
            "tiles_skipped": item.get("tiles_skipped", 0),
            "output_bytes": item.get("output_bytes", 0),
            "elapsed_seconds": item.get("elapsed_seconds"),
            "warnings": (item.get("warnings") or [])[:2],
            "errors": (item.get("errors") or [])[:2],
        }
        for item in summaries[:5]
    ]


def _compact_scheduled_proof_step(
    scheduled: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    if scheduled is None:
        return None
    steps = scheduled.get("steps") or []
    proof_step = next(
        (step for step in steps if step.get("name") in ("proof_report", "mrms_proof_report")),
        None,
    )
    proof_requested = bool(scheduled.get("proof_requested"))
    if proof_step is None and not proof_requested:
        return {
            "ran": False,
            "proof_requested": False,
            "status": None,
            "elapsed_seconds": None,
            "proof_regression_status": None,
            "proof_regression_detected": False,
            "verified_mrms": False,
            "prototype": True,
        }
    regression_after = scheduled.get("mrms_proof_regression") or {}
    return {
        "ran": proof_step is not None,
        "proof_requested": proof_requested or proof_step is not None,
        "status": (proof_step or {}).get("status"),
        "elapsed_seconds": (proof_step or {}).get("elapsed_seconds"),
        "proof_regression_status": regression_after.get("regression_status"),
        "proof_regression_detected": bool(regression_after.get("regression_detected")),
        "verified_mrms": False,
        "prototype": True,
    }


def _compact_scheduled_validation(
    scheduled: Optional[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    if scheduled is None:
        return None
    batch = scheduled.get("batch_validation") or {}
    queue = scheduled.get("queue_benchmark") or {}
    steps = scheduled.get("steps") or []
    steps_ok = sum(1 for step in steps if step.get("status") in ("succeeded", "warning", "ok"))
    steps_failed = sum(1 for step in steps if step.get("status") in ("failed", "error"))
    compact_steps = [
        {
            "name": step.get("name"),
            "status": step.get("status"),
            "started_at": step.get("started_at"),
            "finished_at": step.get("finished_at"),
            "elapsed_seconds": step.get("elapsed_seconds"),
            "summary": step.get("summary", {}),
            "warnings": (step.get("warnings") or [])[:2],
            "errors": (step.get("errors") or [])[:2],
        }
        for step in steps
    ]
    return {
        "ran_at": scheduled.get("ran_at"),
        "source_mode": scheduled.get("source_mode"),
        "success": scheduled.get("success", False),
        "exit_code": scheduled.get("exit_code", 1),
        "effective_count": scheduled.get("effective_count"),
        "min_zoom": scheduled.get("min_zoom"),
        "max_zoom": scheduled.get("max_zoom"),
        "elapsed_seconds": scheduled.get("elapsed_seconds"),
        "steps_ok": steps_ok,
        "steps_failed": steps_failed,
        "steps": compact_steps,
        "batch_decoded_count": batch.get("decoded_count", 0),
        "queue_jobs_succeeded": queue.get("jobs_succeeded", 0),
        "queue_jobs_failed": queue.get("jobs_failed", 0),
        "warnings": scheduled.get("warnings", [])[:5],
        "errors": scheduled.get("errors", [])[:5],
        "proof_step": _compact_scheduled_proof_step(scheduled),
        "verified_mrms": False,
        "prototype": True,
    }
