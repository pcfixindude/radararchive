"""Compare MRMS visual review manifests — local visual review only."""

from __future__ import annotations

import json
from typing import Any, Optional

from backend.app.services.mrms_proof_bundle_diff import (
    DIFF_IMPROVED,
    DIFF_MIXED,
    DIFF_NO_BASELINE,
    DIFF_UNCHANGED,
    DIFF_UNKNOWN,
    DIFF_WORSENED,
)
from backend.app.services.mrms_visual_review import (
    SUGGESTED_VISUAL_REVIEW_COMMAND,
    TILE_MODE_DECODED_PROTOTYPE,
    TILE_MODE_PLACEHOLDER,
    TILE_MODE_PLACEHOLDER_FOR_REAL_RAW,
    TILE_MODE_PRODUCTION_RENDERED_CACHE,
    load_latest_visual_review,
    load_previous_visual_review,
)
from backend.app.services.storage import LocalStorage

COMPARISON_LATEST_PATH = "dev/mrms_visual_review_comparison_latest.json"
COMPARISON_HISTORY_PATH = "dev/mrms_visual_review_comparison_history.json"
MAX_COMPARISON_HISTORY = 25

RENDER_STATUS_RANK = {
    "placeholder": 0,
    "decoded_prototype": 1,
    "production_pending": 2,
    "production_failed": 2,
    "production_rendered": 3,
}

RAW_KIND_RANK = {
    "demo_seeded_stub": 0,
    "collector_stub": 0,
    "mrms_download_stub": 1,
    "mrms_real_grib2": 2,
}


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _comparison_latest_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(COMPARISON_LATEST_PATH)


def _comparison_history_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(COMPARISON_HISTORY_PATH)


