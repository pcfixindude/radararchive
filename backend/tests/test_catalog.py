from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_layers():
    res = client.get('/api/layers')
    assert res.status_code == 200
    layers = res.json()
    assert any(layer['id'] == 'mrms_reflectivity' for layer in layers)

def test_times():
    res = client.get('/api/times?layer=mrms_reflectivity')
    assert res.status_code == 200
    assert len(res.json()) > 0


def test_latest():
    res = client.get('/api/latest?layer=mrms_reflectivity')
    assert res.status_code == 200
    body = res.json()
    assert body['layer'] == 'mrms_reflectivity'
    assert body['timestamp'] is not None


def test_layers_marked_demo():
    res = client.get('/api/layers')
    layers = res.json()
    mrms = next(layer for layer in layers if layer['id'] == 'mrms_reflectivity')
    assert mrms['source'] == 'demo'
