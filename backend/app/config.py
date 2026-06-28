from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    version: str = "0.1.0"
    frontend_origin: str = "http://localhost:5173"
    database_url: str = "sqlite:///./data/radararchive.sqlite"
    local_storage_root: str = "./data"
    testing: bool = False
    default_demo_plan: str = "pro"
    mrms_source_mode: str = "stub"
    mrms_discovery_limit: int = 5
    mrms_s3_bucket: str = "noaa-mrms-pds"
    mrms_s3_region_prefix: str = "CONUS"
    mrms_request_timeout_seconds: float = 5.0
    mrms_discovery_lookback_days: int = 3
    enable_decoded_tiles: bool = False
    enable_production_radar_tiles: bool = False
    stale_running_job_seconds: int = 3600

    @property
    def sqlite_path(self) -> Optional[Path]:
        if not self.database_url.startswith("sqlite:///"):
            return None
        raw = self.database_url.removeprefix("sqlite:///")
        return Path(raw)


settings = Settings()

VALID_DEMO_PLANS = frozenset({"free", "basic", "pro", "business"})

MRMS_SOURCE_MODE_STUB = "stub"
MRMS_SOURCE_MODE_REAL = "real"
