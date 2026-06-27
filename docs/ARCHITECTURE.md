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
- `radar_files` — indexed frames with UTC ISO timestamps and raw/processed storage paths
- `access_plans` — subscription plan history limits (`free`, `basic`, `pro`, `business`)

API routes read from `backend/app/services/catalog.py`; they do not collect or process radar data during requests.

Seeding:
- `make seed` creates tables and inserts demo rows
- `make db-reset` clears and re-seeds demo rows
- App startup auto-seeds when the catalog is empty (non-test environments)

### Local storage (Phase 3)
`backend/app/services/storage.py` wraps the local filesystem using `LOCAL_STORAGE_ROOT` (default `./data`).

Responsibilities:
- Ensure directories under `data/raw/`, `data/processed/`, and `data/tiles/`
- Write immutable raw placeholder files
- Reserve/write processed placeholder paths
- Compute SHA256 checksums for stored files
- Return normalized repo-relative paths stored in the catalog

MRMS reflectivity stub layout:
- Raw: `data/raw/mrms/reflectivity/{timestamp}.grib2.stub`
- Processed: `data/processed/mrms/reflectivity/{timestamp}.png.stub`

### Collector stub (Phase 3)
`backend/app/services/collector.py` simulates one MRMS reflectivity collection run via CLI (`make collect-once` / `scripts/collect_once.py`).

Flow:
1. Determine next UTC timestamp (latest catalog frame + 5 minutes)
2. Skip if product/timestamp already exists
3. Write raw placeholder file (immutable; not overwritten if present)
4. Write processed placeholder file
5. Insert `radar_files` row with `source: "collector_stub"`

Collection never runs inside API request handlers.

## Frontend
Mobile-first PWA using MapLibre or Leaflet. The map requests tiles and vector layers from the backend.

## Data Rule
Raw source files are immutable. Processed files can be regenerated. Database records point to both raw and processed paths.

## Local storage layout
- `data/radararchive.sqlite` — catalog database
- `data/raw/` — immutable source files (collector stubs in Phase 3)
- `data/processed/` — regenerated processed outputs (placeholders in Phase 3)
- `data/tiles/` — rendered map tiles (later phase)
