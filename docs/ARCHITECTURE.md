# Architecture

## Principle
The phone app is only a viewer. All collection and processing happens in the cloud.

## System
NOAA/AWS data sources → collector worker → raw storage → processor worker → processed storage → catalog database → API/tile server → PWA/mobile app.

## Backend
FastAPI provides API endpoints. Workers collect and process radar data. A SQLite catalog (local dev) or Postgres catalog (production later) indexes layers, products, radar files, and access plans.

### Catalog database (Phase 2+)
Local development uses SQLite at `data/radararchive.sqlite`.

Tables:
- `layers` — map layer metadata (`id`, `name`, `type`, `available`, `source`)
- `products` — product records linked to a layer (`layer_id`)
- `radar_files` — indexed frames with UTC ISO timestamps, raw/processed paths, `processed_status`, `processed_at`, `source`, `source_provider`, `source_url`, `file_size_bytes`, `sha256`, `download_status`, `downloaded_at`
- `access_plans` — subscription plan history limits (`free`, `basic`, `pro`, `business`)

API routes read from `backend/app/services/catalog.py`; they do not collect or process radar data during requests.

Seeding:
- `make seed` creates tables, inserts demo rows, and writes demo raw stub files
- `make db-reset` clears and re-seeds demo rows
- App startup auto-seeds when the catalog is empty (non-test environments)

### Access control (Phase 7)
Demo plan enforcement without real auth or Stripe.

Plan selection:
- Query param: `?plan=free|basic|pro|business`
- Header: `X-Demo-Plan: pro`
- Default local dev plan: `pro` (`DEFAULT_DEMO_PLAN` in config)

Reference time for history windows: latest catalog timestamp for the requested layer (not wall-clock `now`).

Plan windows (from SQLite `access_plans`):
- `free` — `history_days=0` → latest frame only
- `basic` — 7 days
- `pro` — 90 days
- `business` — unrestricted (`history_days=NULL`)

Enforced on:
- `GET /api/times` — returns only allowed timestamps
- `GET /api/latest` — latest allowed timestamp
- `GET /tiles/...` — `403` JSON when outside plan; `404` when unprocessed/unavailable

New endpoints:
- `GET /api/access/plans`
- `GET /api/access/current?plan=pro`

### Local storage (Phase 3+)
`backend/app/services/storage.py` wraps the local filesystem using `LOCAL_STORAGE_ROOT` (default `./data`).

Responsibilities:
- Ensure directories under `data/raw/`, `data/processed/`, and `data/tiles/`
- Write immutable raw placeholder files
- Write processed placeholder PNG files
- Compute SHA256 checksums for stored files
- Return normalized repo-relative paths stored in the catalog

MRMS reflectivity stub layout:
- Raw: `data/raw/mrms/reflectivity/{timestamp}.grib2.stub`
- Processed: `data/processed/mrms/reflectivity/{timestamp}.png`

### Collector stub (Phase 3)
`backend/app/services/collector.py` simulates one MRMS reflectivity collection run via CLI (`make collect-once`).

Flow:
1. Determine next UTC timestamp (latest catalog frame + 5 minutes)
2. Skip if product/timestamp already exists
3. Write raw placeholder file (immutable; not overwritten if present)
4. Insert `radar_files` row with `processed_status: pending` and `source: collector_stub`

### Processor stub (Phase 4)
`backend/app/services/processor.py` processes pending raw frames via CLI (`make process-once`).

Flow:
1. Find catalog rows with raw files present and not yet processed
2. Write processed placeholder PNG under `data/processed/mrms/reflectivity/`
3. Update row with `processed_path`, `processed_status: processed`, and `processed_at`
4. Idempotent: already-processed rows are skipped (no duplicate DB rows)

### Tile server stub (Phase 4)
`GET /tiles/{layer}/{timestamp}/{z}/{x}/{y}.png`

Flow:
1. Validate layer exists and is available
2. Validate timestamp exists and `processed_status == processed`
3. Return generated stub PNG tile (not real radar imagery)
4. Return 404 when unavailable

Tiles are generated on demand by `backend/app/services/tile_service.py` using pure Python PNG encoding (no GDAL/rasterio).

### MRMS source discovery (Phase 8)
`backend/app/sources/mrms.py` discovers public MRMS object metadata without downloading GRIB2.

Modes (`MRMS_SOURCE_MODE`):
- `stub` — offline sample listings for tests and local dev
- `real` — anonymous ListObjectsV2 against `noaa-mrms-pds` via HTTPS (short timeout)

Flow:
1. List recent object keys under `CONUS/ReflectivityAtLowestAltitude_00.50/{YYYYMMDD}/`
2. Parse filename timestamps and normalize metadata (product, UTC timestamp, URL, size)
3. Optionally register catalog rows via `backend/app/services/mrms_discovery.py`
4. Discovered rows use `source: mrms_discovered`, `source_provider: noaa_aws`, `processed_status: pending`

CLI: `make discover-mrms` (`scripts/discover_mrms.py`) with optional `--register`.

Dev API: `GET /api/sources/mrms/latest?product=...&limit=...` — metadata only, not radar rendering.

### MRMS download (Phase 9)
`backend/app/services/mrms_downloader.py` downloads discovered GRIB2.gz files to local raw storage.

Modes (`MRMS_SOURCE_MODE` or script `--mode`):
- `stub` — writes gzip stub placeholders under `data/raw/mrms/reflectivity/*.stub`
- `real` — downloads from public `source_url` via HTTPS

Flow:
1. Select `mrms_discovered` catalog rows with `source_url`
2. Skip when already downloaded (checksum/size match) unless `--force`
3. Write local raw file, compute SHA256, update `raw_path`, `file_size_bytes`, `download_status`, `downloaded_at`
4. Rows remain `processed_status=pending` until processor stub runs (placeholder PNG only)

CLI: `make download-mrms` (`scripts/download_mrms.py`) with `--limit`, `--register-discovered`, `--force`, `--mode`.

Dev API: `GET /api/sources/mrms/download-status` — pending/downloaded/failed counts.

## Frontend
Mobile-first PWA using MapLibre GL JS (Phase 5).

### Map (Phase 5–6)
- Basemap: MapLibre demo style (`https://demotiles.maplibre.org/style.json`) — no API key
- Raster overlay: `GET /tiles/{layer}/{timestamp}/{z}/{x}/{y}.png`
- Layer metadata from `/api/layers` supplies bounds/minzoom/maxzoom for MapLibre raster source
- Playback: play/pause, step, speed, latest; autoplay loops processed timestamps
- Mobile: map ~45vh on top, controls scroll below

## Data Rule
Raw source files are immutable. Processed files can be regenerated. Database records point to both raw and processed paths.

## Local storage layout
- `data/radararchive.sqlite` — catalog database
- `data/raw/` — immutable source files (collector/seed stubs)
- `data/processed/` — processed PNG placeholders (processor stub)
- `data/tiles/` — rendered map tiles directory (reserved for later phases)
