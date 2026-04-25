import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.poi import POIType
from tests.conftest import make_poi


MAPO_BBOX = "126.90,37.54,126.94,37.56"


@pytest.mark.asyncio
async def test_bbox_happy_path(client: AsyncClient, db_session: AsyncSession):
    """Insert 3 POIs in bbox, expect all 3 returned."""
    pois = [
        make_poi(POIType.toilet, lat=37.550, lng=126.920),
        make_poi(POIType.bench, lat=37.551, lng=126.921),
        make_poi(POIType.trash_can, lat=37.552, lng=126.922),
    ]
    for p in pois:
        db_session.add(p)
    await db_session.commit()

    resp = await client.get(f"/api/v1/pois?bbox={MAPO_BBOX}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 3
    assert data["truncated"] is False


@pytest.mark.asyncio
async def test_bbox_filter_by_type(client: AsyncClient, db_session: AsyncSession):
    """Only toilets returned when filtered."""
    pois = [
        make_poi(POIType.toilet, lat=37.550, lng=126.920),
        make_poi(POIType.bench, lat=37.551, lng=126.921),
    ]
    for p in pois:
        db_session.add(p)
    await db_session.commit()

    resp = await client.get(f"/api/v1/pois?bbox={MAPO_BBOX}&type=toilet")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["poi_type"] == "toilet"


@pytest.mark.asyncio
async def test_bbox_excludes_outside(client: AsyncClient, db_session: AsyncSession):
    """POIs outside bbox not returned."""
    poi = make_poi(POIType.toilet, lat=37.60, lng=127.10)  # outside Mapo
    db_session.add(poi)
    await db_session.commit()

    resp = await client.get(f"/api/v1/pois?bbox={MAPO_BBOX}")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 0


@pytest.mark.asyncio
async def test_bbox_malformed(client: AsyncClient):
    """Malformed bbox returns 422."""
    resp = await client.get("/api/v1/pois?bbox=bad")
    assert resp.status_code == 422

    resp = await client.get("/api/v1/pois?bbox=1,2,3")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_bbox_truncated(client: AsyncClient, db_session: AsyncSession):
    """Over 500 POIs triggers truncation."""
    for i in range(510):
        lat = 37.540 + (i % 100) * 0.0001
        lng = 126.910 + (i // 100) * 0.0001
        db_session.add(make_poi(POIType.toilet, lat=lat, lng=lng))
    await db_session.commit()

    resp = await client.get(f"/api/v1/pois?bbox={MAPO_BBOX}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 500
    assert data["truncated"] is True


@pytest.mark.asyncio
async def test_bbox_span_too_large(client: AsyncClient):
    """Span > 0.5 degrees rejected."""
    resp = await client.get("/api/v1/pois?bbox=126.0,37.0,127.0,38.0")
    assert resp.status_code == 422
