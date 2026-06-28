"""Detect MRMS proof report regressions by comparing latest vs previous evidence."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.services.mrms_proof_report import (
    MRMS_PROOF_PREVIOUS_PATH,
    load_mrms_proof_history,
    load_mrms_proof_report,
)
from backend.app.services.storage import LocalStorage

MRMS_PROOF_PREVIOUS_PATH = "dev/mrms_proof_previous.json"
MRMS_PROOF_REGRESSION_LATEST_PATH = "dev/mrms_proof_regression_latest.json"
MRMS_PROOF_REGRESSION_HISTORY_PATH = "dev/mrms_proof_regression_history.json"
MAX_REGRESSION_HISTORY = 10

REGRESSION_NONE = "none"
REGRESSION_DETECTED = "detected"
REGRESSION_IMPROVED = "improved"
REGRESSION_INCONCLUSIVE = "inconclusive"

OVERALL_STATUS_RANK = {
    "ready_for_operator_review": 4,
    "insufficient_evidence": 3,
    "not_started": 2,
    "failed": 1,
}


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def overall_status_rank(status: Optional[str]) -> int:
    return OVERALL_STATUS_RANK.get(str(status or ""), 0)


def _criteria_counts(report: Optional[dict[str, Any]]) -> dict[str, int]:
    if not report:
        return {}
    counts = report.get("criteria_counts") or {}
    return {
        "passed": int(counts.get("passed", 0)),
        "failed": int(counts.get("failed", 0)),
        "warning": int(counts.get("warning", 0)),
        "skipped": int(counts.get("skipped", 0)),
        "unknown": int(counts.get("unknown", 0)),
    }


def _frame_evidence_summary(report: Optional[dict[str, Any]]) -> dict[str, Any]:
    if not report:
        return {
            "frame_count": 0,
            "decode_artifact_frames": 0,
            "tile_evidence_frames": 0,
            "geo_sanity_ok_frames": 0,
            "decoder_used_frames": 0,
        }
    frames = report.get("frames") or []
    decode_count = 0
    tile_count = 0
    geo_ok = 0
    decoder_count = 0
    for frame in frames:
        evidence = frame.get("evidence") or {}
        if evidence.get("decode_artifact_path"):
            decode_count += 1
        if evidence.get("decoder_used"):
            decoder_count += 1
        tiles_written = int(evidence.get("tiles_written") or 0)
        geo_sanity = evidence.get("geo_sanity") or {}
        tile_ok = bool(geo_sanity.get("tile_output_nonempty")) or tiles_written > 0
        if tile_ok:
            tile_count += 1
        if geo_sanity.get("bounds_valid") and geo_sanity.get("grid_positive"):
            geo_ok += 1
    return {
        "frame_count": len(frames),
        "decode_artifact_frames": decode_count,
        "tile_evidence_frames": tile_count,
        "geo_sanity_ok_frames": geo_ok,
        "decoder_used_frames": decoder_count,
    }


def load_previous_proof_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    repo_path = storage.normalize_path(MRMS_PROOF_PREVIOUS_PATH)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        history = load_mrms_proof_history(storage)
        if len(history) >= 2:
            return history[1]
        return None
    try:
        return json.loads(abs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def detect_proof_regressions(
    current: Optional[dict[str, Any]],
    previous: Optional[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return list of regression findings comparing current vs previous proof reports."""
    if current is None:
        return []
    if previous is None:
        return []

    findings: list[dict[str, Any]] = []
    cur_status = current.get("overall_status")
    prev_status = previous.get("overall_status")
    if overall_status_rank(cur_status) < overall_status_rank(prev_status):
        findings.append(
            {
                "kind": "overall_status_worsened",
                "message": f"Overall proof status worsened: {prev_status} -> {cur_status}",
                "previous": prev_status,
                "current": cur_status,
            }
        )

    cur_counts = _criteria_counts(current)
    prev_counts = _criteria_counts(previous)
    if cur_counts.get("passed", 0) < prev_counts.get("passed", 0):
        findings.append(
            {
                "kind": "passed_criteria_decreased",
                "message": (
                    f"Passed criteria decreased: {prev_counts.get('passed')} -> {cur_counts.get('passed')}"
                ),
                "previous": prev_counts.get("passed"),
                "current": cur_counts.get("passed"),
            }
        )
    if cur_counts.get("failed", 0) > prev_counts.get("failed", 0):
        findings.append(
            {
                "kind": "failed_criteria_increased",
                "message": (
                    f"Failed criteria increased: {prev_counts.get('failed')} -> {cur_counts.get('failed')}"
                ),
                "previous": prev_counts.get("failed"),
                "current": cur_counts.get("failed"),
            }
        )
    if cur_counts.get("warning", 0) > prev_counts.get("warning", 0):
        findings.append(
            {
                "kind": "warning_criteria_increased",
                "message": (
                    f"Warning criteria increased: {prev_counts.get('warning')} -> {cur_counts.get('warning')}"
                ),
                "previous": prev_counts.get("warning"),
                "current": cur_counts.get("warning"),
            }
        )

    cur_frames = int(current.get("frame_count") or 0)
    prev_frames = int(previous.get("frame_count") or 0)
    cur_requested = int(current.get("requested_frame_count") or cur_frames)
    prev_requested = int(previous.get("requested_frame_count") or prev_frames)
    if cur_frames < prev_frames and cur_requested >= prev_requested:
        findings.append(
            {
                "kind": "frame_count_decreased",
                "message": f"Frame count decreased unexpectedly: {prev_frames} -> {cur_frames}",
                "previous": prev_frames,
                "current": cur_frames,
            }
        )

    cur_ev = _frame_evidence_summary(current)
    prev_ev = _frame_evidence_summary(previous)
    if prev_ev["tile_evidence_frames"] > 0 and cur_ev["tile_evidence_frames"] < prev_ev["tile_evidence_frames"]:
        findings.append(
            {
                "kind": "tile_evidence_disappeared",
                "message": (
                    f"Tile evidence frames decreased: {prev_ev['tile_evidence_frames']} -> "
                    f"{cur_ev['tile_evidence_frames']}"
                ),
                "previous": prev_ev["tile_evidence_frames"],
                "current": cur_ev["tile_evidence_frames"],
            }
        )
    if prev_ev["geo_sanity_ok_frames"] > 0 and cur_ev["geo_sanity_ok_frames"] < prev_ev["geo_sanity_ok_frames"]:
        findings.append(
            {
                "kind": "geo_sanity_worsened",
                "message": (
                    f"Geo sanity ok frames decreased: {prev_ev['geo_sanity_ok_frames']} -> "
                    f"{cur_ev['geo_sanity_ok_frames']}"
                ),
                "previous": prev_ev["geo_sanity_ok_frames"],
                "current": cur_ev["geo_sanity_ok_frames"],
            }
        )
    if prev_ev["decoder_used_frames"] > 0 and cur_ev["decoder_used_frames"] < prev_ev["decoder_used_frames"]:
        findings.append(
            {
                "kind": "decoder_evidence_disappeared",
                "message": (
                    f"Decoder evidence frames decreased: {prev_ev['decoder_used_frames']} -> "
                    f"{cur_ev['decoder_used_frames']}"
                ),
                "previous": prev_ev["decoder_used_frames"],
                "current": cur_ev["decoder_used_frames"],
            }
        )
    if prev_ev["decode_artifact_frames"] > 0 and cur_ev["decode_artifact_frames"] < prev_ev["decode_artifact_frames"]:
        findings.append(
            {
                "kind": "decode_artifacts_disappeared",
                "message": (
                    f"Decode artifact frames decreased: {prev_ev['decode_artifact_frames']} -> "
                    f"{cur_ev['decode_artifact_frames']}"
                ),
                "previous": prev_ev["decode_artifact_frames"],
                "current": cur_ev["decode_artifact_frames"],
            }
        )

    return findings


