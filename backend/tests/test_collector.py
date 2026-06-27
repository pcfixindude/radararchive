from backend.app.models import RadarFile
from backend.app.services.catalog import latest_timestamp, list_times
from backend.app.services.collector import collect_mrms_reflectivity_once
from backend.app.services.storage import LocalStorage


def test_collector_creates_catalog_row_and_files(db_session, tmp_path):
    storage = LocalStorage(tmp_path)
    before_count = db_session.query(RadarFile).count()

    result = collect_mrms_reflectivity_once(db_session, storage)

    assert result.created is True
    assert result.source == "collector_stub"
    assert result.timestamp == "2026-06-27T20:25:00Z"
    assert db_session.query(RadarFile).count() == before_count + 1
    assert storage.path_exists(result.raw_path)
    assert result.processed_path.endswith(".png.stub")
    assert result.raw_sha256 is not None


def test_collector_duplicate_does_not_create_second_row(db_session, tmp_path):
    storage = LocalStorage(tmp_path)
    first = collect_mrms_reflectivity_once(db_session, storage, timestamp="2026-06-27T20:30:00Z")
    second = collect_mrms_reflectivity_once(db_session, storage, timestamp="2026-06-27T20:30:00Z")

    assert first.created is True
    assert second.created is False
    assert (
        db_session.query(RadarFile)
        .filter(
            RadarFile.product_id == "mrms_reflectivity",
            RadarFile.timestamp == "2026-06-27T20:30:00Z",
        )
        .count()
        == 1
    )


def test_collector_updates_latest_timestamp(db_session, tmp_path):
    storage = LocalStorage(tmp_path)
    result = collect_mrms_reflectivity_once(db_session, storage)

    assert latest_timestamp(db_session, "mrms_reflectivity") == result.timestamp
    times = list_times(db_session, "mrms_reflectivity")
    assert times[-1] == result.timestamp


def test_collector_latest_visible_via_api(client, db_session, tmp_path):
    storage = LocalStorage(tmp_path)
    result = collect_mrms_reflectivity_once(db_session, storage)

    response = client.get("/api/latest?layer=mrms_reflectivity")
    assert response.status_code == 200
    body = response.json()
    assert body["timestamp"] == result.timestamp

    times_response = client.get("/api/times?layer=mrms_reflectivity")
    assert result.timestamp in times_response.json()
