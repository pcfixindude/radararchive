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
        default="Discovery metadata only. Use download-mrms to fetch GRIB2.gz files (no parse yet)."
    )


class MrmsDownloadStatusResponse(BaseModel):
    mode: str
    total: int
    pending: int
    downloaded: int
    failed: int
    note: str = Field(
        default="Download status for mrms_discovered catalog rows. Rendering remains placeholder."
    )


class MrmsProcessingStatusResponse(BaseModel):
    total: int
    pending: int
    placeholder_processed: int
    placeholder_for_real_raw: int
    real_decode_not_implemented: int
    failed: int
    note: str = Field(
        default="Processing status for catalog rows. GRIB2 decode and real radar rendering are not implemented."
    )


@dataclass
class RegisterDiscoveredResult:
    created: int
    skipped: int
    items: list[str]
