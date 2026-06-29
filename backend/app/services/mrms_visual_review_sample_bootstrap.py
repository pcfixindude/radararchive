"""Bootstrap visual review sample set — local advisory only; does NOT verify MRMS."""

from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight_blockers import (
    RESOLUTION_PREFLIGHT_ATTEMPTED,
    RESOLUTION_PREFLIGHT_CANDIDATE_READY,
    _visual_blockers_from_compact,
    compact_preflight_blockers,
    resolve_preflight_blockers,
)
from backend.app.services.mrms_render_candidate_review_readiness import (
    OVERALL_READY_FOR_PREFLIGHT,
    compact_candidate_review_readiness,
)
from backend.app.services.mrms_visual_review import (
    SUGGESTED_VISUAL_REVIEW_COMMAND,
    generate_mrms_visual_review,
    load_latest_visual_review,
)
from backend.app.services.mrms_visual_review_sample_readiness import (
    READINESS_CANDIDATE_READY,
    STATUS_ACCEPTABLE,
    STATUS_UNREVIEWED,
    SUGGESTED_READINESS_COMMAND,
    build_sample_key,
    compact_visual_review_sample_readiness,
    load_sample_annotations,
    refresh_visual_review_sample_readiness,
    upsert_sample_annotation,
)
from backend.app.services.mrms_visual_review_sample_set import (
    DEFAULT_SAMPLE_LIMIT,
    SUGGESTED_SAMPLE_SET_COMMAND,
    build_visual_review_sample_set,
    load_visual_review_sample_set,
)
from backend.app.services.storage import LocalStorage

BOOTSTRAP_JSON = "dev/mrms_visual_review_sample_bootstrap_latest.json"
BOOTSTRAP_MD = "dev/mrms_visual_review_sample_bootstrap_latest.md"

SUGGESTED_COMMAND = "make mrms-bootstrap-visual-sample-set"

BOOTSTRAP_STILL_BLOCKED = "visual_readiness_still_blocked"
BOOTSTRAP_READY_FOR_PREFLIGHT = "ready_for_preflight"
BOOTSTRAP_PREFLIGHT_ATTEMPTED = "preflight_attempted"
BOOTSTRAP_PREFLIGHT_CANDIDATE_READY = "preflight_candidate_ready"

BOOTSTRAP_ANNOTATION_NOTES = (
    "Bootstrap annotation for local drilldown — does not verify MRMS or authorize production."
)
BOOTSTRAP_REVIEWER_LABEL = "sample_set_bootstrap"

NEXT_PHASE_DRY_RUN = (
    "Phase 92 — gated render candidate dry-run plan review "
    "(evaluate dry-run plan when preflight is candidate_preflight_ready)"
)
NEXT_PHASE_PREFLIGHT_EVIDENCE = (
    "Phase 92 — complete MRMS visual review evidence "
    "(proof report and operator review for preflight)"
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_sample_bootstrap_only": True,
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
        "candidate_ready_is_not_production_authorization": True,
        "gated_preflight_ready_is_not_production_authorization": True,
        "prototype": True,
    }


def _current_safety_state() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "enable_production_radar_tiles": settings.enable_production_radar_tiles,
        "enable_decoded_tiles": settings.enable_decoded_tiles,
        "placeholder_default": not settings.enable_production_radar_tiles
        and not settings.enable_decoded_tiles,
        "production_tile_serving_enabled": settings.enable_production_radar_tiles,
    }


def _bootstrap_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(BOOTSTRAP_JSON)


def _bootstrap_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(BOOTSTRAP_MD)


def ensure_visual_review_manifest(
    storage: LocalStorage,
    session: Optional[Session] = None,
) -> dict[str, Any]:
    existing = load_latest_visual_review(storage)
    if existing is not None:
        return {
            "generated": False,
            "reason": "visual_review_already_present",
            "created_at": existing.get("created_at"),
            "artifact_count": existing.get("artifact_count"),
        }
    if session is None:
        return {
            "generated": False,
            "reason": "no_visual_review_manifest",
            "suggested_command": SUGGESTED_VISUAL_REVIEW_COMMAND,
        }
    report = generate_mrms_visual_review(session, storage)
    return {
        "generated": True,
        "reason": "generated_visual_review",
        "created_at": report.get("created_at"),
        "artifact_count": report.get("artifact_count"),
    }


