"""Pydantic schemas for user-facing endpoints (Phase 2.2.2)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class UserMe(BaseModel):
    """Returned by GET /api/v1/auth/me."""

    id: uuid.UUID
    display_name: str
    email: str | None = None
    avatar_url: str | None = None
    is_admin: bool = False
    reputation: int = 0

    model_config = {"from_attributes": True}
