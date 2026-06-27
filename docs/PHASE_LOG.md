# Phase Log

## Phase 0 - Repo Setup

Created initial project structure, docs, and development rules. No app logic yet.

## Phase 1 - Thin Vertical Slice

Built and verified the local demo stack without real NOAA/MRMS downloads.

### Backend
- FastAPI app with typed routes under `backend/app/api/routes.py`
- Demo catalog in `backend/app/demo/catalog.py` (clearly labeled stub data)
- Pydantic schemas in `backend/app/schemas/catalog.py`
- Endpoints verified:
  - `GET /api/health`
  - `GET /api/layers`
  - `GET /api/times?layer=mrms_reflectivity`
  - `GET /api/latest?layer=mrms_reflectivity`

### Frontend
- Vite + React mobile-first shell
- Loads layers and timestamps from the backend API
- Map placeholder (no real radar tiles yet)
- Layer panel, time slider, playback controls
- PWA manifest at `frontend/public/manifest.webmanifest`
- Demo banner and NOAA/NWS attribution footer

### Known limitations
- Demo timestamps were hard-coded in memory
- No database-backed catalog yet

## Phase 2 - Catalog + Storage Foundation

Replaced in-memory demo catalog with a SQLite-backed catalog while keeping API response shapes stable.

### Backend
- SQLAlchemy models: `Layer`, `Product`, `RadarFile`, `AccessPlan`
- SQLite database at `data/radararchive.sqlite`
- Catalog service reads layers/timestamps/latest from the database
- Access control service reads plan limits (`free`, `basic`, `pro`, `business`)
- Demo seed via `scripts/seed_demo_data.py` with stub raw/processed storage paths
- Auto-seed on app startup when catalog is empty
- `make db-reset` clears and re-seeds demo rows

### Frontend
- No API contract changes; frontend still loads layers and timestamps from existing endpoints
- Disabled layers remain visibly disabled in the layer panel

### Run commands

```bash
make setup
make seed
make test
make backend
```

In another terminal:

```bash
make frontend
```

Open http://127.0.0.1:5173

### Test commands

```bash
make test
make lint
make seed
make db-reset
cd frontend && npm run build
```

### Known limitations
- Demo rows only; no real MRMS collection or GRIB2 processing
- Stub storage paths recorded but files are not created
- No tile endpoint or rendering yet
- Access plans stored but not enforced on API routes yet

## Phase 3 - Local Storage + Collector Stub

Added a local storage abstraction and collector stub that writes placeholder files and registers new demo frames in SQLite.

### Backend
- `backend/app/services/storage.py` — local storage helpers (paths, writes, SHA256)
- `backend/app/services/collector.py` — simulated MRMS reflectivity collection
- `scripts/collect_once.py` — runs one collector stub via CLI
- `make collect-once` — Makefile target for the collector stub
- Placeholder files under `data/raw/mrms/reflectivity/` and `data/processed/mrms/reflectivity/`
- New frames registered in SQLite with `source: "collector_stub"`
- Duplicate product/timestamp pairs are idempotent (no second row)

### Frontend
- Demo banner notes seeded demo data or collector stubs
- No API contract changes; additional timestamps appear automatically

### Run commands

```bash
make setup
make seed
make collect-once
make test
make backend
```

In another terminal:

```bash
make frontend
```

Open http://127.0.0.1:5173

### Test commands

```bash
make test
make lint
make seed
make collect-once
make db-reset
cd frontend && npm run build
```

### Known limitations
- Collector stub only; no real NOAA/MRMS/AWS downloads
- Placeholder `.stub` files, not GRIB2 or PNG radar imagery
- No tile rendering or processor worker yet
- Access plans still not enforced on API routes
