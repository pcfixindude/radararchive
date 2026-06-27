"""GRIB2 inspection/evaluation spike — metadata only, no production rendering."""

from __future__ import annotations

import gzip
import importlib.util
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Protocol

from backend.app.services.raw_file_classifier import (
    RAW_KIND_DEMO_SEEDED_STUB,
    RAW_KIND_MRMS_DOWNLOAD_STUB,
    RAW_KIND_MRMS_REAL_GRIB2,
    RAW_KIND_UNKNOWN,
    is_real_grib2_raw_kind,
)
from backend.app.services.storage import LocalStorage

GRIB_MAGIC = b"GRIB"
GZIP_MAGIC = b"\x1f\x8b"


class Grib2InspectError(Exception):
    """Raised when inspection cannot proceed."""


@dataclass(frozen=True)
class DecoderAvailability:
    wgrib2: bool
    wgrib2_path: Optional[str]
    gdal: bool
    rasterio: bool
    pygrib: bool
    cfgrib: bool

    @property
    def any_decoder(self) -> bool:
        return self.wgrib2 or self.gdal or self.rasterio or self.pygrib or self.cfgrib

    def summary_message(self) -> str:
        available = []
        if self.wgrib2:
            available.append(f"wgrib2 ({self.wgrib2_path})")
        if self.gdal:
            available.append("gdal (python)")
        if self.rasterio:
            available.append("rasterio")
        if self.pygrib:
            available.append("pygrib")
        if self.cfgrib:
            available.append("cfgrib")
        if available:
            return "Available decoders: " + ", ".join(available)
        return (
            "No GRIB2 decoder tools detected. Install wgrib2 for CLI inspection, "
            "or optional Python packages (rasterio/GDAL, pygrib, cfgrib) for future phases."
        )


@dataclass
class Grib2InspectResult:
    raw_path: str
    raw_kind: str
    file_exists: bool
    inspectable: bool
    compressed_size_bytes: Optional[int] = None
    decompressed_size_bytes: Optional[int] = None
    staged_grib2_path: Optional[str] = None
    has_grib_magic: Optional[bool] = None
    decoder_used: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    error: Optional[str] = None


class Wgrib2Runner(Protocol):
    def __call__(self, command: list[str], *, timeout: float) -> subprocess.CompletedProcess[str]: ...


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, AttributeError, ValueError):
        return False


def detect_decoder_availability(
    *,
    which: Callable[[str], Optional[str]] = shutil.which,
) -> DecoderAvailability:
    wgrib2_path = which("wgrib2")
    return DecoderAvailability(
        wgrib2=wgrib2_path is not None,
        wgrib2_path=wgrib2_path,
        gdal=_module_available("osgeo.gdal"),
        rasterio=_module_available("rasterio"),
        pygrib=_module_available("pygrib"),
        cfgrib=_module_available("cfgrib"),
    )


def classify_raw_path(raw_path: str) -> str:
    """Classify a local raw path without a catalog row."""
    lowered = raw_path.lower()
    if "/raw/demo/" in lowered or lowered.endswith(".grib2.stub") and "/demo/" in lowered:
        return RAW_KIND_DEMO_SEEDED_STUB
    if lowered.endswith(".stub"):
        return RAW_KIND_MRMS_DOWNLOAD_STUB
    if lowered.endswith(".grib2.gz"):
        return RAW_KIND_MRMS_REAL_GRIB2
    if lowered.endswith(".grib2"):
        return RAW_KIND_MRMS_REAL_GRIB2
    return RAW_KIND_UNKNOWN


def is_inspectable_grib2_path(raw_path: str, raw_kind: Optional[str] = None) -> bool:
    kind = raw_kind or classify_raw_path(raw_path)
    return is_real_grib2_raw_kind(kind) or raw_path.lower().endswith(".grib2")


def build_wgrib2_inventory_command(
    grib_path: str,
    *,
    wgrib2_bin: str = "wgrib2",
) -> list[str]:
    """Build wgrib2 inventory command for evaluation/spike use."""
    return [wgrib2_bin, "-s", grib_path]


