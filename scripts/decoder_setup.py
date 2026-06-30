"""Decoder setup check and optional venv install guidance."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.decoder_setup import (
    SUGGESTED_CHECK_COMMAND,
    SUGGESTED_DECODE_RETRY_COMMAND,
    SUGGESTED_INSTALL_COMMAND,
    gather_decoder_setup_status,
    install_decoders_in_venv,
    save_decoder_setup_report,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(description="Check optional GRIB2 decoder tooling (local dev).")
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install rasterio+numpy into active .venv from requirements-optional-decoders.txt",
    )
    args = parser.parse_args()

    storage = LocalStorage(settings.local_storage_root)
    report = gather_decoder_setup_status()

    if args.install:
        report["install_result"] = install_decoders_in_venv()
        report["ready_for_decode"] = report["install_result"]["decoder_after"]["any_decoder"]
        report["decoder"] = report["install_result"]["decoder_after"]

    report = save_decoder_setup_report(storage, report)

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    decoder = report.get("decoder") or {}
    print("Decoder setup (optional local dev dependencies):")
    print(f"  ready_for_decode: {report.get('ready_for_decode')}")
    print(f"  {decoder.get('summary_message')}")
    print(f"  preferred_decode_path: {decoder.get('preferred_decode_path')}")
    print(f"  wgrib2: {decoder.get('wgrib2')} ({decoder.get('wgrib2_path') or 'not found'})")
    print(f"  rasterio: {decoder.get('rasterio')}")
    print(f"  gdal: {decoder.get('gdal')}")
    if report.get("install_result"):
        install = report["install_result"]
        print(f"  install_success: {install.get('success')}")
        if install.get("stderr"):
            print(f"  install_stderr: {install['stderr'][:300]}")
    if not report.get("ready_for_decode"):
        print(f"  suggested_install: {SUGGESTED_INSTALL_COMMAND}")
    print(f"  suggested_decode_retry: {SUGGESTED_DECODE_RETRY_COMMAND}")
    print(f"  markdown_path: {report.get('markdown_path')}")
    print(f"  suggested_command: {SUGGESTED_CHECK_COMMAND}")


if __name__ == "__main__":
    main()
