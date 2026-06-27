"""Create or reset the local SQLite catalog with demo rows."""

from backend.app.config import settings
from backend.app.database import get_session_factory, init_db
from backend.app.demo.seed import seed_demo_catalog
from backend.app.services.storage import LocalStorage


def main(*, reset: bool = False) -> None:
    init_db()
    session = get_session_factory()()
    storage = LocalStorage(settings.local_storage_root)
    try:
        counts = seed_demo_catalog(session, reset=reset, storage=storage)
    finally:
        session.close()

    print("Demo catalog seeded into SQLite (stub data, not real NOAA/MRMS downloads):")
    for key, value in counts.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
