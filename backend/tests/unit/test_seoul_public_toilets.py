"""Unit tests for ``seoul_public_toilets`` importer.

Schema verified against the 2024-02-18 standard-data snapshot
(see SOURCES.md). The fixture rows below mirror that real shape — no
``화장실관리번호`` PK column, no ``남녀공용화장실여부`` flag,
accessibility derived from per-fixture disabled-stall counts.
"""

from __future__ import annotations

import asyncio

from app.importers.seoul_public_toilets import (
    SeoulPublicToiletsImporter,
    _row_external_id,
)


def _row(**overrides):
    base = {
        # No 화장실관리번호 in the real schema — only sequential 번호.
        "번호": "42",
        "구분": "개방화장실",
        "화장실명": "마포구청 1층 화장실",
        "소재지도로명주소": "서울특별시 마포구 월드컵로 212",
        "소재지지번주소": "서울특별시 마포구 성산동 370-1",
        "WGS84위도": "37.566535",
        "WGS84경도": "126.901320",
        "남성용-대변기수": "3",
        "남성용-소변기수": "3",
        "남성용-장애인용대변기수": "1",
        "남성용-장애인용소변기수": "0",
        "여성용-대변기수": "4",
        "여성용-장애인용대변기수": "1",
        "개방시간": "정시",
        "개방시간상세": "06:30~22:00",
        "기저귀교환대유무": "Y",
        "데이터기준일자": "2024-02-18",
    }
    base.update(overrides)
    return base


# --- happy path --------------------------------------------------------------


def test_normalize_happy_path():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(_row())
    assert item is not None
    assert item.external_id.startswith("seoul-tol-")
    assert item.name == "마포구청 1층 화장실"
    assert abs(item.lat - 37.566535) < 1e-6
    assert abs(item.lng - 126.901320) < 1e-6
    # Accessibility: 1+0+1 = 2 → True.
    assert item.attributes["accessibility"] is True
    # Gender: men_total = 6, women = 4 → separate.
    assert item.attributes["gender"] == "separate"
    assert item.attributes["is_free"] is True
    assert item.attributes["has_baby_changing"] is True
    # Opening_hours prefers the detail column.
    assert item.attributes["opening_hours"] == "06:30~22:00"
    assert item.last_verified_at is not None


# --- gender inference --------------------------------------------------------


def test_gender_male_only():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(
        _row(
            **{
                "여성용-대변기수": "0",
                "남성용-대변기수": "1",
                "남성용-소변기수": "1",
            }
        )
    )
    assert item is not None
    assert item.attributes["gender"] == "male_only"


def test_gender_female_only():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(
        _row(
            **{
                "남성용-대변기수": "0",
                "남성용-소변기수": "0",
                "여성용-대변기수": "2",
            }
        )
    )
    assert item is not None
    assert item.attributes["gender"] == "female_only"


def test_gender_blank_when_all_zero():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(
        _row(
            **{
                "남성용-대변기수": "0",
                "남성용-소변기수": "0",
                "여성용-대변기수": "0",
            }
        )
    )
    assert item is not None
    assert "gender" not in item.attributes  # None values are dropped


# --- accessibility from disabled-stall counts --------------------------------


def test_accessibility_true_when_any_disabled_stall():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(
        _row(
            **{
                "남성용-장애인용대변기수": "0",
                "남성용-장애인용소변기수": "0",
                "여성용-장애인용대변기수": "1",
            }
        )
    )
    assert item is not None
    assert item.attributes["accessibility"] is True


def test_accessibility_false_when_all_zero():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(
        _row(
            **{
                "남성용-장애인용대변기수": "0",
                "남성용-장애인용소변기수": "0",
                "여성용-장애인용대변기수": "0",
            }
        )
    )
    assert item is not None
    assert item.attributes["accessibility"] is False


def test_accessibility_omitted_when_all_blank():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(
        _row(
            **{
                "남성용-장애인용대변기수": "",
                "남성용-장애인용소변기수": "",
                "여성용-장애인용대변기수": "",
            }
        )
    )
    assert item is not None
    assert "accessibility" not in item.attributes


# --- composite external id ---------------------------------------------------


def test_composite_external_id_is_deterministic():
    a = _row()
    b = _row()
    assert _row_external_id(a) == _row_external_id(b)


def test_composite_external_id_differs_by_address():
    a = _row()
    b = _row(**{"소재지도로명주소": "서울특별시 마포구 월드컵로 9999"})
    assert _row_external_id(a) != _row_external_id(b)


def test_composite_external_id_differs_by_name():
    a = _row()
    b = _row(**{"화장실명": "마포구청 2층 화장실"})
    assert _row_external_id(a) != _row_external_id(b)


# --- skip rules --------------------------------------------------------------


def test_normalize_skips_outside_district():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(
        _row(
            **{
                "소재지도로명주소": "서울특별시 강남구 테헤란로 1",
                "소재지지번주소": "서울특별시 강남구 역삼동 1",
            }
        )
    )
    assert item is None


def test_normalize_skips_blank_coords_when_no_geocoder():
    imp = SeoulPublicToiletsImporter()
    # Real Mapo data: subway-station rows have blank coords.
    item = imp.normalize(_row(**{"WGS84위도": "", "WGS84경도": ""}))
    assert item is None


def test_normalize_skips_invalid_coords():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(_row(**{"WGS84위도": "abc"}))
    assert item is None


