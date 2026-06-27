"""Worker entrypoint for processing jobs (CLI/scripts only in Phase 4)."""

from backend.app.services.processor import process_pending_frames

__all__ = ["process_pending_frames"]
