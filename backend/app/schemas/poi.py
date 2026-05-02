from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.poi import POIType, POIStatus


class LatLng(BaseModel):
    lat: float
    lng: float


class BBox(BaseModel):
    west: float
    south: float
    east: float
    north: float

    @field_validator("west", "east")
    @classmethod
    def lng_range(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError("longitude must be between -180 and 180")
        return v

    @field_validator("south", "north")
    @classmethod
    def lat_range(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError("latitude must be between -90 and 90")
        return v


class POIRead(BaseModel):
    id: uuid.UUID
    poi_type: POIType
    location: LatLng
    name: str | None = None
    attributes: dict | None = None
    source: str
    status: POIStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class POIDetail(POIRead):
    """Full detail view including importer metadata (1.3.7)."""

    external_id: str | None = None
    last_verified_at: datetime | None = None
    verification_count: int = 0


class POIListResponse(BaseModel):
    items: list[POIRead]
    truncated: bool
