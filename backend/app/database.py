from collections.abc import Generator
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.config import settings


class Base(DeclarativeBase):
    pass


def _ensure_sqlite_parent() -> None:
    sqlite_path = settings.sqlite_path
    if sqlite_path is not None:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _ensure_sqlite_parent()
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(settings.database_url, connect_args=connect_args)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal


def init_db() -> None:
    from backend.app import models  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _ensure_radar_file_columns(engine)


def _ensure_radar_file_columns(engine) -> None:
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "radar_files" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("radar_files")}
    statements = []
    if "processed_status" not in columns:
        statements.append(
            "ALTER TABLE radar_files ADD COLUMN processed_status VARCHAR NOT NULL DEFAULT 'pending'"
        )
    if "processed_at" not in columns:
        statements.append("ALTER TABLE radar_files ADD COLUMN processed_at VARCHAR")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def reset_engine(database_url: Optional[str] = None) -> None:
    """Reset cached engine/session factory (used by tests)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
    if database_url is not None:
        settings.database_url = database_url


def configure_test_database(db_path: Path) -> sessionmaker[Session]:
    reset_engine(f"sqlite:///{db_path}")
    _ensure_sqlite_parent()
    init_db()
    return get_session_factory()
