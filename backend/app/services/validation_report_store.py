"""Persist latest dev validation and benchmark reports to local JSON files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from backend.app.services.storage import LocalStorage

VALIDATION_REPORT_PATH = "dev/validation_latest.json"
BENCHMARK_REPORT_PATH = "dev/benchmark_latest.json"
QUEUE_BENCHMARK_REPORT_PATH = "dev/queue_benchmark_latest.json"
VALIDATION_HISTORY_PATH = "dev/validation_history.json"
QUEUE_BENCHMARK_HISTORY_PATH = "dev/queue_benchmark_history.json"
SCHEDULED_VALIDATION_REPORT_PATH = "dev/scheduled_validation_latest.json"
SCHEDULED_VALIDATION_HISTORY_PATH = "dev/scheduled_validation_history.json"
MAX_VALIDATION_HISTORY = 10
MAX_QUEUE_BENCHMARK_HISTORY = 10
MAX_SCHEDULED_VALIDATION_HISTORY = 10


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json(storage: LocalStorage, repo_path: str, payload: Any) -> str:
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return repo_path


def save_validation_report(storage: LocalStorage, payload: dict[str, Any]) -> str:
    """Write latest validation/batch report and append to bounded history."""
    record = dict(payload)
    record.setdefault("validated_at", _utc_now())
    record.setdefault("verified_mrms", False)
    record.setdefault("prototype", True)
    repo_path = storage.normalize_path(VALIDATION_REPORT_PATH)
    _write_json(storage, repo_path, record)
    _append_validation_history(storage, record)
    return repo_path


def save_latest_validation_report(storage: LocalStorage, payload: dict[str, Any]) -> str:
    """Backward-compatible alias for single-frame validation persistence."""
    return save_validation_report(storage, payload)


def load_latest_validation_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    repo_path = storage.normalize_path(VALIDATION_REPORT_PATH)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return None
    try:
        return json.loads(abs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _append_validation_history(storage: LocalStorage, record: dict[str, Any]) -> None:
    history = load_validation_history(storage)
    compact = {
        "validated_at": record.get("validated_at"),
        "source_mode": record.get("source_mode"),
        "batch": record.get("batch", False),
        "requested_frame_count": record.get("requested_frame_count", record.get("discovered_count", 0)),
        "effective_frame_count": record.get("effective_frame_count"),
        "discovered_count": record.get("discovered_count", 0),
        "downloaded_count": record.get("downloaded_count", 0),
        "decoded_count": record.get("decoded_count", 0),
        "elapsed_seconds": record.get("elapsed_seconds"),
        "verified_mrms": False,
        "prototype": True,
    }
    history.insert(0, compact)
    history = history[:MAX_VALIDATION_HISTORY]
    repo_path = storage.normalize_path(VALIDATION_HISTORY_PATH)
    _write_json(storage, repo_path, history)


def load_validation_history(storage: LocalStorage) -> list[dict[str, Any]]:
    repo_path = storage.normalize_path(VALIDATION_HISTORY_PATH)
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


def save_latest_benchmark_report(storage: LocalStorage, payload: dict[str, Any]) -> str:
    record = dict(payload)
    record.setdefault("benchmarked_at", _utc_now())
    record.setdefault("verified_mrms", False)
    record.setdefault("prototype", True)
    repo_path = storage.normalize_path(BENCHMARK_REPORT_PATH)
    _write_json(storage, repo_path, record)
    return repo_path


def load_latest_benchmark_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    repo_path = storage.normalize_path(BENCHMARK_REPORT_PATH)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return None
    try:
        return json.loads(abs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_queue_benchmark_report(storage: LocalStorage, payload: dict[str, Any]) -> str:
    record = dict(payload)
    record.setdefault("benchmarked_at", _utc_now())
    record.setdefault("verified_mrms", False)
    record.setdefault("prototype", True)
    repo_path = storage.normalize_path(QUEUE_BENCHMARK_REPORT_PATH)
    _write_json(storage, repo_path, record)
    _append_queue_benchmark_history(storage, record)
    return repo_path


def load_latest_queue_benchmark_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    repo_path = storage.normalize_path(QUEUE_BENCHMARK_REPORT_PATH)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return None
    try:
        return json.loads(abs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _append_queue_benchmark_history(storage: LocalStorage, record: dict[str, Any]) -> None:
    history = load_queue_benchmark_history(storage)
    compact = {
        "benchmarked_at": record.get("benchmarked_at"),
        "source_mode": record.get("source_mode"),
        "effective_count": record.get("effective_count"),
        "min_zoom": record.get("min_zoom"),
        "max_zoom": record.get("max_zoom"),
        "dry_run": record.get("dry_run", False),
        "jobs_enqueued": record.get("jobs_enqueued", 0),
        "jobs_processed": record.get("jobs_processed", 0),
        "jobs_succeeded": record.get("jobs_succeeded", 0),
        "jobs_failed": record.get("jobs_failed", 0),
        "total_tiles_written": record.get("total_tiles_written", 0),
        "total_tiles_skipped": record.get("total_tiles_skipped", 0),
        "total_output_bytes": record.get("total_output_bytes", 0),
        "total_elapsed_seconds": record.get("total_elapsed_seconds"),
        "verified_mrms": False,
        "prototype": True,
    }
    history.insert(0, compact)
    history = history[:MAX_QUEUE_BENCHMARK_HISTORY]
    repo_path = storage.normalize_path(QUEUE_BENCHMARK_HISTORY_PATH)
    _write_json(storage, repo_path, history)


def load_queue_benchmark_history(storage: LocalStorage) -> list[dict[str, Any]]:
    repo_path = storage.normalize_path(QUEUE_BENCHMARK_HISTORY_PATH)
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


def save_scheduled_validation_report(storage: LocalStorage, payload: dict[str, Any]) -> str:
    record = dict(payload)
    record.setdefault("ran_at", _utc_now())
    record.setdefault("verified_mrms", False)
    record.setdefault("prototype", True)
    repo_path = storage.normalize_path(SCHEDULED_VALIDATION_REPORT_PATH)
    _write_json(storage, repo_path, record)
    _append_scheduled_validation_history(storage, record)
    return repo_path


def load_latest_scheduled_validation_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    repo_path = storage.normalize_path(SCHEDULED_VALIDATION_REPORT_PATH)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return None
    try:
        return json.loads(abs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _append_scheduled_validation_history(storage: LocalStorage, record: dict[str, Any]) -> None:
    history = load_scheduled_validation_history(storage)
    compact = {
        "ran_at": record.get("ran_at"),
        "source_mode": record.get("source_mode"),
        "success": record.get("success", False),
        "exit_code": record.get("exit_code", 1),
        "effective_count": record.get("effective_count"),
        "min_zoom": record.get("min_zoom"),
        "max_zoom": record.get("max_zoom"),
        "elapsed_seconds": record.get("elapsed_seconds"),
        "batch_decoded_count": (record.get("batch_validation") or {}).get("decoded_count", 0),
        "queue_jobs_succeeded": (record.get("queue_benchmark") or {}).get("jobs_succeeded", 0),
        "queue_jobs_failed": (record.get("queue_benchmark") or {}).get("jobs_failed", 0),
        "verified_mrms": False,
        "prototype": True,
    }
    history.insert(0, compact)
    history = history[:MAX_SCHEDULED_VALIDATION_HISTORY]
    repo_path = storage.normalize_path(SCHEDULED_VALIDATION_HISTORY_PATH)
    _write_json(storage, repo_path, history)


def load_scheduled_validation_history(storage: LocalStorage) -> list[dict[str, Any]]:
    repo_path = storage.normalize_path(SCHEDULED_VALIDATION_HISTORY_PATH)
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