def test_normalize_skips_out_of_korea():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(_row(**{"WGS84위도": "10.0", "WGS84경도": "10.0"}))
    assert item is None


# --- async geocoder fallback -------------------------------------------------


def test_normalize_async_uses_geocoder_when_coords_blank():
    calls = []

    async def fake_geocoder(addr: str):
        calls.append(addr)
        return (37.553, 126.945)

    imp = SeoulPublicToiletsImporter(geocoder=fake_geocoder)
    row = _row(**{"WGS84위도": "", "WGS84경도": ""})
    item = asyncio.run(imp._normalize_async(row))
    assert item is not None
    assert abs(item.lat - 37.553) < 1e-6
    assert abs(item.lng - 126.945) < 1e-6
    assert calls == ["서울특별시 마포구 월드컵로 212"]


def test_normalize_async_caches_geocoder_calls():
    calls = []

    async def fake_geocoder(addr: str):
        calls.append(addr)
        return (37.553, 126.945)

    imp = SeoulPublicToiletsImporter(geocoder=fake_geocoder)
    row = _row(**{"WGS84위도": "", "WGS84경도": ""})

    async def run_twice():
        await imp._normalize_async(row)
        await imp._normalize_async(row)

    asyncio.run(run_twice())
    assert len(calls) == 1  # second hit served from cache


def test_normalize_async_skips_when_geocoder_returns_none():
    async def fake_geocoder(addr: str):
        return None

    imp = SeoulPublicToiletsImporter(geocoder=fake_geocoder)
    row = _row(**{"WGS84위도": "", "WGS84경도": ""})
    item = asyncio.run(imp._normalize_async(row))
    assert item is None


# --- CSV reader fallbacks ----------------------------------------------------


def test_csv_reader_decodes_cp949(tmp_path):
    headers = [
        "번호", "화장실명", "소재지도로명주소", "소재지지번주소",
        "WGS84위도", "WGS84경도",
        "남성용-대변기수", "남성용-소변기수",
        "남성용-장애인용대변기수", "남성용-장애인용소변기수",
        "여성용-대변기수", "여성용-장애인용대변기수",
        "개방시간", "개방시간상세", "기저귀교환대유무", "데이터기준일자",
    ]
    rows = [
        [
            "1", "마포구청 화장실",
            "서울특별시 마포구 월드컵로 212", "서울특별시 마포구 성산동 370-1",
            "37.566535", "126.901320",
            "3", "3", "1", "0", "4", "1",
            "정시", "09:00-18:00", "Y", "2024-02-18",
        ]
    ]
    csv_text = ",".join(headers) + "\n" + ",".join(rows[0]) + "\n"
    p = tmp_path / "toilets.csv"
    p.write_bytes(csv_text.encode("cp949"))

    imp = SeoulPublicToiletsImporter(csv_path=p)
    parsed = imp._read_csv(p.read_bytes())
    assert len(parsed) == 1
    assert parsed[0]["화장실명"] == "마포구청 화장실"


def test_csv_reader_falls_back_to_utf8(tmp_path):
    """Some mirrors re-serve the file as UTF-8 — accept it without complaint."""
    headers = [
        "번호", "화장실명", "소재지도로명주소", "소재지지번주소",
        "WGS84위도", "WGS84경도", "남성용-대변기수", "여성용-대변기수",
    ]
    body = ",".join(headers) + "\n" + ",".join(
        ["1", "테스트화장실", "마포구 어딘가 1", "마포구 어딘가 1",
         "37.5", "127.0", "1", "1"]
    ) + "\n"
    p = tmp_path / "toilets.csv"
    p.write_bytes(body.encode("utf-8"))

    imp = SeoulPublicToiletsImporter(csv_path=p, encoding="cp949")
    parsed = imp._read_csv(p.read_bytes())
    assert parsed[0]["화장실명"] == "테스트화장실"


# --- xlsx round trip ---------------------------------------------------------


def test_xlsx_reader_round_trip(tmp_path):
    """End-to-end: build a tiny xlsx in the same shape as the standard data,
    feed it through the importer, and verify the row reaches normalize()."""
    openpyxl = __import__("openpyxl")
    headers = [
        "번호", "화장실명", "소재지도로명주소", "소재지지번주소",
        "WGS84위도", "WGS84경도",
        "남성용-대변기수", "남성용-소변기수",
        "남성용-장애인용대변기수", "남성용-장애인용소변기수",
        "여성용-대변기수", "여성용-장애인용대변기수",
        "개방시간", "개방시간상세", "기저귀교환대유무", "데이터기준일자",
    ]
    row = [
        1, "마포구청 화장실",
        "서울특별시 마포구 월드컵로 212",
        "서울특별시 마포구 성산동 370-1",
        "37.566535", "126.901320",
        "3", "3", "1", "0", "4", "1",
        "정시", "06:30~22:00", "Y", "2024-02-18",
    ]
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    ws.append(row)
    p = tmp_path / "toilets.xlsx"
    wb.save(p)

    imp = SeoulPublicToiletsImporter(xlsx_path=p)
    parsed = imp._read_xlsx(p)
    assert len(parsed) == 1
    item = imp.normalize(parsed[0])
    assert item is not None
    assert item.name == "마포구청 화장실"
    assert abs(item.lat - 37.566535) < 1e-6
    assert item.attributes["accessibility"] is True
    assert item.attributes["gender"] == "separate"
