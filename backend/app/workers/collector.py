"""Worker entrypoint for collection jobs (CLI/scripts only in Phase 3)."""

from backend.app.services.collector import collect_mrms_reflectivity_once

__all__ = ["collect_mrms_reflectivity_once"]
