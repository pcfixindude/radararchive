"""Cron-friendly scheduled local validation orchestrator (dev/prototype only)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from backend.app.config import MRMS_SOURCE_MODE_REAL, MRMS_SOURCE_MODE_STUB, settings
from backend.app.services.catalog_status import build_catalog_status
from backend.app.services.mrms_batch_validation import (
    DEFAULT_BATCH_FRAME_COUNT,
    BatchValidationReport,
    run_mrms_batch_validation,
)
from backend.app.services.mrms_validation import resolve_validation_source_mode
from backend.app.services.render_queue import get_queue_summary
from backend.app.services.render_queue_benchmark import (
    DEFAULT_MAX_ZOOM,
    DEFAULT_MIN_ZOOM,
    RenderQueueBenchmarkReport,
    run_render_queue_benchmark,
)
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_dashboard import build_validation_summary
from backend.app.services.validation_failure_log import append_validation_failure
from backend.app.services.validation_report_store import save_scheduled_validation_report

DEFAULT_SCHEDULED_COUNT = DEFAULT_BATCH_FRAME_COUNT
DEFAULT_SCHEDULED_MIN_ZOOM = DEFAULT_MIN_ZOOM
DEFAULT_SCHEDULED_MAX_ZOOM = DEFAULT_MAX_ZOOM
SMOKE_TEST_COUNT = 1
SMOKE_TEST_MIN_ZOOM = 0
SMOKE_TEST_MAX_ZOOM = 0

STEP_SUCCEEDED = "succeeded"
STEP_FAILED = "failed"
STEP_WARNING = "warning"
STEP_SKIPPED = "skipped"


@dataclass
class ScheduledValidationStep:
    name: str
    status: str = STEP_SUCCEEDED
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    elapsed_seconds: float = 0.0
    summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
            "summary": self.summary,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass
class ScheduledValidationReport:
    source_mode: str
    requested_count: int = DEFAULT_SCHEDULED_COUNT
    effective_count: int = DEFAULT_SCHEDULED_COUNT
    min_zoom: int = DEFAULT_SCHEDULED_MIN_ZOOM
    max_zoom: int = DEFAULT_SCHEDULED_MAX_ZOOM
    real_requested: bool = False
    success: bool = True
    exit_code: int = 0
    steps: list[ScheduledValidationStep] = field(default_factory=list)
    catalog: Optional[dict[str, Any]] = None
    batch_validation: Optional[dict[str, Any]] = None
    queue_benchmark: Optional[dict[str, Any]] = None
    render_queue: Optional[dict[str, Any]] = None
    validation_summary: Optional[dict[str, Any]] = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    production_rendering_enabled: bool = False
    verified_mrms: bool = False
    prototype: bool = True
    ran_at: Optional[str] = None
    command_context: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_mode": self.source_mode,
            "requested_count": self.requested_count,
            "effective_count": self.effective_count,
            "min_zoom": self.min_zoom,
            "max_zoom": self.max_zoom,
            "real_requested": self.real_requested,
            "success": self.success,
            "exit_code": self.exit_code,
            "steps": [step.to_dict() for step in self.steps],
            "catalog": self.catalog,
            "batch_validation": self.batch_validation,
            "queue_benchmark": self.queue_benchmark,
            "render_queue": self.render_queue,
            "validation_summary": self.validation_summary,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "elapsed_seconds": round(self.elapsed_seconds, 4),
            "production_rendering_enabled": self.production_rendering_enabled,
            "verified_mrms": self.verified_mrms,
            "prototype": self.prototype,
            "ran_at": self.ran_at,
            "command_context": self.command_context,
        }


def resolve_scheduled_source_mode(*, real_requested: bool) -> str:
    """Stub/offline by default; real only when explicitly requested."""
    return resolve_validation_source_mode(real_requested=real_requested)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _finalize_step_status(step: ScheduledValidationStep) -> None:
    if step.errors:
        step.status = STEP_FAILED
    elif step.warnings:
        step.status = STEP_WARNING
    elif step.status not in (STEP_SKIPPED, STEP_FAILED, STEP_WARNING):
        step.status = STEP_SUCCEEDED


def _run_step(
    name: str,
    fn: Callable[[], Any],
    *,
    summarize: Callable[[Any], dict[str, Any]],
) -> tuple[ScheduledValidationStep, Any]:
    step = ScheduledValidationStep(name=name, started_at=_utc_now())
    start = time.perf_counter()
    try:
        result = fn()
        step.summary = summarize(result)
        step.elapsed_seconds = time.perf_counter() - start
        step.finished_at = _utc_now()
        _finalize_step_status(step)
        return step, result
    except Exception as exc:
        step.status = STEP_FAILED
        step.errors.append(str(exc))
        step.elapsed_seconds = time.perf_counter() - start
        step.finished_at = _utc_now()
        return step, None


def _log_step_failures(
    storage: LocalStorage,
    *,
    phase: str,
    source_mode: str,
    command_context: Optional[str],
    step: ScheduledValidationStep,
) -> None:
    if step.status not in (STEP_FAILED, STEP_WARNING):
        return
    append_validation_failure(
        storage,
        phase=phase,
        step=step.name,
        source_mode=source_mode,
        command_context=command_context,
        error_message=step.errors[0] if step.errors else (step.warnings[0] if step.warnings else None),
        warnings=step.warnings,
        errors=step.errors,
    )


def _log_report_failures(
    storage: LocalStorage,
    report: ScheduledValidationReport,
) -> None:
    if report.success and not report.errors:
        return
    for error in report.errors[:5]:
        append_validation_failure(
            storage,
            phase="scheduled_validation",
            step=None,
            source_mode=report.source_mode,
            command_context=report.command_context,
            error_message=error,
            warnings=report.warnings[:5],
        )


def run_scheduled_validation(
    session: Session,
    storage: LocalStorage,
    *,
    count: int = DEFAULT_SCHEDULED_COUNT,
    min_zoom: int = DEFAULT_SCHEDULED_MIN_ZOOM,
    max_zoom: int = DEFAULT_SCHEDULED_MAX_ZOOM,
    real_requested: bool = False,
    persist: bool = True,
    command_context: Optional[str] = None,
    batch_fn: Optional[Callable[..., BatchValidationReport]] = None,
    queue_benchmark_fn: Optional[Callable[..., RenderQueueBenchmarkReport]] = None,
) -> ScheduledValidationReport:
    """Run catalog → batch validation → queue benchmark → queue status → summary."""
    start = time.perf_counter()
    mode = resolve_scheduled_source_mode(real_requested=real_requested)

    report = ScheduledValidationReport(
        source_mode=mode,
        requested_count=count,
        effective_count=count,
        min_zoom=min_zoom,
        max_zoom=max_zoom,
        real_requested=real_requested,
        production_rendering_enabled=settings.enable_production_radar_tiles,
        verified_mrms=False,
        prototype=True,
        command_context=command_context,
    )
    report.warnings.append(
        "Scheduled validation is local dev/prototype tooling — not verified MRMS production"
    )
    if not settings.enable_production_radar_tiles:
        report.warnings.append(
            "Production tile serving remains disabled (ENABLE_PRODUCTION_RADAR_TILES=false)"
        )
    if mode == MRMS_SOURCE_MODE_STUB:
        report.warnings.append(
            "Stub/offline mode (default): no network discovery unless --real is passed"
        )
    elif mode == MRMS_SOURCE_MODE_REAL:
        report.warnings.append(
            "Real mode: may download NOAA MRMS data; optional decoder required for full success"
        )

    batch_runner = batch_fn or run_mrms_batch_validation
    queue_runner = queue_benchmark_fn or run_render_queue_benchmark

    catalog_step, catalog = _run_step(
        "catalog_status",
        lambda: build_catalog_status(session),
        summarize=lambda result: {
            "total_frames": result.get("total_frames", 0),
            "mrms_discovered_frames": result.get("mrms_discovered_frames", 0),
        },
    )
    report.steps.append(catalog_step)
    if catalog is not None:
        report.catalog = catalog
    if catalog_step.errors:
        report.errors.extend(catalog_step.errors)
    _log_step_failures(
        storage,
        phase="scheduled_validation",
        source_mode=mode,
        command_context=command_context,
        step=catalog_step,
    )

    batch_step, batch_result = _run_step(
        "batch_validation",
        lambda: batch_runner(
            session,
            storage,
            frame_count=count,
            source_mode=mode,
            run_worker=False,
            persist=True,
        ),
        summarize=lambda result: {
            "discovered_count": result.discovered_count,
            "downloaded_count": result.downloaded_count,
            "decoded_count": result.decoded_count,
            "tiles_written": result.tiles_written,
            "frame_summaries": len(result.frame_summaries),
        },
    )
    report.steps.append(batch_step)
    if batch_result is not None:
        report.batch_validation = batch_result.to_dict()
        report.effective_count = batch_result.effective_frame_count
        if batch_result.warnings:
            batch_step.warnings.extend(batch_result.warnings[:5])
            report.warnings.extend(batch_result.warnings[:5])
        if batch_result.errors:
            batch_step.errors.extend(batch_result.errors[:5])
            report.errors.extend(batch_result.errors[:5])
        _finalize_step_status(batch_step)
    elif batch_step.status == STEP_FAILED:
        report.errors.extend(batch_step.errors)

    _log_step_failures(
        storage,
        phase="scheduled_validation",
        source_mode=mode,
        command_context=command_context,
        step=batch_step,
    )

    queue_step, queue_result = _run_step(
        "queue_benchmark",
        lambda: queue_runner(
            session,
            storage,
            count=count,
            min_zoom=min_zoom,
            max_zoom=max_zoom,
            force=False,
            dry_run=False,
            source_mode=mode,
            persist=True,
        ),
        summarize=lambda result: {
            "jobs_enqueued": result.jobs_enqueued,
            "jobs_processed": result.jobs_processed,
            "jobs_succeeded": result.jobs_succeeded,
            "jobs_failed": result.jobs_failed,
            "total_tiles_written": result.total_tiles_written,
        },
    )
    report.steps.append(queue_step)
    if queue_result is not None:
        report.queue_benchmark = queue_result.to_dict()
        if queue_result.warnings:
            queue_step.warnings.extend(queue_result.warnings[:5])
            report.warnings.extend(queue_result.warnings[:5])
        if queue_result.errors:
            queue_step.errors.extend(queue_result.errors[:5])
            report.errors.extend(queue_result.errors[:5])
        if queue_result.jobs_failed > 0:
            queue_step.errors.append(f"{queue_result.jobs_failed} queue job(s) failed")
            report.errors.append(f"{queue_result.jobs_failed} queue job(s) failed")
        _finalize_step_status(queue_step)
    elif queue_step.status == STEP_FAILED:
        report.errors.extend(queue_step.errors)

    _log_step_failures(
        storage,
        phase="scheduled_validation",
        source_mode=mode,
        command_context=command_context,
        step=queue_step,
    )

    queue_status_step, queue_summary = _run_step(
        "render_queue_status",
        lambda: get_queue_summary(session),
        summarize=lambda result: result.to_dict(),
    )
    report.steps.append(queue_status_step)
    if queue_summary is not None:
        report.render_queue = queue_summary.to_dict()
    if queue_status_step.errors:
        report.errors.extend(queue_status_step.errors)
    _log_step_failures(
        storage,
        phase="scheduled_validation",
        source_mode=mode,
        command_context=command_context,
        step=queue_status_step,
    )

    summary_step, summary = _run_step(
        "validation_summary",
        lambda: build_validation_summary(session, storage),
        summarize=lambda result: {
            "validation_available": result.get("validation_available", False),
            "queue_benchmark_available": result.get("queue_benchmark_available", False),
            "placeholder_default": result.get("placeholder_default", True),
        },
    )
    report.steps.append(summary_step)
    if summary is not None:
        report.validation_summary = summary
    if summary_step.errors:
        report.errors.extend(summary_step.errors)
    _log_step_failures(
        storage,
        phase="scheduled_validation",
        source_mode=mode,
        command_context=command_context,
        step=summary_step,
    )

    report.elapsed_seconds = time.perf_counter() - start
    report.ran_at = _utc_now()
    report.success = not report.errors and all(
        step.status in (STEP_SUCCEEDED, STEP_WARNING) for step in report.steps
    )
    report.exit_code = 0 if report.success else 1

    if not report.success:
        _log_report_failures(storage, report)

    if persist:
        save_scheduled_validation_report(storage, report.to_dict())
    return report


def run_real_mrms_smoke_test(
    session: Session,
    storage: LocalStorage,
    *,
    persist: bool = True,
    batch_fn: Optional[Callable[..., BatchValidationReport]] = None,
    queue_benchmark_fn: Optional[Callable[..., RenderQueueBenchmarkReport]] = None,
) -> ScheduledValidationReport:
    """Intentionally limited real-mode smoke test: count 1, zoom 0 only."""
    return run_scheduled_validation(
        session,
        storage,
        count=SMOKE_TEST_COUNT,
        min_zoom=SMOKE_TEST_MIN_ZOOM,
        max_zoom=SMOKE_TEST_MAX_ZOOM,
        real_requested=True,
        persist=persist,
        command_context="make real-mrms-smoke-test",
        batch_fn=batch_fn,
        queue_benchmark_fn=queue_benchmark_fn,
    )
