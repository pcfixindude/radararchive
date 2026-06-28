"""Local operator sign-off persistence (does NOT set verified_mrms=true)."""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from backend.app.config import settings
from backend.app.services.mrms_proof_report import load_mrms_proof_report
from backend.app.services.storage import LocalStorage

MRMS_SIGNOFFS_PATH = "dev/mrms_signoffs.json"
MAX_SIGNOFFS = 50


class SignoffValidationError(ValueError):
    """Raised when sign-off input fails validation."""


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _signoffs_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(MRMS_SIGNOFFS_PATH)


def load_signoffs(storage: LocalStorage) -> list[dict[str, Any]]:
    repo_path = _signoffs_repo_path(storage)
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


def _save_signoffs(storage: LocalStorage, entries: list[dict[str, Any]]) -> str:
    repo_path = _signoffs_repo_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    bounded = entries[:MAX_SIGNOFFS]
    storage.absolute_path(repo_path).write_text(
        json.dumps(bounded, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return repo_path


def validate_signoff_input(
    *,
    operator_name: Optional[str] = None,
    operator_initials: Optional[str] = None,
    operator_notes: Optional[str] = None,
    accepted_limitations: Optional[str] = None,
) -> None:
    identity = (operator_name or "").strip() or (operator_initials or "").strip()
    if not identity:
        raise SignoffValidationError("operator_name or operator_initials is required")

    notes = (operator_notes or "").strip()
    limitations = (accepted_limitations or "").strip()
    if not notes and not limitations:
        raise SignoffValidationError("operator_notes or accepted_limitations is required")


def create_signoff_record(
    storage: LocalStorage,
    *,
    operator_name: Optional[str] = None,
    operator_initials: Optional[str] = None,
    operator_notes: Optional[str] = None,
    accepted_limitations: Optional[str] = None,
    proof_report_timestamp: Optional[str] = None,
    frame_count_reviewed: Optional[int] = None,
) -> dict[str, Any]:
    """Create and persist a local operator sign-off record."""
    validate_signoff_input(
        operator_name=operator_name,
        operator_initials=operator_initials,
        operator_notes=operator_notes,
        accepted_limitations=accepted_limitations,
    )

    proof = load_mrms_proof_report(storage)
    proof_ts = proof_report_timestamp or (proof or {}).get("generated_at")
    frames = frame_count_reviewed
    if frames is None and proof:
        frames = proof.get("frame_count", 0)

    record = {
        "signoff_id": str(uuid.uuid4()),
        "created_at": _utc_now(),
        "operator_name": (operator_name or "").strip() or None,
        "operator_initials": (operator_initials or "").strip() or None,
        "proof_report_timestamp": proof_ts,
        "frame_count_reviewed": frames or 0,
        "operator_notes": (operator_notes or "").strip() or None,
        "accepted_limitations": (accepted_limitations or "").strip() or None,
        "verified_mrms": False,
        "does_not_set_verified_mrms": True,
        "does_not_enable_production": True,
        "production_enabled": settings.enable_production_radar_tiles,
        "no_automatic_promotion": True,
        "local_signoff_only": True,
        "prototype": True,
    }

    from backend.app.services.mrms_proof_regression import load_proof_regression_report

    regression = load_proof_regression_report(storage)
    regression_active = bool(regression and regression.get("regression_detected"))
    record["proof_regression_reviewed"] = regression_active
    record["proof_regression_still_active_after_signoff"] = regression_active

    entries = load_signoffs(storage)
    entries.insert(0, record)
    _save_signoffs(storage, entries)
    return record


def create_signoff_and_refresh_alert(
    storage: LocalStorage,
    *,
    operator_name: Optional[str] = None,
    operator_initials: Optional[str] = None,
    operator_notes: Optional[str] = None,
    accepted_limitations: Optional[str] = None,
    proof_report_timestamp: Optional[str] = None,
    frame_count_reviewed: Optional[int] = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create sign-off and refresh alert marker (regression stays active if present)."""
    from backend.app.services.validation_alerts import refresh_validation_alert, save_validation_alert

    record = create_signoff_record(
        storage,
        operator_name=operator_name,
        operator_initials=operator_initials,
        operator_notes=operator_notes,
        accepted_limitations=accepted_limitations,
        proof_report_timestamp=proof_report_timestamp,
        frame_count_reviewed=frame_count_reviewed,
    )

    alert = refresh_validation_alert(storage)
    regression_still_active = bool(record.get("proof_regression_still_active_after_signoff"))
    alert["latest_signoff_at"] = record.get("created_at")
    alert["latest_signoff_operator"] = record.get("operator_name") or record.get("operator_initials")
    alert["proof_regression_reviewed"] = bool(record.get("proof_regression_reviewed"))
    alert["proof_regression_still_active"] = regression_still_active
    if regression_still_active:
        alert["suggested_next_action"] = (
            "Operator sign-off recorded (local only — not verified MRMS). "
            "Proof regression remains active until evidence improves; see make mrms-proof-regression."
        )
    save_validation_alert(storage, alert)
    return record, alert


def _proof_regression_still_active(storage: LocalStorage) -> bool:
    from backend.app.services.mrms_proof_regression import load_proof_regression_report

    regression = load_proof_regression_report(storage)
    return bool(regression and regression.get("regression_detected"))


def compact_signoff_summary(storage: LocalStorage) -> dict[str, Any]:
    from backend.app.services.mrms_proof_history import compact_signoff_item

    entries = load_signoffs(storage)
    latest = entries[0] if entries else None
    regression_still_active = _proof_regression_still_active(storage)
    return {
        "signoff_count": len(entries),
        "latest_signoff_at": latest.get("created_at") if latest else None,
        "latest_operator": (
            latest.get("operator_name") or latest.get("operator_initials") if latest else None
        ),
        "proof_regression_still_active": regression_still_active,
        "proof_regression_reviewed": bool(latest and latest.get("proof_regression_reviewed")),
        "verified_mrms": False,
        "local_signoff_only": True,
        "does_not_set_verified_mrms": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def list_compact_signoffs(storage: LocalStorage, *, limit: int = MAX_SIGNOFFS) -> list[dict[str, Any]]:
    from backend.app.services.mrms_proof_history import compact_signoff_item

    bounded = max(1, min(limit, MAX_SIGNOFFS))
    return [compact_signoff_item(item) for item in load_signoffs(storage)[:bounded]]
