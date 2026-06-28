"""Export local MRMS proof evidence bundles — does NOT verify MRMS or enable production."""

from __future__ import annotations

import json
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.catalog_status import build_catalog_status
from backend.app.services.mrms_proof_history import (
    build_proof_history_payload,
    build_regression_history_payload,
    build_signoffs_list_payload,
)
from backend.app.services.render_queue import get_queue_summary
from backend.app.services.storage import LocalStorage
from backend.app.services.validation_alerts import load_validation_alert
from backend.app.services.validation_failure_log import load_recent_validation_failures

BUNDLE_BASE_DIR = "dev/proof_bundles"
BUNDLE_LATEST_MANIFEST = "dev/proof_bundles_latest.json"
BUNDLE_INDEX_PATH = "dev/proof_bundles_index.json"
MAX_BUNDLE_INDEX = 20

RUNBOOK_DOC_SOURCES: list[tuple[str, str]] = [
    ("docs/RUNBOOK_REAL_MRMS_VALIDATION.md", "docs/RUNBOOK_REAL_MRMS_VALIDATION.md"),
    ("docs/VERIFIED_MRMS_CRITERIA.md", "docs/VERIFIED_MRMS_CRITERIA.md"),
    ("docs/MRMS_OPERATOR_SIGNOFF_TEMPLATE.md", "docs/MRMS_OPERATOR_SIGNOFF_TEMPLATE.md"),
    ("docs/GRIB2_DECODE.md", "docs/GRIB2_DECODE.md"),
]

RUNBOOK_LINK_METADATA: list[dict[str, str]] = [
    {
        "title": "Real MRMS validation runbook",
        "path": "docs/RUNBOOK_REAL_MRMS_VALIDATION.md",
        "anchor": "proof-regression-and-sign-off-phase-27",
    },
    {
        "title": "Verified MRMS criteria (not met)",
        "path": "docs/VERIFIED_MRMS_CRITERIA.md",
        "anchor": "regression-and-sign-off-workflow-phase-27",
    },
    {
        "title": "Operator sign-off template",
        "path": "docs/MRMS_OPERATOR_SIGNOFF_TEMPLATE.md",
        "anchor": "recording-sign-off-phase-27",
    },
    {
        "title": "GRIB2 decode prototype notes",
        "path": "docs/GRIB2_DECODE.md",
        "anchor": "proof-review-history-phase-28",
    },
]

STORAGE_EVIDENCE_FILES: list[tuple[str, str]] = [
    ("dev/mrms_proof_latest.json", "evidence/mrms_proof_latest.json"),
    ("dev/mrms_proof_regression_latest.json", "evidence/mrms_proof_regression_latest.json"),
    ("dev/mrms_signoffs.json", "evidence/mrms_signoffs.json"),
    ("dev/validation_alert_latest.json", "evidence/validation_alert_latest.json"),
    ("dev/scheduled_validation_latest.json", "evidence/scheduled_validation_latest.json"),
    ("dev/validation_latest.json", "evidence/validation_latest.json"),
    ("dev/benchmark_latest.json", "evidence/benchmark_latest.json"),
    ("dev/queue_benchmark_latest.json", "evidence/queue_benchmark_latest.json"),
]

STORAGE_HISTORY_FILES: list[tuple[str, str]] = [
    ("dev/mrms_proof_history.json", "evidence/mrms_proof_history.json"),
    ("dev/mrms_proof_regression_history.json", "evidence/mrms_proof_regression_history.json"),
]

BUNDLE_README = """# MRMS Proof Bundle (Local Evidence Only)

This archive packages **draft prototype evidence** from local RadarArchive dev tooling.

## Important

- This bundle is **proof evidence only** — it does **NOT** verify MRMS production output.
- `verified_mrms` remains **false** everywhere in this project.
- Exporting this bundle does **NOT** enable production rendering.
- Operator review is still required before any future verified-MRMS launch decision.
- Production tiles remain behind `ENABLE_PRODUCTION_RADAR_TILES` plus catalog gates.

## Contents

- `manifest.json` — bundle metadata (`files_included`, `files_missing`, flags)
- `runbook_links.json` — references to operator runbooks in the repo
- `evidence/` — copied or generated JSON snapshots
- `docs/` — copies of key runbook markdown files (when present in the repo)

## Runbooks (repo paths)

See `runbook_links.json` for titles and anchors. Primary docs:

- docs/RUNBOOK_REAL_MRMS_VALIDATION.md
- docs/VERIFIED_MRMS_CRITERIA.md
- docs/MRMS_OPERATOR_SIGNOFF_TEMPLATE.md
- docs/GRIB2_DECODE.md

## Regenerating evidence

```bash
make mrms-proof-report
make mrms-proof-regression
make mrms-proof-bundle
```
"""


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _bundle_timestamp() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _project_root(storage: LocalStorage) -> Path:
    return storage.storage_root.parent


