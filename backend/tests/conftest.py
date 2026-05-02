import uuid
from typing import AsyncGenerator

import pytest_asyncio
from geoalchemy2 import WKTElement
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.db import get_session
from app.main import app
from app.models.poi import POI, POIType, POIStatus

TEST_DB_URL = settings.database_url

# NullPool = fresh connection per checkout, no sharing conflicts
test_engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


_TABLES = (
    "notifications",
    "report_confirmations",
    "reports",
    "poi_confirmations",
    "photo_uploads",
    "pois",
    "users",
)


async def _truncate_all() -> None:
    async with test_engine.begin() as conn:
        await conn.execute(
            text(
                f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY CASCADE"
            )
        )


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    """Ensure PostGIS is on and tables are clean. Tables themselves are
    created by Alembic before the test run (see CI workflow)."""
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    await _truncate_all()
    yield
    await _truncate_all()
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_db) -> AsyncGenerator[AsyncSession, None]:
    """Per-test session — truncate every Phase-2 table after each test."""
    async with test_session_factory() as session:
        yield session
    await _truncate_all()


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


# --- Phase 2 helpers ------------------------------------------------------


async def _make_user(
    db_session: AsyncSession, *, kakao_id: int, is_admin: bool = False
):
    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        kakao_id=kakao_id,
        display_name=f"User {kakao_id}",
        email=None,
        avatar_url=None,
        reputation=0,
        is_admin=is_admin,
        is_banned=False,
    )
    db_session.add(user)
    await db_session.commit()
    return user


def _auth_cookie_for(user_id) -> dict[str, str]:
    """Mint a session cookie for a test user."""
    from app.core.jwt_tokens import issue_session_token

    return {settings.auth_cookie_name: issue_session_token(user_id)}


@pytest_asyncio.fixture
async def make_user(db_session: AsyncSession):
    counter = {"i": 100_000}

    async def _factory(*, is_admin: bool = False):
        counter["i"] += 1
        return await _make_user(db_session, kakao_id=counter["i"], is_admin=is_admin)

    return _factory


@pytest_asyncio.fixture
async def auth_cookie():
    """Returns a callable: auth_cookie(user) -> dict cookies."""

    def _build(user):
        return _auth_cookie_for(user.id)

    return _build


@pytest_asyncio.fixture(autouse=True)
def _reset_rate_limiter():
    """Each test gets a fresh in-memory rate limiter."""
    from app.core.rate_limit import get_limiter

    get_limiter().reset()
    yield
    get_limiter().reset()