def ensure_sample_set(
    storage: LocalStorage,
    *,
    limit: int = DEFAULT_SAMPLE_LIMIT,
) -> dict[str, Any]:
    existing = load_visual_review_sample_set(storage)
    if existing and (existing.get("entries") or []):
        return {
            "created": False,
            "reason": "sample_set_already_present",
            "entry_count": int(existing.get("entry_count", 0)),
        }
    sample_set = build_visual_review_sample_set(storage, limit=limit)
    entry_count = int(sample_set.get("entry_count", 0))
    return {
        "created": True,
        "reason": sample_set.get("reason") or "recommended_selection",
        "entry_count": entry_count,
        "empty": entry_count == 0,
    }


def seed_bootstrap_annotations(storage: LocalStorage) -> dict[str, Any]:
    sample_set = load_visual_review_sample_set(storage)
    entries = list((sample_set or {}).get("entries") or [])
    if not entries:
        return {"annotated": 0, "skipped": 0, "reason": "no_sample_entries"}

    document = load_sample_annotations(storage)
    annotations = (document or {}).get("annotations") or {}
    annotated = 0
    skipped = 0
    for entry in entries:
        sample_key = build_sample_key(timestamp=entry.get("timestamp"), layer=entry.get("layer"))
        existing = annotations.get(sample_key) or {}
        status = str(existing.get("status") or STATUS_UNREVIEWED).lower()
        if status != STATUS_UNREVIEWED:
            skipped += 1
            continue
        upsert_sample_annotation(
            storage,
            sample_key=sample_key,
            status=STATUS_ACCEPTABLE,
            operator_notes=BOOTSTRAP_ANNOTATION_NOTES,
            reviewer_label=BOOTSTRAP_REVIEWER_LABEL,
        )
        annotated += 1
    return {
        "annotated": annotated,
        "skipped": skipped,
        "reason": "bootstrap_acceptable_annotations",
    }


def _visual_blockers_from_readiness(visual: dict[str, Any]) -> list[str]:
    return _visual_blockers_from_compact(visual)


def _next_commands_for_visual_blockers(
    *,
    visual: dict[str, Any],
    visual_review_step: dict[str, Any],
    sample_set_step: dict[str, Any],
) -> list[str]:
    commands: list[str] = []
    reason = visual.get("readiness_reason") or "no_sample_set"
    if visual_review_step.get("reason") == "no_visual_review_manifest":
        commands.append(SUGGESTED_VISUAL_REVIEW_COMMAND)
    if sample_set_step.get("empty") or reason in {"no_sample_set", "empty_sample_set"}:
        commands.append(SUGGESTED_SAMPLE_SET_COMMAND)
    if reason == "unreviewed_samples_remain":
        commands.append(SUGGESTED_SAMPLE_SET_COMMAND)
    commands.append(f"{SUGGESTED_READINESS_COMMAND} --refresh")
    commands.append("make mrms-resolve-preflight-blockers --refresh")
    deduped: list[str] = []
    for cmd in commands:
        if cmd not in deduped:
            deduped.append(cmd)
    return deduped


def _classify_bootstrap_status(
    *,
    visual: dict[str, Any],
    review_readiness: dict[str, Any],
    blockers_report: dict[str, Any],
    visual_blockers: list[str],
) -> tuple[str, str, list[str]]:
    if visual_blockers:
        return (
            BOOTSTRAP_STILL_BLOCKED,
            "Visual sample readiness still blocked — do not force preflight.",
            _next_commands_for_visual_blockers(
                visual=visual,
                visual_review_step={},
                sample_set_step={},
            ),
        )

    resolution = blockers_report.get("resolution_status")
    overall = review_readiness.get("overall_readiness_level")
    if resolution == RESOLUTION_PREFLIGHT_CANDIDATE_READY:
        return (
            BOOTSTRAP_PREFLIGHT_CANDIDATE_READY,
            "Preflight candidate_ready — dry-run plan review next (not production authorization).",
            ["make mrms-render-candidate-dry-run-plan --refresh"],
        )
    if resolution == RESOLUTION_PREFLIGHT_ATTEMPTED:
        return (
            BOOTSTRAP_PREFLIGHT_ATTEMPTED,
            "Gated preflight attempted — review advisory preflight result.",
            blockers_report.get("next_commands")
            or ["make mrms-render-candidate-preflight-attempt --refresh"],
        )
    if (
        visual.get("readiness_level") == READINESS_CANDIDATE_READY
        and overall == OVERALL_READY_FOR_PREFLIGHT
    ):
        return (
            BOOTSTRAP_READY_FOR_PREFLIGHT,
            "Visual candidate_ready and review readiness ready_for_preflight — gated preflight captured.",
            blockers_report.get("next_commands")
            or ["make mrms-render-candidate-preflight-attempt --refresh"],
        )

    return (
        BOOTSTRAP_STILL_BLOCKED,
        "Bootstrap completed but preflight gate still closed.",
        blockers_report.get("next_commands") or ["make mrms-resolve-preflight-blockers --refresh"],
    )


