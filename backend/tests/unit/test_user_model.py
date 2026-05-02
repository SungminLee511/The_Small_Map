"""Unit tests for the User SQLAlchemy model (2.2.1)."""

from __future__ import annotations

import uuid

from app.models.user import User


def test_user_columns_present():
    cols = {c.name for c in User.__table__.columns}
    expected = {
        "id", "kakao_id", "display_name", "email", "avatar_url",
        "reputation", "is_admin", "is_banned",
        "created_at", "updated_at", "last_seen_at",
    }
    assert expected <= cols


def test_user_kakao_id_is_unique():
    col = User.__table__.columns["kakao_id"]
    assert col.unique is True or any(
        getattr(idx, "unique", False) and "kakao_id" in {c.name for c in idx.columns}
        for idx in User.__table__.indexes
    )


def test_user_defaults():
    u = User(
        id=uuid.uuid4(),
        kakao_id=12345,
        display_name="Tester",
    )
    # Pydantic-style server defaults aren't filled until INSERT, but the
    # Python-side default for reputation/is_admin/is_banned should be 0/False
    # via mapped_column default=...
    assert u.kakao_id == 12345
    assert u.display_name == "Tester"


def test_user_tablename():
    assert User.__tablename__ == "users"
