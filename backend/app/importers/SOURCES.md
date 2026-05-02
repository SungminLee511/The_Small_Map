# Importer Data Sources

This document maps the public datasets used by Phase 1 importers to the
internal `POI` model. **Verify the URLs and schemas at the time of import** —
Korean public data portals change column names and formats frequently.

Target district for v1: **Mapo-gu (마포구), Seoul**.

All `POI.location` is `geography(Point, 4326)` (WGS84). Datasets in EPSG:5174
or EPSG:5179 must be reprojected with `pyproj` before insert.

---

## 1. Public Toilets (`seoul.public_toilets`)

| Field          | Value                                                                 |
|----------------|-----------------------------------------------------------------------|
| Dataset        | 전국공중화장실표준데이터 (National Public Toilet Standard Data)       |
| Portal URL     | https://www.data.go.kr/data/15012892/standard.do                      |
| Format         | CSV (file download) + Open API (JSON/XML)                             |
| Encoding       | CP949 / EUC-KR (CSV) — must be decoded                                |
| Coord system   | WGS84 (lat/lng columns provided)                                      |
| License        | KOGL Type 1 (attribution required)                                    |
| Update freq    | Monthly                                                               |
| Managing org   | Ministry of Interior and Safety                                       |
| External ID    | `화장실관리번호` (toilet management number)                           |
| Filter         | `소재지도로명주소` LIKE '%마포구%' OR `소재지지번주소` LIKE '%마포구%' |

### Schema mapping

| Source column                | POI field                              |
|------------------------------|----------------------------------------|
| `화장실명`                   | `name`                                 |
| `소재지도로명주소`           | `attributes.address` (kept for debug)  |
| `WGS84위도`                  | `location.lat`                         |
| `WGS84경도`                  | `location.lng`                         |
| `남녀공용화장실여부`         | `attributes.gender` (`unisex` if "Y")  |
| `남성용-대변기수` etc.       | `attributes.gender` (`separate` if both genders > 0) |
| `장애인용화장실설치여부`     | `attributes.accessibility` (bool)      |
| `개방시간`                   | `attributes.opening_hours`             |
| `기저귀교환대유무`           | `attributes.has_baby_changing` (bool)  |
| `데이터기준일자`             | `last_verified_at`                     |
| `화장실관리번호`             | `external_id`                          |

`is_free`: assumed `true` for public toilets unless source flags otherwise.

---

## 2. Smoking Areas (`mapo.smoking_areas`)

| Field          | Value                                                                 |
|----------------|-----------------------------------------------------------------------|
| Dataset        | 서울특별시 마포구_흡연시설 현황                                       |
| Portal URL     | https://www.data.go.kr/data/15068847/fileData.do                      |
| Format         | CSV (file download)                                                   |
| Encoding       | CP949 likely                                                          |
| Coord system   | Address-only (no lat/lng) → **geocode with Kakao Local API**          |
| License        | KOGL Type 1                                                           |
| Update freq    | Quarterly (last seen 2025-04-30)                                      |
| Managing org   | 마포구청 (Mapo-gu Office)                                             |
| External ID    | row index + address hash (no stable PK)                               |

### Schema mapping

| Source column            | POI field                                |
|--------------------------|------------------------------------------|
| `시설명` / `상호`        | `name`                                   |
| `주소` / `소재지`        | (geocoded → `location`)                  |
| `흡연시설형태`           | `attributes.enclosed` (bool: 폐쇄형=true)|
| `운영시간` (if present)  | `attributes.opening_hours`               |

### Notes

- Geocoding cache: store `(address → lat/lng, geocoded_at)` in a
  `geocode_cache` table to avoid repeat Kakao calls.
- Mapo-gu publishes business-level smoking facilities, not street-level
  designated outdoor smoking zones — match the user expectation in the UI.

---

## 3. Datasets Investigated, Deferred for Phase 1

These are not implemented in Phase 1 due to coverage / quality issues:

| Type            | Dataset                                  | Reason deferred                             |
|-----------------|------------------------------------------|---------------------------------------------|
| Trash cans      | None Mapo-specific found                 | No Mapo-gu open dataset; user-submitted only |
| Benches         | Park furniture datasets vary             | Not standardized; pending park-level fetch  |
| Water fountains | Park drinking-water spots (Seoul-wide)   | Coverage in Mapo too sparse to be useful    |

Plan: re-evaluate after Phase 2 user submissions populate these types.

---

## 4. Geocoder

- **Kakao Local API** — `GET https://dapi.kakao.com/v2/local/search/address.json`
- Header: `Authorization: KakaoAK <REST_API_KEY>`
- Quota: 100,000/day (free tier).
- Response: `documents[0].x` (lng), `documents[0].y` (lat) — strings, cast to float.
- Cache results indefinitely; addresses rarely move.

---

## 5. License & Attribution

All KOGL Type 1 datasets require attribution. The frontend POI detail panel
must show:

> 출처: 공공데이터포털 (data.go.kr) — `<dataset name>` (`<as_of date>`)

Add a global attributions block on the About page listing every importer's
source, license, and last-fetched date.
