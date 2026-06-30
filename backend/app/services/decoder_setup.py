"""Decoder setup detection and Mac developer install guidance (optional deps)."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from typing import Any, Callable, Optional

from backend.app.services.grib2_inspector import DecoderAvailability, detect_decoder_availability
from backend.app.services.storage import LocalStorage

SETUP_JSON = "dev/decoder_setup_latest.json"
SETUP_MD = "dev/decoder_setup_latest.md"
OPTIONAL_REQUIREMENTS = "requirements-optional-decoders.txt"

SUGGESTED_CHECK_COMMAND = "make check-decoders"
SUGGESTED_INSTALL_COMMAND = "make install-decoders"
SUGGESTED_DECODE_RETRY_COMMAND = "make decode-retry"


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safety_fields() -> dict[str, Any]:
    return {
        "verified_mrms": False,
        "optional_dependencies_only": True,
        "does_not_enable_production": True,
        "prototype": True,
    }


def decoder_availability_dict(availability: DecoderAvailability) -> dict[str, Any]:
    return {
        "any_decoder": availability.any_decoder,
        "wgrib2": availability.wgrib2,
        "wgrib2_path": availability.wgrib2_path,
        "gdal": availability.gdal,
        "rasterio": availability.rasterio,
        "pygrib": availability.pygrib,
        "cfgrib": availability.cfgrib,
        "summary_message": availability.summary_message(),
        "preferred_decode_path": _preferred_decode_path(availability),
    }


def _preferred_decode_path(availability: DecoderAvailability) -> Optional[str]:
    if availability.rasterio:
        return "rasterio"
    if availability.wgrib2:
        return "wgrib2_bin"
    return None


def mac_setup_instructions() -> list[dict[str, str]]:
    """Documented Mac developer setup steps — does not run installs automatically."""
    return [
        {
            "step": "check",
            "command": SUGGESTED_CHECK_COMMAND,
            "description": "Report wgrib2/GDAL/rasterio availability for this machine.",
        },
        {
            "step": "install_python",
            "command": SUGGESTED_INSTALL_COMMAND,
            "description": (
                "Install rasterio+numpy into the project .venv from "
                f"{OPTIONAL_REQUIREMENTS} (preferred decode path)."
            ),
        },
        {
            "step": "install_wgrib2",
            "command": "# wgrib2 is not in default Homebrew — build from NOAA source or use conda-forge",
            "description": "Optional CLI fallback when rasterio is unavailable.",
        },
        {
            "step": "install_gdal",
            "command": "brew install gdal",
            "description": "Optional system GDAL for other geospatial tooling (not required when rasterio wheels work).",
        },
        {
            "step": "decode",
            "command": 'make decode-grib2 ARGS="--latest-mrms"',
            "description": "Decode latest real MRMS .grib2.gz into data/staging/grib2_decode/.",
        },
        {
            "step": "preview",
            "command": "make mrms-local-render-pipeline",
            "description": "Render local decoded_prototype preview PNG under data/dev/.",
        },
        {
            "step": "retry_all",
            "command": SUGGESTED_DECODE_RETRY_COMMAND,
            "description": "Check decoders, decode latest MRMS, rerun local render pipeline.",
        },
    ]


def gather_decoder_setup_status() -> dict[str, Any]:
    availability = detect_decoder_availability()
    system = platform.system().lower()
    brew_available = shutil.which("brew") is not None
    return {
        "ran_at": _utc_now(),
        "platform": system,
        "brew_available": brew_available,
        "python_executable": sys.executable,
        "decoder": decoder_availability_dict(availability),
        "ready_for_decode": availability.any_decoder,
        "mac_setup_instructions": mac_setup_instructions() if system == "darwin" else [],
        "suggested_check_command": SUGGESTED_CHECK_COMMAND,
        "suggested_install_command": SUGGESTED_INSTALL_COMMAND,
        "suggested_decode_retry_command": SUGGESTED_DECODE_RETRY_COMMAND,
        **_safety_fields(),
    }


def install_decoders_in_venv(
    *,
    requirements_path: str = OPTIONAL_REQUIREMENTS,
    pip_runner: Optional[Callable[..., subprocess.CompletedProcess[str]]] = None,
) -> dict[str, Any]:
    """Install optional decoder Python packages into the active venv only."""
    run = pip_runner or subprocess.run
    command = [sys.executable, "-m", "pip", "install", "-r", requirements_path]
    completed = run(command, capture_output=True, text=True, check=False)
    after = detect_decoder_availability()
    return {
        "ran_at": _utc_now(),
        "install_attempted": True,
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "stdout": (completed.stdout or "").strip(),
        "stderr": (completed.stderr or "").strip(),
        "success": completed.returncode == 0 and after.any_decoder,
        "decoder_after": decoder_availability_dict(after),
        "next_command": SUGGESTED_DECODE_RETRY_COMMAND if after.any_decoder else SUGGESTED_INSTALL_COMMAND,
        **_safety_fields(),
    }


def build_setup_markdown(report: dict[str, Any]) -> str:
    decoder = report.get("decoder") or {}
    lines = [
        "# Decoder setup (local dev)",
        "",
        f"- Ran at: {report.get('ran_at')}",
        f"- Platform: {report.get('platform')}",
        f"- Ready for decode: {report.get('ready_for_decode')}",
        f"- {decoder.get('summary_message')}",
        f"- Preferred decode path: {decoder.get('preferred_decode_path') or 'none'}",
        "",
        "## Tooling status",
        "",
        f"- wgrib2: {decoder.get('wgrib2')} ({decoder.get('wgrib2_path') or 'not found'})",
        f"- gdal (python): {decoder.get('gdal')}",
        f"- rasterio: {decoder.get('rasterio')}",
        f"- pygrib: {decoder.get('pygrib')}",
        f"- cfgrib: {decoder.get('cfgrib')}",
        "",
        "## Mac setup",
        "",
    ]
    for item in report.get("mac_setup_instructions") or []:
        lines.append(f"- **{item['step']}**: {item['description']}")
        lines.append(f"  - `{item['command']}`")
    if report.get("install_result"):
        install = report["install_result"]
        lines.extend(["", "## Install attempt", ""])
        lines.append(f"- success: {install.get('success')}")
        lines.append(f"- command: `{install.get('command')}`")
        if install.get("stderr"):
            lines.append(f"- stderr: {install['stderr'][:500]}")
    lines.append("")
    return "\n".join(lines)


def save_decoder_setup_report(
    storage: LocalStorage,
    report: dict[str, Any],
) -> dict[str, Any]:
    json_path = storage.normalize_path(SETUP_JSON)
    md_path = storage.normalize_path(SETUP_MD)
    storage.ensure_directories(json_path.rsplit("/", 1)[0])
    report = {
        **report,
        "json_path": json_path,
        "markdown_path": md_path,
        **_safety_fields(),
    }
    storage.absolute_path(json_path).write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    storage.absolute_path(md_path).write_text(build_setup_markdown(report), encoding="utf-8")
    return report


def load_decoder_setup_report(storage: LocalStorage) -> Optional[dict[str, Any]]:
    abs_path = storage.absolute_path(storage.normalize_path(SETUP_JSON))
    if not abs_path.is_file():
        return None
    try:
        data = json.loads(abs_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def compact_decoder_setup(storage: LocalStorage) -> dict[str, Any]:
    latest = load_decoder_setup_report(storage)
    if latest is None:
        status = gather_decoder_setup_status()
        return {
            "available": False,
            "ready_for_decode": status["ready_for_decode"],
            "decoder": status["decoder"],
            "suggested_install_command": SUGGESTED_INSTALL_COMMAND,
            "suggested_decode_retry_command": SUGGESTED_DECODE_RETRY_COMMAND,
            **_safety_fields(),
        }
    return {
        "available": True,
        "ready_for_decode": latest.get("ready_for_decode"),
        "decoder": latest.get("decoder"),
        "ran_at": latest.get("ran_at"),
        "json_path": latest.get("json_path"),
        "markdown_path": latest.get("markdown_path"),
        "suggested_install_command": SUGGESTED_INSTALL_COMMAND,
        "suggested_decode_retry_command": SUGGESTED_DECODE_RETRY_COMMAND,
        **_safety_fields(),
    }
