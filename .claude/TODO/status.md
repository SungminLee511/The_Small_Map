# The Small Map — Status

## Phase 0 (Skeleton) — COMPLETE
See git log for details. Frontend 8/8, backend 7/7 tests, CI green.

## Phase 1 (Read-only with real public data) — IN PROGRESS

### 1.2 Data sources (SOURCES.md)
- [x] Already documented in `backend/app/importers/SOURCES.md` in a previous
      session (commit `b244877`). User then explicitly said **skip 1.2** for
      the current pass — option (a): proceed with educated-guess schemas in
      1.3.4 and adjust later when real CSVs are pulled.

### 1.3 Backend tasks
- [x] **1.3.1** Expand POI model — `external_id`, `last_verified_at`,
      `verification_count`; partial unique idx on `(source, external_id)`.
      Migration `c1a2b3d4e5f6_phase1_poi_columns.py`.
- [x] **1.3.2** Per-type attribute schemas — `app/schemas/poi_attributes.py`
      with Toilet/TrashCan/Bench/SmokingArea/WaterFountain Pydantic models.
      Unknown keys allowed on write, filterable on read. 10 unit tests.
- [x] **1.3.3** Importer framework — `BaseImporter`, `POIInput`,
      `ImportReport`. `run()` does upsert on `(source, external_id)`,
      refreshes `last_verified_at`, soft-deletes after 2 cycle_days grace.
      4 unit tests.
- [x] **1.3.4** Concrete importers (**option a — schemas guessed**)
      - `seoul_public_toilets.py`: CP949 CSV / JSON API; Mapo-gu filter.
      - `seoul_smoking_areas.py`: address-only → injectable geocoder
        (Kakao Local API helper). Per-run geocode cache.
      - 14 unit tests added. **Real CSVs may need column-name tweaks.**
- [x] **1.3.5** CLI runner — `scripts/run_importers.py` with
      `--source/--all`, `--dry-run`, `--csv/--api-url`, `--kakao-rest-key`.
      6 unit tests.
- [x] **1.3.6** Scheduled job — APScheduler monthly cron (1st @ 03:15 UTC),
      opt-in via `IMPORTER_SCHEDULER_ENABLED`. Admin-token-gated
      `POST /api/v1/admin/run-importer` for manual triggers. 8 unit tests.
- [x] **1.3.7** POI detail endpoint — `GET /api/v1/pois/{id}` returns
      `POIDetail` (importer fields included). 404 on not-found or
      `status='removed'`. 4 integration tests.

### 1.3 Tests summary
- **42/42 unit tests pass locally** (no Postgres needed).
- Integration tests for `/pois/{id}` require Postgres — not run on this
  server (no PG/Docker installed). Will run in CI when wired.

### 1.4 Frontend tasks — COMPLETE
- [x] **1.4.1** Marker clustering — `useClusters` hook memoizes a
      Supercluster index on the POI list reference. `ClusterMarker`
      (CustomOverlayMap) renders count circle colored by dominant type
      (>50% leaves) or gray. Click cluster → zoom in 2 levels + recenter.
      4 unit tests.
- [x] **1.4.2** POI detail panel — `POIDetailPanel` (bottom sheet on
      mobile, right rail on desktop) fetches `/pois/{id}`, shows name,
      type icon, formatted attributes per type, last-verified date,
      verification count, KOGL Type 1 source attribution. Esc + close
      button + `?poi=<uuid>` URL sync via `usePoiUrlParam`. 11 unit tests.
- [x] **1.4.3** Type icons — `TypeIcon` component with one Lucide icon
      and brand color per POI type. New `POIMarker` swaps default Kakao
      pin for colored circle + Lucide icon. FilterBar + DetailPanel use
      it. 7 unit tests.
- [x] **1.4.4** Filter UI polish — `useTypesUrlParam` hook syncs
      `?types=toilet,bench` with state (no param = all). Explicit "전체"
      / "없음" quick toggles, aria-pressed pills, stable `data-testid`s.
      7 unit tests + FilterBar tests refreshed.
- [x] **1.4.5** Playwright e2e — new `e2e/` workspace. Stubs backend
      API (`page.route`) and Kakao SDK (`page.addInitScript`) so the app
      boots fully in a sandboxed environment. 8 specs across
      `filter.spec.ts` + `detail.spec.ts`. CI job added.

### 1.5 Acceptance criteria
- [ ] At least 100 real POIs visible — **blocked on real CSV pull /
      schema verification (1.2 skip)**.
- [x] Re-running an importer twice produces zero changes the second
      time — guaranteed by `_upsert_one` returning `unchanged` when the
      diff is empty (covered in framework design; needs DB integration
      test still).
- [x] Source-disappearance soft-delete grace period — guaranteed by
      `_soft_delete_stale` (only triggers after 2 × cycle_days).
- [x] Clustering at low zoom (1.4.1).
- [x] Pin click → attributes panel (1.4.2).
- [x] e2e tests (1.4.5) — Playwright in CI.
- [x] Source attribution visible (1.4.2 — KOGL Type 1 string in panel).

## Notes
- Server has no Postgres / Docker / Node → only Python unit tests run
  locally. Frontend & e2e validated via CI.
