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

## Phase 7 - Access Plan Enforcement (Stub)

Added demo subscription-style history limits without real auth or Stripe billing.

### Backend
- Demo plan via `?plan=` query param or `X-Demo-Plan` header (default: `pro`)
- Plan windows enforced on `/api/times`, `/api/latest`, and `/tiles`
- Reference time for limits: latest catalog timestamp (not wall clock)
- `free` = latest frame only (`history_days=0`); `basic`=7d; `pro`=90d; `business`=unrestricted
- `GET /api/access/plans` and `GET /api/access/current?plan=pro`
- Tile requests outside plan return `403` JSON with upgrade message

### Frontend
- Demo plan selector (Free / Basic / Pro / Business)
- Plan limit messaging and upgrade-style warnings
- Plan passed on all API/tile requests
- Clear message when timestamp is outside plan limit

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

Plan API checks:

```bash
curl http://127.0.0.1:8000/api/access/plans
curl "http://127.0.0.1:8000/api/access/current?plan=free"
curl "http://127.0.0.1:8000/api/times?layer=mrms_reflectivity&plan=free"
```

### Known limitations
- Demo plan selector only — no accounts, JWT, or Stripe
- Plan limits use catalog latest timestamp as reference (dev/test behavior)
- Still no real MRMS collection or GRIB2 processing

## Phase 8 - MRMS Source Discovery (Real listing, no GRIB2)

Added real MRMS object discovery from public NOAA AWS without downloading or parsing GRIB2.

### Backend
- `backend/app/sources/mrms.py` — parse S3 keys, list objects, normalize metadata
- `backend/app/services/mrms_discovery.py` — optional catalog registration with dedupe
- `backend/app/api/sources.py` — `GET /api/sources/mrms/latest`
- Config: `MRMS_SOURCE_MODE=stub|real`, `MRMS_DISCOVERY_LIMIT`, lookback days, request timeout
- `RadarFile` columns: `source_provider`, `source_url`, `file_size_bytes`
- Discovered rows: `source=mrms_discovered`, `source_provider=noaa_aws`, `processed_status=pending`

### Scripts / Makefile
- `scripts/discover_mrms.py` — discover with optional `--register`
- `make discover-mrms`

### Frontend
- Demo banner notes MRMS discovery is available; rendering still placeholder

### Run commands

```bash
make setup
make seed
make process-once
make discover-mrms
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
make discover-mrms
cd frontend && npm run build
```

Discovery checks:

```bash
make discover-mrms -- --limit 5
make discover-mrms -- --register --limit 5
curl "http://127.0.0.1:8000/api/sources/mrms/latest?limit=3"
MRMS_SOURCE_MODE=real make discover-mrms -- --limit 5
```

### Known limitations
- Lists metadata only — no GRIB2 download, parse, or real radar tiles
- Initial product: `MRMS_ReflectivityAtLowestAltitude` only
- Stub mode uses sample 2026-06-26 timestamps (avoids demo seed collision)
- Discovered catalog rows are not processed; map still shows demo processed frames
- Real mode requires network; fails gracefully with clear message when offline

## Phase 9 - MRMS Download (GRIB2.gz to local raw storage, no parse)

Added MRMS download support for discovered catalog rows — stores GRIB2.gz (or stub placeholders) locally without GRIB2 parsing.

### Backend
- `backend/app/services/mrms_downloader.py` — download, SHA256, duplicate skip, force re-download
- `RadarFile` columns: `sha256`, `download_status`, `downloaded_at`
- Local paths: `data/raw/mrms/reflectivity/{timestamp}_{filename}[.stub]`
- `GET /api/sources/mrms/download-status` — dev download counts

### Scripts / Makefile
- `scripts/download_mrms.py` — `--limit`, `--register-discovered`, `--force`, `--mode stub|real`
- `make download-mrms`

### Frontend
- Banner updated: “MRMS discovery/download available; rendering still placeholder”

### Run commands

```bash
make setup
make seed
make process-once
make test
make download-mrms -- --register-discovered --limit 5
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
make download-mrms -- --register-discovered --limit 3
cd frontend && npm run build
```

Download checks:

