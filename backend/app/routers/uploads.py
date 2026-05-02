"""Photo upload endpoints (Phase 2.2.5).

Flow:
1. ``POST /api/v1/uploads/photo-presign`` — auth required. Server inserts
   a ``photo_uploads`` row with ``status='pending'`` and returns a
   short-lived presigned PUT URL for R2.
2. The browser PUTs the bytes directly to R2 using ``upload_url``.
3. ``POST /api/v1/pois`` (Phase 2.2.4) accepts ``photo_upload_id``; the
   submission service will HEAD the object, verify magic bytes, copy from
   ``tmp/`` to ``photos/`` and mark the upload claimed (claim glue lives
   in services/photo_service; the wiring on POST /pois is added separately
   to keep this commit small).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import r2
from app.db import get_session
from app.deps import get_current_user
from app.models.user import User
from app.schemas.upload import PhotoPresignRequest, PhotoPresignResponse
from app.services.photo_service import create_pending_upload

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post(
    "/photo-presign",
    response_model=PhotoPresignResponse,
    status_code=status.HTTP_201_CREATED,
)
async def photo_presign(
    payload: PhotoPresignRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> PhotoPresignResponse:
    if not (settings.r2_account_id and settings.r2_access_key_id):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="photo storage not configured",
        )

    try:
        upload = await create_pending_upload(
            session,
            user_id=user.id,
            content_type=payload.content_type,
            ttl_seconds=settings.photo_upload_ttl_seconds,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        spec = r2.presign_put(
            settings,
            key=upload.object_key,
            content_type=payload.content_type,
            expires_in=settings.photo_upload_ttl_seconds,
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"presign failed: {e}",
        )

    await session.commit()

    return PhotoPresignResponse(
        upload_id=upload.id,
        upload_url=spec.url,
        fields=spec.fields,
        expires_at=upload.expires_at,
    )
