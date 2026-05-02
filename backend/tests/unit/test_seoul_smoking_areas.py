"""Unit tests for ``seoul_smoking_areas`` importer (1.3.4)."""

from __future__ import annotations

import pytest

from app.importers.seoul_smoking_areas import (
    MapoSmokingAreasImporter,
    _row_external_id,
)


def _row(**overrides):
    base = {
        "시설명": "마포구청 옆 흡연부스",
        "주소": "서울특별시 마포구 월드컵로 212",
        "흡연시설형태": "폐쇄형",
        "운영시간": "24시간",
    }
    base.update(overrides)
    return base


async def _stub_geocoder(addr: str):
    # Map any Mapo address to a fixed point for testing
    if "마포" in addr:
        return (37.566535, 126.901320)
    return None


@pytest.mark.asyncio
async def test_normalize_async_happy_path():
    imp = MapoSmokingAreasImporter(rows=[_row()], geocoder=_stub_geocoder)
    raw_rows = await imp.fetch_raw()
    item = await imp._normalize_async(raw_rows[0], idx=0)
    assert item is not None
    assert item.name == "마포구청 옆 흡연부스"
    assert abs(item.lat - 37.566535) < 1e-6
    assert item.attributes["enclosed"] is True
    assert item.attributes["opening_hours"] == "24시간"


@pytest.mark.asyncio
async def test_normalize_async_open_form():
    row = _row(**{"흡연시설형태": "개방형"})
    imp = MapoSmokingAreasImporter(rows=[row], geocoder=_stub_geocoder)
    item = await imp._normalize_async((await imp.fetch_raw())[0], idx=0)
    assert item is not None
    assert item.attributes["enclosed"] is False


@pytest.mark.asyncio
async def test_normalize_async_skips_no_address():
    row = _row(**{"주소": ""})
    imp = MapoSmokingAreasImporter(rows=[row], geocoder=_stub_geocoder)
    item = await imp._normalize_async((await imp.fetch_raw())[0], idx=0)
    assert item is None


@pytest.mark.asyncio
async def test_normalize_async_skips_geocode_fail():
    async def failing_geocoder(addr):
        return None

    imp = MapoSmokingAreasImporter(rows=[_row()], geocoder=failing_geocoder)
    item = await imp._normalize_async((await imp.fetch_raw())[0], idx=0)
    assert item is None


def test_external_id_stable():
    row = _row()
    a = _row_external_id(row, idx=5)
    b = _row_external_id(row, idx=5)
    assert a == b
    assert a.startswith("mapo-smk-")


def test_external_id_changes_with_idx():
    row = _row()
    assert _row_external_id(row, idx=1) != _row_external_id(row, idx=2)


@pytest.mark.asyncio
async def test_geocode_cache_hits_once():
    calls = {"n": 0}

    async def counting_geocoder(addr):
        calls["n"] += 1
        return (37.5, 127.0)

    imp = MapoSmokingAreasImporter(
        rows=[_row(), _row()],  # same address twice
        geocoder=counting_geocoder,
    )
    raw = await imp.fetch_raw()
    await imp._normalize_async(raw[0], idx=0)
    await imp._normalize_async(raw[1], idx=1)
    assert calls["n"] == 1
