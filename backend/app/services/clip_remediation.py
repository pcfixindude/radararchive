"""Bounded warm/decode remediation plan from imported clip problem frames (prototype only)."""

from __future__ import annotations

from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.decoder_setup import SUGGESTED_DECODE_RETRY_COMMAND
from backend.app.services.frame_quality_report import (
    READINESS_COLD,
    READINESS_FAILED,
    READINESS_INVALID,
    READINESS_MISSING,
    READINESS_PARTIAL,
    READINESS_STUB,
)
from backend.app.services.mrms_bulk_ingest import DEFAULT_LIMIT, MAX_LIMIT
from backend.app.services.mrms_ingest_window import PRESET_REPLAY_RANGE, build_guided_make_command
from backend.app.services.playback_cache_status import SUGGESTED_WARM_COMMAND
from backend.app.services.selected_frame_decode import DOWNLOAD_MRMS_COMMAND

PROBLEM_READINESS = {
    READINESS_COLD,
    READINESS_MISSING,
    READINESS_FAILED,
    READINESS_STUB,
    READINESS_PARTIAL,
    READINESS_INVALID,
}

PLAN_STATUS_EMPTY = "empty"
PLAN_STATUS_READY = "ready"
PLAN_STATUS_INVALID = "invalid"

DEFAULT_REMEDIATION_LIMIT = DEFAULT_LIMIT

READINESS_LABELS: dict[str, str] = {
    READINESS_MISSING: "Missing raw MRMS",
    READINESS_COLD: "Cold cache",
    READINESS_FAILED: "Failed decode/warm",
    READINESS_STUB: "Stub/placeholder raw",
    READINESS_PARTIAL: "Partial (needs decode)",
    READINESS_INVALID: "Invalid/unassessed",
}

# Higher priority first when bounding problem frames for commands.
READINESS_PRIORITY: dict[str, int] = {
    READINESS_MISSING: 0,
    READINESS_FAILED: 1,
    READINESS_COLD: 2,
    READINESS_STUB: 3,
    READINESS_PARTIAL: 4,
    READINESS_INVALID: 5,
}

REPORT_JSON = "dev/clip_remediation_latest.json"


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_dev_only": True,
        "prototype": True,
        "production_tile_serving": settings.enable_production_radar_tiles,
        "status_only": True,
        "does_not_run_ingest": True,
        "does_not_run_decode": True,
        "does_not_run_real_downloads": True,
        "commands_not_auto_run": True,
    }


def _clamp_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_LIMIT))


def _normalize_readiness(value: str) -> str:
    if value in PROBLEM_READINESS:
        return value
    return value


