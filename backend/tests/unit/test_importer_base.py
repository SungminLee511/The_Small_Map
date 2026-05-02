"""Unit tests for the importer base framework (1.3.3).

Pure-unit tests of POIInput / ImportReport / normalize behavior — DB-touching
behavior is exercised in integration tests (1.3.4).
"""

from __future__ import annotations

from app.importers.base import ImportReport, POIInput
from app.models.poi import POIType


def test_poi_input_defaults():
    item = POIInput(
        external_id="EXT-1",
        poi_type=POIType.toilet,
        lat=37.5,
        lng=126.9,
    )
    assert item.name is None
    assert item.attributes == {}
    assert item.last_verified_at is None


def test_import_report_total():
    report = ImportReport(source_id="x", created=2, updated=3, unchanged=5)
    assert report.total() == 10


def test_import_report_str():
    report = ImportReport(
        source_id="src", created=1, updated=2, unchanged=3, removed=4
    )
    s = str(report)
    assert "[src]" in s
    assert "created=1" in s
    assert "updated=2" in s
    assert "unchanged=3" in s
    assert "removed=4" in s


def test_import_report_errors():
    report = ImportReport(source_id="x")
    report.errors.append("oops")
    assert "errors=1" in str(report)
