"""Gated MRMS render candidate preflight attempt — does NOT verify MRMS or enable production."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_render_candidate_preflight import (
    PREFLIGHT_BLOCKED,
    PREFLIGHT_CANDIDATE_READY,
    PREFLIGHT_NEEDS_REVIEW,
    SUGGESTED_PREFLIGHT_COMMAND,
    compact_render_candidate_preflight,
    generate_render_candidate_preflight,
)
from backend.app.services.mrms_render_candidate_review_readiness import (
    OVERALL_BLOCKED,
    OVERALL_NEEDS_REVIEW,
    OVERALL_PREFLIGHT_CANDIDATE_READY,
    OVERALL_READY_FOR_PREFLIGHT,
    SUGGESTED_COMMAND as SUGGESTED_READINESS_COMMAND,
    evaluate_candidate_review_readiness,
    gather_review_chain_evidence,
    generate_candidate_review_readiness,
)
from backend.app.services.storage import LocalStorage

ATTEMPT_JSON = "dev/mrms_render_candidate_preflight_attempt_latest.json"

SUGGESTED_COMMAND = "make mrms-render-candidate-preflight-attempt"

ATTEMPT_BLOCKED_BY_READINESS = "blocked_by_readiness"
ATTEMPT_RAN_BLOCKED = "ran_blocked"
ATTEMPT_RAN_NEEDS_REVIEW = "ran_needs_review"
ATTEMPT_RAN_CANDIDATE_READY = "ran_candidate_ready"

GATE_ALLOWED_LEVELS = frozenset(
    {OVERALL_READY_FOR_PREFLIGHT, OVERALL_PREFLIGHT_CANDIDATE_READY}
)

NEXT_PHASE_BLOCKERS = (
    "Phase 91 — bootstrap visual review sample set "
    "(trend-hint chain bootstrap available via make mrms-bootstrap-trend-hint-chain)"
)
NEXT_PHASE_SUCCESS = (
    "Phase 92 — gated render candidate dry-run plan review "
    "(evaluate dry-run plan when preflight is candidate_preflight_ready)"
)


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_preflight_attempt_only": True,
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
        "gated_preflight_ready_is_not_production_authorization": True,
        "prototype": True,
    }


def _attempt_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(ATTEMPT_JSON)


def _readiness_allows_preflight(readiness: dict[str, Any]) -> bool:
    overall = readiness.get("overall_readiness_level")
    return overall in GATE_ALLOWED_LEVELS and bool(readiness.get("review_chain_ready"))


def _attempt_status_from_preflight(preflight_level: Optional[str]) -> str:
    if preflight_level == PREFLIGHT_CANDIDATE_READY:
        return ATTEMPT_RAN_CANDIDATE_READY
    if preflight_level == PREFLIGHT_NEEDS_REVIEW:
        return ATTEMPT_RAN_NEEDS_REVIEW
    return ATTEMPT_RAN_BLOCKED


def _next_phase_for_attempt(attempt: dict[str, Any]) -> str:
    if attempt.get("attempt_status") == ATTEMPT_BLOCKED_BY_READINESS:
        return NEXT_PHASE_BLOCKERS
    if attempt.get("preflight_level") == PREFLIGHT_CANDIDATE_READY:
        return NEXT_PHASE_SUCCESS
    return NEXT_PHASE_BLOCKERS


def _next_operator_step_for_attempt(attempt: dict[str, Any]) -> str:
    status = attempt.get("attempt_status")
    if status == ATTEMPT_BLOCKED_BY_READINESS:
        return attempt.get("gate_reason") or "Resolve review readiness blockers before gated preflight"
    if status == ATTEMPT_RAN_CANDIDATE_READY:
        return "Preflight candidate_preflight_ready — consider dry-run plan (still not production authorization)"
    if status == ATTEMPT_RAN_NEEDS_REVIEW:
        return "Preflight needs review — resolve warnings before dry-run plan"
    return "Preflight blocked — resolve visual evidence blockers and retry gated preflight"


def attempt_gated_preflight(storage: LocalStorage) -> dict[str, Any]:
    readiness = evaluate_candidate_review_readiness(gather_review_chain_evidence(storage))
    base = {
        "attempted_at": _utc_now(),
        "readiness_level": readiness.get("overall_readiness_level"),
        "chain_readiness_level": readiness.get("chain_readiness_level"),
        "review_chain_ready": readiness.get("review_chain_ready"),
        "preflight_not_run": True,
        "preflight_level": None,
        "preflight_reason": None,
        "preflight_json_path": None,
        "preflight_markdown_path": None,
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }

    if not _readiness_allows_preflight(readiness):
        attempt = {
            **base,
            "attempt_status": ATTEMPT_BLOCKED_BY_READINESS,
            "gate_reason": (
                "review readiness is not ready_for_preflight "
                f"(overall={readiness.get('overall_readiness_level')}, "
                f"chain={readiness.get('chain_readiness_level')})"
            ),
            "blocking_items": readiness.get("blocking_items") or [],
            "warnings": readiness.get("warnings") or [],
            "suggested_commands": readiness.get("suggested_commands") or [
                f"{SUGGESTED_READINESS_COMMAND} --refresh",
                "make mrms-render-candidate-trend-hint-review-digest --refresh",
            ],
            "next_operator_step": readiness.get("next_operator_step"),
            "next_phase_recommendation": NEXT_PHASE_BLOCKERS,
        }
        return save_preflight_attempt(storage, attempt)

    preflight = generate_render_candidate_preflight(storage)
    generate_candidate_review_readiness(storage)
    attempt_status = _attempt_status_from_preflight(preflight.get("preflight_level"))
    attempt = {
        **base,
        "attempt_status": attempt_status,
        "preflight_not_run": False,
        "gate_reason": None,
        "preflight_level": preflight.get("preflight_level"),
        "preflight_reason": preflight.get("preflight_reason"),
        "preflight_json_path": preflight.get("json_path"),
        "preflight_markdown_path": preflight.get("markdown_path"),
        "blocking_items": preflight.get("blocking_items") or [],
        "warnings": preflight.get("warnings") or [],
        "suggested_commands": (
            ["make mrms-render-candidate-dry-run-plan --refresh"]
            if preflight.get("preflight_level") == PREFLIGHT_CANDIDATE_READY
            else [f"{SUGGESTED_PREFLIGHT_COMMAND} --refresh"]
        ),
        "next_operator_step": None,
        "next_phase_recommendation": None,
    }
    attempt["next_operator_step"] = _next_operator_step_for_attempt(attempt)
    attempt["next_phase_recommendation"] = _next_phase_for_attempt(attempt)
    return save_preflight_attempt(storage, attempt)


def save_preflight_attempt(storage: LocalStorage, attempt: dict[str, Any]) -> dict[str, Any]:
    path = _attempt_json_path(storage)
    storage.ensure_directories(path.rsplit("/", 1)[0])
    record = {
        **attempt,
        "json_path": path,
        "suggested_command": SUGGESTED_COMMAND,
        **_safety_fields(),
    }
    storage.absolute_path(path).write_text(
        json.dumps(record, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return record


def load_preflight_attempt(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_attempt_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def compact_preflight_attempt(storage: LocalStorage) -> dict[str, Any]:
    latest = load_preflight_attempt(storage)
    readiness = evaluate_candidate_review_readiness(gather_review_chain_evidence(storage))
    preflight = compact_render_candidate_preflight(storage)
    if latest is None:
        return {
            "available": False,
            "attempt_status": None,
            "readiness_level": readiness.get("overall_readiness_level"),
            "review_chain_ready": readiness.get("review_chain_ready"),
            "gate_open": _readiness_allows_preflight(readiness),
            "preflight_level": preflight.get("preflight_level"),
            "preflight_not_run": True,
            "blocking_items": readiness.get("blocking_items") or [],
            "warnings": readiness.get("warnings") or [],
            "suggested_commands": readiness.get("suggested_commands") or [],
            "next_operator_step": readiness.get("next_operator_step"),
            "suggested_command": SUGGESTED_COMMAND,
            "next_phase_recommendation": (
                NEXT_PHASE_SUCCESS
                if preflight.get("preflight_level") == PREFLIGHT_CANDIDATE_READY
                else NEXT_PHASE_BLOCKERS
            ),
            **_safety_fields(),
        }
    return {
        "available": True,
        "attempt_status": latest.get("attempt_status"),
        "attempted_at": latest.get("attempted_at"),
        "readiness_level": latest.get("readiness_level"),
        "review_chain_ready": latest.get("review_chain_ready"),
        "gate_open": _readiness_allows_preflight(readiness),
        "preflight_not_run": bool(latest.get("preflight_not_run")),
        "preflight_level": latest.get("preflight_level") or preflight.get("preflight_level"),
        "preflight_reason": latest.get("preflight_reason") or preflight.get("preflight_reason"),
        "blocking_items": latest.get("blocking_items") or [],
        "warnings": latest.get("warnings") or [],
        "suggested_commands": latest.get("suggested_commands") or [],
        "next_operator_step": latest.get("next_operator_step")
        or _next_operator_step_for_attempt(latest),
        "gate_reason": latest.get("gate_reason"),
        "json_path": latest.get("json_path"),
        "preflight_json_path": latest.get("preflight_json_path"),
        "preflight_markdown_path": latest.get("preflight_markdown_path"),
        "suggested_command": SUGGESTED_COMMAND,
        "next_phase_recommendation": latest.get("next_phase_recommendation")
        or _next_phase_for_attempt(latest),
        **_safety_fields(),
    }


def build_preflight_attempt_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_preflight_attempt(storage)
    return {
        **_safety_fields(),
        "latest": latest or {},
        "compact": compact_preflight_attempt(storage),
    }
