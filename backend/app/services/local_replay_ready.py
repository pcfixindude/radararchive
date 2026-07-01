"""One-shot local replay setup status and bounded post-ingest actions (prototype only)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.decode_retry import load_decode_retry_report, run_decode_retry
from backend.app.services.frame_cache_warmer import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    load_bulk_ingest_report,
    run_cache_warm,
    select_cache_window,
)
from backend.app.services.mrms_ingest_window import SUGGESTED_GUIDED_COMMAND
from backend.app.services.playback_cache_status import build_playback_cache_status
from backend.app.services.storage import LocalStorage

STATUS_OK = "ok"
STATUS_WARN = "warning"
STATUS_MISSING = "missing"
STATUS_ERROR = "error"

STEP_LOCAL_FRAMES = "local_frames"
STEP_FRAME_CACHE = "frame_cache"
STEP_DECODED_ARTIFACTS = "decoded_artifacts"
STEP_UI = "open_ui"

WARM_COMMAND = "make mrms-warm-frame-cache"
DECODE_COMMAND = "make decode-retry"
UI_COMMAND = "make backend && make frontend"
INGEST_COMMAND = f"{SUGGESTED_GUIDED_COMMAND} RUN=1 REAL=1"
LOCAL_REPLAY_READY_RUN_COMMAND = "make local-replay-ready RUN=1"

DECODE_OK_STATUSES = {"preview_ok", "pipeline_partial"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_dev_only": True,
        "prototype": True,
        "does_not_run_real_ingest": True,
        "production_tile_serving": settings.enable_production_radar_tiles,
    }


def _checklist_item(
    *,
    step_id: str,
    label: str,
    status: str,
    message: str,
    next_command: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    return {
        "id": step_id,
        "label": label,
        "status": status,
        "message": message,
        "next_command": next_command,
        "details": details or {},
    }


def _decode_artifacts_ok(decode_report: Optional[dict[str, Any]], warmed_count: int) -> bool:
    if warmed_count > 0:
        return True
    if not decode_report:
        return False
    status = decode_report.get("decode_retry_status")
    if status in DECODE_OK_STATUSES:
        return True
    if decode_report.get("produced_decoded_preview"):
        return True
    return False


def build_local_replay_ready_plan(
    session: Session,
    storage: LocalStorage,
    *,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Assess post-ingest readiness without running warm/decode or ingest."""
    bounded_limit = max(1, min(limit, MAX_LIMIT))
    timestamps, window_source = select_cache_window(session, storage, limit=bounded_limit)
    ingest_report = load_bulk_ingest_report(storage)
    decode_report = load_decode_retry_report(storage)

    checklist: list[dict[str, Any]] = []

    if not timestamps:
        checklist.append(
            _checklist_item(
                step_id=STEP_LOCAL_FRAMES,
                label="Local MRMS frames",
                status=STATUS_MISSING,
                message="No real local MRMS frames found in catalog or ingest report.",
                next_command=INGEST_COMMAND,
                details={"frame_count": 0, "window_source": window_source},
            )
        )
        cache_status = None
        warmed_count = 0
        decode_ok = False
    else:
        checklist.append(
            _checklist_item(
                step_id=STEP_LOCAL_FRAMES,
                label="Local MRMS frames",
                status=STATUS_OK,
                message=f"Found {len(timestamps)} local frame(s) for replay setup.",
                details={
                    "frame_count": len(timestamps),
                    "window_source": window_source,
                    "sample_timestamps": timestamps[:3],
                },
            )
        )
        cache_status = build_playback_cache_status(session, storage, timestamps)
        warmed_count = int(cache_status.get("warmed_count") or 0)
        decode_ok = _decode_artifacts_ok(decode_report, warmed_count)

        if cache_status.get("playback_ready"):
            checklist.append(
                _checklist_item(
                    step_id=STEP_FRAME_CACHE,
                    label="Frame cache warm",
                    status=STATUS_OK,
                    message=f"Playback cache ready ({warmed_count} warmed frame(s)).",
                    details={
                        "warmed_count": warmed_count,
                        "cold_count": cache_status.get("cold_count"),
                        "failed_count": cache_status.get("failed_count"),
                        "cache_warm_status": cache_status.get("cache_warm_status"),
                    },
                )
            )
        elif warmed_count > 0:
            checklist.append(
                _checklist_item(
                    step_id=STEP_FRAME_CACHE,
                    label="Frame cache warm",
                    status=STATUS_WARN,
                    message="Some frames are cached, but playback cache is not fully ready.",
                    next_command=WARM_COMMAND,
                    details={
                        "warmed_count": warmed_count,
                        "cold_count": cache_status.get("cold_count"),
                        "failed_count": cache_status.get("failed_count"),
                    },
                )
            )
        else:
            checklist.append(
                _checklist_item(
                    step_id=STEP_FRAME_CACHE,
                    label="Frame cache warm",
                    status=STATUS_MISSING,
                    message="Frame cache is cold or missing — warming speeds up replay.",
                    next_command=LOCAL_REPLAY_READY_RUN_COMMAND,
                    details={
                        "warmed_count": 0,
                        "cold_count": cache_status.get("cold_count"),
                        "missing_count": cache_status.get("missing_count"),
                    },
                )
            )

        if decode_ok:
            quality_status = None
            if decode_report:
                pipeline = decode_report.get("pipeline") or {}
                quality_status = pipeline.get("frame_quality_status") or decode_report.get("frame_quality_status")
            checklist.append(
                _checklist_item(
                    step_id=STEP_DECODED_ARTIFACTS,
                    label="Decoded artifacts",
                    status=STATUS_OK,
                    message="Decoded preview/cache artifacts are available for local replay.",
                    details={
                        "decode_retry_status": decode_report.get("decode_retry_status") if decode_report else None,
                        "warmed_count": warmed_count,
                        "frame_quality_status": quality_status,
                    },
                )
            )
        else:
            checklist.append(
                _checklist_item(
                    step_id=STEP_DECODED_ARTIFACTS,
                    label="Decoded artifacts",
                    status=STATUS_MISSING,
                    message="Decoded artifacts missing or stale — run bounded local decode.",
                    next_command=DECODE_COMMAND,
                    details={
                        "decode_retry_status": decode_report.get("decode_retry_status") if decode_report else None,
                        "warmed_count": warmed_count,
                    },
                )
            )

    core_ready = bool(timestamps) and (
        cache_status is not None and cache_status.get("playback_ready") and decode_ok
    )
    ui_status = STATUS_OK if core_ready else STATUS_WARN
    checklist.append(
        _checklist_item(
            step_id=STEP_UI,
            label="Open replay UI",
            status=ui_status,
            message=(
                "Start backend and frontend, then use range/loop controls."
                if core_ready
                else "Complete setup steps above before opening the UI."
            ),
            next_command=UI_COMMAND if core_ready else None,
        )
    )

    next_command = _resolve_next_command(checklist, core_ready)
    operator_steps = [
        "Use Load frames or a bookmark ingest command.",
        f"Run explicit real ingest if needed: {INGEST_COMMAND}",
        "Run make local-replay-ready to check post-ingest status.",
        "If needed, rerun with RUN=1 to warm/decode local files only.",
        "Open the UI and replay with range/loop.",
    ]

    return {
        "ran_at": _utc_now(),
        "ready": core_ready,
        "ready_label": "Ready to replay" if core_ready else "Setup needed",
        "dry_run": True,
        "frame_count": len(timestamps),
        "window_source": window_source,
        "ingest_report_available": ingest_report is not None,
        "cache_status": cache_status,
        "decode_retry_status": decode_report.get("decode_retry_status") if decode_report else None,
        "checklist": checklist,
        "next_command": next_command,
        "next_commands": _collect_next_commands(checklist),
        "operator_steps": operator_steps,
        "suggested_run_command": LOCAL_REPLAY_READY_RUN_COMMAND,
        **_safety_fields(),
    }