def _group_problem_frames(problem_frames: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for frame in problem_frames:
        readiness = _normalize_readiness(str(frame.get("readiness_summary") or READINESS_INVALID))
        groups.setdefault(readiness, []).append(frame)
    return groups


def _select_bounded_frames(
    problem_frames: list[dict[str, Any]],
    *,
    limit: int,
) -> tuple[list[dict[str, Any]], bool]:
    if not problem_frames:
        return [], False
    sorted_frames = sorted(
        problem_frames,
        key=lambda frame: (
            READINESS_PRIORITY.get(
                _normalize_readiness(str(frame.get("readiness_summary") or READINESS_INVALID)),
                99,
            ),
            str(frame.get("timestamp") or ""),
        ),
    )
    truncated = len(sorted_frames) > limit
    return sorted_frames[:limit], truncated


def _warm_command(*, start: str, end: str, limit: int) -> str:
    return f'{SUGGESTED_WARM_COMMAND} ARGS="--start {start} --end {end} --limit {limit}"'


def _ingest_command(*, range_start: str, range_end: str, limit: int) -> str:
    return build_guided_make_command(
        preset=PRESET_REPLAY_RANGE,
        limit=limit,
        warm_cache=False,
        replay_start=range_start,
        replay_end=range_end,
    ) + " RUN=1 REAL=1"


def _frame_quality_command(timestamps: list[str]) -> str:
    joined = ",".join(timestamps)
    return f'make frame-quality ARGS="--timestamps {joined}"'


def _revalidate_command() -> str:
    return 'make clip-import ARGS="--file data/dev/playback_export_latest.json"'


def _build_command_steps(
    *,
    groups: dict[str, list[dict[str, Any]]],
    bounded_frames: list[dict[str, Any]],
    manifest: Optional[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    step_num = 1
    range_start = (manifest or {}).get("range_start")
    range_end = (manifest or {}).get("range_end")
    bounded_types = {
        _normalize_readiness(str(frame.get("readiness_summary") or READINESS_INVALID))
        for frame in bounded_frames
    }

    if READINESS_MISSING in bounded_types and range_start and range_end:
        command = _ingest_command(range_start=range_start, range_end=range_end, limit=limit)
        steps.append(
            {
                "step": step_num,
                "category": "ingest",
                "label": "Ingest missing frames for clip range",
                "command": command,
                "frame_count": len(groups.get(READINESS_MISSING, [])),
                "note": "Requires explicit REAL=1 — does not download automatically from UI.",
            }
        )
        step_num += 1

    if READINESS_STUB in bounded_types:
        steps.append(
            {
                "step": step_num,
                "category": "ingest",
                "label": "Replace stub raw with real local MRMS",
                "command": DOWNLOAD_MRMS_COMMAND,
                "frame_count": len(groups.get(READINESS_STUB, [])),
                "note": "Run only when you intend a bounded real MRMS download.",
            }
        )
        step_num += 1

    cold_frames = groups.get(READINESS_COLD, [])
    if READINESS_COLD in bounded_types and cold_frames:
        cold_timestamps = sorted(str(frame["timestamp"]) for frame in cold_frames if frame.get("timestamp"))
        warm_start = cold_timestamps[0] if cold_timestamps else range_start
        warm_end = cold_timestamps[-1] if cold_timestamps else range_end
        if warm_start and warm_end:
            steps.append(
                {
                    "step": step_num,
                    "category": "warm",
                    "label": "Warm cold frame cache for clip",
                    "command": _warm_command(start=warm_start, end=warm_end, limit=limit),
                    "frame_count": len(cold_frames),
                    "note": "Warms local decode cache — does not run from UI.",
                }
            )
            step_num += 1

    needs_decode = bounded_types & {
        READINESS_FAILED,
        READINESS_PARTIAL,
        READINESS_COLD,
        READINESS_STUB,
    }
    if needs_decode:
        decode_count = sum(len(groups.get(key, [])) for key in needs_decode)
        steps.append(
            {
                "step": step_num,
                "category": "decode",
                "label": "Retry decode for clip frames",
                "command": SUGGESTED_DECODE_RETRY_COMMAND,
                "frame_count": decode_count,
                "note": "Runs bounded local decode retry — not triggered from UI.",
            }
        )
        step_num += 1

    check_timestamps = sorted(
        {str(frame["timestamp"]) for frame in bounded_frames if frame.get("timestamp")}
    )
    if check_timestamps:
        steps.append(
            {
                "step": step_num,
                "category": "verify",
                "label": "Spot-check frame quality after remediation",
                "command": _frame_quality_command(check_timestamps[:limit]),
                "frame_count": len(check_timestamps),
                "note": "Status-only report — no ingest or decode work.",
            }
        )
        step_num += 1

    if manifest:
        steps.append(
            {
                "step": step_num,
                "category": "verify",
                "label": "Re-validate imported clip readiness",
                "command": _revalidate_command(),
                "frame_count": None,
                "note": "Re-run clip import after warm/decode steps.",
            }
        )

    return steps


def _build_command_block(steps: list[dict[str, Any]], *, clip_id: Optional[str]) -> str:
    lines = [
        "# Clip remediation plan (prototype — NOT verified MRMS)",
        "# Commands are NOT auto-run — copy and paste into your terminal manually.",
    ]
    if clip_id:
        lines.append(f"# Clip: {clip_id}")
    lines.append("")
    for item in steps:
        lines.append(f"# Step {item['step']}: {item['label']}")
        if item.get("note"):
            lines.append(f"# {item['note']}")
        lines.append(str(item["command"]))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_clip_remediation_plan(
    import_report: dict[str, Any],
    *,
    limit: int = DEFAULT_REMEDIATION_LIMIT,
) -> dict[str, Any]:
    """Build bounded warm/decode command plan from a clip import report — status only."""
    bounded_limit = _clamp_limit(limit)
    valid = bool(import_report.get("valid"))
    manifest = import_report.get("manifest")
    clip_id = (manifest or {}).get("clip_id") if isinstance(manifest, dict) else None
    problem_frames = list(import_report.get("problem_frames") or [])

    if not valid:
        return {
            "clip_id": clip_id,
            "valid": False,
            "plan_status": PLAN_STATUS_INVALID,
            "problem_groups": [],
            "group_summary": {
                "total_problem_count": 0,
                "assessed_count": 0,
                "cold_count": 0,
                "missing_count": 0,
                "failed_count": 0,
                "stub_count": 0,
                "partial_count": 0,
                "invalid_count": 0,
            },
            "commands": [],
            "command_block": "",
            "operator_note": "Import manifest is invalid — fix validation errors before remediation.",
            "bounded_frame_limit": bounded_limit,
            "truncated": False,
            "assessed_at": _utc_now(),
            **_safety_fields(),
        }

    if not problem_frames:
        return {
            "clip_id": clip_id,
            "valid": True,
            "plan_status": PLAN_STATUS_EMPTY,
            "problem_groups": [],
            "group_summary": {
                "total_problem_count": 0,
                "assessed_count": 0,
                "cold_count": 0,
                "missing_count": 0,
                "failed_count": 0,
                "stub_count": 0,
                "partial_count": 0,
                "invalid_count": 0,
            },
            "commands": [],
            "command_block": "",
            "operator_note": "All clip frames are ready — no remediation commands needed.",
            "bounded_frame_limit": bounded_limit,
            "truncated": False,
            "assessed_at": _utc_now(),
            **_safety_fields(),
        }

    groups = _group_problem_frames(problem_frames)
    bounded_frames, truncated = _select_bounded_frames(problem_frames, limit=bounded_limit)

    problem_groups: list[dict[str, Any]] = []
    for readiness in sorted(groups.keys(), key=lambda key: READINESS_PRIORITY.get(key, 99)):
        frames = groups[readiness]
        timestamps = sorted(str(frame["timestamp"]) for frame in frames if frame.get("timestamp"))
        bounded_in_group = [
            frame
            for frame in bounded_frames
            if _normalize_readiness(str(frame.get("readiness_summary") or "")) == readiness
        ]
        problem_groups.append(
            {
                "readiness_type": readiness,
                "label": READINESS_LABELS.get(readiness, readiness),
                "count": len(frames),
                "assessed_count": len(bounded_in_group),
                "truncated": len(frames) > len(bounded_in_group),
                "timestamps": timestamps[:bounded_limit],
            }
        )

    group_summary = {
        "total_problem_count": len(problem_frames),
        "assessed_count": len(bounded_frames),
        "cold_count": len(groups.get(READINESS_COLD, [])),
        "missing_count": len(groups.get(READINESS_MISSING, [])),
        "failed_count": len(groups.get(READINESS_FAILED, [])),
        "stub_count": len(groups.get(READINESS_STUB, [])),
        "partial_count": len(groups.get(READINESS_PARTIAL, [])),
        "invalid_count": len(groups.get(READINESS_INVALID, [])),
    }

    commands = _build_command_steps(
        groups=groups,
        bounded_frames=bounded_frames,
        manifest=manifest if isinstance(manifest, dict) else None,
        limit=bounded_limit,
    )
    command_block = _build_command_block(commands, clip_id=clip_id)

    return {
        "clip_id": clip_id,
        "valid": True,
        "plan_status": PLAN_STATUS_READY,
        "problem_groups": problem_groups,
        "group_summary": group_summary,
        "commands": commands,
        "command_block": command_block,
        "operator_note": (
            "Copy commands below and run manually in your terminal. "
            "No ingest, warm, decode, or MRMS download runs automatically from the UI."
        ),
        "bounded_frame_limit": bounded_limit,
        "truncated": truncated,
        "assessed_at": _utc_now(),
        **_safety_fields(),
    }


def is_clip_import_report(data: dict[str, Any]) -> bool:
    """True when JSON looks like a clip import report (not a raw manifest)."""
    return "import_status" in data or "problem_frames" in data or "readiness_summary" in data


def is_clip_manifest(data: dict[str, Any]) -> bool:
    return data.get("export_kind") == "playback_clip_manifest"
