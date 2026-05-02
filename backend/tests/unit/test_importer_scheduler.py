"""Unit tests for the importer scheduler glue (1.3.6)."""

from __future__ import annotations

from app.config import Settings
from app.jobs.importer_scheduler import build_default_importers


def test_build_default_importers_yields_two():
    s = Settings()
    imps = build_default_importers(s)
    ids = [imp.source_id for imp in imps]
    assert "seoul.public_toilets" in ids
    assert "mapo.smoking_areas" in ids


def test_build_default_importers_no_geocoder_when_key_missing():
    s = Settings(kakao_rest_api_key="")
    imps = build_default_importers(s)
    smoking = next(i for i in imps if i.source_id == "mapo.smoking_areas")
    assert smoking.geocoder is None


def test_build_default_importers_with_geocoder_when_key_present():
    s = Settings(kakao_rest_api_key="dummy-key")
    imps = build_default_importers(s)
    smoking = next(i for i in imps if i.source_id == "mapo.smoking_areas")
    assert smoking.geocoder is not None


def test_scheduler_disabled_by_default():
    from app.jobs.importer_scheduler import start_scheduler, stop_scheduler

    s = Settings()
    assert s.importer_scheduler_enabled is False
    # Should be a no-op
    start_scheduler(s)
    stop_scheduler()
