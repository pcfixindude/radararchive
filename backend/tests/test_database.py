from backend.app.database import Base, configure_test_database, init_db
from backend.app.demo.seed import catalog_is_empty, seed_demo_catalog
from backend.app.models import AccessPlan, Layer, Product, RadarFile


def test_database_creation(tmp_path):
    db_path = tmp_path / "create.sqlite"
    configure_test_database(db_path)
    init_db()

    assert db_path.exists()
    assert "layers" in Base.metadata.tables
    assert "products" in Base.metadata.tables
    assert "radar_files" in Base.metadata.tables
    assert "access_plans" in Base.metadata.tables


def test_seed_demo_data(tmp_path):
    db_path = tmp_path / "seed.sqlite"
    session_factory = configure_test_database(db_path)
    session = session_factory()

    assert catalog_is_empty(session)
    counts = seed_demo_catalog(session)
    assert counts["layers"] == 4
    assert counts["products"] == 1
    assert counts["radar_files"] == 5
    assert counts["access_plans"] == 4

    mrms = session.get(Layer, "mrms_reflectivity")
    assert mrms is not None
    assert mrms.source == "demo"

    frame = session.query(RadarFile).filter(RadarFile.timestamp == "2026-06-27T20:20:00Z").one()
    assert frame.source == "demo"
    assert frame.raw_path.startswith("data/raw/demo/")
    assert frame.processed_path.startswith("data/processed/demo/")
    assert frame.processed_status == "pending"
