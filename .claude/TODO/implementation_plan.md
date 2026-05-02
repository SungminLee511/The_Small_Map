# The Small Map Project — Implementation Plan

This document is written to be handed directly to Claude Code (or any coding agent) as a working brief. It is divided into phases. Each phase has explicit tasks, schema changes, tests, and acceptance criteria. **Do not skip ahead.** Each phase ends in a working, testable, deployed-to-staging product before the next one starts.

-----

## 0. Project Overview

The Small Map Project is a community map of small public infrastructure (toilets, trash cans, benches, smoking areas, water fountains) with crowdsourced submissions and real-time issue reporting. v1 targets a single Seoul gu.

**Three core entities to keep distinct:**

- **POI**: a physical thing that exists (a toilet at a location). Long-lived.
- **Report**: a transient issue tied to a POI (“this toilet is out of order”). Auto-expires.
- **User**: a person who can submit, confirm, and report.

-----

## 1. Locked Technical Decisions

These are decided. Do not re-debate them while implementing.

|Concern              |Choice                                                                                        |Reason                                         |
|---------------------|----------------------------------------------------------------------------------------------|-----------------------------------------------|
|Backend language     |Python 3.12                                                                                   |FastAPI ecosystem, easy data work for importers|
|Web framework        |FastAPI                                                                                       |Async, OpenAPI, Pydantic v2                    |
|Database             |PostgreSQL 16 + PostGIS 3.4                                                                   |Geospatial queries are non-negotiable          |
|ORM                  |SQLAlchemy 2.x (async) + Alembic for migrations                                               |Standard                                       |
|Validation           |Pydantic v2                                                                                   |Comes with FastAPI                             |
|Frontend             |React 18 + Vite + TypeScript                                                                  |Fast dev loop                                  |
|Map SDK              |Kakao Maps JavaScript SDK via `react-kakao-maps-sdk`                                          |Best Korean detail                             |
|State / data fetching|TanStack Query (React Query)                                                                  |Server state                                   |
|Client state         |Zustand                                                                                       |Lightweight, only if needed                    |
|Styling              |Tailwind CSS                                                                                  |Fast iteration                                 |
|Auth                 |Kakao OAuth 2.0 → server-issued JWT                                                           |Korean user expectation                        |
|Object storage       |Cloudflare R2 (S3-compatible)                                                                 |Cheap, no egress fees                          |
|Local dev            |Docker Compose                                                                                |One command to run everything                  |
|Hosting (staging)    |Fly.io or Railway                                                                             |Easy Postgres + app deploy                     |
|Tests                |pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend), Playwright (e2e)|Standard                                       |
|Lint/format          |ruff + black (backend), eslint + prettier (frontend)                                          |Standard                                       |

-----

## 2. Repository Structure

Use a single monorepo:

```
small-map/
├── README.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Pydantic Settings
│   │   ├── db.py                # async engine, session
│   │   ├── deps.py              # FastAPI dependencies
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Business logic
│   │   ├── importers/           # Government data importers
│   │   ├── jobs/                # Scheduled jobs (decay, cleanup)
│   │   └── core/                # auth, security, storage
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   └── integration/
│   └── scripts/                 # one-off CLI tools
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/                 # API client
│   │   ├── components/
│   │   ├── features/            # feature-grouped: map, auth, submit, report
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── pages/               # if router used
│   │   └── types/               # TS types mirroring backend schemas
│   └── tests/
└── e2e/                          # Playwright tests, added Phase 1+
    └── tests/
```

-----

## 3. Conventions Every Phase Must Follow

### API conventions

- Base path: `/api/v1`
- All endpoints return JSON
- Errors follow `{ "error": { "code": "STRING_CODE", "message": "Human readable" } }`
- POST/PUT request bodies are validated by Pydantic schemas; reject with 422 on failure
- All POI coordinates use **WGS84** (EPSG:4326), passed as `{lat: float, lng: float}` in JSON, stored as `geography(Point, 4326)` in Postgres
- Bounding box queries use `?bbox=west,south,east,north` (lng/lat order, OSM convention)
- Pagination is **NOT** used for map queries — instead, hard-cap results at 500 per bbox query and return `{ "items": [...], "truncated": bool }`
- All timestamps are ISO 8601 UTC

### Database conventions

- All tables have `id` (UUID v7 if available, else v4), `created_at`, `updated_at`
- Soft-delete via `deleted_at` column where deletion needs auditing (POIs, Reports). Hard-delete is fine for ephemeral things.
- Every migration is reversible. Test the down-migration locally before merging.
- No raw SQL in routers. Business logic in `services/`.

### Code conventions

- Backend: type hints required everywhere, ruff + black enforced in CI
- Frontend: strict TypeScript, no `any` without a comment explaining why
- Commits: conventional commits (`feat:`, `fix:`, `chore:`, `test:`)
- One PR per task group. PRs include test updates and a manual-QA checklist.

### Testing conventions

- Every endpoint must have at least one happy-path and one validation-failure integration test
- Business logic in services has unit tests
- Database tests run against a real Postgres in Docker (via `pytest-postgresql` or a docker-compose service), NOT SQLite — PostGIS won’t work otherwise
- Each phase ends with a manual QA pass against the staging deploy

### Environment variables (`.env.example`)

```
# Database
DATABASE_URL=postgresql+asyncpg://smallmap:smallmap@localhost:5432/smallmap

# App
APP_ENV=development
APP_SECRET_KEY=change-me
APP_BASE_URL=http://localhost:8000
FRONTEND_BASE_URL=http://localhost:5173

# Auth
KAKAO_CLIENT_ID=
KAKAO_CLIENT_SECRET=
KAKAO_REDIRECT_URI=http://localhost:5173/auth/kakao/callback
JWT_SECRET=change-me
JWT_ISSUER=smallmap
JWT_AUDIENCE=smallmap-web
JWT_TTL_SECONDS=2592000

# Storage (Phase 2+)
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET=smallmap-photos
R2_PUBLIC_BASE_URL=

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_KAKAO_MAPS_JS_KEY=
```

-----

## 4. Prerequisites (do these once before Phase 0)

1. Register a Kakao Developers app at https://developers.kakao.com — get **JavaScript key** (for Maps SDK) and **REST API key + client secret** (for OAuth login). Add `http://localhost:5173` to allowed domains and `http://localhost:5173/auth/kakao/callback` to redirect URIs.
1. Create a Cloudflare R2 bucket (skip until Phase 2 if you want).
1. Install Docker, Docker Compose, Python 3.12, Node 20, pnpm.
1. `cp .env.example .env` and fill in Kakao JS key.

