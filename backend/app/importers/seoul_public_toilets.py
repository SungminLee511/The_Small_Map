"""Importer: Seoul (Mapo-gu) public toilets.

Source: 전국공중화장실표준데이터 (National Public Toilet Standard Data)
Portal: https://www.data.go.kr/data/15012892/standard.do

NOTE (Phase 1.2 was skipped at user request — option (a)). The exact column
names and API shape below are educated guesses based on the standard-data
documentation; verify against a real CSV/API response and adjust ``normalize``
accordingly. The fixture-based unit tests document the assumed shape.
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import httpx

from app.importers.base import BaseImporter, POIInput
from app.models.poi import POIType

logger = logging.getLogger(__name__)


# Source column names (Korean) — may need adjusting once we hit a real file.
COL_EXTERNAL_ID = "화장실관리번호"
COL_NAME = "화장실명"
COL_ROAD_ADDR = "소재지도로명주소"
COL_LOT_ADDR = "소재지지번주소"
COL_LAT = "WGS84위도"
COL_LNG = "WGS84경도"
COL_UNISEX = "남녀공용화장실여부"
COL_MEN_TOILETS = "남성용-대변기수"
COL_WOMEN_TOILETS = "여성용-대변기수"
COL_ACCESSIBLE = "장애인용화장실설치여부"
COL_HOURS = "개방시간"
COL_BABY = "기저귀교환대유무"
COL_AS_OF = "데이터기준일자"

DISTRICT_KEYWORD = "마포구"


def _truthy(val) -> bool | None:
    """Korean public CSVs use 'Y'/'N'/'있음'/'없음'. Map to bool, None if blank."""
    if val is None:
        return None
    s = str(val).strip().upper()
    if s in {"", "-", "N/A", "NULL"}:
        return None
    if s in {"Y", "YES", "TRUE", "1", "있음", "유"}:
        return True
    if s in {"N", "NO", "FALSE", "0", "없음", "무"}:
        return False
    return None


def _to_int(val) -> int | None:
    if val is None or str(val).strip() == "":
        return None
    try:
        return int(float(str(val).strip()))
    except (TypeError, ValueError):
        return None


def _parse_as_of(val) -> datetime | None:
    if not val:
        return None
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


class SeoulPublicToiletsImporter(BaseImporter):
    source_id = "seoul.public_toilets"
    poi_type = POIType.toilet
    cycle_days = 30

    def __init__(
        self,
        *,
        csv_path: str | Path | None = None,
        api_url: str | None = None,
        district_keyword: str = DISTRICT_KEYWORD,
        encoding: str = "cp949",
    ):
        self.csv_path = Path(csv_path) if csv_path else None
        self.api_url = api_url
        self.district_keyword = district_keyword
        self.encoding = encoding

    async def fetch_raw(self) -> Sequence[dict]:
        """Read rows from a local CSV (preferred for testing) or HTTP API."""
        if self.csv_path is not None:
            return self._read_csv(self.csv_path.read_bytes())
        if self.api_url is not None:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(self.api_url)
                resp.raise_for_status()
                # Public-data portal often returns JSON with 'data' key
                payload = resp.json()
                if isinstance(payload, dict) and "data" in payload:
                    return payload["data"]
                if isinstance(payload, list):
                    return payload
                return []
        raise RuntimeError("Either csv_path or api_url must be provided")

    def _read_csv(self, raw_bytes: bytes) -> list[dict]:
        # Korean public CSVs are typically CP949
        text = raw_bytes.decode(self.encoding, errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        return list(reader)

    def _is_in_district(self, row: dict) -> bool:
        if not self.district_keyword:
            return True
        for col in (COL_ROAD_ADDR, COL_LOT_ADDR):
            v = row.get(col)
            if v and self.district_keyword in str(v):
                return True
        return False

    def normalize(self, raw: dict) -> POIInput | None:
        if not self._is_in_district(raw):
            return None

        ext_id = (raw.get(COL_EXTERNAL_ID) or "").strip()
        if not ext_id:
            return None

        try:
            lat = float(raw.get(COL_LAT))
            lng = float(raw.get(COL_LNG))
        except (TypeError, ValueError):
            logger.warning("toilet %s: missing/invalid lat-lng, skipping", ext_id)
            return None

        # Sanity: rough Korea bbox
        if not (33.0 <= lat <= 39.0 and 124.0 <= lng <= 132.0):
            logger.warning("toilet %s: lat/lng out of Korea bbox, skipping", ext_id)
            return None

        # Gender layout
        unisex = _truthy(raw.get(COL_UNISEX))
        men = _to_int(raw.get(COL_MEN_TOILETS)) or 0
        women = _to_int(raw.get(COL_WOMEN_TOILETS)) or 0
        if unisex is True:
            gender = "unisex"
        elif men > 0 and women > 0:
            gender = "separate"
        elif men > 0:
            gender = "male_only"
        elif women > 0:
            gender = "female_only"
        else:
            gender = None

        attributes = {
            "accessibility": _truthy(raw.get(COL_ACCESSIBLE)),
            "gender": gender,
            "opening_hours": (raw.get(COL_HOURS) or None) or None,
            "is_free": True,  # Public toilets are free unless flagged otherwise
            "has_baby_changing": _truthy(raw.get(COL_BABY)),
            # Keep original address for debugging — extra='allow' on schema
            "address": (raw.get(COL_ROAD_ADDR) or raw.get(COL_LOT_ADDR) or None),
        }
        # Drop None values to keep storage tidy
        attributes = {k: v for k, v in attributes.items() if v is not None}

        return POIInput(
            external_id=ext_id,
            poi_type=POIType.toilet,
            lat=lat,
            lng=lng,
            name=(raw.get(COL_NAME) or "").strip() or None,
            attributes=attributes,
            last_verified_at=_parse_as_of(raw.get(COL_AS_OF)),
        )
