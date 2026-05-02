"""Unit tests for POI submission validation (Phase 2.2.4).

Pure-function tests; the DB-touching behaviour (duplicate lookup, insert)
is exercised via integration tests against PostGIS in CI.
"""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.poi import POICreate, SubmittedGPS


def _payload(**overrides):
    base = dict(
        poi_type="toilet",
        location={"lat": 37.566535, "lng": 126.901320},
        name="Test toilet",
        attributes={"is_free": True},
        submitted_gps={"lat": 37.566535, "lng": 126.901320, "accuracy_m": 12.0},
    )
    base.update(overrides)
    return base


def test_create_payload_valid():
    p = POICreate.model_validate(_payload())
    assert p.poi_type == "toilet"
    assert isinstance(p.submitted_gps, SubmittedGPS)
    assert p.submitted_gps.accuracy_m == 12.0


def test_create_payload_rejects_unknown_type():
    with pytest.raises(ValidationError):
        POICreate.model_validate(_payload(poi_type="alien"))


def test_create_payload_negative_accuracy_rejected():
    with pytest.raises(ValidationError):
        POICreate.model_validate(
            _payload(submitted_gps={"lat": 37.5, "lng": 126.9, "accuracy_m": -1})
        )


def test_create_payload_rejects_long_name():
    with pytest.raises(ValidationError):
        POICreate.model_validate(_payload(name="x" * 256))


def test_create_payload_optional_photo_upload_id():
    p = POICreate.model_validate(_payload(photo_upload_id=str(uuid.uuid4())))
    assert isinstance(p.photo_upload_id, uuid.UUID)
