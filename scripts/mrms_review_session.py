"""Record a local MRMS proof review session (does NOT verify MRMS)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.services.mrms_review_session import (
    ReviewSessionValidationError,
    create_review_session_record,
)
from backend.app.services.mrms_review_session_export import try_export_after_review_session_create
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record local MRMS proof review session (Phase 41 — local review only)."
    )
    parser.add_argument("--operator", "--operator-name", dest="operator_name", help="Operator name")
    parser.add_argument("--initials", help="Operator initials")
    parser.add_argument("--notes", help="Session review notes")
    parser.add_argument(
        "--checklist-reviewed",
        help="Comma-separated checklist items reviewed (from operator handoff checklist)",
    )
    parser.add_argument(
        "--accepted-limitations",
        action="store_true",
        help="Acknowledge this does not verify MRMS (required)",
    )
    parser.add_argument("--limitations-text", help="Optional accepted limitations text")
    parser.add_argument(
        "--export-after-create",
        "--export",
        dest="export_after_create",
        action="store_true",
        help="Export Markdown summary immediately after creating this session",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON record")
    args = parser.parse_args()

    print(
        "WARNING: Review session is local only — does NOT verify MRMS, clear alerts, "
        "or enable production rendering.",
        file=sys.stderr,
    )

    checklist = []
    if args.checklist_reviewed:
        checklist = [part.strip() for part in args.checklist_reviewed.split(",") if part.strip()]

    storage = LocalStorage(settings.local_storage_root)
    try:
        record = create_review_session_record(
            storage,
            operator_name=args.operator_name,
            operator_initials=args.initials,
            session_notes=args.notes,
            checklist_items_reviewed=checklist,
            accepted_limitations=args.accepted_limitations,
            accepted_limitations_text=args.limitations_text,
        )
    except ReviewSessionValidationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    export_status: dict = {}
    if args.export_after_create:
        export_status = try_export_after_review_session_create(storage, record)

    if args.json:
        output = {"review_session": record, **export_status}
        print(json.dumps(output, indent=2, sort_keys=True))
        return

    print("MRMS proof review session recorded (local review only — NOT verified MRMS):")
    print(f"  session_id: {record.get('session_id')}")
    print(f"  created_at: {record.get('created_at')}")
    print(f"  operator: {record.get('operator_name') or record.get('operator_initials')}")
    print(f"  escalation_level: {record.get('latest_escalation_level')}")
    print(f"  open_attention_count: {record.get('open_attention_count', 0)}")
    print(f"  verified_mrms: {record.get('verified_mrms')}")
    if args.export_after_create:
        if export_status.get("export_generated"):
            print(f"  export_path: {export_status.get('export_path')}")
            print(f"  export_metadata_path: {export_status.get('export_metadata_path')}")
        elif export_status.get("export_error"):
            print(f"  export_error: {export_status.get('export_error')}", file=sys.stderr)


if __name__ == "__main__":
    main()
