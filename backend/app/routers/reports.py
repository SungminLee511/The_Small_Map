"""Report endpoints (Phase 3.3.1, 3.3.4)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import RateLimitExceeded, hit as rate_hit
from app.db import get_session
from app.deps import get_current_user, require_admin
from app.models.report import ReportStatus
from app.models.user import User
from app.schemas.poi import BBox
from app.schemas.report import (
    ReportConfirmResponse,
    ReportCreate,
    ReportDismissBody,
    ReportListResponse,
    ReportRead,
    ReportResolveBody,
)
from app.services.report_service import (
    AlreadyConfirmed,
    CannotConfirmOwnReport,
    CreateReportInput,
    POINotFound,
    ReportNotFound,
    ResolutionTooEarly,
    confirm_report,
    create_report,
    dismiss_report,
    list_reports_for_poi,
    list_reports_in_bbox,
    resolve_report,
)

router = APIRouter(tags=["reports"])


# --- POI-scoped report endpoints ----------------------------------------


@router.post(
    "/pois/{poi_id}/reports",
    response_model=ReportRead,
    status_code=status.HTTP_201_CREATED,
)
async def submit_report(
    poi_id: uuid.UUID,
    payload: ReportCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if user.is_banned:
        raise HTTPException(status_code=403, detail="banned")
    try:
        rate_hit(user.id, "submit_report")
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail=f"rate limit: {e.action}",
            headers={"Retry-After": str(e.retry_after)},
        )

    try:
        report = await create_report(
            session,
            poi_id=poi_id,
            reporter_id=user.id,
            payload=CreateReportInput(
                report_type=payload.report_type,
                description=payload.description,
                photo_url=payload.photo_url,
            ),
        )
    except POINotFound:
        raise HTTPException(status_code=404, detail="POI not found")
    await session.commit()
    return ReportRead.model_validate(report)


@router.get(
    "/pois/{poi_id}/reports", response_model=ReportListResponse
)
async def list_reports_for_poi_endpoint(
    poi_id: uuid.UUID,
    status_param: ReportStatus | None = Query(
        ReportStatus.active, alias="status"
    ),
    session: AsyncSession = Depends(get_session),
):
    rows = await list_reports_for_poi(
        session, poi_id=poi_id, status_filter=status_param
    )
    return ReportListResponse(
        items=[ReportRead.model_validate(r) for r in rows],
        truncated=False,
    )


# --- Bulk bbox endpoint -------------------------------------------------


@router.get("/reports", response_model=ReportListResponse)
async def list_reports_in_bbox_endpoint(
    bbox: str = Query(..., description="west,south,east,north"),
    status_param: ReportStatus | None = Query(
        ReportStatus.active, alias="status"
    ),
    session: AsyncSession = Depends(get_session),
):
    parts = bbox.split(",")
    if len(parts) != 4:
        raise HTTPException(status_code=422, detail="bbox must be 4 floats")
    try:
        west, south, east, north = (float(p) for p in parts)
    except ValueError:
        raise HTTPException(status_code=422, detail="bbox values must be floats")
    if west >= east or south >= north:
        raise HTTPException(status_code=422, detail="invalid bbox order")
    if (east - west) > 0.5 or (north - south) > 0.5:
        raise HTTPException(status_code=422, detail="bbox span must be < 0.5°")

    bbox_obj = BBox(west=west, south=south, east=east, north=north)
    rows, truncated = await list_reports_in_bbox(
        session, bbox=bbox_obj, status_filter=status_param
    )
    return ReportListResponse(
        items=[ReportRead.model_validate(r) for r in rows],
        truncated=truncated,
    )


# --- Confirm / Resolve / Dismiss ----------------------------------------


@router.post(
    "/reports/{report_id}/confirm", response_model=ReportConfirmResponse
)
async def confirm_report_endpoint(
    report_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    try:
        rate_hit(user.id, "confirm_report")
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail=f"rate limit: {e.action}",
            headers={"Retry-After": str(e.retry_after)},
        )
    try:
        report = await confirm_report(
            session, report_id=report_id, user_id=user.id
        )
    except ReportNotFound:
        raise HTTPException(status_code=404, detail="report not found")
    except CannotConfirmOwnReport:
        raise HTTPException(
            status_code=400, detail="cannot confirm your own report"
        )
    except AlreadyConfirmed:
        raise HTTPException(status_code=409, detail="already confirmed")
    await session.commit()
    return ReportConfirmResponse(
        report_id=report.id,
        confirmation_count=report.confirmation_count,
    )


@router.post("/reports/{report_id}/resolve", response_model=ReportRead)
async def resolve_report_endpoint(
    report_id: uuid.UUID,
    body: ReportResolveBody,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    try:
        report = await resolve_report(
            session,
            report_id=report_id,
            user_id=user.id,
            resolution_note=body.resolution_note,
            photo_url=body.photo_url,
        )
    except ReportNotFound:
        raise HTTPException(status_code=404, detail="report not found")
    except ResolutionTooEarly as e:
        raise HTTPException(
            status_code=403,
            detail="only the reporter can resolve before 24h",
            headers={"Retry-After": str(e.retry_after_seconds)},
        )
    await session.commit()
    return ReportRead.model_validate(report)


@router.post("/reports/{report_id}/dismiss", response_model=ReportRead)
async def dismiss_report_endpoint(
    report_id: uuid.UUID,
    body: ReportDismissBody,
    session: AsyncSession = Depends(get_session),
    admin: User = Depends(require_admin),
):
    try:
        report = await dismiss_report(
            session,
            report_id=report_id,
            admin_id=admin.id,
            reason=body.reason,
        )
    except ReportNotFound:
        raise HTTPException(status_code=404, detail="report not found")
    await session.commit()
    return ReportRead.model_validate(report)
