from backend.app.models import RadarFile
from backend.app.models.radar_file import (
    PROCESSED_STATUS_PENDING,
    PROCESSED_STATUS_PLACEHOLDER_PROCESSED,
)
from backend.app.services.processor import process_pending_frames


def test_processor_creates_processed_placeholder(db_session, storage):
    result = process_pending_frames(db_session, storage)

    assert len(result.processed) == 5
    frame = db_session.query(RadarFile).filter(RadarFile.timestamp == "2026-06-27T20:00:00Z").one()
    assert frame.processed_status == PROCESSED_STATUS_PLACEHOLDER_PROCESSED
    assert frame.processed_at is not None
    assert frame.processed_path is not None
    assert storage.path_exists(frame.processed_path)
    assert frame.processed_path.endswith(".png")


def test_processor_is_idempotent(db_session, storage):
    first = process_pending_frames(db_session, storage)
    second = process_pending_frames(db_session, storage)

    assert len(first.processed) == 5
    assert len(second.processed) == 0
    assert second.skipped == 5
    assert db_session.query(RadarFile).count() == 5


def test_processor_only_processes_rows_with_raw_files(db_session, storage):
    row = RadarFile(
        product_id="mrms_reflectivity",
        timestamp="2026-06-27T21:00:00Z",
        raw_path="data/raw/missing/file.stub",
        processed_status=PROCESSED_STATUS_PENDING,
        source="demo",
    )
    db_session.add(row)
    db_session.commit()

    result = process_pending_frames(db_session, storage)
    assert all(item.timestamp != "2026-06-27T21:00:00Z" for item in result.processed)

    missing = db_session.query(RadarFile).filter(RadarFile.timestamp == "2026-06-27T21:00:00Z").one()
    assert missing.processed_status == PROCESSED_STATUS_PENDING