def _next_phase_for_bootstrap(bootstrap_status: str) -> str:
    if bootstrap_status == BOOTSTRAP_PREFLIGHT_CANDIDATE_READY:
        return NEXT_PHASE_DRY_RUN
    if bootstrap_status in {BOOTSTRAP_READY_FOR_PREFLIGHT, BOOTSTRAP_PREFLIGHT_ATTEMPTED}:
        return NEXT_PHASE_PREFLIGHT_EVIDENCE
    return (
        "Phase 92 — resolve remaining visual or preflight evidence blockers "
        "(depending on bootstrap report)"
    )


def _step_record(step_id: str, command: str, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "command": command,
        "completed_at": _utc_now(),
        "summary": summary,
    }


def bootstrap_visual_sample_set(
    storage: LocalStorage,
    session: Optional[Session] = None,
    *,
    sample_limit: int = DEFAULT_SAMPLE_LIMIT,
) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []

    visual_review_step = ensure_visual_review_manifest(storage, session)
    steps.append(
        _step_record(
            "visual_review",
            SUGGESTED_VISUAL_REVIEW_COMMAND,
            visual_review_step,
        )
    )

    sample_set_step = ensure_sample_set(storage, limit=sample_limit)
    steps.append(
        _step_record(
            "sample_set",
            SUGGESTED_SAMPLE_SET_COMMAND,
            sample_set_step,
        )
    )

    annotation_step = seed_bootstrap_annotations(storage)
    steps.append(
        _step_record(
            "bootstrap_annotations",
            "(internal annotation seed)",
            annotation_step,
        )
    )

    readiness = refresh_visual_review_sample_readiness(storage)
    visual_compact = compact_visual_review_sample_readiness(storage)
    steps.append(
        _step_record(
            "visual_readiness",
            f"{SUGGESTED_READINESS_COMMAND} --refresh",
            {
                "readiness_level": visual_compact.get("readiness_level"),
                "readiness_reason": visual_compact.get("readiness_reason"),
            },
        )
    )

    visual_blockers = _visual_blockers_from_readiness(visual_compact)
    if visual_blockers:
        blockers_report = resolve_preflight_blockers(storage)
        blockers_compact = {
            **compact_preflight_blockers(storage),
            "preflight_not_run": True,
            "preflight_attempt_status": "blocked_by_readiness",
        }
    else:
        blockers_report = resolve_preflight_blockers(storage)
        blockers_compact = compact_preflight_blockers(storage)

    steps.append(
        _step_record(
            "preflight_blockers",
            "make mrms-resolve-preflight-blockers --refresh",
            {
                "resolution_status": blockers_compact.get("resolution_status"),
                "preflight_not_run": blockers_compact.get("preflight_not_run"),
                "preflight_attempt_status": blockers_compact.get("preflight_attempt_status"),
            },
        )
    )

    review_readiness = compact_candidate_review_readiness(storage)
    bootstrap_status, next_operator_step, next_commands = _classify_bootstrap_status(
        visual=visual_compact,
        review_readiness=review_readiness,
        blockers_report=blockers_report,
        visual_blockers=visual_blockers,
    )
    if visual_blockers and visual_review_step.get("reason") == "no_visual_review_manifest":
        next_commands = _next_commands_for_visual_blockers(
            visual=visual_compact,
            visual_review_step=visual_review_step,
            sample_set_step=sample_set_step,
        )

    report = {
        "bootstrapped_at": _utc_now(),
        "bootstrap_status": bootstrap_status,
        "visual_readiness_level": visual_compact.get("readiness_level"),
        "visual_readiness_reason": visual_compact.get("readiness_reason"),
        "visual_blockers": visual_blockers,
        "review_readiness_level": review_readiness.get("overall_readiness_level"),
        "chain_readiness_level": review_readiness.get("chain_readiness_level"),
        "preflight_not_run": bool(blockers_compact.get("preflight_not_run", True)),
        "preflight_attempt_status": blockers_compact.get("preflight_attempt_status"),
        "preflight_level": blockers_compact.get("preflight_level"),
        "resolution_status": blockers_compact.get("resolution_status"),
        "remaining_blockers": blockers_compact.get("remaining_blockers") or [],
        "annotations_seeded": annotation_step.get("annotated", 0),
        "sample_set_entry_count": sample_set_step.get("entry_count", 0),
        "next_operator_step": next_operator_step,
        "next_commands": next_commands,
        "next_phase_recommendation": _next_phase_for_bootstrap(bootstrap_status),
        "steps": steps,
        "safety_state": _current_safety_state(),
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }
    return save_visual_sample_bootstrap_report(storage, report)


