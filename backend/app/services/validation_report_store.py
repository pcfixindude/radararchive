"""Persist latest dev validation and benchmark reports to local JSON files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from backend.app.services.storage import LocalStorage

VALIDATION_REPORT_PATH = "dev/validation_latest.json"
BENCHMARK_REPORT_PATH = "dev/benchmark_latest.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def save_latest_validation_report(storage: LocalStorage, payload: dict[str, Any]) -> str:
    """Write latest validation report JSON; returns repo-relative path."""
    record = dict(payload)
    record.setdefault("validated_at", _utc_now())
    record.setdefault("verified_mrms", False)
    record.setdefault("prototype", True)
    repo_path = storage.normalize_path(VALIDATION_REPORT_PATH)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(record, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return repo_path


def load_latest_validation_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    repo_path = storage.normalize_path(VALIDATION_REPORT_PATH)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return None
    try:
        return json.loads(abs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_latest_benchmark_report(storage: LocalStorage, payload: dict[str, Any]) -> str:
    record = dict(payload)
    record.setdefault("benchmarked_at", _utc_now())
    record.setdefault("verified_mrms", False)
    record.setdefault("prototype", True)
    repo_path = storage.normalize_path(BENCHMARK_REPORT_PATH)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(record, indent=2, sort_keys=True),
        encoding="utf-8",
    )
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
