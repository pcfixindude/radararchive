"""Real MRMS one-frame smoke test (intentionally limited, experimental prototype)."""

from __future__ import annotations

import argparse
import json
import sys

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.services.scheduled_validation import (
    SMOKE_TEST_COUNT,
    SMOKE_TEST_MAX_ZOOM,
    run_real_mrms_smoke_test,
)
from backend.app.services.storage import LocalStorage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Real MRMS smoke test: count=1, zoom=0 only (Phase 24 prototype)."
    )
    parser.add_argument("--json-report", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    print(
        "WARNING: Real MRMS smoke test may download NOAA data. "
        "NOT verified MRMS production output.",
        file=sys.stderr,
    )
    print(
        f"Limits: count={SMOKE_TEST_COUNT}, min_zoom={SMOKE_TEST_MAX_ZOOM}, "
        f"max_zoom={SMOKE_TEST_MAX_ZOOM}, mark_catalog=false\n",
        file=sys.stderr,
    )

    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)
    try:
        report = run_real_mrms_smoke_test(session, storage)
    finally:
        session.close()

    if args.json_report:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(f"Smoke test success={report.success} exit_code={report.exit_code}")
        print(f"  source_mode: {report.source_mode}")
        print(f"  verified_mrms: {report.verified_mrms}")
        for step in report.steps:
            print(f"  - {step.name}: {step.status} ({step.elapsed_seconds:.4f}s)")

    raise SystemExit(report.exit_code)


if __name__ == "__main__":
    main()
