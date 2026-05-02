"""Integration tests for /api/v1/notifications (Phase 3.3.6)."""

from __future__ import annotations

import pytest

from app.models.notification import Notification, NotificationType


async def _seed_notification(db_session, user, *, payload=None, read=False):
    n = Notification(
        user_id=user.id,
        type=NotificationType.report_expired,
        payload=payload or {},
        read_at=None,
    )
    db_session.add(n)
    await db_session.commit()
    return n


@pytest.mark.asyncio
async def test_list_requires_auth(client):
    resp = await client.get("/api/v1/notifications")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_returns_only_my_notifications(
    client, db_session, make_user, auth_cookie
):
    user = await make_user()
    other = await make_user()
    await _seed_notification(db_session, user, payload={"x": 1})
    await _seed_notification(db_session, other, payload={"x": 2})

    resp = await client.get(
        "/api/v1/notifications", cookies=auth_cookie(user)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["payload"]["x"] == 1


@pytest.mark.asyncio
async def test_unread_count(client, db_session, make_user, auth_cookie):
    user = await make_user()
    await _seed_notification(db_session, user)
    await _seed_notification(db_session, user)
    resp = await client.get(
        "/api/v1/notifications/unread-count", cookies=auth_cookie(user)
    )
    assert resp.json() == {"unread": 2}


@pytest.mark.asyncio
async def test_mark_one_read(client, db_session, make_user, auth_cookie):
    user = await make_user()
    n = await _seed_notification(db_session, user)
    resp = await client.post(
        f"/api/v1/notifications/{n.id}/read", cookies=auth_cookie(user)
    )
    assert resp.status_code == 200
    assert resp.json()["read_at"] is not None


@pytest.mark.asyncio
async def test_mark_one_read_404_for_other_users_notification(
    client, db_session, make_user, auth_cookie
):
    user = await make_user()
    other = await make_user()
    n = await _seed_notification(db_session, other)
    resp = await client.post(
        f"/api/v1/notifications/{n.id}/read", cookies=auth_cookie(user)
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_mark_all_read(client, db_session, make_user, auth_cookie):
    user = await make_user()
    await _seed_notification(db_session, user)
    await _seed_notification(db_session, user)
    resp = await client.post(
        "/api/v1/notifications/read-all", cookies=auth_cookie(user)
    )
    assert resp.status_code == 204
    cnt = await client.get(
        "/api/v1/notifications/unread-count", cookies=auth_cookie(user)
    )
    assert cnt.json() == {"unread": 0}
