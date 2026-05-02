"""Integration tests for GET /api/v1/me/reputation (Phase 4.3.2)."""

from __future__ import annotations

import pytest

from app.models.reputation_event import ReputationEventType
from app.services.reputation_service import append_event


@pytest.mark.asyncio
async def test_reputation_endpoint_requires_auth(client):
    resp = await client.get("/api/v1/me/reputation")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_reputation_endpoint_returns_only_my_events(
    client, db_session, make_user, auth_cookie
):
    user = await make_user()
    other = await make_user()
    await append_event(
        db_session, user=user, event_type=ReputationEventType.confirmation
    )
    await append_event(
        db_session, user=other, event_type=ReputationEventType.confirmation
    )
    await db_session.commit()

    resp = await client.get(
        "/api/v1/me/reputation", cookies=auth_cookie(user)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["delta"] == 1
    assert body[0]["event_type"] == "confirmation"


@pytest.mark.asyncio
async def test_reputation_endpoint_returns_descending_order(
    client, db_session, make_user, auth_cookie
):
    user = await make_user()
    await append_event(
        db_session, user=user, event_type=ReputationEventType.confirmation
    )
    await append_event(
        db_session,
        user=user,
        event_type=ReputationEventType.poi_submitted_verified,
    )
    await db_session.commit()
    resp = await client.get(
        "/api/v1/me/reputation", cookies=auth_cookie(user)
    )
    body = resp.json()
    assert len(body) == 2
    # Most recent first
    ts0 = body[0]["created_at"]
    ts1 = body[1]["created_at"]
    assert ts0 >= ts1
