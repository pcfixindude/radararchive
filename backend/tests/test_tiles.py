from backend.app.services.processor import process_pending_frames
from backend.app.services.tile_service import generate_placeholder_tile_png


def test_tile_png_generation():
    png = generate_placeholder_tile_png(z=1, x=2, y=3)
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(png) > 100


def test_tile_endpoint_returns_png_for_processed_timestamp(client, db_session, storage):
    process_pending_frames(db_session, storage)

    timestamp = "2026-06-27T20:00:00Z"
    response = client.get(f"/tiles/mrms_reflectivity/{timestamp}/0/0/0.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert response.headers.get("x-radararchive-tile") == "placeholder"


def test_tile_endpoint_404_for_unprocessed_timestamp(client):
    response = client.get("/tiles/mrms_reflectivity/2099-01-01T00:00:00Z/0/0/0.png")
    assert response.status_code == 404


def test_tile_endpoint_404_for_unknown_layer(client, db_session, storage):
    process_pending_frames(db_session, storage)

    response = client.get("/tiles/unknown_layer/2026-06-27T20:00:00Z/0/0/0.png")
    assert response.status_code == 404


def test_tile_endpoint_404_for_unavailable_layer(client, db_session, storage):
    process_pending_frames(db_session, storage)

    response = client.get("/tiles/hrrr_wind/2026-06-27T20:00:00Z/0/0/0.png")
    assert response.status_code == 404
