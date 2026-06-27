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

## Phase 4 - Processor Stub + Tile Placeholder

Added processor stub and placeholder tile endpoint proving raw → processed → tile pipeline.

### Backend
- `backend/app/services/processor.py` — processes pending raw frames into PNG placeholders
- `backend/app/services/tile_service.py` — generates obvious stub PNG tiles (pure Python, no GDAL)
- `GET /tiles/{layer}/{timestamp}/{z}/{x}/{y}.png` — returns PNG for processed frames, 404 otherwise
- `RadarFile.processed_status` and `processed_at` catalog fields
- `scripts/process_once.py` and `make process-once`
- Seed now writes demo raw stub files so processor can run after `make seed`

### Frontend
- Map placeholder shows tile availability and preview image when processed tiles exist
- Demo/stub labeling remains obvious

### Run commands

```bash
make setup
make seed
make collect-once
make process-once
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
make process-once
make db-reset
cd frontend && npm run build
```

Manual tile check:

```bash
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
```

### Known limitations
- Processor writes placeholder PNGs, not real GRIB2-derived radar
- Tiles are generated stub PNGs, not georeferenced MapLibre tiles
- Seeded demo frames need raw stub files on disk before processing
- Access plans still not enforced on API routes

## Phase 5 - MapLibre Integration

Replaced the static map preview with an interactive MapLibre map that requests placeholder raster tiles from the backend.

### Backend
- No API contract changes
- CORS updated to allow `http://127.0.0.1:5173` tile/image requests

### Frontend
- MapLibre GL JS map with free demo basemap (`demotiles.maplibre.org`)
- Raster overlay from `/tiles/{layer}/{timestamp}/{z}/{x}/{y}.png`
- Tile source refreshes when the selected timestamp changes
- Only `mrms_reflectivity` is selectable for tiles; other layers show “tiles later”
- Radar opacity slider (0–100%)
- Map badge: “Placeholder tiles — not real radar”
- Status message when no processed tiles exist

### Run commands

```bash
make setup
make seed
make process-once
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
cd frontend && npm run build
```

### Known limitations
- Placeholder tiles are not georeferenced to real MRMS extent
- Basemap uses MapLibre demo tiles (not production map hosting)
- No auto-play animation yet
- Still no real GRIB2 processing or NOAA downloads

## Phase 6 - Playback Polish + Tile Bounds

Added playback controls, mobile-friendly layout, layer tile metadata, and CONUS bounds for placeholder tiles.

### Backend
- `/api/layers` now includes optional metadata: `bounds`, `minzoom`, `maxzoom`, `tile_support`, `placeholder`
- `/api/times?processed_only=true` returns only processed timestamps (backward-compatible optional param)
- Tile endpoint unchanged (PNG for processed, 404 otherwise)

### Frontend
- Play/pause, step forward/back, speed selector (0.5x–4x), jump to latest
- Autoplay loops through processed timestamps; slider stays synced
- UTC + local timestamp display
- CONUS bounds applied to raster overlay; map fits bounds on load
- Mobile layout: map on top (~45vh), scrollable controls below
- No-data states: backend down, no processed tiles, unprocessed timestamp selected
- Future layers visible but disabled with “(future layer)” label

### Run commands

```bash
make setup
make seed
make process-once
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
cd frontend && npm run build
```

### Known limitations
- Bounds are approximate CONUS placeholders, not real MRMS grid alignment
- Autoplay uses processed timestamps only
- Still no real GRIB2 processing or NOAA downloads
- Access plans not enforced on tile/history endpoints