-----

# PHASE 0 — Skeleton

**Duration estimate:** 3–5 working days
**Goal:** A deployed staging environment where a hardcoded POI appears as a pin on a Kakao map, served by a FastAPI endpoint reading from a real Postgres+PostGIS database. No features. Just the wiring.

## 0.1 Deliverables

- Backend serves `GET /api/v1/health` returning `{ "status": "ok" }`
- Backend serves `GET /api/v1/pois?bbox=...` returning hardcoded seed POIs from the DB
- Frontend renders Kakao Map centered on the chosen district, fetches POIs in the visible bbox, renders pins
- Docker Compose runs Postgres+PostGIS, backend, and frontend locally with one command
- CI runs lint + tests on every PR
- Staging deploy reachable at a URL

## 0.2 Backend tasks (in order)

### 0.2.1 Project bootstrap

- Initialize `backend/` with `pyproject.toml`. Dependencies: `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `geoalchemy2`, `pydantic`, `pydantic-settings`, `python-jose[cryptography]`, `httpx`. Dev: `pytest`, `pytest-asyncio`, `ruff`, `black`, `mypy`.
- Create `app/main.py` with a minimal FastAPI app and a `/api/v1/health` route.
- Create `app/config.py` using `pydantic_settings.BaseSettings` to load from `.env`.

### 0.2.2 Database wiring

- Create `app/db.py`: async engine, async session factory, `get_session` dependency.
- Set up Alembic configured for async SQLAlchemy. Confirm `alembic init`, edit `env.py` for async, point `script_location` correctly.
- First migration: enable PostGIS extension (`CREATE EXTENSION IF NOT EXISTS postgis;`).

### 0.2.3 POI model — minimal

Create `app/models/poi.py`:

```python
class POI:
    id: UUID (pk)
    poi_type: Enum('toilet','trash_can','bench','smoking_area','water_fountain')
    location: geography(Point, 4326)  # NOT NULL
    name: Optional[str]
    attributes: JSONB  # type-specific, see Phase 1 for schemas
    source: str  # 'seed', later 'scraped:...', 'user:<uuid>'
    status: Enum('active','removed')  default 'active'
    created_at, updated_at: timestamptz
