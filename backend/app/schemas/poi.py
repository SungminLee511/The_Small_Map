from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.poi import POIType, POIStatus, POIVerificationStatus


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
    verification_status: POIVerificationStatus = POIVerificationStatus.verified
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


# --- Phase 2.2.4 submission ------------------------------------------------


class SubmittedGPS(BaseModel):
    lat: float
    lng: float
    accuracy_m: float = Field(..., ge=0)


class POICreate(BaseModel):
    """User-submitted POI (POST /api/v1/pois)."""

    poi_type: POIType
    location: LatLng
    name: str | None = Field(None, max_length=255)
    attributes: dict | None = None
    submitted_gps: SubmittedGPS
    photo_upload_id: uuid.UUID | None = None


class POICreateDuplicateResponse(BaseModel):
    """Returned when a POI of the same type already exists nearby."""

    duplicate: bool = True
    existing_poi_id: uuid.UUID
    distance_m: float


class POIConfirmResponse(BaseModel):
    """Returned by POST /api/v1/pois/{id}/confirm (Phase 2.2.7)."""

    poi_id: uuid.UUID
    verification_count: int
    verification_status: POIVerificationStatus
    flipped_to_verified: bool
