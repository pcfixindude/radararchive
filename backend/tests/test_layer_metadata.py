def test_layers_include_tile_metadata(client):
    res = client.get("/api/layers")
    assert res.status_code == 200
    mrms = next(layer for layer in res.json() if layer["id"] == "mrms_reflectivity")
    assert mrms["tile_support"] is True
    assert mrms["placeholder"] is True
    assert mrms["bounds"] == [-125.0, 24.0, -66.0, 50.0]
    assert mrms["minzoom"] == 3
    assert mrms["maxzoom"] == 8

    hrrr = next(layer for layer in res.json() if layer["id"] == "hrrr_wind")
    assert hrrr["tile_support"] is False
    assert hrrr["placeholder"] is False


def test_times_processed_only_filters_unprocessed(client):
    all_times = client.get("/api/times?layer=mrms_reflectivity").json()
    processed_times = client.get("/api/times?layer=mrms_reflectivity&processed_only=true").json()

    assert len(all_times) == 5
    assert processed_times == []


def test_times_processed_only_after_processing(client, db_session, storage):
    from backend.app.services.processor import process_pending_frames

    process_pending_frames(db_session, storage)

    processed_times = client.get("/api/times?layer=mrms_reflectivity&processed_only=true").json()
    assert len(processed_times) == 5
