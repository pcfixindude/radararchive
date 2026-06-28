"""MRMS visual review sample-set selection — local drilldown only, not verified MRMS."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from backend.app.services.mrms_visual_review import (
    RUNBOOK_PATH,
    SUGGESTED_VISUAL_REVIEW_COMMAND,
    load_latest_visual_review,
)
from backend.app.services.mrms_visual_review_compare import compact_visual_review_comparison_summary
from backend.app.services.mrms_visual_review_hint import compact_visual_review_hint
from backend.app.services.storage import LocalStorage

SAMPLE_SET_JSON = "dev/mrms_visual_review_sample_set.json"
SAMPLE_SET_MD = "dev/mrms_visual_review_sample_set.md"

SUGGESTED_SAMPLE_SET_COMMAND = "make mrms-visual-review-sample-set"

SELECTION_RECOMMENDED = "recommended"
SELECTION_EXPLICIT = "explicit"

DEFAULT_SAMPLE_LIMIT = 5
MAX_SAMPLE_LIMIT = 10

TILE_MODE_PRIORITY = {
    "production_rendered_cache": 5,
    "production_gated": 4,
    "decoded_prototype": 3,
    "placeholder_for_real_raw": 2,
    "placeholder": 1,
    "unknown": 0,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sample_set_json_path(storage: LocalStorage) -> str:
    return storage.normalize_path(SAMPLE_SET_JSON)


def _sample_set_md_path(storage: LocalStorage) -> str:
    return storage.normalize_path(SAMPLE_SET_MD)


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "local_sample_set_only": True,
        "does_not_clear_alerts": True,
        "does_not_enable_production": True,
        "does_not_download_or_decode": True,
        "no_external_notifications": True,
        "prototype": True,
    }


def _artifact_score(item: dict[str, Any]) -> int:
    score = 0
    missing = item.get("missing_artifacts") or []
    if missing:
        score += 10 + len(missing)
    tile_mode = str(item.get("tile_mode") or "unknown")
    score += TILE_MODE_PRIORITY.get(tile_mode, 0) * 2
    paths = item.get("artifact_paths_found") or []
    score += min(len(paths), 3)
    return score


def _build_context(storage: LocalStorage) -> dict[str, Any]:
    hint = compact_visual_review_hint(storage)
    comparison = compact_visual_review_comparison_summary(storage)
    return {
        "visual_review_regeneration_recommended": bool(
            hint.get("visual_review_regeneration_recommended")
        ),
        "visual_review_hint_reason": hint.get("reason"),
        "stale_visual_review": bool(hint.get("stale_visual_review")),
        "latest_visual_review_comparison_status": comparison.get(
            "overall_visual_review_diff_status"
        ),
        "comparison_available": bool(comparison.get("available")),
    }


def _entry_from_artifact(
    artifact: dict[str, Any],
    *,
    selection_reason: str,
    source_visual_review_at: Optional[str],
    context: dict[str, Any],
    notes: Optional[str] = None,
) -> dict[str, Any]:
    paths = artifact.get("artifact_paths_found") or []
    primary_path = paths[0] if paths else None
    return {
        "timestamp": artifact.get("timestamp"),
        "layer": artifact.get("layer"),
        "tile_mode": artifact.get("tile_mode"),
        "render_status": artifact.get("render_status"),
        "raw_kind": artifact.get("raw_kind"),
        "artifact_paths_found": paths,
        "primary_artifact_path": primary_path,
        "missing_artifacts": artifact.get("missing_artifacts") or [],
        "selection_reason": selection_reason,
        "source_visual_review_at": source_visual_review_at,
        "visual_review_regeneration_recommended": context.get(
            "visual_review_regeneration_recommended"
        ),
        "visual_review_hint_reason": context.get("visual_review_hint_reason"),
        "stale_visual_review": context.get("stale_visual_review"),
        "latest_visual_review_comparison_status": context.get(
            "latest_visual_review_comparison_status"
        ),
        "notes": notes,
        **_safety_fields(),
    }


def select_recommended_sample_entries(
    manifest: dict[str, Any],
    *,
    limit: int = DEFAULT_SAMPLE_LIMIT,
    context: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """Pick a small prioritized subset from a visual review manifest."""
    artifacts = list(manifest.get("artifacts") or [])
    if not artifacts:
        return []

    bounded = max(1, min(limit, MAX_SAMPLE_LIMIT))
    ctx = context or {}
    source_at = manifest.get("created_at")
    ranked = sorted(
        artifacts,
        key=lambda item: (_artifact_score(item), str(item.get("timestamp") or "")),
        reverse=True,
    )
    selected: list[dict[str, Any]] = []
    seen_modes: set[str] = set()
    for item in ranked:
        if len(selected) >= bounded:
            break
        mode = str(item.get("tile_mode") or "unknown")
        reason = "recommended_priority_score"
        if item.get("missing_artifacts"):
            reason = "missing_artifacts"
        elif mode not in seen_modes and mode != "placeholder":
            reason = "diverse_tile_mode"
        seen_modes.add(mode)
        selected.append(
            _entry_from_artifact(
                item,
                selection_reason=reason,
                source_visual_review_at=source_at,
                context=ctx,
            )
        )
    return selected


def select_explicit_sample_entries(
    manifest: dict[str, Any],
    *,
    timestamps: list[str],
    context: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    ctx = context or {}
    source_at = manifest.get("created_at")
    by_timestamp = {
        str(item.get("timestamp")): item for item in (manifest.get("artifacts") or [])
    }
    entries: list[dict[str, Any]] = []
    for timestamp in timestamps:
        artifact = by_timestamp.get(timestamp)
        if artifact is None:
            continue
        entries.append(
            _entry_from_artifact(
                artifact,
                selection_reason="explicit_timestamp",
                source_visual_review_at=source_at,
                context=ctx,
            )
        )
    return entries


def build_sample_set_markdown(sample_set: dict[str, Any]) -> str:
    created_at = sample_set.get("created_at") or _utc_now()
    lines = [
        "# MRMS Visual Review Sample Set (Local Drilldown Only)",
        "",
        f"Generated at: {created_at}",
        "",
        "> **WARNING:** This sample set is local operator drilldown evidence only.",
        "> It does **NOT** verify MRMS, clear validation alerts, enable production rendering,",
        "> download/decode MRMS, create production tiles, or send external notifications.",
        "",
        "## Selection",
        "",
        f"- Selection mode: {sample_set.get('selection_mode') or '—'}",
        f"- Entry limit: {sample_set.get('limit')}",
        f"- Entries selected: {sample_set.get('entry_count', 0)}",
        f"- Source visual review at: {sample_set.get('source_visual_review_at') or '—'}",
        f"- Source manifest path: `{sample_set.get('source_visual_review_path') or '—'}`",
        "",
        "## Context",
        "",
    ]
    context = sample_set.get("context") or {}
    lines.extend(
        [
            f"- Visual review regeneration recommended: "
            f"{context.get('visual_review_regeneration_recommended')}",
            f"- Visual review hint reason: {context.get('visual_review_hint_reason') or '—'}",
            f"- Stale visual review: {context.get('stale_visual_review')}",
            f"- Comparison status: {context.get('latest_visual_review_comparison_status') or '—'}",
            "",
            "## Sample entries",
            "",
        ]
    )
    entries = sample_set.get("entries") or []
    if not entries:
        lines.append(
            "No sample entries selected — generate a visual review manifest first with "
            "`make mrms-visual-review`."
        )
    else:
        lines.append(
            "| Timestamp | Layer | Tile mode | Primary path | Missing | Selection reason |"
        )
        lines.append("|---|---|---|---|---|---|")
        for entry in entries:
            missing = entry.get("missing_artifacts") or []
            missing_cell = ", ".join(missing[:2]) if missing else "—"
            lines.append(
                f"| {entry.get('timestamp')} | {entry.get('layer')} | {entry.get('tile_mode')} | "
                f"`{entry.get('primary_artifact_path') or '—'}` | {missing_cell} | "
                f"{entry.get('selection_reason')} |"
            )

    lines.extend(
        [
            "",
            "## Suggested local commands",
            "",
            f"```bash\n{sample_set.get('suggested_command') or SUGGESTED_SAMPLE_SET_COMMAND}\n```",
            "",
            f"Regenerate visual review manifest: `{SUGGESTED_VISUAL_REVIEW_COMMAND}`",
            "",
            "## Runbook reference",
            "",
            f"- `{RUNBOOK_PATH}` — MRMS visual review sample-set drilldown",
        ]
    )
    return "\n".join(lines) + "\n"


def save_visual_review_sample_set(
    storage: LocalStorage,
    sample_set: dict[str, Any],
) -> dict[str, Any]:
    json_path = _sample_set_json_path(storage)
    md_path = _sample_set_md_path(storage)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    sample_set = {
        **sample_set,
        "json_path": json_path,
        "markdown_path": md_path,
        "suggested_command": SUGGESTED_SAMPLE_SET_COMMAND,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(sample_set, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(
        build_sample_set_markdown(sample_set),
        encoding="utf-8",
    )
    return sample_set


def load_visual_review_sample_set(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(_sample_set_json_path(storage))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def build_visual_review_sample_set(
    storage: LocalStorage,
    *,
    selection_mode: str = SELECTION_RECOMMENDED,
    limit: int = DEFAULT_SAMPLE_LIMIT,
    timestamps: Optional[list[str]] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    """Build and persist a local visual review sample set from existing manifest."""
    manifest = load_latest_visual_review(storage)
    context = _build_context(storage)
    if manifest is None:
        sample_set = {
            "created_at": _utc_now(),
            "selection_mode": selection_mode,
            "limit": limit,
            "source_visual_review_at": None,
            "source_visual_review_path": None,
            "reason": "no_visual_review_manifest",
            "entries": [],
            "entry_count": 0,
            "context": context,
            "notes": notes,
        }
        return save_visual_review_sample_set(storage, sample_set)

    if selection_mode == SELECTION_EXPLICIT and timestamps:
        entries = select_explicit_sample_entries(
            manifest,
            timestamps=timestamps,
            context=context,
        )
        reason = "explicit_timestamps"
    else:
        entries = select_recommended_sample_entries(
            manifest,
            limit=limit,
            context=context,
        )
        reason = "recommended_selection"

    if notes:
        for entry in entries:
            entry["notes"] = notes

    sample_set = {
        "created_at": _utc_now(),
        "selection_mode": selection_mode,
        "limit": max(1, min(limit, MAX_SAMPLE_LIMIT)),
        "source_visual_review_at": manifest.get("created_at"),
        "source_visual_review_path": manifest.get("json_path"),
        "reason": reason,
        "entries": entries,
        "entry_count": len(entries),
        "context": context,
        "notes": notes,
    }
    return save_visual_review_sample_set(storage, sample_set)


def compact_visual_review_sample_set(storage: LocalStorage) -> dict[str, Any]:
    latest = load_visual_review_sample_set(storage)
    empty = {
        "available": False,
        "created_at": None,
        "selection_mode": None,
        "entry_count": 0,
        "limit": DEFAULT_SAMPLE_LIMIT,
        "json_path": _sample_set_json_path(storage),
        "markdown_path": _sample_set_md_path(storage),
        "source_visual_review_at": None,
        "source_visual_review_path": None,
        "reason": "no_sample_set",
        "suggested_command": SUGGESTED_SAMPLE_SET_COMMAND,
        "context": _build_context(storage),
        **_safety_fields(),
    }
    if latest is None:
        return empty
    return {
        "available": True,
        "created_at": latest.get("created_at"),
        "selection_mode": latest.get("selection_mode"),
        "entry_count": int(latest.get("entry_count", 0)),
        "limit": latest.get("limit"),
        "json_path": latest.get("json_path") or _sample_set_json_path(storage),
        "markdown_path": latest.get("markdown_path") or _sample_set_md_path(storage),
        "source_visual_review_at": latest.get("source_visual_review_at"),
        "source_visual_review_path": latest.get("source_visual_review_path"),
        "reason": latest.get("reason"),
        "suggested_command": latest.get("suggested_command") or SUGGESTED_SAMPLE_SET_COMMAND,
        "context": latest.get("context") or _build_context(storage),
        **_safety_fields(),
    }


def build_visual_review_sample_set_payload(storage: LocalStorage) -> dict[str, Any]:
    latest = load_visual_review_sample_set(storage)
    return {
        **_safety_fields(),
        "latest": latest,
        "compact": compact_visual_review_sample_set(storage),
    }