def build_proof_regression_report(storage: LocalStorage) -> dict[str, Any]:
    """Build regression report from latest vs previous proof snapshots."""
    current = load_mrms_proof_report(storage)
    previous = load_previous_proof_report(storage)
    findings = detect_proof_regressions(current, previous)

    if current is None:
        status = REGRESSION_INCONCLUSIVE
    elif previous is None:
        status = REGRESSION_INCONCLUSIVE
    elif not findings:
        if overall_status_rank(current.get("overall_status")) > overall_status_rank(
            previous.get("overall_status")
        ):
            status = REGRESSION_IMPROVED
        else:
            status = REGRESSION_NONE
    else:
        status = REGRESSION_DETECTED

    return {
        "checked_at": _utc_now(),
        "regression_status": status,
        "regression_detected": status == REGRESSION_DETECTED,
        "regression_count": len(findings),
        "findings": findings,
        "current_proof_generated_at": (current or {}).get("generated_at"),
        "previous_proof_generated_at": (previous or {}).get("generated_at")
        if isinstance(previous, dict)
        else (previous or {}).get("generated_at") if previous else None,
        "current_overall_status": (current or {}).get("overall_status"),
        "previous_overall_status": (previous or {}).get("overall_status") if previous else None,
        "verified_mrms": False,
        "proof_only": True,
        "prototype": True,
    }


