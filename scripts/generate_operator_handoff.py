"""Generate local MRMS operator handoff checklist (does NOT verify MRMS)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.mrms_operator_handoff import generate_operator_handoff
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate local operator handoff checklist (Phase 31 — review only)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print JSON metadata")
    args = parser.parse_args()

    print(
        "WARNING: Operator handoff checklist is local review only — NOT verified MRMS. "
        "Does not enable production rendering.",
        file=sys.stderr,
    )

    init_db()
    session_factory = get_session_factory()
    storage = LocalStorage(settings.local_storage_root)

    with session_factory() as session:
        record = generate_operator_handoff(session, storage)

    if args.json_report:
        print(json.dumps(record, indent=2, sort_keys=True))
        return

    print("Operator handoff checklist generated (local review only — NOT verified MRMS):")
    print(f"  created_at: {record.get('created_at')}")
    print(f"  markdown_path: {record.get('markdown_path')}")
    print(f"  json_path: {record.get('json_path')}")
    print(f"  question_count: {record.get('question_count')}")
    print(f"  verified_mrms: {record.get('verified_mrms')}")
    print(f"  does_not_enable_production: {record.get('does_not_enable_production')}")


if __name__ == "__main__":
    main()
