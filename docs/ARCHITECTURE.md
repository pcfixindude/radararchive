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

Headers always include `X-RadarArchive-Production-Rendering: false` for placeholder and decoded prototype modes.

### Render status + production gate (Phase 14)
`backend/app/services/render_metadata.py` — `GeoRenderMetadata` + `geo_metadata.json` per decode artifact.

`backend/app/services/render_status.py` — classify catalog frames, report render status, sync catalog fields.

Catalog render fields on `radar_files`:
- `render_status`: `placeholder` | `decoded_prototype` | `production_pending` | `production_rendered` | `production_failed`
- `render_mode`, `production_rendering`, `render_artifact_path`, `render_metadata_path`, `render_error`, `rendered_at`

Feature flags:
- `ENABLE_DECODED_TILES=false` — decoded prototype tiles (Phase 13)
- `ENABLE_PRODUCTION_RADAR_TILES=false` — production warping prototype tiles (Phase 15)

Tile serving order in `decoded_tile_cache.serve_tile_with_optional_decode`:
1. Production prototype when `ENABLE_PRODUCTION_RADAR_TILES=true` + catalog `production_rendering=true` + `render_status=production_rendered` + cached tile at `data/tiles/production/{layer}/{timestamp}/{z}/{x}/{y}.png`
2. Decoded prototype when `ENABLE_DECODED_TILES=true`
3. Placeholder (default)

### Production tile warping prototype (Phase 15)
`backend/app/services/tile_pyramid.py` — validate geo metadata, Web Mercator tile bounds, WGS84 bounds → grid bilinear sampling (stdlib math).

`backend/app/services/production_tile_builder.py` — read decode artifact + `geo_metadata.json`, warp to EPSG:3857 tiles, write production cache.

CLI: `make build-production-tiles` (`scripts/build_production_tiles.py`); optional `--mark-catalog` for test/fixture frames only.

### Production build batch + multi-zoom (Phase 16)
Build flow:
1. `plan_production_tile_jobs` — scan decode artifacts, validate geo metadata, compute bounds-intersecting XYZ tiles per zoom
2. `execute_production_tile_batch` — batch executor with progress callbacks
3. Idempotent write: skip existing cache paths unless `--force`
4. `--dry-run` reports planned tiles without writing

### Render queue + local worker (Phase 17–18)
SQLite table `render_jobs` tracks queued production tile builds.

Flow:
1. Enqueue via `make enqueue-render-job`, `POST /api/render/jobs`, or `scripts/enqueue_render_job.py`
2. Worker claims oldest runnable `queued` job → `running` via `make render-worker-once` (one job) or `make render-worker` (continuous loop)
3. Worker calls `build_production_tiles` with job params; updates `progress_current`/`progress_total`
4. On failure: re-queue with `next_retry_at` when `attempt_count < max_attempts`; else terminal `failed`
5. Explicit retry: `POST /api/render/jobs/{id}/retry` for failed jobs with attempts remaining
6. Cancel: `POST /api/render/jobs/{id}/cancel` for queued/running jobs

Retry fields: `attempt_count`, `max_attempts`, `last_error_at`, `next_retry_at`, `canceled_at`.

Continuous worker (`run_worker_loop`): configurable `--max-jobs` (default 100) and `--sleep` when queue empty. Graceful exit when max jobs reached.

Queue observability:
- `make render-queue-status` / `GET /api/render/jobs/summary` — counts by status + tile/byte totals
- `make render-status` includes queue summary section
- `GET /api/render/jobs` filters: `status`, `layer`, `timestamp`, `job_type`

No Redis/Celery. Local dev SQLite only. Tile serving gates unchanged.

Dev API: `GET/POST /api/render/jobs`, `GET /api/render/jobs/summary`, `GET /api/render/jobs/{id}`, `POST .../retry`, `POST .../cancel`

Makefile `ARGS` forwarding: `make render-worker ARGS="--max-jobs 5 --sleep 0.5"`

### MRMS validation pipeline (Phase 19)
Experimental end-to-end orchestrator (not verified production radar):

1. Recover stale `running` jobs (1h threshold)
2. Discover MRMS candidates (stub default; real requires `--real` or `MRMS_SOURCE_MODE=real`)
3. Register catalog rows
4. Download raw `.grib2.gz` (stub or real)
5. Inspect GRIB2 metadata
6. Decode when optional decoder available
7. Enqueue render job when decode artifact exists
8. Optionally run one worker pass (`--run-worker`)

CLI: `make validate-real-mrms` (`scripts/validate_real_mrms.py`)

