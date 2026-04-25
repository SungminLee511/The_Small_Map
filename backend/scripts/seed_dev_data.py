"""Seed development data — ~10 hand-picked POIs in Mapo-gu, Seoul."""
import asyncio
import uuid

from geoalchemy2 import WKTElement
from sqlalchemy import text

from app.db import async_session_factory
from app.models.poi import POI, POIType, POIStatus

SEED_POIS = [
    {"poi_type": POIType.toilet, "name": "홍대입구역 공중화장실", "lat": 37.5571, "lng": 126.9244},
    {"poi_type": POIType.toilet, "name": "합정역 공중화장실", "lat": 37.5495, "lng": 126.9137},
    {"poi_type": POIType.trash_can, "name": "홍대 걷고싶은거리 쓰레기통", "lat": 37.5563, "lng": 126.9237},
    {"poi_type": POIType.trash_can, "name": "망원한강공원 쓰레기통", "lat": 37.5550, "lng": 126.8950},
    {"poi_type": POIType.bench, "name": "경의선숲길 벤치 1", "lat": 37.5530, "lng": 126.9210},
    {"poi_type": POIType.bench, "name": "경의선숲길 벤치 2", "lat": 37.5535, "lng": 126.9195},
    {"poi_type": POIType.smoking_area, "name": "홍대입구역 흡연구역", "lat": 37.5568, "lng": 126.9250},
    {"poi_type": POIType.smoking_area, "name": "합정역 흡연구역", "lat": 37.5492, "lng": 126.9140},
    {"poi_type": POIType.water_fountain, "name": "망원한강공원 음수대", "lat": 37.5548, "lng": 126.8955},
    {"poi_type": POIType.water_fountain, "name": "홍대 연트럴파크 음수대", "lat": 37.5540, "lng": 126.9215},
]


async def seed():
    async with async_session_factory() as session:
        # Check if already seeded
        result = await session.execute(text("SELECT count(*) FROM pois WHERE source='seed'"))
        count = result.scalar()
        if count and count > 0:
            print(f"Already seeded ({count} POIs). Skipping.")
            return

        for data in SEED_POIS:
            poi = POI(
                id=uuid.uuid4(),
                poi_type=data["poi_type"],
                name=data["name"],
                location=WKTElement(f"POINT({data['lng']} {data['lat']})", srid=4326),
                source="seed",
                status=POIStatus.active,
                attributes={},
            )
            session.add(poi)

        await session.commit()
        print(f"Seeded {len(SEED_POIS)} POIs in Mapo-gu.")


if __name__ == "__main__":
    asyncio.run(seed())
