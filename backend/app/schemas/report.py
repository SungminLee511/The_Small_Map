"""Pydantic schemas for reports + notifications (Phase 3)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.notification import NotificationType
from app.models.report import ReportStatus, ReportType


class ReportCreate(BaseModel):
    report_type: ReportType
    description: str | None = Field(None, max_length=500)
    photo_url: str | None = Field(None, max_length=1024)


class ReportRead(BaseModel):
    id: uuid.UUID
    poi_id: uuid.UUID
    reporter_id: uuid.UUID
    report_type: ReportType
    description: str | None = None
    photo_url: str | None = None
    status: ReportStatus
    confirmation_count: int
    resolved_at: datetime | None = None
    resolved_by: uuid.UUID | None = None
    resolution_note: str | None = None
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    items: list[ReportRead]
    truncated: bool = False


class ReportConfirmResponse(BaseModel):
    report_id: uuid.UUID
    confirmation_count: int


class ReportResolveBody(BaseModel):
    resolution_note: str = Field(..., min_length=1, max_length=500)
    photo_url: str | None = Field(None, max_length=1024)


class ReportDismissBody(BaseModel):
    reason: str | None = Field(None, max_length=500)


# Notifications


class NotificationRead(BaseModel):
    id: uuid.UUID
    type: NotificationType
    payload: dict
    read_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
