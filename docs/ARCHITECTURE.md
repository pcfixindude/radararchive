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
- `radar_files` — indexed frames with UTC ISO timestamps, raw/processed paths, `processed_status`, `processed_at`
- `access_plans` — subscription plan history limits (`free`, `basic`, `pro`, `business`)

API routes read from `backend/app/services/catalog.py`; they do not collect or process radar data during requests.

Seeding:
- `make seed` creates tables, inserts demo rows, and writes demo raw stub files
- `make db-reset` clears and re-seeds demo rows
- App startup auto-seeds when the catalog is empty (non-test environments)

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

## Frontend
Mobile-first PWA using MapLibre or Leaflet. Phase 4 shows a placeholder map panel with tile availability and a preview image from the tile endpoint.

## Data Rule
Raw source files are immutable. Processed files can be regenerated. Database records point to both raw and processed paths.

## Local storage layout
- `data/radararchive.sqlite` — catalog database
- `data/raw/` — immutable source files (collector/seed stubs)
- `data/processed/` — processed PNG placeholders (processor stub)
- `data/tiles/` — rendered map tiles directory (reserved for later phases)
