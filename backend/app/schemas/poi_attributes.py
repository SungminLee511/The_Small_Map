"""Per-type attribute schemas for POI.attributes JSONB.

The POI model stores type-specific attributes in a JSONB column. These Pydantic
schemas validate the shape per type. Unknown keys are allowed but ignored on
read (model_config: extra='allow' on write, but we strip to known keys when
serializing back).
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Union

from pydantic import BaseModel, ConfigDict, Field

from app.models.poi import POIType


class Gender(str, Enum):
    separate = "separate"
    unisex = "unisex"
    male_only = "male_only"
    female_only = "female_only"


class _AttrsBase(BaseModel):
    """Base for per-type attribute schemas. Allows unknown keys on input."""

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)


class ToiletAttributes(_AttrsBase):
    accessibility: bool | None = None
    gender: Gender | None = None
    opening_hours: str | None = None
    is_free: bool | None = None
    has_baby_changing: bool | None = None


class TrashCanAttributes(_AttrsBase):
    recycling: bool | None = None
    general: bool | None = None


class BenchAttributes(_AttrsBase):
    material: str | None = None
    has_back: bool | None = None
    shaded: bool | None = None


class SmokingAreaAttributes(_AttrsBase):
    enclosed: bool | None = None
    opening_hours: str | None = None


class WaterFountainAttributes(_AttrsBase):
    is_potable: bool | None = None
    seasonal: bool | None = None


# Discriminated union helper. Map POIType -> schema class.
ATTRIBUTE_SCHEMAS: dict[POIType, type[_AttrsBase]] = {
    POIType.toilet: ToiletAttributes,
    POIType.trash_can: TrashCanAttributes,
    POIType.bench: BenchAttributes,
    POIType.smoking_area: SmokingAreaAttributes,
    POIType.water_fountain: WaterFountainAttributes,
}


# Known keys per type, used to strip unknown fields on read.
_KNOWN_KEYS: dict[POIType, frozenset[str]] = {
    pt: frozenset(cls.model_fields.keys())
    for pt, cls in ATTRIBUTE_SCHEMAS.items()
}


def validate_attributes(poi_type: POIType, raw: dict | None) -> dict:
    """Validate raw attribute dict against the schema for poi_type.

    Unknown keys are accepted but kept as-is in storage (extra='allow').
    Returns the validated dict (defaults applied, types coerced).
    Raises ValidationError on malformed values.
    """
    if raw is None:
        return {}
    schema_cls = ATTRIBUTE_SCHEMAS[poi_type]
    obj = schema_cls.model_validate(raw)
    return obj.model_dump(mode="json", exclude_none=False)


def filter_known_keys(poi_type: POIType, raw: dict | None) -> dict:
    """Return only the known keys for a type — unknown keys ignored on read."""
    if raw is None:
        return {}
    known = _KNOWN_KEYS[poi_type]
    return {k: v for k, v in raw.items() if k in known}


# Convenience union type (not used directly by SQLAlchemy, but useful elsewhere)
POIAttributes = Annotated[
    Union[
        ToiletAttributes,
        TrashCanAttributes,
        BenchAttributes,
        SmokingAreaAttributes,
        WaterFountainAttributes,
    ],
    Field(description="Type-specific POI attributes"),
]