def save_proof_regression_report(storage: LocalStorage, report: dict[str, Any]) -> str:
    record = dict(report)
    record.setdefault("checked_at", _utc_now())
    record.setdefault("verified_mrms", False)
    repo_path = storage.normalize_path(MRMS_PROOF_REGRESSION_LATEST_PATH)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(record, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    _append_regression_history(storage, record)
    return repo_path


def load_proof_regression_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    repo_path = storage.normalize_path(MRMS_PROOF_REGRESSION_LATEST_PATH)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return None
    try:
        return json.loads(abs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _append_regression_history(storage: LocalStorage, record: dict[str, Any]) -> None:
    history = load_proof_regression_history(storage)
    compact = {
        "checked_at": record.get("checked_at"),
        "regression_status": record.get("regression_status"),
        "regression_detected": record.get("regression_detected", False),
        "regression_count": record.get("regression_count", 0),
        "verified_mrms": False,
        "prototype": True,
    }
    history.insert(0, compact)
    history = history[:MAX_REGRESSION_HISTORY]
    repo_path = storage.normalize_path(MRMS_PROOF_REGRESSION_HISTORY_PATH)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(history, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def load_proof_regression_history(storage: LocalStorage) -> list[dict[str, Any]]:
    repo_path = storage.normalize_path(MRMS_PROOF_REGRESSION_HISTORY_PATH)
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


def run_proof_regression_check(storage: LocalStorage) -> dict[str, Any]:
    """Detect regressions and persist latest regression report."""
    report = build_proof_regression_report(storage)
    save_proof_regression_report(storage, report)
    return report


def compact_proof_regression(report: Optional[dict[str, Any]]) -> dict[str, Any]:
    if report is None:
        return {
            "regression_status": REGRESSION_INCONCLUSIVE,
            "regression_detected": False,
            "regression_count": 0,
            "checked_at": None,
            "verified_mrms": False,
            "prototype": True,
        }
    return {
        "checked_at": report.get("checked_at"),
        "regression_status": report.get("regression_status", REGRESSION_INCONCLUSIVE),
        "regression_detected": bool(report.get("regression_detected")),
        "regression_count": int(report.get("regression_count", 0)),
        "current_overall_status": report.get("current_overall_status"),
        "previous_overall_status": report.get("previous_overall_status"),
        "verified_mrms": False,
        "prototype": True,
    }
