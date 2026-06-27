def test_layers(client):
    res = client.get("/api/layers")
    assert res.status_code == 200
    layers = res.json()
    assert any(layer["id"] == "mrms_reflectivity" for layer in layers)


def test_times(client):
    res = client.get("/api/times?layer=mrms_reflectivity")
    assert res.status_code == 200
    times = res.json()
    assert len(times) == 5
    assert times[0] == "2026-06-27T20:00:00Z"
    assert times[-1] == "2026-06-27T20:20:00Z"


def test_latest(client):
    res = client.get("/api/latest?layer=mrms_reflectivity")
    assert res.status_code == 200
    body = res.json()
    assert body["layer"] == "mrms_reflectivity"
    assert body["timestamp"] == "2026-06-27T20:20:00Z"


def test_layers_marked_demo(client):
    res = client.get("/api/layers")
    layers = res.json()
    mrms = next(layer for layer in layers if layer["id"] == "mrms_reflectivity")
    assert mrms["source"] == "demo"


def test_unavailable_layer_returns_empty_times(client):
    res = client.get("/api/times?layer=hrrr_wind")
    assert res.status_code == 200
    assert res.json() == []