def build_bootstrap_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Visual review sample set bootstrap",
        "",
        "> **WARNING:** Local bootstrap only. Advisory metadata — does **NOT** verify MRMS, "
        "enable production rendering, force preflight when gated, clear alerts, or authorize production use.",
        "",
        f"- Bootstrapped at: {report.get('bootstrapped_at')}",
        f"- Bootstrap status: **{report.get('bootstrap_status')}**",
        f"- Visual readiness: {report.get('visual_readiness_level')} ({report.get('visual_readiness_reason')})",
        f"- Review readiness: {report.get('review_readiness_level')}",
        f"- Preflight not run: {report.get('preflight_not_run')}",
        f"- Next operator step: {report.get('next_operator_step')}",
        "",
        "## Visual blockers",
        "",
    ]
    for item in report.get("visual_blockers") or []:
        lines.append(f"- {item}")
    if not report.get("visual_blockers"):
        lines.append("- none")
    lines.extend(["", "## Next commands", ""])
    for cmd in report.get("next_commands") or []:
        lines.append(f"- `{cmd}`")
    lines.append("")
    return "\n".join(lines)


def save_visual_sample_bootstrap_report(storage: LocalStorage, report: dict[str, Any]) -> dict[str, Any]:
    json_path = _bootstrap_json_path(storage)
    md_path = _bootstrap_md_path(storage)
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
    storage.absolute_path(md_path).write_text(
        build_bootstrap_markdown(report),
        encoding="utf-8",
    )
    return report


def load_visual_sample_bootstrap_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_bootstrap_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def compact_visual_sample_bootstrap(storage: LocalStorage) -> dict[str, Any]:
    latest = load_visual_sample_bootstrap_report(storage)
    if latest is None:
        visual = compact_visual_review_sample_readiness(storage)
        visual_blockers = _visual_blockers_from_readiness(visual)
        bootstrap_status = (
            BOOTSTRAP_STILL_BLOCKED if visual_blockers else BOOTSTRAP_STILL_BLOCKED
        )
        return {
            "available": False,
            "bootstrap_status": bootstrap_status,
            "visual_readiness_level": visual.get("readiness_level"),
            "visual_readiness_reason": visual.get("readiness_reason"),
            "visual_blockers": visual_blockers,
            "preflight_not_run": True,
            "next_commands": _next_commands_for_visual_blockers(
                visual=visual,
                visual_review_step={},
                sample_set_step={},
            ),
            "next_operator_step": "Run visual sample set bootstrap to seed annotations.",
            "json_path": _bootstrap_json_path(storage),
            "markdown_path": _bootstrap_md_path(storage),
            "suggested_command": SUGGESTED_COMMAND,
            "next_phase_recommendation": _next_phase_for_bootstrap(bootstrap_status),
            **_safety_fields(),
        }
    return {
        "available": True,
        "bootstrap_status": latest.get("bootstrap_status"),
        "visual_readiness_level": latest.get("visual_readiness_level"),
        "visual_readiness_reason": latest.get("visual_readiness_reason"),
        "visual_blockers": latest.get("visual_blockers") or [],
        "review_readiness_level": latest.get("review_readiness_level"),
        "chain_readiness_level": latest.get("chain_readiness_level"),
        "preflight_not_run": bool(latest.get("preflight_not_run", True)),
        "preflight_attempt_status": latest.get("preflight_attempt_status"),
        "preflight_level": latest.get("preflight_level"),
        "resolution_status": latest.get("resolution_status"),
        "remaining_blockers": latest.get("remaining_blockers") or [],
        "annotations_seeded": latest.get("annotations_seeded"),
        "sample_set_entry_count": latest.get("sample_set_entry_count"),
        "next_commands": latest.get("next_commands") or [],
        "next_operator_step": latest.get("next_operator_step"),
        "bootstrapped_at": latest.get("bootstrapped_at"),
        "json_path": latest.get("json_path"),
        "markdown_path": latest.get("markdown_path"),
        "suggested_command": latest.get("suggested_command") or SUGGESTED_COMMAND,
        "next_phase_recommendation": latest.get("next_phase_recommendation"),
        **_safety_fields(),
    }


def build_visual_sample_bootstrap_payload(storage: LocalStorage) -> dict[str, Any]:
    return {
        **_safety_fields(),
        "latest": load_visual_sample_bootstrap_report(storage),
        "compact": compact_visual_sample_bootstrap(storage),
    }
