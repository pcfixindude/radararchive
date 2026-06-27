from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str


class Layer(BaseModel):
    id: str
    name: str
    type: str
    available: bool
    source: str = Field(default="demo", description="demo until real catalog ingestion lands")
    bounds: Optional[list[float]] = Field(
        default=None,
        description="Optional [west, south, east, north] tile bounds",
    )
    minzoom: Optional[int] = None
    maxzoom: Optional[int] = None
    tile_support: bool = False
    placeholder: bool = Field(
        default=False,
        description="True when tiles are stub placeholders, not real radar",
    )


class LatestResponse(BaseModel):
    layer: str
    timestamp: Optional[str]