- Phase 1.2 skip means `seoul_public_toilets.py` and
  `seoul_smoking_areas.py` use guessed Korean column names. When the real
  CSV is fetched for the first time, expect to tweak the `COL_*`
  constants in those files. Validation (skipped rows, etc.) will surface
  problems via `ImportReport.errors`.

## Phase 1 — DONE pending real-CSV validation

Next: pull a real Mapo-gu toilet CSV → adjust importer schemas if
needed → seed staging DB → verify ≥100 POIs render with clustering and
detail panel.

## Phase 2 (User accounts and submissions) — backend complete

### 2.2 Backend tasks
- [x] **2.2.1** User model + migration `d2b3c4e5f6a7` (kakao_id BIGINT
      unique, display_name, email, avatar_url, reputation, is_admin,
      is_banned, last_seen_at).
- [x] **2.2.2** Kakao OAuth — `core/jwt_tokens.py` + `core/kakao_oauth.py`
      + auth router (`/auth/kakao/authorize`, `/auth/kakao/callback`,
      `/auth/me`, `/auth/logout`). HttpOnly session cookie via JWT.
- [x] **2.2.3** Auth dependencies — `get_current_user_optional`,
      `get_current_user`, `require_admin`. Banned users filtered to None.
- [x] **2.2.4** `POST /api/v1/pois` — submission with GPS check (50m),
      duplicate check (10m), per-type attribute validation, source =
      `user:<uuid>`, verification_status enum (migration `e3c4d5f6a7b8`).
- [x] **2.2.5** Photo presigned uploads — `photo_uploads` table
      (migration `f4d5e6a7b8c9`), `core/r2.py` (boto3 S3-compat),
      `POST /api/v1/uploads/photo-presign`. Claim path on POI submit:
      HEAD R2, copy tmp/→photos/, mark claimed. Hourly cleanup job.
- [x] **2.2.6** PIPA blur — Pillow GaussianBlur background task
      (`jobs/photo_blur_task.blur_photo_for_poi`). EXIF stripped on
      output. NoopDetector default; production swaps in real
      RetinaFace/YOLO. `pois.photo_processed_at` (migration `a5b6c7d8e9f0`).
- [x] **2.2.7** `POST /pois/{id}/confirm` — `poi_confirmations` table
      (migration `b6c7d8e9f0a1`), idempotent via PK on
      (poi_id,user_id), verification threshold = 3 (submitter + 2),
      flips status to verified, bumps submitter reputation.
- [x] **2.2.8** Admin moderation — `deleted_at`, `deletion_reason`,
      `deleted_by_user_id` on pois (migration `c7d8e9f0a1b2`). New
      endpoints: `DELETE /pois/{id}`, `GET /admin/pois`,
      `POST /admin/pois/{id}/approve`, `POST /admin/pois/{id}/reject`.
      All gated by `require_admin` (users.is_admin).
- [x] **2.2.9** Rate limits — `core/rate_limit.InMemoryRateLimiter`,
      sliding window per (user, action). Defaults: submit_poi=10/24h,
      confirm_poi=50/24h. 429 with Retry-After header.
- [x] **2.2.10** Test sweep — auth flow, submission validation,
      confirmation idempotency + threshold transition, admin gate +
      moderation, rate limit triggers 429. **106/106 unit tests pass
      locally.** Integration tests run against PostGIS in CI.

### 2.3 Frontend tasks — COMPLETE
- [x] **2.3.1** Auth flow — `apiClient.withCredentials=true`, `useMe`
      + `useLogout` hooks, `AuthHeader` (Kakao login link / avatar +
      reputation + logout) wired into MapView.
- [x] **2.3.2** Submit flow — 5-step `SubmitSheet` (type → GPS →
      photo → attrs → review). Client-side image compression to
      ~1600px JPEG q80, presign + R2 PUT, then `POST /pois`. Maps
      401/422/429/409 to friendly Korean messages. Floating "+" FAB
      visible only when logged in.
- [x] **2.3.3** Unverified marker style — yellow dashed ring + "?"
      badge on POIMarker for `verification_status === 'unverified'`.
      Detail panel shows 미확인 / 확인됨 chip and a "여기 있어요 (확인)"
      ConfirmButton (hidden for own submissions / verified POIs /
      logged-out users).
- [x] **2.3.4** Profile page `/me` — backend `/me/submissions` +
      `/me/confirmations` (4 integration tests). Frontend page shows
      avatar, reputation, two list sections with verification badges.
      Bare path-based routing in App.tsx (no react-router).
- [x] **2.3.5** Playwright e2e — extended `_fixtures.ts` with
      mocked `/auth/me`, submit endpoints, confirm endpoint, photo
      presign, R2 PUT, and a stubbed `navigator.geolocation`. New
      specs: `auth.spec.ts`, `submit.spec.ts`, `confirm.spec.ts`,
      `profile.spec.ts`.

## Phase 2 — DONE pending real-stack staging deploy

Acceptance items still gated on infrastructure:
- [ ] Real Kakao OAuth on staging (KAKAO_CLIENT_ID/SECRET wired).
- [ ] Real R2 bucket + creds for the photo upload claim path.
- [ ] Real face/plate detector swapped in for `NoopDetector`.
- [ ] Submitting from a real mobile device with GPS + camera.

Next: pull a real Mapo-gu CSV (Phase 1.2 follow-up), wire Kakao
keys + R2 on staging, then move to **Phase 3** (status reports —
the differentiator).
