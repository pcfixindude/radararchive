"""Tests for validation alert markers and failure grouping (Phase 25)."""

from __future__ import annotations

from backend.app.config import settings
from backend.app.services.validation_alerts import (
    ALERT_OK,
    ALERT_WARNING,
    CAUSE_DECODER_UNAVAILABLE,
    CAUSE_NO_GRIB2_ARTIFACT,
    CAUSE_PRODUCTION_FLAG_OFF,
    build_validation_alert,
    classify_failure_cause,
    group_validation_failures,
    load_validation_alert,
    normalize_cause_message,
    refresh_validation_alert,
    save_validation_alert,
)
from backend.app.services.validation_failure_log import append_validation_failure


def test_classify_failure_cause():
    assert classify_failure_cause("connection timeout to NOAA") == "no_network"
    assert classify_failure_cause("no optional decoder installed") == CAUSE_DECODER_UNAVAILABLE
    assert classify_failure_cause("No inspectable real MRMS catalog candidates") == CAUSE_NO_GRIB2_ARTIFACT
    assert (
        classify_failure_cause("Production tile serving remains disabled (ENABLE_PRODUCTION_RADAR_TILES=false)")
        == CAUSE_PRODUCTION_FLAG_OFF
    )
    assert classify_failure_cause("something else entirely") == "unknown"


def test_normalize_cause_message_groups_similar_text():
    a = normalize_cause_message("Requested 3 frames exceeds max 10")
    b = normalize_cause_message("Requested 5 frames exceeds max 10")
    assert a == b


def test_group_validation_failures_by_step_and_cause(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    append_validation_failure(
        storage,
        phase="scheduled_validation",
        step="batch_validation",
        error_message="no optional decoder installed",
    )
    append_validation_failure(
        storage,
        phase="scheduled_validation",
        step="batch_validation",
        warnings=["no optional decoder installed"],
    )
    grouped = group_validation_failures(
        [
            {
                "step": "batch_validation",
                "error_message": "no optional decoder installed",
                "logged_at": "2026-06-28T10:00:00Z",
            },
            {
                "step": "batch_validation",
                "warnings": ["no optional decoder installed"],
                "logged_at": "2026-06-28T10:01:00Z",
            },
        ]
    )
    assert len(grouped) >= 1
    assert grouped[0]["step"] == "batch_validation"
    assert grouped[0]["cause"] == CAUSE_DECODER_UNAVAILABLE
    assert grouped[0]["count"] >= 1


def test_validation_alert_marker_shape(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    alert = build_validation_alert(storage, scheduled=None)
    assert alert["status"] == ALERT_OK
    assert alert["verified_mrms"] is False
    assert alert["prototype"] is True
    assert "suggested_next_action" in alert
    assert isinstance(alert["grouped_failure_causes"], list)


def test_refresh_validation_alert_persists(storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    append_validation_failure(
        storage,
        phase="test",
        step="batch_validation",
        warnings=["Stub/offline mode: stub downloads are not real GRIB2"],
    )
    alert = refresh_validation_alert(storage)
    saved = load_validation_alert(storage)
    assert saved is not None
    assert saved["verified_mrms"] is False
    assert alert["warning_count"] >= 1 or alert["status"] in (ALERT_WARNING, ALERT_OK)


def test_validation_summary_includes_alert(client, db_session, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    save_validation_alert(
        storage,
        {
            "status": "warning",
            "failure_count": 0,
            "warning_count": 2,
            "operator_attention_needed": True,
            "suggested_next_action": "Check decoder",
            "grouped_failure_causes": [
                {
                    "step": "batch_validation",
                    "cause": "no_grib2_artifact",
                    "message": "No inspectable real MRMS",
                    "count": 2,
                    "latest_logged_at": "2026-06-28T10:00:00Z",
                }
            ],
            "verified_mrms": False,
            "prototype": True,
        },
    )

    response = client.get("/api/validation/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["validation_alert"] is not None
    assert body["validation_alert"]["status"] == "warning"
    assert body["validation_alert"]["verified_mrms"] is False
    assert len(body["grouped_failure_causes"]) >= 1


def test_validation_alerts_endpoint(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/alerts?refresh=true")
    assert response.status_code == 200
    body = response.json()
    assert body["verified_mrms"] is False
    assert body["alert"] is not None
    assert body["alert"]["verified_mrms"] is False


def test_validation_summary_missing_failures_ok_state(client, storage, monkeypatch):
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))
    response = client.get("/api/validation/summary")
    body = response.json()
    assert body["validation_failures_count"] == 0
    assert body["validation_alert"] is not None
    assert body["validation_alert"]["status"] == ALERT_OK
    assert body["validation_alert"]["verified_mrms"] is False


def test_production_tile_serving_still_gated_phase25(client, db_session, storage, monkeypatch):
    from backend.app.models import RadarFile
    from backend.app.models.radar_file import RENDER_STATUS_PRODUCTION_RENDERED
    from backend.app.services.decoded_tile_cache import TILE_MODE_PLACEHOLDER

    monkeypatch.setattr(settings, "enable_production_radar_tiles", False)
    monkeypatch.setattr(settings, "local_storage_root", str(storage.storage_root))

    timestamp = "2026-06-28T01:00:00Z"
    frame = RadarFile(
        product_id="mrms_reflectivity",
        timestamp=timestamp,
        raw_path=storage.normalize_path("raw", "mrms", "reflectivity", "phase25_gate.grib2.gz"),
        processed_status="placeholder_for_real_raw",
        render_status=RENDER_STATUS_PRODUCTION_RENDERED,
        production_rendering=True,
        source="mrms_discovered",
    )
    db_session.add(frame)
    db_session.commit()

    response = client.get(f"/tiles/mrms_reflectivity/{timestamp}/0/0/0.png")
    assert response.status_code == 200
    assert response.headers.get("x-radararchive-production-rendering") == "false"
    assert response.headers.get("x-radararchive-tile") in (TILE_MODE_PLACEHOLDER, "placeholder_for_real_raw")
