# The_Small_Map Skill

## Overview
Map-based civic utility finder (toilets, trash cans, benches, smoking areas, water fountains) for Seoul.

## Stack
- **Backend**: FastAPI + SQLAlchemy 2 (async) + PostGIS + Alembic
- **Frontend**: React + TypeScript + Vite + Tailwind + Kakao Maps SDK + TanStack Query
- **DB**: PostgreSQL 14 + PostGIS

## Directory Tree
```
The_Small_Map/
  .claude/
    skills/SKILL.md
    TODO/
      implementation_plan.md
      status.md
  .env.example
  .gitignore
  docker-compose.yml
  Makefile
  backend/
    .env                  # local only, gitignored
    pyproject.toml
    Dockerfile
    alembic.ini
    alembic/
      env.py
      versions/
        bd261a97346e_initial_poi_table.py
    app/
      __init__.py
      main.py             # FastAPI app, CORS, health endpoint
      config.py            # pydantic-settings
      db.py                # async engine, session factory, Base
      deps.py              # get_db dependency
      models/
        __init__.py
        poi.py             # POI model (Geography POINT, POIType enum)
      schemas/
        __init__.py
        poi.py             # BBox, POIRead, POIListResponse
      services/
        __init__.py
        poi_service.py     # list_pois_in_bbox (ST_Intersects + ST_MakeEnvelope)
      routers/
        __init__.py
        pois.py            # GET /api/v1/pois?bbox=&type=
      importers/           # Phase 1+
      jobs/                # Phase 1+
      core/                # Phase 2+
    scripts/
      seed_dev_data.py     # 10 POIs in Mapo-gu
    tests/
      conftest.py          # NullPool engine, TRUNCATE cleanup
      unit/
      integration/
        test_health.py
        test_pois_bbox.py  # 7 tests
  frontend/
    Dockerfile
    package.json
    tsconfig.app.json
    vite.config.ts
    src/
      main.tsx
      index.css            # Tailwind import
      App.tsx              # QueryClientProvider + MapView
      api/
        client.ts          # axios instance
        pois.ts            # fetchPOIs(bbox, types)
      types/
        poi.ts             # POI, POIType, BBox, labels, icons
      features/map/
        MapView.tsx         # Kakao Map + bbox fetch on idle
        FilterBar.tsx       # POI type toggle buttons
```

## Key API
- `GET /api/v1/health` → `{"status": "ok"}`
- `GET /api/v1/pois?bbox=west,south,east,north&type=toilet&type=bench`
  - bbox span must be < 0.5 degrees
  - Returns max 500 items + `truncated` flag

## Running Locally (no Docker)
```bash
# DB setup (one-time)
psql -U postgres -c "CREATE USER smallmap WITH PASSWORD 'smallmap'"
psql -U postgres -c "CREATE DATABASE smallmap OWNER smallmap"
psql -U postgres -d smallmap -c "CREATE EXTENSION IF NOT EXISTS postgis"

# Backend
cd backend
alembic upgrade head
python -m scripts.seed_dev_data
uvicorn app.main:app --reload

# Tests
pytest tests/ -v

# Frontend
cd frontend
pnpm install
pnpm dev
```

## Gotchas
- Tests require `alembic upgrade head` first (tests don't create tables)
- Tests use NullPool to avoid asyncpg connection conflicts
- Docker containers fail on this server (unshare permission) — use native
- `spatial_ref_sys` excluded from Alembic autogenerate via `include_object`
- Frontend needs `VITE_KAKAO_MAPS_JS_KEY` env var for map rendering

## Conda Env
Uses default `SML_env` — Python 3.10
Python path: `/root/miniconda3/envs/SML_env/bin/python`
