from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field


class MrmsDiscoveredFileSchema(BaseModel):
    product: str
    timestamp: str
    object_key: str
    source_url: str
    file_name: str
    size_bytes: Optional[int] = None
    source_provider: str
    catalog_product_id: str


class MrmsDiscoveryResponse(BaseModel):
    mode: str
    product: str
    count: int
    items: list[MrmsDiscoveredFileSchema]
    note: str = Field(
        default="Discovery metadata only. GRIB2 files are not downloaded or parsed in Phase 8."
    )


@dataclass
class RegisterDiscoveredResult:
    created: int
    skipped: int
    items: list[str]
