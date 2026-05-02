"""Schemas for photo presign endpoint (Phase 2.2.5)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PhotoPresignRequest(BaseModel):
    content_type: Literal["image/jpeg", "image/png", "image/webp"] = Field(
        ..., description="MIME type of the image to upload"
    )


class PhotoPresignResponse(BaseModel):
    upload_id: uuid.UUID
    upload_url: str
    fields: dict[str, str]
    expires_at: datetime
