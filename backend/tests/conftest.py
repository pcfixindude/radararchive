import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

os.environ["TESTING"] = "1"

from backend.app.database import configure_test_database, get_db, reset_engine
from backend.app.demo.seed import seed_demo_catalog
from backend.app.main import app
from backend.app.services.storage import LocalStorage


@pytest.fixture()
def storage_root(tmp_path):
    return tmp_path / "storage"


@pytest.fixture()
def storage(storage_root):
    return LocalStorage(storage_root)


@pytest.fixture()
def db_session(tmp_path, storage) -> Session:
    db_path = tmp_path / "test.sqlite"
    session_factory = configure_test_database(db_path)
    session = session_factory()
    seed_demo_catalog(session, storage=storage)
    yield session
    session.close()
    reset_engine()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
