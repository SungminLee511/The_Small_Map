"""Unit tests for ``seoul_public_toilets`` importer normalize() (1.3.4)."""

from __future__ import annotations

from app.importers.seoul_public_toilets import SeoulPublicToiletsImporter


def _row(**overrides):
    base = {
        "화장실관리번호": "MAPO-T-0001",
        "화장실명": "마포구청 1층 화장실",
        "소재지도로명주소": "서울특별시 마포구 월드컵로 212",
        "소재지지번주소": "서울특별시 마포구 성산동 370-1",
        "WGS84위도": "37.566535",
        "WGS84경도": "126.901320",
        "남녀공용화장실여부": "N",
        "남성용-대변기수": "3",
        "여성용-대변기수": "4",
        "장애인용화장실설치여부": "Y",
        "개방시간": "09:00-18:00",
        "기저귀교환대유무": "Y",
        "데이터기준일자": "2026-04-30",
    }
    base.update(overrides)
    return base


def test_normalize_happy_path():
    imp = SeoulPublicToiletsImporter(csv_path=None)
    row = _row()
    item = imp.normalize(row)
    assert item is not None
    assert item.external_id == "MAPO-T-0001"
    assert item.name == "마포구청 1층 화장실"
    assert abs(item.lat - 37.566535) < 1e-6
    assert abs(item.lng - 126.901320) < 1e-6
    assert item.attributes["accessibility"] is True
    assert item.attributes["gender"] == "separate"
    assert item.attributes["is_free"] is True
    assert item.attributes["has_baby_changing"] is True
    assert item.attributes["opening_hours"] == "09:00-18:00"
    assert item.last_verified_at is not None


def test_normalize_unisex():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(_row(**{"남녀공용화장실여부": "Y"}))
    assert item is not None
    assert item.attributes["gender"] == "unisex"


def test_normalize_skips_outside_district():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(
        _row(**{
            "소재지도로명주소": "서울특별시 강남구 테헤란로 1",
            "소재지지번주소": "서울특별시 강남구 역삼동 1",
        })
    )
    assert item is None


def test_normalize_skips_missing_id():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(_row(**{"화장실관리번호": ""}))
    assert item is None


def test_normalize_skips_invalid_coords():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(_row(**{"WGS84위도": "abc"}))
    assert item is None


def test_normalize_skips_out_of_korea():
    imp = SeoulPublicToiletsImporter()
    item = imp.normalize(_row(**{"WGS84위도": "10.0", "WGS84경도": "10.0"}))
    assert item is None


def test_csv_reader_decodes_cp949(tmp_path):
    # Build a CP949-encoded CSV in memory
    headers = [
        "화장실관리번호", "화장실명", "소재지도로명주소", "소재지지번주소",
        "WGS84위도", "WGS84경도", "남녀공용화장실여부",
        "남성용-대변기수", "여성용-대변기수",
        "장애인용화장실설치여부", "개방시간", "기저귀교환대유무", "데이터기준일자",
    ]
    rows = [
        [
            "MAPO-T-0001", "마포구청 화장실", "서울특별시 마포구 월드컵로 212",
            "서울특별시 마포구 성산동 370-1",
            "37.566535", "126.901320", "N", "3", "4", "Y", "09:00-18:00", "Y",
            "2026-04-30",
        ]
    ]
    csv_text = ",".join(headers) + "\n" + ",".join(rows[0]) + "\n"
    p = tmp_path / "toilets.csv"
    p.write_bytes(csv_text.encode("cp949"))

    imp = SeoulPublicToiletsImporter(csv_path=p)
    parsed = imp._read_csv(p.read_bytes())
    assert len(parsed) == 1
    assert parsed[0]["화장실관리번호"] == "MAPO-T-0001"
