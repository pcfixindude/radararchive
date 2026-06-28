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
- `radar_files` — indexed frames with UTC ISO timestamps, raw/processed paths, `processed_status`, `processed_at`, `source`, `source_provider`, `source_url`, `file_size_bytes`, `sha256`, `download_status`, `downloaded_at`, `raw_kind`
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

### Processor (Phase 4, updated Phase 10)
`backend/app/services/processor.py` processes raw files via CLI (`make process-once`).

Raw file kinds (`backend/app/services/raw_file_classifier.py`):
- `demo_seeded_stub` — seeded demo raw under `data/raw/demo/`
- `collector_stub` — collector stub under `data/raw/mrms/reflectivity/*.grib2.stub`
- `mrms_download_stub` — MRMS download stub mode (`*.stub`)
- `mrms_real_grib2` — real downloaded `.grib2.gz`

Processing statuses (`processed_status`):
- `pending` — not yet processed
- `placeholder_processed` — stub/demo raw → placeholder PNG (tiles available)
- `placeholder_for_real_raw` — real GRIB2.gz → labeled placeholder preview (decode not implemented)
- `real_decode_not_implemented` — awaiting real decode (no tiles unless preview exists)
- `failed` — processing error

Flow:
1. Classify raw file kind from `source` + `raw_path`
2. Stub kinds → placeholder PNG at `data/processed/mrms/reflectivity/{token}.png`, status `placeholder_processed`
3. Real `.grib2.gz` → labeled preview at `*.placeholder_for_real_raw.png`, status `placeholder_for_real_raw`
4. Idempotent: already placeholder-processed rows are skipped

### Tile server stub (Phase 4, updated Phase 10)
`GET /tiles/{layer}/{timestamp}/{z}/{x}/{y}.png`

Flow:
1. Validate layer exists and is available
2. Validate timestamp has placeholder tile status (`placeholder_processed` or `placeholder_for_real_raw`)
3. Return generated stub PNG tile (not real radar imagery)
4. Response headers: `X-RadarArchive-Tile: placeholder` or `placeholder_for_real_raw`
5. Return 404 when unavailable or `real_decode_not_implemented` without preview

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

### MRMS processing status (Phase 10)
Processor distinguishes stub vs real raw files. No GRIB2 decode yet.

Dev API: `GET /api/sources/mrms/processing-status` — processing counts by status.

CLI: `make process-once` prints summary counts.

### GRIB2 inspection spike (Phase 11)
Evaluation-only metadata path — does not change placeholder tiles or processor statuses.

Modules:
- `backend/app/services/grib2_inspector.py` — decoder detection, gzip staging, wgrib2 inventory when available
- `backend/app/services/grib2_inspect_catalog.py` — find latest real `.grib2.gz` catalog candidates

Decoder backends (optional, detected at runtime):
- **wgrib2** CLI — used for `-s` inventory when installed
- **GDAL/rasterio, pygrib, cfgrib** — detected but not required; reserved for Phase 12+

Future decode/render pipeline (see `docs/GRIB2_DECODE.md`):
```
GRIB2.gz raw → decoded raster → normalized values → color table → COG/tile cache → /tiles endpoint
```

CLI: `make inspect-grib2` (`scripts/inspect_grib2.py`) with `--file`, `--latest-mrms`, `--limit`.

### GRIB2 decode prototype (Phase 12)
`backend/app/services/grib2_decoder.py` — optional rasterio or wgrib2 bin export to normalized artifacts.

Output: `data/staging/grib2_decode/{token}/decode_manifest.json` + raster file.

CLI: `make decode-grib2` (`scripts/decode_grib2.py`).

**Does not change** catalog `processed_status` or default `/tiles` behavior.

### Decoded tile cache prototype (Phase 13)
`backend/app/services/decoded_tile_cache.py` — optional prototype tiles from Phase 12 artifacts.

Feature flag: `ENABLE_DECODED_TILES=false` (default).

When enabled + valid artifact:
- Serves `decoded-prototype` PNG tiles derived from `normalized.raw` / `normalized.tif`
- Caches under `data/tiles/decoded_prototype/{timestamp}/{z}/{x}/{y}.png`

When disabled or artifact missing:
- Falls back to existing placeholder tile behavior

CLI: `make build-tile-cache` (`scripts/build_tile_cache.py`).

Dev endpoint: `GET /tiles/config`

Headers always include `X-RadarArchive-Production-Rendering: false`.

Staging: decompressed copies under `data/staging/grib2_inspect/` for tool inspection only.

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
- `data/staging/grib2_inspect/` — decompressed GRIB2 staging for inspection spike (Phase 11)
- `data/staging/grib2_decode/` — prototype normalized raster artifacts (Phase 12, not served by API)
- `data/tiles/decoded_prototype/` — optional prototype tile cache (Phase 13, feature-flagged)
- `data/tiles/` — rendered map tiles directory (reserved for later phases)