Report fields: `source_mode`, discovery/download/inspect/decode counts, jobs enqueued/processed, `tile_cache`, warnings/errors, `production_rendering_enabled`, `verified_mrms: false`.

Worker hardening (Phase 19):
- `recover_stale_running_jobs` before claim and worker loop start
- Continuous worker: SIGINT/SIGTERM clean exit, structured logging, interruptible idle sleep
- Stale threshold: `STALE_RUNNING_JOB_SECONDS` env (default 3600)

### Validation dashboard + benchmark (Phase 20)
Persisted dev reports under `data/dev/validation_latest.json` and `data/dev/benchmark_latest.json`.

Dev API (prototype):
- `GET /api/validation/summary` — dashboard: decoder, queue, validation/benchmark compact metrics, flags
- `GET /api/validation/latest` — full persisted validation + benchmark JSON

CLI:
- `make benchmark-real-mrms` — per-stage timing (`validation_pipeline`, `tile_build`) + tile metrics
- `make validate-real-mrms` — persists latest validation report

Frontend: `ValidationStatusPanel` in controls sidebar (mobile-friendly).

All responses include `verified_mrms: false` and `prototype: true`.

### Batch validation + catalog growth (Phase 21)
Batch orchestrator processes up to N frames (default 3, max 10):

1. Discover/register/download N candidates
2. Per-frame inspect/decode with `frame_summaries`
3. Aggregate tile metrics + elapsed seconds
4. Persist to `validation_latest.json` + append bounded history (last 10)

CLI: `make validate-real-mrms-batch`, `make catalog-status`

Dev API additions:
- `GET /api/validation/history` — last 10 compact validation runs
- `GET /api/catalog/status` — MRMS catalog counts by status + latest timestamps

### Queue benchmark (Phase 22)
Multi-zoom tile builds through the render queue for small batches:

1. Select up to N catalog frames (default 3, max 10)
2. Enqueue one `production_tiles` job per frame (`min_zoom`/`max_zoom`, default 0–1)
3. Process jobs via render worker (bounded; `mark_catalog=false`)
4. Collect per-job metrics + aggregate totals
5. Persist to `data/dev/queue_benchmark_latest.json` + bounded history (last 10)

CLI: `make benchmark-render-queue` (`--dry-run` plans only; `--force` rebuilds tiles)

Dev API additions:
- `GET /api/validation/benchmarks` — latest queue benchmark + history
- `GET /api/validation/summary` — adds `queue_benchmark`, compact `validation_history`

### Scheduled local validation (Phase 23)
Cron-friendly orchestrator runs in sequence (safe defaults: count 3, zoom 0–1):

1. Catalog status snapshot
2. Batch MRMS validation (persisted, no worker by default in batch step)
3. Queue benchmark (multi-zoom jobs through render worker)
4. Render queue status
5. Validation dashboard summary snapshot

CLI: `make scheduled-validation` (`--real` intentional; exits with report exit code)

Persisted to `data/dev/scheduled_validation_latest.json` + bounded history (last 10).

Dev API: `GET /api/validation/scheduled`, summary field `scheduled_validation`, per-frame `frame_summaries`.

Safe defaults:
- `--min-zoom 0 --max-zoom 0` (single zoom level)
- Max zoom capped at z4
- Max 256 tiles per build

Benchmark report (`BuildProductionTilesResult.to_dict()`):
- `frames_considered`, `frames_skipped`, `zooms_built`, `tiles_written`, `tiles_planned`
- `elapsed_seconds`, `output_bytes`, `errors`
- `prototype: true`, `verified_mrms: false`

Production cache: `data/tiles/production/{layer}/{timestamp}/{z}/{x}/{y}.png`

Tile mode when served: `production-prototype` with `X-RadarArchive-Production-Rendering: true`.

Build CLI flags (Phase 16): `--min-zoom`, `--max-zoom`, `--force`, `--dry-run`, `--json-report`, `--limit`, `--mark-catalog`.

CLI: `make render-status` (`scripts/render_status.py`) — reports frame/artifact counts; `--sync` updates catalog without marking production.

Response headers:
- `X-RadarArchive-Tile` — tile mode string
- `X-RadarArchive-Production-Rendering` — `true`/`false`
- `X-RadarArchive-Render-Status` — catalog render status for served tile

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
- `data/staging/grib2_decode/` — prototype normalized raster artifacts + `geo_metadata.json` (Phase 12–14, not production tiles)
- `data/tiles/decoded_prototype/` — optional prototype tile cache (Phase 13, feature-flagged)
- `data/tiles/production/` — geo-warped production prototype cache (Phase 15, gated)
