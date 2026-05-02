"""Unit tests for per-type POI attribute schemas (1.3.2)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.poi import POIType
from app.schemas.poi_attributes import (
    Gender,
    ToiletAttributes,
    TrashCanAttributes,
    filter_known_keys,
    validate_attributes,
)


class TestToiletAttributes:
    def test_full_payload(self):
        obj = ToiletAttributes(
            accessibility=True,
            gender="separate",
            opening_hours="Mo-Fr 09:00-18:00",
            is_free=True,
            has_baby_changing=False,
        )
        assert obj.gender == Gender.separate
        assert obj.accessibility is True

    def test_all_none_defaults(self):
        obj = ToiletAttributes()
        assert obj.accessibility is None
        assert obj.gender is None

    def test_invalid_gender_raises(self):
        with pytest.raises(ValidationError):
            ToiletAttributes(gender="other")

    def test_unknown_keys_allowed(self):
        obj = ToiletAttributes(accessibility=True, source_note="seoul-2024")
        # extra='allow' means unknown keys survive on the model
        assert obj.model_dump().get("source_note") == "seoul-2024"


class TestTrashCanAttributes:
    def test_basic(self):
        obj = TrashCanAttributes(recycling=True, general=False)
        assert obj.recycling is True
        assert obj.general is False


class TestValidateAttributes:
    def test_validate_toilet(self):
        out = validate_attributes(
            POIType.toilet,
            {"accessibility": True, "gender": "unisex"},
        )
        assert out["accessibility"] is True
        assert out["gender"] == "unisex"

    def test_validate_none_returns_empty(self):
        assert validate_attributes(POIType.bench, None) == {}

    def test_validate_invalid_raises(self):
        with pytest.raises(ValidationError):
            validate_attributes(POIType.toilet, {"gender": "alien"})


class TestFilterKnownKeys:
    def test_strips_unknown(self):
        out = filter_known_keys(
            POIType.toilet,
            {"accessibility": True, "address": "Mapo-gu", "noise": 1},
        )
        assert out == {"accessibility": True}

    def test_none_returns_empty(self):
        assert filter_known_keys(POIType.toilet, None) == {}
