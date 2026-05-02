"""Importer framework for ingesting public-data POIs.

Each importer subclass:
  - declares ``source_id`` (e.g. ``seoul.public_toilets``) and ``poi_type``
  - implements ``fetch_raw()`` to pull raw rows from the source
  - implements ``normalize()`` to map a raw row to a ``POIInput``
  - inherits ``run()`` which handles upsert, idempotency, and soft-delete

Idempotency is enforced via the partial unique index on
``(source, external_id)`` on the ``pois`` table (Phase 1.3.1 migration).

Soft-delete grace period
------------------------
When the source no longer contains a POI we previously imported, we don't
delete it on the very next run — sources flake. We allow 2 import cycles
of staleness before flipping ``status = removed``. Concretely: if a POI's
``last_verified_at`` is older than ``now - 2 * cycle_days``, soft-delete it.
"""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Sequence

from geoalchemy2 import WKTElement
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.poi import POI, POIStatus, POIType
from app.schemas.poi_attributes import validate_attributes

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class POIInput:
    """Normalized POI ready to upsert. Coordinates already in WGS84."""

    external_id: str
    poi_type: POIType
    lat: float
    lng: float
    name: str | None = None
    attributes: dict = field(default_factory=dict)
    last_verified_at: datetime | None = None  # source's "as of" date if known


@dataclass
class ImportReport:
    """Summary of an importer run."""

    source_id: str
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    removed: int = 0
    errors: list[str] = field(default_factory=list)

    def total(self) -> int:
        return self.created + self.updated + self.unchanged

    def __str__(self) -> str:
        return (
            f"[{self.source_id}] created={self.created} updated={self.updated} "
            f"unchanged={self.unchanged} removed={self.removed} "
            f"errors={len(self.errors)}"
        )


class BaseImporter(abc.ABC):
    """Subclass and implement ``fetch_raw`` + ``normalize``."""

    source_id: str
    poi_type: POIType
    cycle_days: int = 30  # how often this importer runs; used for grace period

    @abc.abstractmethod
    async def fetch_raw(self) -> Sequence[dict]:
        """Pull raw rows from the source. Must return iterable of dict-like rows."""

    @abc.abstractmethod
    def normalize(self, raw: dict) -> POIInput | None:
        """Map a raw row to a POIInput. Return None to skip the row."""

    # --- internals -----------------------------------------------------------

    def _wkt(self, lat: float, lng: float) -> WKTElement:
        return WKTElement(f"POINT({lng} {lat})", srid=4326)

    async def _upsert_one(
        self, session: AsyncSession, item: POIInput, now: datetime
    ) -> str:
        """Insert or update a single POI by (source, external_id).

        Returns one of: 'created', 'updated', 'unchanged'.
        """
        validated_attrs = validate_attributes(item.poi_type, item.attributes)
        last_verified = item.last_verified_at or now

        # Try to find existing
        existing = (
            await session.execute(
                select(POI).where(
                    POI.source == self.source_id,
                    POI.external_id == item.external_id,
                )
            )
        ).scalar_one_or_none()

        wkt = self._wkt(item.lat, item.lng)

        if existing is None:
            stmt = pg_insert(POI).values(
                poi_type=item.poi_type,
                location=wkt,
                name=item.name,
                attributes=validated_attrs,
                source=self.source_id,
                external_id=item.external_id,
                last_verified_at=last_verified,
                status=POIStatus.active,
            )
            await session.execute(stmt)
            return "created"

        # Detect changes (cheap-ish)
        changed = (
            existing.poi_type != item.poi_type
            or existing.name != item.name
            or (existing.attributes or {}) != validated_attrs
            or existing.status != POIStatus.active
        )
        # Always refresh last_verified_at on a re-import (proves it's still there)
        existing.last_verified_at = last_verified
        if changed:
            existing.poi_type = item.poi_type
            existing.location = wkt
            existing.name = item.name
            existing.attributes = validated_attrs
            existing.status = POIStatus.active
            return "updated"
        return "unchanged"

    async def _soft_delete_stale(
        self, session: AsyncSession, run_started_at: datetime
    ) -> int:
        """Soft-delete POIs from this source whose last_verified_at predates
        ``run_started_at - 2 * cycle_days``.
        """
        cutoff = run_started_at - timedelta(days=2 * self.cycle_days)
        stmt = (
            update(POI)
            .where(
                POI.source == self.source_id,
                POI.status == POIStatus.active,
                POI.last_verified_at.is_not(None),
                POI.last_verified_at < cutoff,
            )
            .values(status=POIStatus.removed)
        )
        result = await session.execute(stmt)
        return result.rowcount or 0

    # --- public API ----------------------------------------------------------

    async def run(self, session: AsyncSession) -> ImportReport:
        """Run a full import cycle: fetch → normalize → upsert → soft-delete."""
        report = ImportReport(source_id=self.source_id)
        run_started_at = datetime.now(timezone.utc)

        try:
            raw_rows = await self.fetch_raw()
        except Exception as e:  # noqa: BLE001
            report.errors.append(f"fetch_raw failed: {e}")
            logger.exception("fetch_raw failed for %s", self.source_id)
            return report

        for raw in raw_rows:
            try:
                item = self.normalize(raw)
            except Exception as e:  # noqa: BLE001
                report.errors.append(f"normalize failed: {e}")
                continue
            if item is None:
                continue
            try:
                outcome = await self._upsert_one(session, item, run_started_at)
                if outcome == "created":
                    report.created += 1
                elif outcome == "updated":
                    report.updated += 1
                else:
                    report.unchanged += 1
            except Exception as e:  # noqa: BLE001
                report.errors.append(f"upsert failed for {item.external_id}: {e}")

        try:
            report.removed = await self._soft_delete_stale(session, run_started_at)
        except Exception as e:  # noqa: BLE001
            report.errors.append(f"soft-delete failed: {e}")

        await session.commit()
        logger.info(str(report))
        return report
