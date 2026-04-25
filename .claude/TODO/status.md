# The Small Map — Phase 0 Status

## 0.2 Backend Tasks
- [x] 0.2.1 Project bootstrap (pyproject.toml, main.py, config.py)
- [x] 0.2.2 Database wiring (db.py, Alembic, PostGIS extension)
- [x] 0.2.3 POI model (models/poi.py, migration, indexes)
- [x] 0.2.4 POI bbox endpoint (schemas, service, router, CORS)
- [x] 0.2.5 Seed data script
- [x] 0.2.6 Tests (health, bbox, conftest) — 7/7 passing
- [x] 0.2.7 Docker + dev ergonomics (docker-compose, Dockerfile, Makefile)

## 0.3 Frontend Tasks
- [x] 0.3.1 Project bootstrap (Vite + React + TS + Tailwind)
- [x] 0.3.2 API client (axios, pois fetch, types)
- [x] 0.3.3 Map page (Kakao Map, bbox fetch, markers, filter)
- [x] 0.3.4 Tests (API mock 3/3, FilterBar component 5/5) — 8/8 passing

## 0.4 CI
- [x] GitHub Actions workflow (.github/workflows/ci.yml)

## 0.5 Staging Deploy
- [ ] Skipped for now (local-first)

## 0.6 Acceptance Criteria
- [x] `make test` passes (backend 7/7)
- [x] Frontend builds cleanly (pnpm build)
- [x] Frontend tests pass (vitest 8/8)
- [x] CI workflow created (backend + frontend jobs)
- [ ] `make up` brings full stack locally with seeded pins (Docker broken on this server — tested natively)
- [ ] Pan/zoom triggers new bbox API calls (needs Kakao key)
- [ ] Filtering by type works (needs Kakao key)

## Notes
- Docker `run` fails on this server (unshare permission denied) — tested natively instead
- PostGIS 3 installed locally on PG14
- Tests use NullPool + TRUNCATE (no drop_all) to avoid alembic conflicts
- Frontend needs VITE_KAKAO_MAPS_JS_KEY to render map

## Phase 0 COMPLETE — ready for Phase 1
