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


class LatestResponse(BaseModel):
    layer: str
    timestamp: Optional[str]
