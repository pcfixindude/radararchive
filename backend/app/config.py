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

    @property
    def sqlite_path(self) -> Optional[Path]:
        if not self.database_url.startswith("sqlite:///"):
            return None
        raw = self.database_url.removeprefix("sqlite:///")
        return Path(raw)


settings = Settings()

VALID_DEMO_PLANS = frozenset({"free", "basic", "pro", "business"})
