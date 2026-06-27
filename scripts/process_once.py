"""Run one processor pass over pending raw stub frames (stub, not real GRIB2)."""

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
            seed_demo_catalog(session)

        result = process_pending_frames(session, storage)
        print(f"Processor stub run complete:")
        print(f"  processed: {len(result.processed)}")
        print(f"  skipped: {result.skipped}")
        for item in result.processed:
            status = "updated" if not item.created else "processed"
            print(f"  - {status} {item.product_id} @ {item.timestamp} -> {item.processed_path}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