def _resolve_next_command(checklist: list[dict[str, Any]], core_ready: bool) -> Optional[str]:
    if core_ready:
        return UI_COMMAND
    for item in checklist:
        if item["status"] in {STATUS_MISSING, STATUS_ERROR, STATUS_WARN} and item.get("next_command"):
            return item["next_command"]
    return LOCAL_REPLAY_READY_RUN_COMMAND


def _collect_next_commands(checklist: list[dict[str, Any]]) -> list[str]:
    commands: list[str] = []
    for item in checklist:
        cmd = item.get("next_command")
        if cmd and cmd not in commands:
            commands.append(cmd)
    return commands


def _needs_warm(plan: dict[str, Any]) -> bool:
    for item in plan.get("checklist") or []:
        if item.get("id") == STEP_FRAME_CACHE and item.get("status") != STATUS_OK:
            return True
    return False


def _needs_decode(plan: dict[str, Any]) -> bool:
    for item in plan.get("checklist") or []:
        if item.get("id") == STEP_DECODED_ARTIFACTS and item.get("status") != STATUS_OK:
            return True
    return False


def run_local_replay_ready(
    session: Session,
    storage: LocalStorage,
    *,
    limit: int = DEFAULT_LIMIT,
    run: bool = False,
) -> dict[str, Any]:
    """Check readiness; optionally run bounded local warm/decode only (never real ingest)."""
    plan = build_local_replay_ready_plan(session, storage, limit=limit)
    if not run:
        return plan

    if not plan.get("frame_count"):
        plan["run_mode"] = "blocked_no_frames"
        plan["run_message"] = "Cannot warm/decode without local frames — run explicit ingest first."
        plan["next_command"] = INGEST_COMMAND
        return plan

    actions: list[dict[str, Any]] = []
    warm_report = None
    decode_report = None

    if _needs_warm(plan):
        warm_report = run_cache_warm(session, storage, limit=limit, real_only=True)
        actions.append(
            {
                "action": "warm_cache",
                "status": warm_report.get("warm_status"),
                "frames_decoded": warm_report.get("frames_decoded"),
                "frames_matched": warm_report.get("frames_matched"),
            }
        )

    plan = build_local_replay_ready_plan(session, storage, limit=limit)

    if _needs_decode(plan):
        decode_report = run_decode_retry(session, storage)
        actions.append(
            {
                "action": "decode_retry",
                "status": decode_report.get("decode_retry_status"),
                "produced_decoded_preview": decode_report.get("produced_decoded_preview"),
            }
        )
        plan = build_local_replay_ready_plan(session, storage, limit=limit)

    plan["dry_run"] = False
    plan["run_mode"] = "local_warm_decode_only"
    plan["actions_run"] = actions
    plan["warm_report_status"] = warm_report.get("warm_status") if warm_report else None
    plan["decode_retry_status"] = (
        decode_report.get("decode_retry_status") if decode_report else plan.get("decode_retry_status")
    )
    if not plan.get("ready"):
        plan["run_message"] = "Local warm/decode finished — review checklist for remaining steps."
    else:
        plan["run_message"] = "Local replay setup complete — open the UI to replay."
    return plan
