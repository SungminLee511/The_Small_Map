# Importer Data Sources

> ✅ **Phase 1.2 schema verification complete (2026-05-02).**
> The toilet schema below was verified against the
> 전국공중화장실표준데이터 snapshot dated **2024-02-18** (32 columns,
> 6 089 rows nationwide, 194 in Mapo-gu). The smoking-area schema is
> still an educated guess — the data.go.kr file is login-gated and we
> have not yet pulled a real snapshot. When that happens, expect
> `seoul_smoking_areas.py` to need adjustments.

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
| Format         | CSV (CP949) **and** XLSX — the importer accepts either                |
| Encoding       | CSV: CP949 with UTF-8 / UTF-8-sig fallback. XLSX: native              |
| Coord system   | WGS84 — but **47 % of nationwide rows have blank coords**             |
| License        | KOGL Type 1 (attribution required)                                    |
| Update freq    | Monthly                                                               |
| Managing org   | Ministry of Interior and Safety                                       |
| External ID    | **Synthetic** — sha1 of `(road_addr | lot_addr | name)`               |
| Filter         | `소재지도로명주소` LIKE '%마포구%' OR `소재지지번주소` LIKE '%마포구%' |
| Snapshot used  | 2024-02-18 (mirror: github.com/NiSeullent/neomu-geuphae)              |

### Real schema (32 columns)

```
번호, 구분, 근거, 화장실명, 소재지도로명주소, 소재지지번주소,
남성용-대변기수, 남성용-소변기수,
남성용-장애인용대변기수, 남성용-장애인용소변기수,
남성용-어린이용대변기수, 남성용-어린이용소변기수,
여성용-대변기수, 여성용-장애인용대변기수, 여성용-어린이용대변기수,
관리기관명, 전화번호, 개방시간, 개방시간상세, 설치연월,
WGS84위도, WGS84경도, 화장실소유구분, 오물처리방식,
안전관리시설설치대상여부, 비상벨설치여부, 비상벨설치장소,
화장실입구CCTV설치유무, 기저귀교환대유무, 기저귀교환대장소,
리모델링연월, 데이터기준일자
```

### Schema mapping

| Source column                              | POI field                              |
|--------------------------------------------|----------------------------------------|
| `화장실명`                                 | `name`                                 |
| `소재지도로명주소` / `소재지지번주소`      | `attributes.address` (kept for debug)  |
| `WGS84위도`                                | `location.lat` (or geocode address)    |
| `WGS84경도`                                | `location.lng` (or geocode address)    |
| sum of `남성용-*` / `여성용-*` stall cols  | `attributes.gender` (separate / male_only / female_only) |
| sum of `*-장애인용*` stall cols > 0        | `attributes.accessibility` (bool)      |
| `개방시간상세` ‖ `개방시간`                 | `attributes.opening_hours`             |
| `기저귀교환대유무`                          | `attributes.has_baby_changing` (bool)  |
| `데이터기준일자`                            | `last_verified_at`                     |
| sha1(`addr | name`) → `seoul-tol-<16 hex>` | `external_id`                          |

`is_free`: assumed `true` for public toilets unless source flags otherwise.

### Phase 1.2 surprises (vs the original guess)

1. **No stable PK column.** The dataset has only a sequential `번호`
   that is not stable across snapshots. We synthesise an `external_id`
   from `(road_addr | lot_addr | name)` and rely on the partial unique
   index `(source, external_id)` for upsert idempotency.
2. **No `남녀공용화장실여부` flag.** Gender is derived purely from the
   per-fixture stall counts. (Unisex rows in the wild are rare — usually
   appear as separate male+female counts.)
3. **No `장애인용화장실설치여부` flag.** Accessibility = `True` when
   the sum of disabled-stall counts is positive, `False` when all are
   zero, `None` when every disabled-stall column is blank.
4. **Mapo-gu has 0 % coordinate coverage.** All 194 Mapo rows in the
   2024-02-18 snapshot have blank `WGS84위도/경도` (most are subway
   station toilets). The importer therefore **requires** an injected
   geocoder for Mapo to recover any rows. Without one, every Mapo row
   is skipped and the count is reported in `ImportReport.errors`.
5. **47 % nationwide coord coverage.** Other gu have varying coverage;
   the same geocoder fallback applies.
6. **Two opening-hours columns.** `개방시간` is coarse (`정시`,
   `평일`, etc.); `개방시간상세` is the actual time window. The importer
   prefers the detail column.

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
| Schema status  | ⚠️ Still guessed — no real CSV pulled yet                              |

### Schema mapping (guessed)

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

**Importer wiring:** both `seoul_public_toilets` and
`seoul_smoking_areas` accept an injectable `geocoder: Callable[[str],
Awaitable[(lat,lng) | None]]`. They share an in-memory per-run cache
keyed on the raw address string.

---

## 5. License & Attribution

All KOGL Type 1 datasets require attribution. The frontend POI detail panel
must show:

> 출처: 공공데이터포털 (data.go.kr) — `<dataset name>` (`<as_of date>`)

Add a global attributions block on the About page listing every importer's
source, license, and last-fetched date.

---

## 6. Known good snapshot mirrors (for testing without the portal login)

The official `data.go.kr` file download is gated behind a logged-in
session. For unattended CI / test pulls, the following community
mirrors have been verified to serve the same XLSX bytes:

| Source                                             | Dataset                | Snapshot date |
|----------------------------------------------------|------------------------|---------------|
| `github.com/NiSeullent/neomu-geuphae`              | Public toilets         | 2024-02-18    |
| `github.com/NiSeullent/neomu-geuphae` (same repo)  | Free Wi-Fi (unrelated) | —             |

Mirrors are not under our control — treat them as opportunistic and
fall back to the official portal for production runs.