```

Create matching Alembic migration. Add a GiST index on `location`. Add a btree index on `(poi_type, status)`.

### 0.2.4 POI bbox endpoint

- Create `app/schemas/poi.py` with `POIRead` Pydantic schema (note: convert PostGIS Point to `{lat, lng}` in a serializer).
- Create `app/services/poi_service.py` with `list_pois_in_bbox(session, bbox, types=None, limit=500)` using `ST_MakeEnvelope` + `ST_Intersects`.
- Create `app/routers/pois.py` with `GET /api/v1/pois?bbox=west,south,east,north&type=toilet&type=bench`.
- Reject malformed bbox (must be 4 floats, west<east, south<north, span < 0.5 degrees to prevent abuse) with 422.
- Wire router into `main.py`. Set up CORS to allow `FRONTEND_BASE_URL`.

### 0.2.5 Seed data script

- Create `backend/scripts/seed_dev_data.py` that inserts ~10 hand-picked POIs in your chosen district (mix of types).
- Document running it: `python -m scripts.seed_dev_data`.

### 0.2.6 Tests

- `tests/integration/test_health.py`: GETs `/health`, asserts 200 and body.
- `tests/integration/test_pois_bbox.py`:
  - happy path: insert 3 POIs, query bbox containing them, assert 3 returned
  - filter by type: insert mixed types, query with `?type=toilet`, assert only toilets
  - bbox excludes: query bbox not containing the POIs, assert 0 returned
  - validation: malformed bbox returns 422
  - limit: insert 600 POIs, assert 500 returned + `truncated: true`
- `tests/conftest.py`: provides a fresh test DB per test (use a transactional rollback fixture; see SQLAlchemy async testing patterns).
- `pytest.ini` configured to discover tests, async mode auto.

### 0.2.7 Docker + dev ergonomics

- `docker-compose.yml` services: `db` (postgis/postgis:16-3.4), `backend` (built from backend/Dockerfile), `frontend` (vite dev server).
- Backend Dockerfile: multi-stage, uses `uv` or `pip-tools` for deps.
- A `Makefile` (or `justfile`) at repo root with: `make up`, `make down`, `make migrate`, `make seed`, `make test`, `make lint`.

## 0.3 Frontend tasks (in order)

### 0.3.1 Project bootstrap

- `pnpm create vite frontend --template react-ts`.
- Install: `react-kakao-maps-sdk`, `@tanstack/react-query`, `axios` (or fetch wrapper), `tailwindcss`, `@types/*`.
- Set up Tailwind. Set up path aliases (`@/` → `src/`).

### 0.3.2 API client

- `src/api/client.ts`: axios instance with `VITE_API_BASE_URL`, JSON defaults, error normalization.
- `src/api/pois.ts`: `fetchPOIs(bbox, types)` returning typed `POI[]`.
- `src/types/poi.ts`: TypeScript types matching backend schemas. Keep these in sync manually for now; consider OpenAPI codegen later.

### 0.3.3 Map page

- `src/features/map/MapView.tsx`: Kakao Map centered on chosen district default coords.
- On map idle (pan/zoom finished), read current bbox, call `useQuery(['pois', bbox, types], () => fetchPOIs(...))`.
- Render each POI as a `<MapMarker>` with simple emoji-or-icon by type.
- Add a basic filter bar (checkbox per POI type) controlling the `types` state.

### 0.3.4 Tests

- `tests/api/pois.test.ts`: mock fetch, verify URL + params built correctly.
- `tests/components/MapView.test.tsx`: mock the Kakao SDK, verify markers render given a POI list. (Mocking the Kakao SDK is tedious; if it gets messy, defer detailed map tests to e2e in Phase 1.)

## 0.4 CI

- GitHub Actions workflow `.github/workflows/ci.yml`:
  - On push and PR
  - Job: backend (run ruff, black –check, pytest with a postgis service container)
  - Job: frontend (eslint, vitest, tsc –noEmit, build)

## 0.5 Staging deploy

- Pick Fly.io or Railway. Set up:
  - Postgres with PostGIS extension enabled (Fly: use the `flyio/postgres-flex` and `CREATE EXTENSION` after; Railway: Postgres add-on, then enable PostGIS via psql)
  - Backend service with env vars
  - Frontend served as static site (Vercel or Cloudflare Pages is also fine)
- Run migrations on deploy.
- Run the seed script once against staging.

## 0.6 Acceptance criteria

- [ ] `make up` brings up the full stack locally; map appears with seeded pins
- [ ] `make test` passes
- [ ] CI passes on a PR
- [ ] Staging URL works: opening it shows the map with seeded pins for your chosen district
- [ ] You can pan/zoom and the API is called with new bboxes (verify in network tab)
- [ ] Filtering by type works

## 0.7 Common pitfalls

- **PostGIS in CI:** the GitHub Actions postgres service image must be `postgis/postgis:16-3.4`, not vanilla `postgres`.
- **Geography vs Geometry:** use `geography(Point, 4326)` for Earth-scale lat/lng; geometry has different distance semantics.
- **Kakao SDK script loading:** `react-kakao-maps-sdk` requires the Kakao script tag loaded before React mounts the map — use the library’s `useKakaoLoader` hook.
- **CORS:** include both `http://localhost:5173` (dev) and your staging frontend URL in the FastAPI CORS middleware allowlist.

-----

# PHASE 1 — Read-only with real public data

**Duration estimate:** 1–2 weeks
**Goal:** Replace seed data with real, periodically refreshed public data. Map shows hundreds of real toilets, trash cans, smoking areas, etc., across the chosen district. Marker clustering at low zoom. POI detail popup.

## 1.1 Deliverables

- At least 2 importer scripts running against real public datasets, idempotent (re-running doesn’t duplicate)
- A scheduled job to re-import monthly
- Frontend marker clustering when zoomed out
- Click a pin → detail panel with name, type, attributes, last-verified date, source attribution
- e2e Playwright test covering map load + click

## 1.2 Data sources to investigate (assign to a task before coding)

The exact dataset URLs and schemas need to be verified at implementation time — they change. Start by searching:

- **Public toilets nationwide:** data.go.kr — search “전국공중화장실표준데이터” (Standard Public Toilet Data). Usually includes: name, address, lat/lng, gender layout, accessibility, opening hours, manager contact.
- **Smoking areas (Seoul):** data.seoul.go.kr — search “흡연구역”. Coverage varies by gu.
- **Street trash cans:** much harder — some gu publish, most don’t. Check the specific gu’s open data portal.
- **Public benches / rest areas:** often part of “park facilities” or “street furniture” datasets per gu.
- **Drinking fountains / water:** check city park datasets.

Document findings in `backend/importers/SOURCES.md` before writing any importer code: dataset name, URL, license, format (CSV/JSON/XML), update frequency, schema mapping to your POI model.

## 1.3 Backend tasks

### 1.3.1 Expanded POI model

Add to the `POI` table:

- `external_id`: nullable string — the source’s primary key, used for upsert idempotency
- `last_verified_at`: timestamptz — for scraped data, this is the source’s `as_of` date; for user data (Phase 2+), it’s the latest confirmation
- `verification_count`: int default 0
- Compound unique index on `(source, external_id)` where both not null

### 1.3.2 Per-type attribute schemas

Define Pydantic models for `attributes` JSONB by type:

- **toilet**: `accessibility: bool | null`, `gender: 'separate'|'unisex'|'male_only'|'female_only'|null`, `opening_hours: str | null` (OSM-style: `Mo-Fr 09:00-18:00`), `is_free: bool | null`, `has_baby_changing: bool | null`
- **trash_can**: `recycling: bool | null`, `general: bool | null`
- **bench**: `material: str | null`, `has_back: bool | null`, `shaded: bool | null`
- **smoking_area**: `enclosed: bool | null`, `opening_hours: str | null`
- **water_fountain**: `is_potable: bool | null`, `seasonal: bool | null`

Validate attributes against the type-specific schema on write. Unknown keys allowed but ignored on read.

### 1.3.3 Importer framework

Create `app/importers/base.py`:

```python
class BaseImporter:
    source_id: str  # e.g. "seoul.public_toilets"
    poi_type: str
    
    async def fetch_raw(self) -> list[dict]: ...
    def normalize(self, raw: dict) -> POIInput | None: ...
    async def run(self, session) -> ImportReport: ...
```

- `run` upserts on `(source, external_id)`; updates `last_verified_at = now()`; sets soft-delete on POIs that disappeared from the source (with a 2-cycle grace period).
- Returns an `ImportReport` with counts: `created`, `updated`, `unchanged`, `removed`.

### 1.3.4 Concrete importers (start with two)

- `app/importers/seoul_public_toilets.py`
- `app/importers/seoul_smoking_areas.py` (if your district has data)
- Each is a `BaseImporter` subclass.

### 1.3.5 Importer CLI

- `backend/scripts/run_importers.py [--source X] [--dry-run]`
- Logs counts and errors. On dry-run, prints what would change without writing.

### 1.3.6 Scheduled job

- Add APScheduler or run as a separate cron container in Compose
- Schedule: monthly per importer (configurable per importer)
- For staging, also expose a protected endpoint `POST /api/v1/admin/run-importer` (admin-token gated) to trigger manually

### 1.3.7 POI detail endpoint

- `GET /api/v1/pois/{id}` returns full POI with attributes, source, last_verified_at
- 404 if not found or soft-deleted

### 1.3.8 Tests

- Unit: each importer’s `normalize()` against fixture raw data (committed JSON files in `tests/fixtures/`)
- Integration: `run()` against a fixture twice, verify second run produces all `unchanged`
- Integration: removal grace period — fixture A on run 1, fixture B (missing one item) on runs 2 and 3, verify item is soft-deleted on run 3 not run 2
- Integration: `GET /pois/{id}` happy path + 404
- Validation tests for type-specific attribute schemas

## 1.4 Frontend tasks

### 1.4.1 Marker clustering

- Install `supercluster` and integrate. At zoom < 15, group POIs into clusters; clicking a cluster zooms in.
- Cluster style: numbered circle, color by majority type (or neutral gray if mixed).

### 1.4.2 POI detail panel

- Click a marker → bottom sheet (mobile) or right panel (desktop) with name, type icon, attributes formatted nicely (e.g., “♿ Accessible · 24/7 · Free”), last verified date, source attribution link.
- Close button. Keyboard `Esc` closes.
- Route: optional `?poi=<uuid>` query param for shareable links.

### 1.4.3 Type icons

- Use Lucide or a custom set. One icon per POI type.
- Markers should be visually distinct enough to read at a glance on a busy map.

### 1.4.4 Filter UI polish

- Persistent filter bar at the top
- “All / None” quick toggles
- Filter state persisted in URL query params (`?types=toilet,bench`)

### 1.4.5 e2e tests (Playwright)

- Set up `e2e/` workspace, configure to run against the local stack
- Test: visit `/`, wait for map, assert >0 markers visible
- Test: click filter to deselect “toilet”, assert toilet markers disappear
- Test: click a marker, assert detail panel shows POI name

## 1.5 Acceptance criteria

- [ ] At least 100 real POIs visible across the district
- [ ] Re-running an importer twice produces zero changes the second time
- [ ] Removing a row from the source data eventually soft-deletes the POI in the DB (after grace period)
- [ ] Clustering visually works at low zoom; clusters expand to individual pins on zoom-in
- [ ] Clicking a pin shows attributes for its type
- [ ] e2e tests pass in CI
- [ ] Source attribution is visible somewhere on every POI detail (legal/ethical baseline)

## 1.6 Common pitfalls

- **Coordinate systems in Korean datasets:** many use EPSG:5174 (Korean Bessel) or EPSG:5179 (Korea 2000). You MUST reproject to EPSG:4326 in the importer. Use `pyproj` or PostGIS `ST_Transform`. Verify by spot-checking a known location.
- **Encoding:** Korean public CSVs often come in CP949/EUC-KR, not UTF-8. Detect and decode in the fetcher.
- **Address vs lat/lng:** some datasets only have addresses. You’ll need a geocoder. Kakao Local API has a free address-to-coord endpoint — use that. Cache results.
- **License attribution:** the public data license usually requires attribution. Add it in the POI detail panel and the app’s About page.
- **Cluster lifecycle:** rebuilding the supercluster index on every render is slow. Memoize on the POI list reference.

-----

# PHASE 2 — User accounts and submissions

**Duration estimate:** 2–3 weeks
**Goal:** Real users can log in via Kakao, submit new POIs with a photo and verified GPS, and confirm existing POIs. Submitted POIs become “verified” after 2 independent confirmations.

## 2.1 Deliverables

- Kakao OAuth login flow end-to-end
- “Add POI” flow on the frontend with photo upload + GPS capture
- POI submissions stored, returned in the map (with `verification_status` distinguishing unverified vs verified)
- “Confirm this exists” action on POI detail
- Admin moderation queue (basic)

## 2.2 Backend tasks

### 2.2.1 User model

```
users:
  id: UUID
  kakao_id: bigint, unique, NOT NULL
  display_name: str
  email: str | null
  avatar_url: str | null
  reputation: int default 0
  is_admin: bool default false
  is_banned: bool default false
  created_at, updated_at, last_seen_at
```

### 2.2.2 Kakao OAuth flow

- `GET /api/v1/auth/kakao/authorize` → redirects to Kakao authorize URL with state cookie
- `GET /api/v1/auth/kakao/callback?code=...&state=...` → exchanges code for token, fetches profile, upserts user, issues JWT, redirects to frontend with token in URL fragment (or sets HttpOnly cookie — pick one and document)
- `GET /api/v1/auth/me` returns current user (requires JWT)
- `POST /api/v1/auth/logout` invalidates (cookie clear; for JWT, just instruct frontend to drop)

**Decision:** start with JWT in HttpOnly Secure cookie. Easier CSRF model for a web app, no localStorage exposure. Add a CSRF token header for state-changing requests.

### 2.2.3 Auth middleware / dependency

- `get_current_user(required=True/False)` FastAPI dependency
- Returns `User` or raises 401

### 2.2.4 POI submission endpoint

`POST /api/v1/pois` (auth required)
Request:

```json
{
  "poi_type": "toilet",
  "location": {"lat": 37.5, "lng": 127.0},
  "name": "...",
  "attributes": {...},
  "submitted_gps": {"lat": 37.5, "lng": 127.0, "accuracy_m": 12},
  "photo_upload_id": "<uuid from presigned upload>"
}
```

Server-side validation:

- `submitted_gps` must be within 50m of `location`. Reject if not — this prevents armchair spam.
- `photo_upload_id` must reference an actual uploaded object owned by this user, uploaded in the last 10 minutes.
- Reject if a POI of the same type exists within 10m of `location` — return the existing POI’s ID and prompt the user to confirm it instead. (Frontend handles the prompt.)
- New POI gets `verification_status = 'unverified'`, `source = f'user:{user.id}'`, `verification_count = 1` (the submitter counts).

### 2.2.5 Photo upload (presigned URL pattern)

- `POST /api/v1/uploads/photo-presign` returns `{ upload_id, upload_url, fields }` for direct R2 upload
- Frontend uploads directly to R2
- On POI submission, server verifies the upload exists in R2 and is a real image (HEAD + size + magic-byte check)
- On success, the upload becomes “claimed” and is moved/renamed to the canonical path
- Unclaimed uploads older than 1 hour are deleted by a cleanup job

### 2.2.6 Photo handling and PIPA

**Required:** auto-blur faces and license plates server-side before the photo becomes publicly visible.

- Use a model like RetinaFace or a lightweight YOLO face/plate detector
- Run as a background task on submission (Celery, Arq, or FastAPI BackgroundTasks for v1)
- Before processing completes, the POI shows a placeholder photo
- Add a “report photo” button on every POI photo for human review fallback

### 2.2.7 Confirmation endpoint

`POST /api/v1/pois/{id}/confirm` (auth required)

- Records a `POIConfirmation` row: `(poi_id, user_id, created_at)`
- Unique constraint on `(poi_id, user_id)` — a user can only confirm once
- On confirmation:
  - `verification_count++`
  - `last_verified_at = now()`
  - If count crosses threshold (default 2 distinct confirmations beyond submitter, so 3 total), set `verification_status = 'verified'`
  - Increment submitter’s reputation by 1

### 2.2.8 Soft-delete and admin

- `DELETE /api/v1/pois/{id}` (admin only): soft-delete with reason
- `GET /api/v1/admin/pois?status=unverified` (admin only): moderation queue
- `POST /api/v1/admin/pois/{id}/approve` and `/reject` (admin only)

### 2.2.9 Rate limiting

- Submission: 10 POIs per user per 24h
- Confirmation: 50 per user per 24h
- Use `slowapi` or implement with Redis if you have it; in-memory dict is fine for single-instance staging
- Return 429 with `Retry-After` header

### 2.2.10 Tests

- OAuth flow: mock Kakao endpoints, verify cookie set, `/auth/me` works
- Submission happy path
- Submission rejected: GPS too far from claimed location
- Submission rejected: duplicate within 10m
- Submission rejected: photo doesn’t exist or wrong owner
- Confirmation: idempotent per user
- Verification threshold transition
- Rate limit triggers 429
- Admin endpoints reject non-admin (403)

## 2.3 Frontend tasks

### 2.3.1 Auth flow

- “Login with Kakao” button → hits `/api/v1/auth/kakao/authorize`
- Handle redirect back, fetch `/auth/me`, store user in TanStack Query cache
- Logout button
- Show login state in header

### 2.3.2 Submit flow

- “+” button on map → opens submit sheet
- Step 1: pick type (5 large tappable icons)
- Step 2: capture GPS via `navigator.geolocation.getCurrentPosition` — show accuracy. Reject if accuracy >50m. Also drop a draggable pin user can fine-tune *within 30m* of GPS reading.
- Step 3: capture/upload photo (use `<input type="file" capture="environment" accept="image/*">` for mobile camera). Show preview. Compress client-side to ~1600px max + JPEG quality 80 before upload.
- Step 4: type-specific attributes form
- Step 5: review and submit
- On duplicate-nearby response, show “We found an existing X 8m from here — is this the same?” with a “Yes, confirm it” button or “No, mine is different” option

### 2.3.3 Visual distinction for unverified POIs

- Different marker style (dashed outline, lower opacity, or “?” badge)
- POI detail clearly labels verification status
- “Confirm this exists” button on detail panel for verified-status-pending POIs (auth required, hides own submissions)

### 2.3.4 Profile page (basic)

- `/me` shows: my submissions, my confirmations, my reputation
- Each submission’s verification status

### 2.3.5 Tests

- e2e: full submit flow with mocked geolocation and a fixture image. Verify POI appears on map after submission.
- e2e: confirm flow. Verify status transitions to verified after threshold.

## 2.4 Acceptance criteria

- [ ] User can log in with Kakao on staging
- [ ] User can submit a POI from a real mobile device with camera and GPS
- [ ] Submitted POI appears on map with “unverified” styling
- [ ] After 2 confirmations from other users, status flips to verified (test with multiple test accounts)
- [ ] Submitting a POI with fake GPS (using browser devtools to spoof location 200m away) is rejected
- [ ] Photos are face-blurred before becoming publicly visible
- [ ] Admin can see and approve/reject items in moderation queue
- [ ] Rate limits work (try 11th submission in a day, get 429)

## 2.5 Common pitfalls

- **Geolocation accuracy on desktop:** desktop browsers often return city-level accuracy (1km+). Don’t reject based on accuracy alone — guide users to mobile for submissions.
- **Kakao OAuth redirect URI:** must EXACTLY match what’s registered in Kakao Developer console, including trailing slashes and ports.
- **Image orientation:** EXIF rotation tags trip up cropping/blurring. Strip and apply orientation before processing.
- **Cookie SameSite:** if frontend and backend are on different domains in production, you need `SameSite=None; Secure` and CORS with credentials. Same domain (or subdomain with proper config) is much simpler — consider it for production.
- **PIPA:** consult the actual law text; auto-blurring is a strong baseline but not a get-out-of-jail-free card. Have a documented takedown process and an email address users can reach.

-----

# PHASE 3 — Status reports (the differentiator)

**Duration estimate:** 2–3 weeks
**Goal:** Users can report issues on a POI (“toilet out of order”, “trash can overflowing”, “bench broken”). Active reports are visible on the map as badges. Reports auto-expire. This is the feature that makes the app worth opening repeatedly.

## 3.1 Deliverables

- Report submission with optional photo
- Reports visible as badges on POIs
- Reports auto-expire after 7 days
- Other users can confirm reports (escalating their visibility)
- Reports can be marked resolved by users
- Notification (basic, in-app) for the original submitter when their report resolves or expires

## 3.2 Schema

```
reports:
  id: UUID
  poi_id: UUID FK pois.id
  reporter_id: UUID FK users.id
  report_type: enum('out_of_order','overflowing','dirty','closed','damaged','vandalized','other')
  description: text (max 500)
  photo_url: text | null
  status: enum('active','resolved','expired','dismissed') default 'active'
  confirmation_count: int default 0
  resolved_at: timestamptz | null
  resolved_by: UUID FK users.id | null
  resolution_note: text | null
  expires_at: timestamptz NOT NULL  -- created_at + 7 days
  created_at, updated_at

report_confirmations:
  report_id, user_id, created_at
  PK (report_id, user_id)
```

Index reports on `(poi_id, status)` and on `expires_at where status = 'active'`.

## 3.3 Backend tasks

### 3.3.1 Endpoints

- `POST /api/v1/pois/{id}/reports` (auth) — create a report
- `GET /api/v1/pois/{id}/reports?status=active` — list reports for a POI
- `GET /api/v1/reports?bbox=...&status=active` — bulk fetch for map overlay (cap 500)
- `POST /api/v1/reports/{id}/confirm` (auth) — corroborate
- `POST /api/v1/reports/{id}/resolve` (auth) — mark resolved with note
- `POST /api/v1/reports/{id}/dismiss` (admin only)

### 3.3.2 Auto-expiry job

- Scheduled job every 15 minutes: `UPDATE reports SET status='expired' WHERE status='active' AND expires_at < now()`
- On expiry, create a notification for the reporter

### 3.3.3 POI list endpoint extension

- `GET /api/v1/pois` now includes `active_report_count: int` per POI
- `GET /api/v1/pois/{id}` includes `active_reports: Report[]` (max 5 most recent)

### 3.3.4 Resolution rules

- The reporter can always resolve their own report
- Any user can resolve someone else’s report after >24h since report creation, with required note + optional confirmation photo
- Admin can dismiss anytime

### 3.3.5 Notifications (basic, in-app only)

```
notifications:
  id, user_id, type, payload JSONB, read_at, created_at
```

- Types: `report_resolved`, `report_expired`, `poi_verified` (from Phase 2)
- `GET /api/v1/notifications`, `POST /api/v1/notifications/{id}/read`
- No push, no email yet

### 3.3.6 Tests

- Report creation, expiry job runs and updates status
- Confirmation idempotency
- Resolution rules: reporter can self-resolve immediately; others must wait 24h
- Bulk bbox query returns counts correctly
- Notification created on resolve + on expire

## 3.4 Frontend tasks

### 3.4.1 Report UI

- “Report issue” button on POI detail
- Modal: pick report type (icon grid), optional description, optional photo
- Submit → POI marker on map gets a red badge

### 3.4.2 Map badges

- POIs with active reports get a small red dot or “!” badge on their marker
- Click POI → detail panel shows active reports section
- Each report shows: type, description, time ago, photo, confirm count, “I see this too” button

### 3.4.3 Resolve flow

- “Mark resolved” button on report (own anytime, others after 24h)
- Required resolution note, optional photo

### 3.4.4 Notifications UI

- Bell icon in header with unread count
- Dropdown lists recent notifications, click to navigate to relevant POI

### 3.4.5 Tests

- e2e: submit a report, verify badge appears, resolve it, verify badge disappears
- Component test for report form validation

## 3.5 Acceptance criteria

- [ ] Submitting a report makes a visible difference on the map within 5 seconds (refetch)
- [ ] Reports older than 7 days transition to expired automatically
- [ ] Resolved reports stop appearing on the map
- [ ] Notification fires on resolve and on expire
- [ ] Cannot confirm own report (silent no-op or 400)
- [ ] All e2e tests still pass

## 3.6 Common pitfalls

- **Stale frontend data:** reports change fast. Set TanStack Query `staleTime` for reports to 30s, much shorter than POIs. Refetch on window focus.
- **Map performance with badges:** custom marker icons can tank performance. Render badges as a separate overlay layer keyed by POI id, not as part of marker styling, so you don’t rebuild markers when badge state changes.
- **Spam reports:** rate limit aggressively (5 reports per user per day initially). Track per-POI report rate and flag for admin if a single POI gets >3 reports in an hour.

-----

# PHASE 4 — Trust, decay, and polish

**Duration estimate:** 2 weeks
**Goal:** The system gracefully handles staleness and bad actors. App feels finished enough to share publicly.

## 4.1 Deliverables

- Reputation system in use across endpoints
- Stale POI re-verification prompts
- Soft-delete proposal flow (“this no longer exists”)
- About page, source attributions, privacy policy
- Localization (Korean + English)

## 4.2 Backend

### 4.2.1 Reputation events

```
reputation_events:
  user_id, event_type, delta, ref_id (poi/report id), created_at
```

Events:

- `poi_submitted_verified`: +5 (when a user’s POI reaches verified status)
- `poi_submitted_rejected`: -3
- `confirmation`: +1
- `report_submitted_resolved`: +2 (encourages real reports)
- `report_dismissed_admin`: -5
- `daily_active`: +0 (just track)

User `reputation` is the sum of their events.
Recompute nightly to fix drift.

### 4.2.2 Trust gating

- Users with reputation < 0 cannot submit (only confirm)
- Reputation < -10 → banned
- Reputation > 50 → “trusted” badge, their submissions auto-verify

### 4.2.3 Stale POI re-verification

- POIs with `last_verified_at` > 180 days old AND no recent reports get a `is_stale = true` computed flag
- Frontend prompts users near stale POIs (within 50m) to re-confirm
- Confirmation refreshes `last_verified_at`

### 4.2.4 “No longer exists” proposal

- `POST /api/v1/pois/{id}/propose-removal` (auth) — creates a removal report (special type)
- 3 independent removal proposals → POI is soft-deleted
- Reversible by admin

### 4.2.5 Tests

- Reputation accumulation
- Stale flag computation
- Trust gating: banned user gets 403 on submit
- Removal threshold

## 4.3 Frontend

### 4.3.1 Stale prompts

- When detail panel opens for a stale POI, show subtle “Last verified 7 months ago — still here?” with confirm/no buttons

### 4.3.2 Profile page polish

- Reputation history graph
- Badges (Trusted, First 100 Mappers, etc.)

### 4.3.3 i18n

- Use `react-i18next`
- Korean strings as primary, English as fallback
- Auto-detect from `navigator.language`, override-able

### 4.3.4 Static pages

- About: project mission, FAQ, license attributions, contact
- Privacy Policy: PIPA-compliant outline (consult a Korean lawyer eventually; for now, clear factual statements about what’s collected and why)
- Terms of Use: basic terms

### 4.3.5 Polish

- Loading skeletons everywhere
- Empty states for “no POIs in this area”
- Error boundary with actionable messages
- Mobile-first responsive pass
- Lighthouse audit, fix obvious issues
- Add favicon, OG image, basic SEO meta

## 4.4 Acceptance criteria

- [ ] Banned user cannot submit
- [ ] Trusted user submissions auto-verify
- [ ] Stale POIs get re-verification prompts
- [ ] Removal proposals work and require 3 to act
- [ ] App is fully usable in Korean and English
- [ ] About + Privacy + Terms pages exist and are linked from the footer
- [ ] Lighthouse mobile score > 80 for performance and accessibility

-----

# 5. Cross-cutting Concerns Reference

## 5.1 Logging

- Backend: structured JSON logs via `structlog`
- Log every API request: method, path, status, latency, user_id (if auth), client_ip
- Don’t log photo bytes, JWT contents, or full request bodies for write endpoints (log just the keys)
- Frontend: send unhandled errors to a Sentry-compatible endpoint (or Sentry itself if you set it up)

## 5.2 Observability

- Add `/api/v1/health` (already in Phase 0) and `/api/v1/health/db` (DB ping)
- Phase 3+: add a simple metrics endpoint or Prometheus integration if needed
- Set up alerting on Fly/Railway for service down

## 5.3 Backup

- From Phase 1 onward: enable daily Postgres snapshots in your hosting provider
- From Phase 2 onward: photos in R2 — enable bucket versioning

## 5.4 Security checklist (review at end of each phase)

- All write endpoints require auth (except `/auth/*`)
- All admin endpoints check `is_admin`
- Rate limits on all write endpoints
- No SQL injection (you’re using SQLAlchemy parameterized queries — verify by grepping for raw string concat)
- CORS allowlist is explicit, no wildcards in production
- HTTPS enforced in production
- JWT secret is a real random 256-bit value, not “change-me”
- HttpOnly+Secure+SameSite cookies
- CSP header: at minimum, restrict frame-ancestors and form-action
- File upload: validate magic bytes server-side, not just MIME type
- Photo paths use UUIDs, not user-controlled names

## 5.5 Pre-launch checklist (end of Phase 4)

- [ ] All env vars documented in `.env.example`
- [ ] README has setup instructions that work on a fresh machine
- [ ] Privacy policy and terms reviewed
- [ ] Source attributions visible
- [ ] Contact email works
- [ ] Backups verified by doing a test restore
- [ ] Load test: 100 concurrent users browsing the map without errors
- [ ] Mobile Safari + Chrome Android tested in person
- [ ] Soft-launch to friends only first; real launch after 2 weeks of feedback

-----

# 5b. Future Work — Detailed Punch List

The code through Phase 5 is feature-complete. Everything below is
**deploy + real-data + QA**, not feature work. Items are grouped by
the artefact they need (data, infra, hardware, paperwork) so they can
be parallelised.

## 5b.1 Real public data (unblocks Phase 1.5)

Phase 1.2 was deliberately skipped — toilet/smoking-area importers
ship with **guessed** Korean column names. Validate against real
data **before** seeding staging.

- [ ] **Pull Mapo-gu public-toilet CSV** from `data.go.kr`
      ("전국공중화장실표준데이터"). Save under `backend/scripts/data/`
      (gitignored).
- [ ] Run `scripts/run_importers.py --source seoul.public_toilets
      --csv <path> --dry-run` and read `ImportReport.errors`.
- [ ] Patch `backend/app/importers/seoul_public_toilets.py`
      `COL_*` constants until 0 errors. Add a regression fixture
      under `tests/fixtures/seoul_public_toilets/` and a unit test.
- [ ] Repeat for `seoul.smoking_areas` (data.seoul.go.kr,
      "흡연구역"). Address-only data → wire `KAKAO_REST_API_KEY` for
      geocoding; cap rate to ~10 req/s.
- [ ] **Verify reprojection:** Korean datasets often ship as
      EPSG:5174 / EPSG:5179. Spot-check a known landmark in QGIS
      after import.
- [ ] **Verify encoding:** detect CP949/EUC-KR vs UTF-8 in the
      fetcher; log the chosen codec.
- [ ] Seed staging DB and confirm **≥100 POIs render** with
      clustering and detail panel (Phase 1.5 acceptance).

## 5b.2 Staging deploy

Pick **one** of: Fly.io, Railway, or Render. The plan assumes Fly.

### 5b.2.1 Postgres + PostGIS
- [ ] Provision PG16 (Fly: `flyio/postgres-flex`).
- [ ] `CREATE EXTENSION postgis` post-install.
- [ ] Run `alembic upgrade head` from a one-off worker.
- [ ] **Enable daily snapshots** (Phase 5.3) — Fly Volumes
      snapshot retention ≥ 7 days.
- [ ] Document the restore procedure in `RUNBOOK.md`.

### 5b.2.2 Backend service
- [ ] Build & push backend Docker image.
- [ ] Set every env var in `.env.example` to a real value:
      `DATABASE_URL`, `APP_ENV=production`, `APP_SECRET_KEY`
      (32 random bytes), `JWT_SECRET` (32 random bytes),
      `KAKAO_CLIENT_ID/SECRET`, `KAKAO_REDIRECT_URI` (must match
      Kakao console exactly), `R2_*`, `ADMIN_TOKEN`,
      `IMPORTER_SCHEDULER_ENABLED=true`, `auth_cookie_secure=true`,
      `auth_cookie_samesite=none` (cross-domain), `FRONTEND_BASE_URL`.
- [ ] Hit `/api/v1/health` and `/api/v1/health/db` from outside.
- [ ] Confirm `enforce_at_startup` does **not** raise (logs are
      clean of `startup_security_issue`).

### 5b.2.3 Frontend hosting
- [ ] Cloudflare Pages or Vercel.
- [ ] Build with `VITE_API_BASE_URL=https://api.<host>/api/v1` and
      `VITE_KAKAO_MAPS_JS_KEY` from Kakao console.
- [ ] Add the Pages domain to Kakao console allowed domains
      list and to the backend CORS allowlist.

### 5b.2.4 Object storage (R2)
- [ ] Create `smallmap-photos` bucket.
- [ ] Generate scoped API token (read+write on that bucket only).
- [ ] **Enable bucket versioning** (Phase 5.3).
- [ ] Add CORS rule allowing PUT from the frontend origin only.
- [ ] Public read: route `R2_PUBLIC_BASE_URL` through a Cloudflare
      custom hostname (don't expose the raw `*.r2.cloudflarestorage.com`).

### 5b.2.5 Auth / Kakao OAuth
- [ ] Register the production Kakao app (separate from dev).
- [ ] Add `https://<frontend>/auth/kakao/callback` to redirect URIs
      **byte-for-byte** matching `KAKAO_REDIRECT_URI`.
- [ ] Smoke-test the full flow with a personal Kakao account.

### 5b.2.6 PIPA blur — production detector
- [ ] Replace `NoopDetector` in `app/jobs/photo_blur_task.py` with a
      real face/plate detector (RetinaFace or YOLOv8-face/plate).
- [ ] Wrap in a tiny wrapper module so the dependency is optional
      (skip-on-missing-import keeps unit tests green).
- [ ] Run on the GPU-less staging box and benchmark median latency
      per photo. If > 5 s, move blur to a worker queue (arq + Redis).
- [ ] Add a regression test: a known face image goes in, the
      output's pixel hash differs at the face bbox.

### 5b.2.7 CI / CD
- [ ] GitHub Actions: on tag push, build → run integration tests
      against a `postgis/postgis:16-3.4` service container →
      deploy backend + frontend.
- [ ] Required status checks on `main`: ruff + black + mypy + pytest +
      eslint + vitest + tsc + Playwright.

## 5b.3 Real-stack QA (mobile, in-person)

These can only be exercised after 5b.2 is up.

- [ ] **Login flow** — Kakao login on mobile Safari + Chrome Android.
- [ ] **Submit POI** — from a phone, real GPS, real camera. Try with
      bad accuracy (>50m) and verify the submit button stays disabled.
- [ ] **GPS spoof test** — devtools location 200m+ off; backend
      returns 422 with the distance.
- [ ] **Duplicate prompt** — submit a 2nd toilet within 10m of an
      existing one; verify the "is this the same?" sheet.
- [ ] **Verification threshold** — 3 different test accounts confirm
      one POI; status flips `unverified → verified`; submitter rep +1
      per confirmation.
- [ ] **Trusted auto-verify** — manually bump a test user to
      reputation ≥ 50; their next submission is born verified.
- [ ] **Banned user** — flip `is_banned=True`; submit returns 403.
- [ ] **Stale prompt** — backdate a POI's `last_verified_at` to
      181 days ago; detail panel shows the yellow re-verify banner.
- [ ] **Removal proposals** — three accounts propose-removal on the
      same POI; POI auto-soft-deletes; admin can undo.
- [ ] **Reports cycle** — submit `out_of_order`; red badge appears
      within 5 s; another user "저도 봤어요"; reporter resolves;
      badge gone within 5 s.
- [ ] **Auto-expiry** — fast-forward `expires_at` past now; the
      15-min cron flips status; reporter gets a `report_expired`
      notification.
- [ ] **Rate limits** — submit 11 POIs in 24h → 429 with
      `Retry-After`; same for 6th report and 51st confirmation.
- [ ] **i18n toggle** — switch KO ↔ EN, refresh; choice survives.
- [ ] **Photo PIPA** — upload a face photo; before blur completes
      the marker shows a placeholder; after, the face is blurred.
- [ ] **Photo upload abuse** — try uploading a `.html` renamed to
      `.jpg` — rejected by magic-byte sniff (Phase 5.4).
- [ ] **Notifications bell** — unread count updates within 60s;
      "모두 읽음" clears; click navigates to the POI.

## 5b.4 Performance + accessibility

- [ ] **Load test** — `k6` script: 100 concurrent users panning
      the Mapo-gu bbox + 5 % submitting reports + 5 % opening
      detail panels. Target: p95 latency < 500 ms,
      0 % 5xx, no DB connection-pool exhaustion.
- [ ] **Lighthouse mobile** — performance ≥ 80, accessibility ≥ 80,
      SEO ≥ 90, PWA optional. Fix LCP / CLS hotspots.
- [ ] **Bundle audit** — `vite build --report`; if > 300 KB
      gzipped, code-split the submit/profile/auth flows.
- [ ] **Map perf** — verify supercluster handles 5 000 POIs without
      jank by seeding a stress dataset.

## 5b.5 Observability (Phase 5.2 polish)

- [ ] Wire backend JSON logs to a log shipper (Fly: `fly logs`
      → Loki / Datadog / Better Stack).
- [ ] Wire frontend `ErrorBoundary` to Sentry (or self-hosted
      `glitchtip`). Sample rate 10 %.
- [ ] Alerts on:
      - any 5xx > 1 % over 5 min,
      - `/health/db` failing 2 consecutive probes,
      - importer scheduler last-run > 35 days ago,
      - photo-blur queue depth > 50.
- [ ] Optional: Prometheus `/metrics` endpoint via
      `prometheus-fastapi-instrumentator`.

## 5b.6 Backups (Phase 5.3 polish)

- [ ] Daily PG snapshot retained 7 d, weekly retained 4 w.
- [ ] R2 bucket versioning + 30 d lifecycle to delete tombstones.
- [ ] **Quarterly restore drill** — restore yesterday's snapshot
      to a scratch DB and run `pytest tests/integration/` against it.
      Document the result in `RUNBOOK.md`.

## 5b.7 Legal + paperwork (blocks public launch)

- [ ] Privacy Policy reviewed by a Korean lawyer (PIPA).
- [ ] Terms of Use reviewed.
- [ ] Public-data attribution (KOGL Type 1) verified per source.
- [ ] Contact email + takedown form in About page works
      end-to-end.
- [ ] Decide a data-retention policy for `reputation_events`
      and deleted POIs; encode it in a nightly job.
- [ ] Cookie consent banner if/when analytics are added.

## 5b.8 Documentation

- [ ] `README.md` setup verified on a clean machine (no Docker
      shortcuts that only work on the author's box).
- [ ] `RUNBOOK.md` (new): deploy, rollback, restore, rotate
      secrets, run an importer manually.
- [ ] `SECURITY.md`: how to report a vulnerability + the
      response SLA.
- [ ] OpenAPI schema dump committed (`openapi.json`) so frontend
      type drift can be diffed.

## 5b.9 Launch sequencing

1. **Soft-launch (≥ 2 weeks):** invite 5–10 friends. Watch logs.
2. **Friends-of-friends:** open registration, keep a `/admin/pois`
   eyeball pass daily.
3. **Public launch:** post in r/korea, /r/seoul, Disquiet,
   Twitter. Be ready to scale Postgres CPU.
4. **Post-launch retro at 30 days:** review reports/POIs ratio,
   spam-rate-limit hits, p95 latency, top-2 user complaints. Plan
   v2 backlog from there.

-----

# 6. Glossary

- **POI (Point of Interest):** a physical thing on the map (a toilet, a bench)
- **Report:** a transient issue tied to a POI
- **Confirmation:** a user attesting that a POI exists and is described correctly
- **Verification status:** unverified → verified (after 2+ confirmations beyond submitter)
- **Stale POI:** a verified POI not re-verified in 180+ days
- **Source:** where data came from (`seed`, `scraped:<importer_id>`, `user:<uuid>`)
- **District / gu (구):** Seoul administrative subdivision; pick one for v1
- **PIPA:** Personal Information Protection Act, Korea’s privacy law

-----

# 7. How to use this plan with Claude Code

For each phase:

1. Open a new Claude Code session pointed at the repo.
1. Paste this command: *“Read IMPLEMENTATION_PLAN.md. Implement Phase N section by section. After each subsection (e.g., 1.3.1, 1.3.2), stop and run the tests for what you just built. Do not proceed to the next subsection until tests pass. At the end of the phase, run the full acceptance criteria checklist and report which items pass and which fail.”*
1. Review each subsection’s PR before merging.
1. Run the manual QA checklist on staging before declaring the phase done.
1. Move to the next phase only after acceptance criteria are met.

Do not let the agent skip ahead to “more interesting” phases. The order matters — Phase 2 depends on Phase 1’s data model, Phase 3 depends on Phase 2’s auth, etc.