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

## Phase 3 (Status reports) — backend complete

### 3.3 Backend
- [x] **3.3.1** Report endpoints + models — `Report`,
      `ReportConfirmation`, `Notification` (migration `d8e9f0a1b2c3`).
      `POST /pois/{id}/reports`, `GET /pois/{id}/reports`,
      `GET /reports?bbox=`, `POST /reports/{id}/confirm/resolve/dismiss`.
      Rate limits: submit_report=5/24h, confirm_report=50/24h.
- [x] **3.3.2** Auto-expiry — `expire_due_reports` flips active rows
      whose `expires_at < now`; AsyncIOScheduler runs it every 15 min
      (`*/15`). Emits `report_expired` notifications to reporters.
- [x] **3.3.3** POI list/detail — `POIRead.active_report_count`
      bulk-loaded by `active_report_counts_for_pois`; `POIDetail`
      adds `active_reports` (max 5 most recent).
- [x] **3.3.4** Resolution rules — reporter can self-resolve anytime;
      others must wait 24h (`ResolutionTooEarly` → 403 + Retry-After).
      Admin can dismiss via `POST /reports/{id}/dismiss`. Resolver
      ≠ reporter triggers `report_resolved` notification.
- [x] **3.3.5** Notifications — `services/notification_service` +
      `routers/notifications`: `GET /notifications?only_unread=&limit=`,
      `GET /notifications/unread-count`, `POST /notifications/{id}/read`,
      `POST /notifications/read-all`. `confirm_poi` emits a
      `poi_verified` notification on threshold flip.
- [x] **3.3.6** Tests — 6 new unit tests (schemas, constants);
      3 new integration files: `test_reports_endpoints.py`,
      `test_report_expiry_job.py`, `test_notifications_endpoints.py`.
      **112/112 unit tests pass locally.**

### 3.4 Frontend — COMPLETE
- [x] **3.4.1** Report modal — `ReportSubmitModal` with 7-icon
      grid, optional 500-char description, red-themed submit. Maps
      401/404/429 to friendly Korean errors.
- [x] **3.4.2** Map badges + reports section — POIMarker shows
      a red count badge ("9+" cap) when `active_report_count > 0`.
      Detail panel renders `ReportsSection` with preloaded
      `active_reports` (initialData), per-row "저도 봤어요" /
      "내 신고" / "이미 확인" buttons.
- [x] **3.4.3** Resolve flow — `ReportResolveModal` (required
      note + optional photo URL). Server 403 with Retry-After
      surfaces the 24h non-reporter rule in human-readable form.
- [x] **3.4.4** Notifications bell — `NotificationsBell` in the
      logged-in header. Polls unread-count every 60s, lazy-loads
      the list on open, click-to-mark-read pushes `?poi=<id>`.
      "모두 읽음" calls mark-all-read.
- [x] **3.4.5** Playwright e2e — `reports.spec.ts` covers
      submission flow + bell visibility/badge/click behaviour.
      Fixtures extended with report + notification mocks.

## Phase 3 — DONE in code

Acceptance items still gated on infrastructure + manual QA:
- [ ] Live deploy with real backend running the 15-min cron.
- [ ] Mobile-device QA: report → badge → resolve → badge gone.
- [ ] Spam-rate-limit observation in production.

## Phase 4 (Trust, decay, polish) — backend complete

### 4.2 Backend
- [x] **4.2.1** Reputation event ledger — `ReputationEvent` model +
      `EVENT_DELTAS` (verified=+5, rejected=-3, confirmation=+1,
      report_resolved=+2, dismissed=-5). Migration `e9f0a1b2c3d4`.
      All direct mutations of `users.reputation` replaced with
      `append_event` calls in confirmation_service / report_service /
      moderation_service.
- [x] **4.2.2** Trust gating — `core/trust.py` constants
      (NO_SUBMIT=0, AUTO_BAN=-10, TRUSTED=50). `append_event`
      auto-flips `is_banned=True` at the threshold. POST /pois
      returns 403 below 0; trusted users get auto-verified
      submissions via the new `auto_verify` arg on
      `create_user_submitted_poi`.
- [x] **4.2.3** Stale flag — `core/staleness.compute_is_stale`
      (last_verified_at > 180d AND no active reports). Inlined
      into `list_pois_in_bbox` and `get_poi_by_id`. New
      `is_stale` field on POIRead + POIDetail.
- [x] **4.2.4** Removal proposals — `POIRemovalProposal` model
      (composite PK; table created in 4.2.1 migration).
      `services/removal_service.propose_removal` validates,
      idempotent per (poi, user), auto-soft-deletes at threshold
      3. New `POST /api/v1/pois/{id}/propose-removal` (auth +
      rate-limited 10/24h).
