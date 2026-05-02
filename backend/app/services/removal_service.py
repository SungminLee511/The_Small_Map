"""Removal-proposal service (Phase 4.2.4).

A user can propose that a POI no longer exists. Once
``REMOVAL_THRESHOLD`` distinct users have proposed it, the POI is
auto-soft-deleted (admin-reversible).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.poi import POI, POIStatus
from app.models.poi_removal_proposal import POIRemovalProposal
from app.services.moderation_service import soft_delete_poi

REMOVAL_THRESHOLD = 3


class POINotFound(Exception):
    pass


class CannotProposeOwnSubmission(Exception):
    pass


class AlreadyProposed(Exception):
    pass


@dataclass
class RemovalProposalResult:
    poi_id: uuid.UUID
    proposal_count: int
    soft_deleted: bool


async def propose_removal(
    session: AsyncSession,
    *,
    poi_id: uuid.UUID,
    user_id: uuid.UUID,
    reason: str | None,
) -> RemovalProposalResult:
    """Record a removal proposal. Idempotent per (poi, user).

    Raises:
      - POINotFound — POI doesn't exist or is already soft-deleted
      - CannotProposeOwnSubmission — submitter trying to remove their own POI
        (use the regular admin path / contact instead)
      - AlreadyProposed — same user already proposed removal of this POI
    """
    poi = (
        await session.execute(
            select(POI).where(POI.id == poi_id, POI.status == POIStatus.active)
        )
    ).scalar_one_or_none()
    if poi is None:
        raise POINotFound(str(poi_id))

    if poi.source == f"user:{user_id}":
        raise CannotProposeOwnSubmission()

    proposal = POIRemovalProposal(
        poi_id=poi.id, user_id=user_id, reason=(reason or None)
    )
    session.add(proposal)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise AlreadyProposed()

    count_res = await session.execute(
        select(func.count())
        .select_from(POIRemovalProposal)
        .where(POIRemovalProposal.poi_id == poi.id)
    )
    count = int(count_res.scalar_one())

    soft_deleted = False
    if count >= REMOVAL_THRESHOLD:
        # Auto soft-delete (no admin user — pass the proposing user as the
        # actor for audit trail; admin can later restore via DB).
        await soft_delete_poi(
            session,
            poi_id=poi.id,
            admin_user_id=user_id,
            reason=(
                f"auto-removed after {count} user proposals"
            ),
        )
        soft_deleted = True

    return RemovalProposalResult(
        poi_id=poi.id, proposal_count=count, soft_deleted=soft_deleted
    )


async def proposal_count_for_poi(
    session: AsyncSession, poi_id: uuid.UUID
) -> int:
    res = await session.execute(
        select(func.count())
        .select_from(POIRemovalProposal)
        .where(POIRemovalProposal.poi_id == poi_id)
    )
    return int(res.scalar_one() or 0)