def _repo_relative_data_path(storage: LocalStorage, absolute: Path) -> str:
    try:
        rel = absolute.resolve().relative_to(storage.storage_root.resolve())
        return storage.normalize_path(*rel.parts)
    except ValueError:
        return str(absolute)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _try_copy_storage_file(
    storage: LocalStorage,
    src_repo: str,
    dest: Path,
) -> bool:
    normalized = storage.normalize_path(src_repo)
    src = storage.absolute_path(normalized)
    if not src.is_file():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return True


def _try_copy_project_doc(project_root: Path, src_rel: str, dest: Path) -> bool:
    src = project_root / src_rel
    if not src.is_file():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return True


def export_mrms_proof_bundle(
    session: Session,
    storage: LocalStorage,
    *,
    include_history: bool = False,
) -> dict[str, Any]:
    """Create timestamped proof bundle folder + ZIP; return manifest dict."""
    bundle_id = str(uuid.uuid4())
    created_at = _utc_now()
    ts = _bundle_timestamp()
    archive_name = f"mrms_proof_bundle_{ts}"
    bundles_root = storage.absolute_path(BUNDLE_BASE_DIR)
    bundle_dir = bundles_root / archive_name
    bundle_dir.mkdir(parents=True, exist_ok=True)

    project_root = _project_root(storage)
    files_included: list[str] = []
    files_missing: list[str] = []

    for src_repo, dest_rel in STORAGE_EVIDENCE_FILES:
        dest = bundle_dir / dest_rel
        if _try_copy_storage_file(storage, src_repo, dest):
            files_included.append(dest_rel)
        else:
            files_missing.append(dest_rel)

    if include_history:
        for src_repo, dest_rel in STORAGE_HISTORY_FILES:
            dest = bundle_dir / dest_rel
            if _try_copy_storage_file(storage, src_repo, dest):
                files_included.append(dest_rel)
            else:
                files_missing.append(dest_rel)
    else:
        compact_proof = build_proof_history_payload(storage)
        compact_regression = build_regression_history_payload(storage)
        proof_dest = bundle_dir / "evidence/mrms_proof_history_compact.json"
        regression_dest = bundle_dir / "evidence/mrms_proof_regression_history_compact.json"
        _write_json(proof_dest, compact_proof)
        _write_json(regression_dest, compact_regression)
        files_included.extend(
            [
                "evidence/mrms_proof_history_compact.json",
                "evidence/mrms_proof_regression_history_compact.json",
            ]
        )

    signoffs_payload = build_signoffs_list_payload(storage)
    signoffs_dest = bundle_dir / "evidence/mrms_signoffs_compact.json"
    _write_json(signoffs_dest, signoffs_payload)
    files_included.append("evidence/mrms_signoffs_compact.json")

    failures = load_recent_validation_failures(storage, limit=25)
    failures_dest = bundle_dir / "evidence/validation_failures_recent.json"
    _write_json(
        failures_dest,
        {
            "prototype": True,
            "verified_mrms": False,
            "count": len(failures),
            "entries": failures,
        },
    )
    files_included.append("evidence/validation_failures_recent.json")

    alert = load_validation_alert(storage)
    if alert is not None and "evidence/validation_alert_latest.json" not in files_included:
        alert_dest = bundle_dir / "evidence/validation_alert_latest.json"
        _write_json(alert_dest, alert)
        files_included.append("evidence/validation_alert_latest.json")

    catalog = build_catalog_status(session)
    catalog_dest = bundle_dir / "evidence/catalog_status.json"
    _write_json(catalog_dest, catalog)
    files_included.append("evidence/catalog_status.json")

    queue = get_queue_summary(session)
    queue_dest = bundle_dir / "evidence/render_queue_status.json"
    _write_json(
        queue_dest,
        {
            "prototype": True,
            "verified_mrms": False,
            **queue.to_dict(),
        },
    )
    files_included.append("evidence/render_queue_status.json")

    runbook_links_path = bundle_dir / "runbook_links.json"
    _write_json(
        runbook_links_path,
        {
            "prototype": True,
            "verified_mrms": False,
            "local_bundle_only": True,
            "links": RUNBOOK_LINK_METADATA,
        },
    )
    files_included.append("runbook_links.json")

    for src_rel, dest_rel in RUNBOOK_DOC_SOURCES:
        dest = bundle_dir / dest_rel
        if _try_copy_project_doc(project_root, src_rel, dest):
            files_included.append(dest_rel)
        else:
            files_missing.append(dest_rel)

    readme_path = bundle_dir / "README.md"
    readme_path.write_text(BUNDLE_README, encoding="utf-8")
    files_included.append("README.md")

    bundle_folder_repo = _repo_relative_data_path(storage, bundle_dir)
    production_enabled = settings.enable_production_radar_tiles
    placeholder_default = not production_enabled and not settings.enable_decoded_tiles

    manifest: dict[str, Any] = {
        "bundle_id": bundle_id,
        "created_at": created_at,
        "bundle_folder": bundle_folder_repo,
        "zip_path": None,
        "archive_name": archive_name,
        "files_included": sorted(files_included),
        "files_missing": sorted(files_missing),
        "file_count": len(files_included),
        "include_history": include_history,
        "verified_mrms": False,
        "proof_only": True,
        "local_bundle_only": True,
        "does_not_enable_production": True,
        "production_rendering_enabled": production_enabled,
        "placeholder_default": placeholder_default,
        "prototype": True,
        "runbook_links": RUNBOOK_LINK_METADATA,
    }

    manifest_path = bundle_dir / "manifest.json"
    _write_json(manifest_path, manifest)
    files_included.append("manifest.json")

    manifest["file_count"] = len(files_included)
    manifest["files_included"] = sorted(files_included)
    _write_json(manifest_path, manifest)

    zip_abs = bundles_root / f"{archive_name}.zip"
    with zipfile.ZipFile(zip_abs, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(bundle_dir.rglob("*")):
            if path.is_file():
                arcname = f"{archive_name}/{path.relative_to(bundle_dir).as_posix()}"
                archive.write(path, arcname=arcname)

    zip_repo = _repo_relative_data_path(storage, zip_abs)
    manifest["zip_path"] = zip_repo
    _write_json(manifest_path, manifest)

    _save_latest_manifest(storage, manifest)
    _append_bundle_index(storage, manifest)
    return manifest


def _save_latest_manifest(storage: LocalStorage, manifest: dict[str, Any]) -> str:
    repo_path = storage.normalize_path(BUNDLE_LATEST_MANIFEST)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    storage.absolute_path(repo_path).write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return repo_path


def load_latest_proof_bundle_manifest(storage: LocalStorage) -> Optional[dict[str, Any]]:
    repo_path = storage.normalize_path(BUNDLE_LATEST_MANIFEST)
    abs_path = storage.absolute_path(repo_path)
    if not abs_path.is_file():
        return None
    try:
        return json.loads(abs_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _append_bundle_index(storage: LocalStorage, manifest: dict[str, Any]) -> None:
    repo_path = storage.normalize_path(BUNDLE_INDEX_PATH)
    abs_path = storage.absolute_path(repo_path)
    entries: list[dict[str, Any]] = []
    if abs_path.is_file():
        try:
            data = json.loads(abs_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                entries = data
        except (json.JSONDecodeError, OSError):
            entries = []
    compact = compact_proof_bundle_manifest(manifest)
    entries.insert(0, compact)
    storage.ensure_directories(repo_path.rsplit("/", 1)[0])
    abs_path.write_text(
        json.dumps(entries[:MAX_BUNDLE_INDEX], indent=2, sort_keys=True),
        encoding="utf-8",
    )


def load_proof_bundle_index(storage: LocalStorage) -> list[dict[str, Any]]:
    repo_path = storage.normalize_path(BUNDLE_INDEX_PATH)
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


def compact_proof_bundle_manifest(manifest: Optional[dict[str, Any]]) -> dict[str, Any]:
    if manifest is None:
        return {
            "available": False,
            "verified_mrms": False,
            "local_bundle_only": True,
            "proof_only": True,
            "does_not_enable_production": True,
            "prototype": True,
        }
    return {
        "available": True,
        "bundle_id": manifest.get("bundle_id"),
        "created_at": manifest.get("created_at"),
        "bundle_folder": manifest.get("bundle_folder"),
        "zip_path": manifest.get("zip_path"),
        "file_count": int(manifest.get("file_count", 0)),
        "files_missing_count": len(manifest.get("files_missing") or []),
        "include_history": bool(manifest.get("include_history")),
        "verified_mrms": False,
        "local_bundle_only": True,
        "proof_only": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def compact_proof_bundle_status(storage: LocalStorage) -> dict[str, Any]:
    manifest = load_latest_proof_bundle_manifest(storage)
    status = compact_proof_bundle_manifest(manifest)
    status["bundle_count"] = len(load_proof_bundle_index(storage))
    return status


def build_proof_bundles_list_payload(storage: LocalStorage, *, limit: int = 10) -> dict[str, Any]:
    bounded = max(1, min(limit, MAX_BUNDLE_INDEX))
    entries = load_proof_bundle_index(storage)[:bounded]
    latest = entries[0] if entries else compact_proof_bundle_manifest(
        load_latest_proof_bundle_manifest(storage)
    )
    return {
        "prototype": True,
        "verified_mrms": False,
        "local_bundle_only": True,
        "proof_only": True,
        "count": len(entries),
        "latest": latest,
        "entries": entries,
        "runbook_references": RUNBOOK_LINK_METADATA,
    }