```bash
make download-mrms -- --register-discovered --limit 5
make download-mrms -- --limit 5
curl "http://127.0.0.1:8000/api/sources/mrms/download-status"
MRMS_SOURCE_MODE=real make download-mrms -- --register-discovered --limit 3
```

### Known limitations
- Downloads GRIB2.gz only — no parse, GDAL/rasterio, or real radar tiles
- Stub mode writes labeled `.stub` gzip placeholders, not real NOAA data
- Processor stub produces placeholder PNGs even from real downloads
- Failed downloads marked `download_status=failed`; retry without `--force` on next run
- Real mode requires network; short timeout with friendly errors when offline

## Phase 10 - Processing Status Pipeline (placeholder only, no GRIB2 decode)

Prepared the processor for future real GRIB2 decoding while keeping tile output as placeholders.

### Backend
- `processed_status` values: `pending`, `placeholder_processed`, `placeholder_for_real_raw`, `real_decode_not_implemented`, `failed`
- `raw_kind` column: `demo_seeded_stub`, `collector_stub`, `mrms_download_stub`, `mrms_real_grib2`
- `backend/app/services/raw_file_classifier.py` — raw file type detection
- Updated `backend/app/services/processor.py` — stub rows → placeholder PNG; real `.grib2.gz` → labeled preview only
- `GET /api/sources/mrms/processing-status` — dev processing counts
- Tile headers: `X-RadarArchive-Tile: placeholder` or `placeholder_for_real_raw`
- Legacy `processed` status migrated to `placeholder_processed`

### Scripts
- `scripts/process_once.py` — summary counts (processed, skipped, real_decode_pending, failed)

### Frontend
- Banner: “Placeholder tiles only — GRIB2 rendering not implemented. MRMS discovery/download available.”

### Run commands

```bash
make setup
make seed
make download-mrms -- --register-discovered --limit 3
make process-once
make test
make backend
```

### Test commands

```bash
make test
make lint
make process-once
cd frontend && npm run build
```

Processing checks:

```bash
make process-once
curl "http://127.0.0.1:8000/api/sources/mrms/processing-status"
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
```

### Known limitations
- No GRIB2 decode, GDAL/rasterio, or real radar rendering
- Real `.grib2.gz` files get `placeholder_for_real_raw` preview PNGs only
- `real_decode_not_implemented` rows without preview do not serve tiles
- All map tiles remain programmatic placeholders

## Phase 11 - GRIB2 Inspection Spike (evaluation only)

Added GRIB2 decode evaluation path without replacing placeholder tiles or adding hard geospatial dependencies.

### Backend
- `backend/app/services/grib2_inspector.py` — decoder detection, gzip staging, wgrib2 inventory spike
- `backend/app/services/grib2_inspect_catalog.py` — latest real MRMS `.grib2.gz` candidates
- Optional backends detected: wgrib2 CLI, GDAL, rasterio, pygrib, cfgrib (none required)
- Staging under `data/staging/grib2_inspect/` for decompressed inspection copies

### Scripts / Makefile
- `scripts/inspect_grib2.py` — `--file`, `--latest-mrms`, `--limit`
- `make inspect-grib2`

### Docs
- `docs/GRIB2_DECODE.md` — future pipeline, decoder tradeoffs, inspection usage

### Frontend
- Banner: “GRIB2 inspection spike available; rendering still placeholder”

### Run commands

```bash
make setup
make test
make inspect-grib2
make backend
```

### Test commands

```bash
make test
make lint
make inspect-grib2
cd frontend && npm run build
```

Inspection checks:

```bash
make inspect-grib2
PYTHONPATH=. python scripts/inspect_grib2.py --file data/raw/mrms/reflectivity/example.grib2.gz
MRMS_SOURCE_MODE=real make download-mrms -- --register-discovered --limit 1
make inspect-grib2
```

### Known limitations
- Evaluation/metadata only — no production GRIB2 decode or real radar tiles
- wgrib2/GDAL/rasterio not installed by default (`make setup` unchanged)
- Without decoders, inspection reports gzip size and GRIB magic only
- Processor statuses and `/tiles` placeholder behavior unchanged
