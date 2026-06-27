from backend.app.services import catalog as catalog_service


def test_list_layers_from_db(db_session):
    layers = catalog_service.list_layers(db_session)
    layer_ids = {layer.id for layer in layers}
    assert layer_ids == {"mrms_reflectivity", "nws_warnings", "hrrr_wind", "wpc_fronts"}


def test_list_times_from_db(db_session):
    times = catalog_service.list_times(db_session, "mrms_reflectivity")
    assert times == [
        "2026-06-27T20:00:00Z",
        "2026-06-27T20:05:00Z",
        "2026-06-27T20:10:00Z",
        "2026-06-27T20:15:00Z",
        "2026-06-27T20:20:00Z",
    ]


def test_latest_timestamp_from_db(db_session):
    assert catalog_service.latest_timestamp(db_session, "mrms_reflectivity") == "2026-06-27T20:20:00Z"
    assert catalog_service.latest_timestamp(db_session, "hrrr_wind") is None
