import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from geoalchemy2 import WKTElement
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.db import Base, get_session
from app.main import app
from app.models.poi import POI, POIType, POIStatus

TEST_DB_URL = settings.database_url

# NullPool = fresh connection per checkout, no sharing conflicts
test_engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    """Ensure tables exist (created by alembic). Just truncate on teardown."""
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.execute(text("TRUNCATE pois"))
    yield
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE pois"))
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_db) -> AsyncGenerator[AsyncSession, None]:
    """Per-test session — truncate pois after each test."""
    async with test_session_factory() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE pois"))


@pytest_asyncio.fixture
async def client(setup_db) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client using real DB sessions (committed data visible)."""

    async def test_get_session():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = test_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def make_poi(
    poi_type: POIType = POIType.toilet,
    lat: float = 37.555,
    lng: float = 126.92,
    name: str | None = "Test POI",
    source: str = "seed",
) -> POI:
    """Helper to create a POI instance."""
    return POI(
        id=uuid.uuid4(),
        poi_type=poi_type,
        name=name,
        location=WKTElement(f"POINT({lng} {lat})", srid=4326),
        source=source,
        status=POIStatus.active,
        attributes={},
    )