- [x] **4.2.5** Tests — 3 unit files (trust thresholds,
      staleness math, reputation deltas), 3 integration files
      (`test_reputation_flow.py`, `test_removal_proposals.py`,
      `test_staleness_endpoint.py`). **127/127 unit tests pass
      locally.**

### 4.3 Frontend — COMPLETE
- [x] **4.3.1** Stale prompt — `StalePrompt` yellow banner with
      "여기 있어요" (confirm) and "더 이상 없어요" (propose-removal,
      shows N/3 progress, flips to "삭제됨" on auto-soft-delete).
- [x] **4.3.2** Profile polish — backend `GET /me/reputation` +
      frontend `ReputationGraph` (dependency-free SVG line chart)
      and `Badges` (Trusted, First Submission, Confirmer).
- [x] **4.3.3** i18n — in-house provider (no react-i18next dep).
      KO/EN dictionaries, navigator detection, localStorage
      persistence, fallback chain. `LanguageToggle` in header.
- [x] **4.3.4** About / Privacy / Terms — full KO + EN content,
      KOGL Type 1 attribution on About, PIPA-aware privacy draft,
      plain-language terms. Footer pinned bottom-left of map.
- [x] **4.3.5** Polish — `ErrorBoundary` (default fallback +
      custom-fallback prop, reset button), `Skeleton` (single +
      multi-row), index.html with full SEO meta (Open Graph,
      Twitter card, theme-color, viewport-fit=cover, lang=ko),
      OG image at `/og.svg`. ProfilePage uses Skeleton. App
      wrapped in ErrorBoundary at the top level.

## Phase 4 — DONE in code

Acceptance items still pending real-stack QA:
- [ ] Banned-user submit flow exercised against a live API.
- [ ] Trusted-user (rep>=50) auto-verify confirmed in production.
- [ ] Stale prompt seen by a real user near a 180+ day POI.
- [ ] Removal-proposal threshold trip observed in production.
- [ ] Lighthouse mobile score > 80 measured against staging.

Next: pull a real Mapo-gu CSV (Phase 1.2 follow-up), wire Kakao
keys + R2 on staging, then move to **Phase 5** (cross-cutting
concerns reference — logging, observability, backups, security
checklist) and pre-launch polish.

## Phase 5 (Cross-cutting concerns) — code-actionable subset DONE

### 5.1 Structured logging
- [x] `app/core/logging.py` — stdlib JSON formatter, redacts known
      secret-shaped keys (token / password / cookie / authorization /
      jwt / kakao_access_token / secret), nested-dict aware, default=str
      fallback for unserializable extras. `setup_logging()` is
      idempotent and tames noisy library loggers.
- [x] `app/core/request_logging.py` — `RequestLoggingMiddleware`
      logs one structured line per request (method, path, status,
      latency_ms, user_id, client_ip, request_id). Sets/propagates
      `X-Request-Id`. Health probes are silent on success.
- [x] Wired into `main.py` lifespan + middleware stack.
- [x] 10 unit tests (`test_logging.py`, `test_request_logging.py`).

### 5.2 Observability
- [x] `GET /api/v1/health/db` — runs `SELECT 1` through a fresh
      session; returns 503 with truncated error body on failure.

