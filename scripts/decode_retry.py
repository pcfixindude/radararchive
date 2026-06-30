"""Decode retry — decode latest MRMS and rerun local render pipeline."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.decode_retry import run_decode_retry
from backend.app.services.decoder_setup import SUGGESTED_DECODE_RETRY_COMMAND
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Decode latest MRMS candidate and rerun local render pipeline."
    )
    parser.add_argument("--json-report", action="store_true", help="Print full JSON report")
    args = parser.parse_args()

    print(
        "WARNING: Decode retry is local prototype only — NOT verified MRMS. "
        "Production tile serving remains off.",
        file=sys.stderr,
    )

    storage = LocalStorage(settings.local_storage_root)
    init_db()
    session = get_session_factory()()
    try:
        report = run_decode_retry(session, storage)
        session.commit()
    finally:
        session.close()

    if args.json_report:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print("Decode retry (local prototype only — NOT verified MRMS):")
    print(f"  decode_retry_status: {report.get('decode_retry_status')}")
    print(f"  decode_success: {report.get('decode_success')}")
    print(f"  pipeline_status: {report.get('pipeline_status')}")
    print(f"  render_mode: {report.get('render_mode')}")
    print(f"  produced_decoded_preview: {report.get('produced_decoded_preview')}")
    print(f"  blocker: {report.get('blocker')}")
    decode = report.get("decode") or {}
    if decode:
        print(f"  decoder_used: {decode.get('decoder_used')}")
        print(f"  decode_grid: {decode.get('width')} x {decode.get('height')}")
        print(f"  decode_output_dir: {decode.get('output_dir')}")
    for path in report.get("preview_paths") or []:
        print(f"  preview_path: {path}")
    for item in report.get("errors") or []:
        print(f"  error: {item}")
    print(f"  next_phase_recommendation: {report.get('next_phase_recommendation')}")
    print(f"  markdown_path: {report.get('markdown_path')}")
    print(f"  suggested_command: {SUGGESTED_DECODE_RETRY_COMMAND}")


if __name__ == "__main__":
    main()
