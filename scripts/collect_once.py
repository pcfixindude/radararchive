"""Run one simulated MRMS reflectivity collection (stub, not real NOAA data)."""

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.services.collector import collect_mrms_reflectivity_once
from backend.app.services.storage import LocalStorage


def main() -> None:
    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)
    try:
        if catalog_is_empty(session):
            seed_demo_catalog(session)

        result = collect_mrms_reflectivity_once(session, storage)
        status = "created" if result.created else "already existed"
        print(f"Collector stub run complete ({status}):")
        print(f"  layer: {result.layer_id}")
        print(f"  product: {result.product_id}")
        print(f"  timestamp: {result.timestamp}")
        print(f"  source: {result.source}")
        print(f"  raw_path: {result.raw_path}")
        print(f"  processed_path: {result.processed_path}")
        if result.raw_sha256:
            print(f"  raw_sha256: {result.raw_sha256}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
