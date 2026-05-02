"""Confirmation service (Phase 2.2.7).

A POI is "verified" once its submitter plus 2 distinct other confirmers
attest to it (3 total). The submitter counts once via
``POI.verification_count = 1`` at submit time; we count *additional*
confirmers here.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.models.poi import POI, POIStatus, POIVerificationStatus
from app.models.poi_confirmation import POIConfirmation
from app.models.user import User

VERIFICATION_THRESHOLD = 3  # submitter + 2 confirmers


class POINotFound(Exception):
    pass


class CannotConfirmOwnSubmission(Exception):
    pass


class AlreadyConfirmed(Exception):
    pass


@dataclass
class ConfirmResult:
    poi_id: uuid.UUID
    verification_count: int
    verification_status: POIVerificationStatus
    flipped_to_verified: bool
    submitter_reputation_delta: int


async def confirm_poi(
    session: AsyncSession, *, poi_id: uuid.UUID, user: User
) -> ConfirmResult:
    """Record a confirmation. Idempotent: re-confirming raises ``AlreadyConfirmed``.

    - Reject if the user is the original submitter (source = "user:<their id>")
    - Increment verification_count, refresh last_verified_at
    - Flip to verified once threshold crossed
    - Bump submitter reputation by 1 on every confirmation (Phase 4 will
      replace this direct mutation with a reputation_event row)
    """
    poi = (
        await session.execute(
            select(POI).where(POI.id == poi_id, POI.status == POIStatus.active)
        )
    ).scalar_one_or_none()
    if poi is None:
        raise POINotFound(str(poi_id))

    if poi.source == f"user:{user.id}":
        raise CannotConfirmOwnSubmission()

    confirmation = POIConfirmation(poi_id=poi.id, user_id=user.id)
    session.add(confirmation)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise AlreadyConfirmed()

    poi.verification_count = (poi.verification_count or 0) + 1
    poi.last_verified_at = datetime.now(timezone.utc)

    flipped = False
    if (
        poi.verification_status != POIVerificationStatus.verified
        and poi.verification_count >= VERIFICATION_THRESHOLD
    ):
        poi.verification_status = POIVerificationStatus.verified
        flipped = True

    submitter_delta = 0
    submitter_id = _submitter_id_from_source(poi.source)
    if submitter_id is not None and submitter_id != user.id:
        submitter = (
            await session.execute(
                select(User).where(User.id == submitter_id)
            )
        ).scalar_one_or_none()
        if submitter is not None and not submitter.is_banned:
            submitter.reputation = (submitter.reputation or 0) + 1
            submitter_delta = 1
            # Phase 3.3.5: notify submitter when their POI flips verified
            if flipped:
                session.add(
                    Notification(
                        id=uuid.uuid4(),
                        user_id=submitter.id,
                        type=NotificationType.poi_verified,
                        payload={
                            "poi_id": str(poi.id),
                            "verified_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                )

    return ConfirmResult(
        poi_id=poi.id,
        verification_count=poi.verification_count,
        verification_status=poi.verification_status,
        flipped_to_verified=flipped,
        submitter_reputation_delta=submitter_delta,
    )


def _submitter_id_from_source(source: str) -> uuid.UUID | None:
    if not source.startswith("user:"):
        return None
    try:
        return uuid.UUID(source.split(":", 1)[1])
    except (ValueError, TypeError):
        return None
