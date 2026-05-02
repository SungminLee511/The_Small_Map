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
detail panel. Then move to **Phase 2** (user accounts + submissions).