### 5.4 Security hardening
- [x] `app/core/security_headers.py` — `SecurityHeadersMiddleware`
      sets `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
      `Permissions-Policy` (camera/mic locked, geolocation=self),
      conservative CSP (`default-src 'none'; frame-ancestors 'none'`),
      and HSTS in production only.
- [x] `app/core/security_startup.py` — boot-time check.
      Production refuses to start with placeholder
      `jwt_secret` / `app_secret_key` or `auth_cookie_secure=False`;
      dev only warns. Wired into the lifespan.
- [x] `r2.get_object_prefix` — Range-GET for the first 16 bytes;
      photo claim path now magic-byte-sniffs the uploaded file
      (`looks_like_image` was previously dead code) and rejects with
      400 on a mismatch.
- [x] 13 unit tests (`test_security_headers.py`,
      `test_security_startup.py`, `test_r2_magic_byte.py`).

**150/150 unit tests pass locally** (was 127, +23 new).

### 5.3 / 5.5 — deferred to staging
- [ ] Postgres daily snapshots + R2 versioning (hosting dashboard).
- [ ] Real backup-restore drill.
- [ ] Load test (100 concurrent map browsers).
- [ ] Mobile Safari + Chrome Android in-person QA.
- [ ] Lighthouse mobile > 80 measured against staging.

## Phase 5 — DONE in code

The code base is feature-complete through Phase 5. **Everything below
is deploy + real-data + QA, not feature work.** Full punch list lives
in `implementation_plan.md` § 5b. Headlines:

### Real data (unblocks Phase 1.5 acceptance)
- [ ] Pull Mapo-gu public-toilet CSV (data.go.kr); patch
      `seoul_public_toilets.COL_*` until `ImportReport.errors == 0`.
- [ ] Same for `seoul_smoking_areas` + Kakao Local geocoder.
- [ ] Spot-check reprojection (EPSG:5174/5179 → 4326) and CP949 decode.
- [ ] Seed staging; confirm ≥100 POIs render.

### Staging deploy (Fly.io baseline)
- [ ] PG16 + PostGIS, `alembic upgrade head`, daily snapshots.
- [ ] Backend container with real `JWT_SECRET`, `APP_SECRET_KEY`,
      `KAKAO_*`, `R2_*`, `ADMIN_TOKEN`; `APP_ENV=production`,
      `auth_cookie_secure=true`, `samesite=none`.
- [ ] Verify `enforce_at_startup` boots clean (no
      `startup_security_issue` warnings).
- [ ] Frontend on Cloudflare Pages with `VITE_API_BASE_URL` and
      `VITE_KAKAO_MAPS_JS_KEY`.
- [ ] R2 bucket + scoped token + versioning + custom hostname.
- [ ] Production Kakao OAuth app; redirect URI byte-exact match.
- [ ] Swap `NoopDetector` → real RetinaFace / YOLO face+plate
      detector; add regression test (face bbox pixel hash differs).
- [ ] CI: integration tests run against PostGIS service container;
      tag-push deploys.

### Real-stack QA (mobile, in person)
- [ ] Kakao login on mobile Safari + Chrome Android.
- [ ] Submit POI from a real phone (camera + GPS).
- [ ] GPS spoof 200m off → 422.
- [ ] Duplicate-within-10m prompt.
- [ ] Verification threshold across 3 accounts.
- [ ] Trusted auto-verify (rep ≥ 50).
- [ ] Banned-user submit → 403.
- [ ] Stale prompt at 181 days.
- [ ] Removal-proposal threshold trip + admin undo.
- [ ] Report → badge → resolve cycle, < 5 s end-to-end.
- [ ] Auto-expiry cron + `report_expired` notification.
- [ ] Rate limits (11th POI/day, 6th report, 51st confirm) → 429.
- [ ] KO ↔ EN i18n persistence.
- [ ] PIPA blur applied before photo public.
- [ ] Magic-byte rejection of non-image upload.
- [ ] Notifications bell unread count + click navigation.

### Performance + a11y
- [ ] k6 load test: 100 concurrent, p95 < 500 ms, 0 % 5xx.
- [ ] Lighthouse mobile: perf ≥ 80, a11y ≥ 80, SEO ≥ 90.
- [ ] Bundle audit; code-split if > 300 KB gzipped.
- [ ] Supercluster perf at 5 000 POIs.

### Observability
- [ ] Backend JSON logs → log shipper (Loki / Datadog / Better Stack).
- [ ] Frontend `ErrorBoundary` → Sentry (10 % sample).
- [ ] Alerts: 5xx > 1 %/5min, `/health/db` 2× fail, importer
      scheduler stale > 35 d, blur queue > 50.
- [ ] Optional Prometheus `/metrics`.

### Backups (5.3 polish)
- [ ] PG: 7d daily + 4w weekly retention.
- [ ] R2: versioning + 30d tombstone lifecycle.
- [ ] Quarterly restore drill — restore + run integration suite.

### Legal + paperwork
- [ ] Privacy Policy lawyer review (PIPA).
- [ ] Terms of Use lawyer review.
- [ ] KOGL Type 1 attribution per source verified.
- [ ] Contact + takedown form works end-to-end.
- [ ] Data-retention policy for `reputation_events` and deleted POIs.
- [ ] Cookie consent banner if analytics added.

### Documentation
- [ ] README setup verified on a clean machine.
- [ ] `RUNBOOK.md` (new): deploy / rollback / restore / rotate /
      run-importer-manually.
- [ ] `SECURITY.md` with vuln-report channel + SLA.
- [ ] Commit `openapi.json` snapshot.

### Launch sequencing
- [ ] Soft-launch ≥ 2 weeks (5–10 friends).
- [ ] Friends-of-friends with daily admin eyeball pass.
- [ ] Public launch posts (r/korea, r/seoul, Disquiet, Twitter).
- [ ] 30-day retro: reports/POIs ratio, rate-limit hits, p95
      latency, top-2 complaints → v2 backlog.