def _load_comparison_history(storage: LocalStorage) -> list[dict[str, Any]]:
    abs_path = storage.absolute_path(_comparison_history_repo_path(storage))
    if not abs_path.is_file():
        return []
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save_comparison_history(storage: LocalStorage, entries: list[dict[str, Any]]) -> None:
    repo_path = _comparison_history_repo_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(entries[:MAX_COMPARISON_HISTORY], indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _count_change_signal(baseline: int, latest: int, *, higher_is_better: bool) -> int:
    if latest == baseline:
        return 0
    if higher_is_better:
        return 1 if latest > baseline else -1
    return 1 if latest < baseline else -1


def _classify_overall_diff(signals: list[int]) -> str:
    if not signals:
        return DIFF_UNKNOWN
    positives = sum(1 for value in signals if value > 0)
    negatives = sum(1 for value in signals if value < 0)
    if positives == 0 and negatives == 0:
        return DIFF_UNCHANGED
    if positives > 0 and negatives == 0:
        return DIFF_IMPROVED
    if negatives > 0 and positives == 0:
        return DIFF_WORSENED
    return DIFF_MIXED


def _append_signal_result(
    label: str,
    signal: int,
    improvements: list[str],
    regressions: list[str],
    unchanged_items: list[str],
) -> None:
    if signal > 0:
        improvements.append(label)
    elif signal < 0:
        regressions.append(label)
    else:
        unchanged_items.append(label)


def _artifact_index(report: Optional[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not report:
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for item in report.get("artifacts") or []:
        timestamp = item.get("timestamp")
        if timestamp:
            indexed[str(timestamp)] = item
    return indexed


def _tile_mode_set(report: Optional[dict[str, Any]]) -> set[str]:
    if not report:
        return set()
    return {str(mode) for mode in (report.get("tile_modes_found") or []) if mode}


def _tile_mode_change_signal(added: set[str], removed: set[str]) -> int:
    positive_modes = {TILE_MODE_DECODED_PROTOTYPE, TILE_MODE_PRODUCTION_RENDERED_CACHE}
    negative_modes = {TILE_MODE_PLACEHOLDER, TILE_MODE_PLACEHOLDER_FOR_REAL_RAW}
    signal = 0
    if added & positive_modes:
        signal += 1
    if removed & positive_modes:
        signal -= 1
    if added & negative_modes and not (added & positive_modes):
        signal -= 1
    if removed & negative_modes and not (removed & positive_modes):
        signal += 1
    return max(-1, min(1, signal))


def compare_visual_reviews(
    baseline: Optional[dict[str, Any]],
    latest: dict[str, Any],
) -> dict[str, Any]:
    """Compare baseline and latest visual review manifests."""
    safety = {
        "verified_mrms": False,
        "local_visual_review_comparison_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }
    latest_created_at = latest.get("created_at")
    latest_report_path = latest.get("json_path")

    if baseline is None:
        return {
            "compared_at": _utc_now(),
            "latest_created_at": latest_created_at,
            "baseline_created_at": None,
            "latest_report_path": latest_report_path,
            "baseline_report_path": None,
            "artifact_count_change": None,
            "missing_artifact_count_change": None,
            "inspected_frame_count_change": None,
            "tile_modes_added": [],
            "tile_modes_removed": [],
            "render_status_changes": [],
            "raw_kind_changes": [],
            "overall_visual_review_diff_status": DIFF_NO_BASELINE,
            "improvements": [],
            "regressions": [],
            "unchanged_items": [],
            "suggested_next_command": SUGGESTED_VISUAL_REVIEW_COMMAND,
            **safety,
        }

    baseline_created_at = baseline.get("created_at")
    baseline_report_path = baseline.get("json_path")
    improvements: list[str] = []
    regressions: list[str] = []
    unchanged_items: list[str] = []
    signals: list[int] = []

    artifact_count_change = {
        "baseline": int(baseline.get("artifact_count", 0)),
        "latest": int(latest.get("artifact_count", 0)),
    }
    missing_artifact_count_change = {
        "baseline": int(baseline.get("missing_artifact_count", 0)),
        "latest": int(latest.get("missing_artifact_count", 0)),
    }
    inspected_frame_count_change = {
        "baseline": int(baseline.get("frame_count", 0)),
        "latest": int(latest.get("frame_count", 0)),
    }

    artifact_signal = _count_change_signal(
        artifact_count_change["baseline"],
        artifact_count_change["latest"],
        higher_is_better=True,
    )
    missing_signal = _count_change_signal(
        missing_artifact_count_change["baseline"],
        missing_artifact_count_change["latest"],
        higher_is_better=False,
    )
    frame_signal = _count_change_signal(
        inspected_frame_count_change["baseline"],
        inspected_frame_count_change["latest"],
        higher_is_better=True,
    )
    signals.extend([artifact_signal, missing_signal, frame_signal])
    _append_signal_result("artifact_count", artifact_signal, improvements, regressions, unchanged_items)
    _append_signal_result(
        "missing_artifact_count",
        missing_signal,
        improvements,
        regressions,
        unchanged_items,
    )
    _append_signal_result(
        "inspected_frame_count",
        frame_signal,
        improvements,
        regressions,
        unchanged_items,
    )

    base_modes = _tile_mode_set(baseline)
    latest_modes = _tile_mode_set(latest)
    tile_modes_added = sorted(latest_modes - base_modes)
    tile_modes_removed = sorted(base_modes - latest_modes)
    tile_mode_signal = _tile_mode_change_signal(set(tile_modes_added), set(tile_modes_removed))
    if tile_modes_added or tile_modes_removed:
        signals.append(tile_mode_signal)
        _append_signal_result("tile_modes", tile_mode_signal, improvements, regressions, unchanged_items)
    else:
        unchanged_items.append("tile_modes")

    base_index = _artifact_index(baseline)
    latest_index = _artifact_index(latest)
    render_status_changes: list[dict[str, Any]] = []
    raw_kind_changes: list[dict[str, Any]] = []
    render_signals: list[int] = []
    raw_signals: list[int] = []

    for timestamp, latest_item in latest_index.items():
        base_item = base_index.get(timestamp)
        if base_item is None:
            continue
        base_render = str(base_item.get("render_status") or "placeholder")
        latest_render = str(latest_item.get("render_status") or "placeholder")
        if base_render != latest_render:
            render_status_changes.append(
                {
                    "timestamp": timestamp,
                    "baseline": base_render,
                    "latest": latest_render,
                }
            )
            base_rank = RENDER_STATUS_RANK.get(base_render, 0)
            latest_rank = RENDER_STATUS_RANK.get(latest_render, 0)
            if latest_rank > base_rank:
                render_signals.append(1)
            elif latest_rank < base_rank:
                render_signals.append(-1)

        base_raw = base_item.get("raw_kind")
        latest_raw = latest_item.get("raw_kind")
        if base_raw != latest_raw:
            raw_kind_changes.append(
                {
                    "timestamp": timestamp,
                    "baseline": base_raw,
                    "latest": latest_raw,
                }
            )
            base_rank = RAW_KIND_RANK.get(str(base_raw or ""), 0)
            latest_rank = RAW_KIND_RANK.get(str(latest_raw or ""), 0)
            if latest_rank > base_rank:
                raw_signals.append(1)
            elif latest_rank < base_rank:
                raw_signals.append(-1)

    if render_signals:
        render_signal = 1 if sum(render_signals) > 0 else (-1 if sum(render_signals) < 0 else 0)
        if render_signal == 0 and render_signals:
            render_signal = 1 if sum(render_signals) > 0 else -1
        signals.append(render_signal)
        _append_signal_result(
            "render_status_changes",
            render_signal,
            improvements,
            regressions,
            unchanged_items,
        )
    elif not render_status_changes:
        unchanged_items.append("render_status")

    if raw_signals:
        raw_signal = 1 if sum(raw_signals) > 0 else (-1 if sum(raw_signals) < 0 else 0)
        signals.append(raw_signal)
        _append_signal_result("raw_kind_changes", raw_signal, improvements, regressions, unchanged_items)
    elif not raw_kind_changes:
        unchanged_items.append("raw_kind")

    overall = _classify_overall_diff(signals)

    return {
        "compared_at": _utc_now(),
        "latest_created_at": latest_created_at,
        "baseline_created_at": baseline_created_at,
        "latest_report_path": latest_report_path,
        "baseline_report_path": baseline_report_path,
        "artifact_count_change": artifact_count_change,
        "missing_artifact_count_change": missing_artifact_count_change,
        "inspected_frame_count_change": inspected_frame_count_change,
        "tile_modes_added": tile_modes_added,
        "tile_modes_removed": tile_modes_removed,
        "render_status_changes": render_status_changes,
        "raw_kind_changes": raw_kind_changes,
        "overall_visual_review_diff_status": overall,
        "improvements": improvements,
        "regressions": regressions,
        "unchanged_items": unchanged_items,
        "suggested_next_command": SUGGESTED_VISUAL_REVIEW_COMMAND,
        **safety,
    }


def record_visual_review_comparison(
    storage: LocalStorage,
    *,
    baseline_report: Optional[dict[str, Any]] = None,
    latest_report: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Compare latest vs previous visual review and persist bounded history."""
    latest = latest_report if latest_report is not None else load_latest_visual_review(storage)
    if latest is None:
        comparison = {
            "compared_at": _utc_now(),
            "latest_created_at": None,
            "baseline_created_at": None,
            "latest_report_path": None,
            "baseline_report_path": None,
            "artifact_count_change": None,
            "missing_artifact_count_change": None,
            "inspected_frame_count_change": None,
            "tile_modes_added": [],
            "tile_modes_removed": [],
            "render_status_changes": [],
            "raw_kind_changes": [],
            "overall_visual_review_diff_status": DIFF_UNKNOWN,
            "improvements": [],
            "regressions": [],
            "unchanged_items": [],
            "suggested_next_command": SUGGESTED_VISUAL_REVIEW_COMMAND,
            "verified_mrms": False,
            "local_visual_review_comparison_only": True,
            "does_not_clear_alerts": True,
            "does_not_enable_production": True,
            "prototype": True,
        }
    else:
        baseline = baseline_report
        if baseline is None:
            baseline = load_previous_visual_review(storage)
        comparison = compare_visual_reviews(baseline, latest)

    latest_repo = _comparison_latest_repo_path(storage)
    storage.ensure_directories(latest_repo.rsplit("/", 1)[0])
    storage.absolute_path(latest_repo).write_text(
        json.dumps(comparison, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    history = _load_comparison_history(storage)
    history.insert(0, comparison)
    _save_comparison_history(storage, history)
    return comparison


def load_latest_visual_review_comparison(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_comparison_latest_repo_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def load_visual_review_comparison_history(
    storage: LocalStorage,
    *,
    limit: int = MAX_COMPARISON_HISTORY,
) -> list[dict[str, Any]]:
    bounded = max(1, min(limit, MAX_COMPARISON_HISTORY))
    return _load_comparison_history(storage)[:bounded]


def compact_visual_review_comparison_summary(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_visual_review_comparison(storage)
    history = _load_comparison_history(storage)
    empty = {
        "available": False,
        "overall_visual_review_diff_status": None,
        "compared_at": None,
        "latest_created_at": None,
        "baseline_created_at": None,
        "artifact_count_change": None,
        "missing_artifact_count_change": None,
        "tile_modes_added": [],
        "tile_modes_removed": [],
        "history_count": len(history),
        "verified_mrms": False,
        "local_visual_review_comparison_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }
    if latest is None:
        return empty
    return {
        "available": True,
        "overall_visual_review_diff_status": latest.get("overall_visual_review_diff_status"),
        "compared_at": latest.get("compared_at"),
        "latest_created_at": latest.get("latest_created_at"),
        "baseline_created_at": latest.get("baseline_created_at"),
        "artifact_count_change": latest.get("artifact_count_change"),
        "missing_artifact_count_change": latest.get("missing_artifact_count_change"),
        "tile_modes_added": latest.get("tile_modes_added") or [],
        "tile_modes_removed": latest.get("tile_modes_removed") or [],
        "history_count": len(history),
        "verified_mrms": False,
        "local_visual_review_comparison_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def build_visual_review_comparison_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_latest_visual_review_comparison(storage)
    history = load_visual_review_comparison_history(storage)
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_visual_review_comparison_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "latest": latest,
        "count": len(history),
        "max_entries": MAX_COMPARISON_HISTORY,
        "entries": history,
        "compact": compact_visual_review_comparison_summary(storage),
    }


def build_visual_review_comparison_history_payload(
    storage: LocalStorage,
    *,
    limit: int = MAX_COMPARISON_HISTORY,
) -> dict[str, Any]:
    bounded = max(1, min(limit, MAX_COMPARISON_HISTORY))
    entries = load_visual_review_comparison_history(storage, limit=bounded)
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_visual_review_comparison_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "no_external_notifications": True,
        "count": len(entries),
        "max_entries": MAX_COMPARISON_HISTORY,
        "entries": entries,
        "compact": compact_visual_review_comparison_summary(storage),
    }