def _default_wgrib2_runner(command: list[str], *, timeout: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def inspect_with_wgrib2(
    grib_path: str,
    *,
    wgrib2_bin: str = "wgrib2",
    timeout: float = 30.0,
    runner: Optional[Wgrib2Runner] = None,
) -> dict:
    command = build_wgrib2_inventory_command(grib_path, wgrib2_bin=wgrib2_bin)
    run = runner or _default_wgrib2_runner
    completed = run(command, timeout=timeout)
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        raise Grib2InspectError(f"wgrib2 failed (exit {completed.returncode}): {stderr or 'unknown error'}")
    inventory = (completed.stdout or "").strip()
    lines = [line for line in inventory.splitlines() if line.strip()]
    return {
        "inventory_lines": lines,
        "inventory_text": inventory,
        "message_count": len(lines),
        "command": command,
    }


def _read_gzip_payload(path: Path, max_bytes: int = 256) -> tuple[int, bytes]:
    size = path.stat().st_size
    with gzip.open(path, "rb") as handle:
        prefix = handle.read(max_bytes)
    return size, prefix


def stage_grib2_gz(
    storage: LocalStorage,
    repo_relative_path: str,
    *,
    staging_dir: str = "data/staging/grib2_inspect",
) -> tuple[str, int]:
    """Decompress .grib2.gz into a staging file for decoder tools."""
    source = storage.absolute_path(repo_relative_path)
    if not source.exists():
        raise Grib2InspectError(f"Raw file not found: {repo_relative_path}")

    storage.ensure_directories(staging_dir)
    token = source.stem.replace(".grib2", "")
    staged_name = f"{token}.grib2"
    staged_repo_path = storage.normalize_path(staging_dir, staged_name)
    staged_abs = storage.absolute_path(staged_repo_path)

    with gzip.open(source, "rb") as src, staged_abs.open("wb") as dst:
        decompressed = src.read()
        dst.write(decompressed)

    return staged_repo_path, len(decompressed)


def inspect_grib2_file(
    storage: LocalStorage,
    raw_path: str,
    *,
    decoders: Optional[DecoderAvailability] = None,
    wgrib2_runner: Optional[Wgrib2Runner] = None,
    timeout: float = 30.0,
) -> Grib2InspectResult:
    """Inspect one local raw file; evaluation only — no tile rendering."""
    raw_kind = classify_raw_path(raw_path)
    result = Grib2InspectResult(
        raw_path=raw_path,
        raw_kind=raw_kind,
        file_exists=storage.path_exists(raw_path),
        inspectable=is_inspectable_grib2_path(raw_path, raw_kind),
    )

    if not result.file_exists:
        result.error = f"File not found: {raw_path}"
        return result

    if not result.inspectable:
        result.notes.append("File is a stub/demo placeholder — not a real GRIB2.gz candidate.")
        result.notes.append("GRIB2 inspection applies to downloaded .grib2.gz files only.")
        return result

    abs_path = storage.absolute_path(raw_path)
    result.compressed_size_bytes = abs_path.stat().st_size

    availability = decoders or detect_decoder_availability()
    result.notes.append(availability.summary_message())

    try:
        if raw_path.lower().endswith(".grib2.gz"):
            staged_path, decompressed_size = stage_grib2_gz(storage, raw_path)
            result.staged_grib2_path = staged_path
            result.decompressed_size_bytes = decompressed_size
            grib_target = storage.absolute_path(staged_path)
        else:
            grib_target = abs_path
            result.decompressed_size_bytes = abs_path.stat().st_size

        header = grib_target.read_bytes()[:4]
        result.has_grib_magic = header.startswith(GRIB_MAGIC)
        if not result.has_grib_magic:
            result.notes.append("Decompressed payload does not start with GRIB magic — may be corrupt or non-GRIB.")
    except gzip.BadGzipFile:
        result.error = "File is not valid gzip content."
        return result
    except OSError as exc:
        result.error = f"Failed to read or stage file: {exc}"
        return result

    if not availability.any_decoder:
        result.notes.append(
            "No decoder installed — reported gzip/GRIB magic checks only. "
            "Install wgrib2 or optional Python geospatial packages for richer metadata."
        )
        return result

    if availability.wgrib2:
        try:
            wgrib2_bin = availability.wgrib2_path or "wgrib2"
            metadata = inspect_with_wgrib2(
                str(grib_target),
                wgrib2_bin=wgrib2_bin,
                timeout=timeout,
                runner=wgrib2_runner,
            )
            result.decoder_used = "wgrib2"
            result.metadata = metadata
            return result
        except Grib2InspectError as exc:
            result.notes.append(f"wgrib2 inspection failed: {exc}")

    optional_notes = []
    if availability.rasterio:
        optional_notes.append("rasterio detected — raster decode path reserved for a future phase.")
    if availability.gdal:
        optional_notes.append("GDAL Python bindings detected — not used in this evaluation spike.")
    if availability.pygrib:
        optional_notes.append("pygrib detected — not used in this evaluation spike.")
    if availability.cfgrib:
        optional_notes.append("cfgrib detected — not used in this evaluation spike.")
    result.notes.extend(optional_notes)

    if not result.decoder_used:
        result.notes.append("No working decoder produced metadata for this file.")

    return result


def inspect_fixture_bytes(
    payload: bytes,
    *,
    filename: str = "fixture.grib2.gz",
    decoders: Optional[DecoderAvailability] = None,
    wgrib2_runner: Optional[Wgrib2Runner] = None,
) -> Grib2InspectResult:
    """Inspect in-memory bytes via a temporary file (tests/fixtures)."""
    with tempfile.TemporaryDirectory(prefix="grib2_inspect_") as tmp:
        root = Path(tmp)
        storage = LocalStorage(root)
        raw_path = storage.normalize_path("raw", "mrms", "reflectivity", filename)
        storage.write_bytes(raw_path, payload)
        return inspect_grib2_file(
            storage,
            raw_path,
            decoders=decoders,
            wgrib2_runner=wgrib2_runner,
        )
