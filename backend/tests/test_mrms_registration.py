from backend.app.services.mrms_discovery import register_discovered_files
from backend.app.sources.mrms import MrmsDiscoveredFile, stub_discoveries


def test_register_discovered_files_creates_rows(db_session):
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 2)
    result = register_discovered_files(db_session, discoveries)

    assert result.created == 2
    assert result.skipped == 0


def test_register_discovered_files_is_idempotent(db_session):
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 2)
    first = register_discovered_files(db_session, discoveries)
    second = register_discovered_files(db_session, discoveries)

    assert first.created == 2
    assert second.created == 0
    assert second.skipped == 2


def test_register_skips_duplicate_timestamp(db_session):
    discoveries = stub_discoveries("MRMS_ReflectivityAtLowestAltitude", 1)
    first = register_discovered_files(db_session, discoveries)

    duplicate = MrmsDiscoveredFile(
        product=discoveries[0].product,
        timestamp=discoveries[0].timestamp,
        object_key="different/key.grib2.gz",
        source_url="https://example.com/different/key.grib2.gz",
        file_name="different.grib2.gz",
        size_bytes=100,
        catalog_product_id="mrms_reflectivity",
    )
    second = register_discovered_files(db_session, [duplicate])

    assert first.created == 1
    assert second.skipped == 1


def test_mrms_sources_api_stub_mode(client):
    res = client.get("/api/sources/mrms/latest?product=MRMS_ReflectivityAtLowestAltitude&limit=3")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 3
    assert body["mode"] == "stub"
    assert body["items"][0]["source_provider"] == "noaa_aws"
