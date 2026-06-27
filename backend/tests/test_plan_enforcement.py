from backend.app.models import RadarFile
from backend.app.models.radar_file import PROCESSED_STATUS_PROCESSED
from backend.app.services.processor import process_pending_frames


def test_times_filtered_by_free_plan(client):
    times = client.get("/api/times?layer=mrms_reflectivity&plan=free").json()
    assert times == ["2026-06-27T20:20:00Z"]


def test_times_default_plan_is_pro(client):
    times = client.get("/api/times?layer=mrms_reflectivity").json()
    assert len(times) == 5


def test_times_pro_includes_all_demo(client):
    times = client.get("/api/times?layer=mrms_reflectivity&plan=pro").json()
    assert len(times) == 5


def test_times_business_includes_all_demo(client):
    times = client.get("/api/times?layer=mrms_reflectivity&plan=business").json()
    assert len(times) == 5


def test_pro_allows_more_history_than_free(client, db_session):
    db_session.add(
        RadarFile(
            product_id="mrms_reflectivity",
            timestamp="2026-06-01T12:00:00Z",
            raw_path="data/raw/demo/mrms_reflectivity/old.grib2.stub",
            processed_status=PROCESSED_STATUS_PROCESSED,
            source="demo",
        )
    )
    db_session.commit()

    free_times = client.get("/api/times?layer=mrms_reflectivity&plan=free").json()
    pro_times = client.get("/api/times?layer=mrms_reflectivity&plan=pro").json()

    assert "2026-06-01T12:00:00Z" not in free_times
    assert "2026-06-01T12:00:00Z" in pro_times
    assert len(pro_times) > len(free_times)


def test_latest_respects_plan(client):
    latest_free = client.get("/api/latest?layer=mrms_reflectivity&plan=free").json()
    latest_pro = client.get("/api/latest?layer=mrms_reflectivity&plan=pro").json()

    assert latest_free["timestamp"] == "2026-06-27T20:20:00Z"
    assert latest_pro["timestamp"] == "2026-06-27T20:20:00Z"


def test_invalid_plan_returns_400(client):
    res = client.get("/api/times?layer=mrms_reflectivity&plan=not-a-plan")
    assert res.status_code == 400
    assert res.json()["detail"]["error"] == "invalid_plan"


def test_access_plans_endpoint(client):
    res = client.get("/api/access/plans")
    assert res.status_code == 200
    plans = {plan["id"]: plan for plan in res.json()}
    assert plans["free"]["history_days"] == 0
    assert plans["business"]["history_days"] is None


def test_access_current_endpoint(client):
    res = client.get("/api/access/current?plan=basic")
    assert res.status_code == 200
    body = res.json()
    assert body["plan"] == "basic"
    assert body["reference_latest"] == "2026-06-27T20:20:00Z"
    assert "Last 7 days" in body["history_limit_label"]


def test_tile_403_when_outside_plan(client, db_session, storage):
    process_pending_frames(db_session, storage)

    res = client.get("/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png?plan=free")
    assert res.status_code == 403
    detail = res.json()["detail"]
    assert detail["error"] == "plan_limit_exceeded"
    assert detail["plan"] == "free"


def test_tile_200_for_allowed_plan(client, db_session, storage):
    process_pending_frames(db_session, storage)

    res = client.get("/tiles/mrms_reflectivity/2026-06-27T20:20:00Z/0/0/0.png?plan=free")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
