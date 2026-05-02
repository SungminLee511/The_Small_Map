"""Importer: Mapo-gu smoking areas.

Source: 서울특별시 마포구_흡연시설 현황 (Mapo-gu smoking facilities)
Portal: https://www.data.go.kr/data/15068847/fileData.do

NOTE (Phase 1.2 was skipped at user request — option (a)). The exact column
names below are guesses; rows in the file have addresses but no lat/lng, so
each row must be geocoded via the Kakao Local API. A geocoder callable is
injected so unit tests can stub it out.
"""

from __future__ import annotations

import csv
import hashlib
import io
import logging
from pathlib import Path
from typing import Awaitable, Callable, Sequence

import httpx

from app.importers.base import BaseImporter, POIInput
from app.models.poi import POIType

logger = logging.getLogger(__name__)


COL_NAME = "시설명"
COL_NAME_ALT = "상호"
COL_ADDR = "주소"
COL_ADDR_ALT = "소재지"
COL_FORM = "흡연시설형태"  # 폐쇄형 / 개방형
COL_HOURS = "운영시간"

ENCLOSED_KEYWORDS = ("폐쇄", "실내", "부스")


GeocoderFn = Callable[[str], Awaitable[tuple[float, float] | None]]


async def kakao_geocode(address: str, *, rest_api_key: str) -> tuple[float, float] | None:
    """Geocode a Korean address with Kakao Local API. Returns (lat, lng) or None."""
    if not address:
        return None
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {rest_api_key}"}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=headers, params={"query": address})
        if resp.status_code != 200:
            logger.warning("Kakao geocode failed (%d) for %s", resp.status_code, address)
            return None
        docs = resp.json().get("documents") or []
        if not docs:
            return None
        try:
            return float(docs[0]["y"]), float(docs[0]["x"])
        except (KeyError, ValueError, TypeError):
            return None


def _row_external_id(row: dict, idx: int) -> str:
    """Stable id from address + name (no source PK in this dataset)."""
    addr = (row.get(COL_ADDR) or row.get(COL_ADDR_ALT) or "").strip()
    name = (row.get(COL_NAME) or row.get(COL_NAME_ALT) or "").strip()
    blob = f"{addr}|{name}|{idx}".encode("utf-8")
    return "mapo-smk-" + hashlib.sha1(blob).hexdigest()[:16]


class MapoSmokingAreasImporter(BaseImporter):
    source_id = "mapo.smoking_areas"
    poi_type = POIType.smoking_area
    cycle_days = 90  # Mapo-gu publishes quarterly

    def __init__(
        self,
        *,
        csv_path: str | Path | None = None,
        rows: Sequence[dict] | None = None,
        geocoder: GeocoderFn | None = None,
        encoding: str = "cp949",
    ):
        self.csv_path = Path(csv_path) if csv_path else None
        self._rows_override = rows
        self.geocoder = geocoder
        self.encoding = encoding
        # Per-run geocode cache so repeated identical addresses don't hammer Kakao
        self._geocode_cache: dict[str, tuple[float, float] | None] = {}

    async def fetch_raw(self) -> Sequence[dict]:
        if self._rows_override is not None:
            return list(self._rows_override)
        if self.csv_path is not None:
            text = self.csv_path.read_bytes().decode(self.encoding, errors="replace")
            return list(csv.DictReader(io.StringIO(text)))
        raise RuntimeError("Either csv_path or rows must be provided")

    async def _geocode(self, address: str) -> tuple[float, float] | None:
        if address in self._geocode_cache:
            return self._geocode_cache[address]
        if self.geocoder is None:
            return None
        result = await self.geocoder(address)
        self._geocode_cache[address] = result
        return result

    def normalize(self, raw: dict) -> POIInput | None:
        # We need geocoding to attach a location, so normalize is a *partial* —
        # see _normalize_async for the full path used by run_async below.
        return None  # pragma: no cover

    async def _normalize_async(
        self, raw: dict, idx: int
    ) -> POIInput | None:
        addr = (raw.get(COL_ADDR) or raw.get(COL_ADDR_ALT) or "").strip()
        if not addr:
            return None
        name = (raw.get(COL_NAME) or raw.get(COL_NAME_ALT) or "").strip() or None
        ext_id = _row_external_id(raw, idx)

        coords = await self._geocode(addr)
        if coords is None:
            logger.warning("smoking %s: geocode failed for %s", ext_id, addr)
            return None
        lat, lng = coords

        form = (raw.get(COL_FORM) or "").strip()
        enclosed: bool | None = None
        if form:
            enclosed = any(kw in form for kw in ENCLOSED_KEYWORDS)

        attributes = {
            "enclosed": enclosed,
            "opening_hours": (raw.get(COL_HOURS) or None),
            "address": addr,
        }
        attributes = {k: v for k, v in attributes.items() if v is not None}

        return POIInput(
            external_id=ext_id,
            poi_type=POIType.smoking_area,
            lat=lat,
            lng=lng,
            name=name,
            attributes=attributes,
        )

    # Override run() to thread the async geocode call through normalize.
    async def run(self, session):  # type: ignore[override]
        from datetime import datetime, timezone

        from app.importers.base import ImportReport

        report = ImportReport(source_id=self.source_id)
        run_started_at = datetime.now(timezone.utc)

        try:
            raw_rows = await self.fetch_raw()
        except Exception as e:  # noqa: BLE001
            report.errors.append(f"fetch_raw failed: {e}")
            return report

        for idx, raw in enumerate(raw_rows):
            try:
                item = await self._normalize_async(raw, idx)
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
        return report
