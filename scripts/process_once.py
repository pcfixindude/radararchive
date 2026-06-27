"""Run one processor pass with raw-kind aware placeholder handling (no real GRIB2 decode)."""

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.services.processor import process_pending_frames
from backend.app.services.storage import LocalStorage


def main() -> None:
    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)
    try:
        if catalog_is_empty(session):
            seed_demo_catalog(session, storage=storage)

        result = process_pending_frames(session, storage)
        print("Processor run complete (placeholder only — no GRIB2 decode):")
        print(f"  processed_count: {result.processed_count}")
        print(f"  skipped_count: {result.skipped_count}")
        print(f"  placeholder_processed_count: {result.placeholder_processed_count}")
        print(f"  placeholder_for_real_raw_count: {result.placeholder_for_real_raw_count}")
        print(f"  real_decode_pending_count: {result.real_decode_pending_count}")
        print(f"  failed_count: {result.failed_count}")
        for item in result.results:
            if not item.created:
                continue
            print(
                f"  - {item.outcome} {item.raw_kind} {item.product_id} @ {item.timestamp}"
                f" -> {item.processed_path} [{item.processed_status}]"
            )
    finally:
        session.close()


if __name__ == "__main__":
    main()
