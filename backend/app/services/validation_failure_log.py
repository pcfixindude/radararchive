"""Append-only local validation failure log for dev/prototype troubleshooting."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from backend.app.services.storage import LocalStorage

VALIDATION_FAILURES_PATH = "dev/validation_failures.jsonl"
MAX_FAILURE_ENTRIES = 100


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _failure_repo_path(storage: LocalStorage) -> str:
    return storage.normalize_path(VALIDATION_FAILURES_PATH)


def _read_all_entries(storage: LocalStorage) -> list[dict[str, Any]]:
    repo_path = _failure_repo_path(storage)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return []
    entries: list[dict[str, Any]] = []
    try:
        for line in abs_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                if isinstance(item, dict):
                    entries.append(item)
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return entries


def _write_entries(storage: LocalStorage, entries: list[dict[str, Any]]) -> None:
    repo_path = _failure_repo_path(storage)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    bounded = entries[-MAX_FAILURE_ENTRIES:]
    text = "\n".join(json.dumps(item, sort_keys=True) for item in bounded)
    if text:
        text += "\n"
    storage.absolute_path(repo_path).write_text(text, encoding="utf-8")


def append_validation_failure(
    storage: LocalStorage,
    *,
    phase: str,
    step: Optional[str] = None,
    source_mode: Optional[str] = None,
    command_context: Optional[str] = None,
    error_message: Optional[str] = None,
    warnings: Optional[list[str]] = None,
    errors: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Append one failure record and trim log to MAX_FAILURE_ENTRIES."""
    messages = list(errors or [])
    if error_message:
        messages.insert(0, error_message)
    record = {
        "logged_at": _utc_now(),
        "phase": phase,
        "step": step,
        "source_mode": source_mode,
        "command_context": command_context,
        "error_message": messages[0] if messages else None,
        "warnings": list(warnings or [])[:10],
        "errors": messages[:10],
        "verified_mrms": False,
        "prototype": True,
    }
    entries = _read_all_entries(storage)
    entries.append(record)
    _write_entries(storage, entries)
    return record


def load_recent_validation_failures(
    storage: LocalStorage,
    *,
    limit: int = 10,
) -> list[dict[str, Any]]:
    entries = _read_all_entries(storage)
    if limit < 1:
        return []
    return entries[-limit:][::-1]


def count_validation_failures(storage: LocalStorage) -> int:
    return len(_read_all_entries(storage))


def compact_failure(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "logged_at": entry.get("logged_at"),
        "phase": entry.get("phase"),
        "step": entry.get("step"),
        "source_mode": entry.get("source_mode"),
        "command_context": entry.get("command_context"),
        "error_message": entry.get("error_message"),
        "warnings": (entry.get("warnings") or [])[:3],
        "verified_mrms": False,
        "prototype": True,
    }
