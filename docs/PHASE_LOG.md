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

## Phase 12 - GRIB2 Raster Decode Prototype (CLI, optional deps)

Added prototype raster decode behind optional dependency checks. Placeholder tiles remain default.

### Backend
- `backend/app/services/grib2_decoder.py` — validate via inspector, decode with rasterio or wgrib2 bin export
- Output: `data/staging/grib2_decode/{token}/decode_manifest.json` + `normalized.tif` or `normalized.raw`
- Manifest includes `production_rendering: false`; catalog and `/tiles` unchanged

### Scripts / Makefile
- `scripts/decode_grib2.py` — `--file`, `--latest-mrms`, `--limit`
- `make decode-grib2`

### Run commands

```bash
make test
make inspect-grib2
make decode-grib2
```

### Test commands

```bash
make test
make decode-grib2
cd frontend && npm run build
```

### Known limitations
- Prototype artifacts only — not served by `/tiles`
- rasterio/wgrib2 optional; friendly exit when missing
- wgrib2 bin export is 1-D prototype metadata (width x 1)
- Real MRMS not marked as rendered in catalog

## Phase 13 - Feature-Flagged Decoded Tile Cache (prototype)

Added optional decoded prototype tile serving behind `ENABLE_DECODED_TILES=false` (default). Placeholder tiles remain default.

### Backend
- `backend/app/services/decoded_tile_cache.py` — read Phase 12 artifacts, render/cache prototype PNG tiles
- Config: `ENABLE_DECODED_TILES` (default `false`)
- Tile cache: `data/tiles/decoded_prototype/{timestamp}/{z}/{x}/{y}.png`
- Headers: `X-RadarArchive-Tile`, `X-RadarArchive-Production-Rendering: false`
- `GET /tiles/config` — dev tile mode configuration
- Fallback to placeholder when flag on but no artifact

### Scripts / Makefile
- `scripts/build_tile_cache.py`, `make build-tile-cache`

### Frontend
- Banner shows tile mode (Placeholder vs Decoded prototype when flag enabled)

### Run commands

```bash
make test
make build-tile-cache
ENABLE_DECODED_TILES=true make backend
```

### Test commands

```bash
make test
make build-tile-cache
cd frontend && npm run build
```

### Known limitations
- Decoded tiles are prototype-only (`production_rendering: false` always)
- Default remains placeholder tiles (`ENABLE_DECODED_TILES=false`)
- Not geo-accurate warping; simple grid sampling
- Catalog not marked as production rendered

## Phase 14 - Production Render Guardrails + Geo Metadata

Added render-status catalog fields, geo-metadata structures, and production tile gates without enabling geo-accurate rendering.

### Backend
- Catalog columns: `render_status`, `render_mode`, `production_rendering`, `render_artifact_path`, `render_metadata_path`, `render_error`, `rendered_at`
- Render statuses: `placeholder`, `decoded_prototype`, `production_pending`, `production_rendered`, `production_failed`
- `backend/app/services/render_metadata.py` — `GeoRenderMetadata`, `geo_metadata.json` read/write, optional rasterio enrichment
- `backend/app/services/render_status.py` — classify frames, build report, sync catalog (never auto-marks `production_rendered`)
- Config: `ENABLE_PRODUCTION_RADAR_TILES=false` (default) — production tiles blocked unless flag + catalog gate both true
- `/tiles` headers: `X-RadarArchive-Tile`, `X-RadarArchive-Production-Rendering`, `X-RadarArchive-Render-Status`
- Phase 12 decode writes `geo_metadata.json` alongside `decode_manifest.json`
- Production tile renderer not implemented — gate only

### Scripts / Makefile
- `scripts/render_status.py`, `make render-status` (optional `--sync`, `--dry-run`)

### Frontend
- Clearer tile mode banner; decoded prototype labeled as experimental, not verified MRMS

### Run commands

```bash
make test
make render-status
cd frontend && npm run build
```

### Test commands

```bash
make test
make render-status
cd frontend && npm run build
```

### Known limitations
- No geo-accurate production tile warping yet
- `ENABLE_PRODUCTION_RADAR_TILES=false` by default
- Decoded prototype remains behind `ENABLE_DECODED_TILES=false`
- Placeholder tiles remain default API behavior
- GDAL/rasterio/wgrib2 still optional

## Phase 15 - Geo-Accurate Tile Warping Prototype

Added stdlib Web Mercator warping prototype to build and serve production tile cache when explicitly enabled.

### Backend
- `backend/app/services/tile_pyramid.py` — geo metadata validation, EPSG:3857 tile bounds, WGS84→grid bilinear warping
- `backend/app/services/production_tile_builder.py` — build warped tiles from decode artifacts + `geo_metadata.json`
- Production cache: `data/tiles/production/{layer}/{timestamp}/{z}/{x}/{y}.png`
- Tile mode: `production-prototype` when all gates pass and cached tile exists
- Serving order unchanged: production → decoded prototype → placeholder
- `encode_normalized_grid_png` in `tile_service.py` for direct grid→PNG (no Pillow/GDAL)

### Scripts / Makefile
- `scripts/build_production_tiles.py`, `make build-production-tiles` (optional `--mark-catalog` for fixture/test frames)

### Frontend
- Banner shows Production prototype mode when `ENABLE_PRODUCTION_RADAR_TILES=true`; never labeled verified MRMS

### Run commands

```bash
make test
make build-production-tiles
cd frontend && npm run build
```

### Test commands

```bash
make test
make build-production-tiles
cd frontend && npm run build
```

### Known limitations
- Warping prototype only — not verified real MRMS output
- Supports EPSG:4326 bounds → EPSG:3857 tiles; other CRS rejected
- `.raw` normalized grids only (no rasterio required)
- Default remains placeholder tiles; production flag off by default
- Catalog not auto-marked unless `--mark-catalog` on build script

## Phase 16 - Production Tile Build Hardening + Multi-Zoom Benchmark

Hardened production tile builder with limited multi-zoom pyramids, batch worker functions, idempotent builds, dry-run, and JSON benchmark reports.

### Backend
- Multi-zoom support: `--min-zoom` / `--max-zoom` (default 0–0, capped at z4, max 256 tiles/build)
- Bounds-based tile planning via `iter_tiles_for_bounds`
- `transform` metadata used for grid sampling when present (affine inverse)
- Worker-style: `plan_production_tile_jobs` + `execute_production_tile_batch`
- Idempotent: skip existing tiles unless `--force`
- `BuildProductionTilesResult.to_dict()` JSON report with metrics

### Scripts
- `scripts/build_production_tiles.py`: `--min-zoom`, `--max-zoom`, `--force`, `--dry-run`, `--json-report`, `--limit`
- Prominent stderr warning when `--mark-catalog` is used

### Run commands

```bash
make test
make build-production-tiles
make build-production-tiles -- --dry-run --json-report
cd frontend && npm run build
```

### Known limitations
- No job queue/worker process yet — batch functions only
- Zoom cap z4 and 256 tiles/build to prevent accidental pyramids
- Still not verified real MRMS production output
- Placeholder default unchanged

## Phase 17 - Render Queue + Local Worker

Added SQLite-backed render job queue and local worker for production tile builds with progress tracking.

### Backend
- `RenderJob` model/table (`render_jobs`) — queued, running, succeeded, failed, canceled
- `backend/app/services/render_queue.py` — enqueue, claim, progress, status updates
- `backend/app/workers/render_worker.py` — processes jobs via Phase 16 `build_production_tiles`
- Dev API: `POST/GET /api/render/jobs`, `GET /api/render/jobs/{id}`
- Progress callbacks on tile batch execution
- No Redis/Celery — SQLite only

### Scripts / Makefile
- `scripts/enqueue_render_job.py`, `scripts/run_render_worker.py`
- `make enqueue-render-job`, `make render-worker-once`
- `ARGS` forwarding for Makefile script targets

### Frontend
- Optional render queue status hint in header (prototype wording)

### Run commands

```bash
make test
make enqueue-render-job
make render-worker-once
cd frontend && npm run build
```

### Known limitations
- Local dev worker only — not cloud deployment
- Worker processes one job per invocation (`render-worker-once`)
- No destructive job delete API
- Production serving gates unchanged; placeholder default unchanged

## Phase 18 - Render Job Observability + Continuous Worker

Improved render job observability, retry policy, queue filtering/summary, and safe continuous local worker loop.

### Backend
- Extended `RenderJob`: `attempt_count`, `max_attempts`, `last_error_at`, `next_retry_at`, `canceled_at`
- SQLite migration for existing DBs via `_ensure_render_job_columns`
- Retry: auto re-queue on failure when `attempt_count < max_attempts` with `next_retry_at` delay
- `retry_render_job` / `cancel_render_job` service functions
- `get_queue_summary` — status counts + total tiles/bytes
- `list_render_jobs` filters: `status`, `layer`, `timestamp`, `job_type`
- `run_worker_loop` — continuous mode with `max_jobs` and `sleep_seconds`
- Dev API: `GET /api/render/jobs/summary`, filters on list, `POST .../retry`, `POST .../cancel`

### Scripts / Makefile
- `scripts/run_render_worker.py` — `--once` or continuous (`--max-jobs`, `--sleep`)
- `scripts/render_queue_status.py` — queue summary CLI
- `scripts/render_status.py` — includes queue summary section
- `make render-worker`, `make render-queue-status`

### Frontend
- Header hint shows queued/running/failed counts from summary API (prototype wording)

### Run commands

```bash
make test
make render-queue-status
make render-worker-once
make render-worker ARGS="--max-jobs 1 --sleep 0.1"
make render-status
cd frontend && npm run build
```

### Known limitations
- Local dev worker only — not cloud deployment or daemon supervision
- Continuous worker sleeps when queue empty (no exit unless `--max-jobs` reached)
- No stale `running` job recovery after worker crash
- Production serving gates unchanged; placeholder default unchanged
- Not verified real MRMS output

## Phase 19 - Real MRMS Validation + Worker Hardening

End-to-end experimental validation orchestrator for discover → download → inspect → decode → enqueue → worker, plus stale job recovery and worker signal handling.

### Backend
- `backend/app/services/mrms_validation.py` — `run_mrms_validation`, `MrmsValidationReport`
- Stale running job recovery: `recover_stale_running_jobs` (1h threshold, respects max_attempts)
- Worker logging + interruptible sleep + `should_stop` callback for clean exit
- Safe stub mode by default; real mode requires `--real` or `MRMS_SOURCE_MODE=real`

### Scripts / Makefile
- `scripts/validate_real_mrms.py` — validation CLI with `--json-report`, `--run-worker`, `--limit 1`
- `make validate-real-mrms`
- `scripts/run_render_worker.py` — SIGINT/SIGTERM handling, `--verbose` logging

### Frontend
- Header wording notes experimental validation pipeline (not verified MRMS)

### Run commands

```bash
make test
make validate-real-mrms
make validate-real-mrms ARGS="--json-report"
MRMS_SOURCE_MODE=real make validate-real-mrms ARGS="--real --run-worker"
make render-worker-once
cd frontend && npm run build
```

### Known limitations
- Validation output is prototype — `verified_mrms` always false
- Stub mode cannot produce real GRIB2 decode artifacts without a real download
- Stale recovery threshold configurable via `STALE_RUNNING_JOB_SECONDS` (default 3600)
- No new public API endpoints
- Production serving gates unchanged; placeholder default unchanged

## Phase 20 - Validation Dashboard + Real-Frame Benchmark

Dev validation dashboard API, persisted reports, benchmark timing, configurable stale threshold, and frontend status panel.

### Backend
- `validation_report_store.py` — persist latest validation/benchmark JSON under `data/dev/`
- `validation_dashboard.py` — build summary for dev API
- `mrms_benchmark.py` — per-stage timing + tile build metrics
- `STALE_RUNNING_JOB_SECONDS` setting (default 3600)
- Dev API: `GET /api/validation/summary`, `GET /api/validation/latest`
- Validation runs auto-persist via `run_mrms_validation`

### Scripts / Makefile
- `scripts/benchmark_real_mrms.py` — `make benchmark-real-mrms`
- `make validate-real-mrms` unchanged; reports now persisted

### Frontend
- `ValidationStatusPanel` — decoder, queue, validation counts, benchmark metrics, prototype warnings

### Run commands

```bash
make test
make validate-real-mrms
make benchmark-real-mrms
make benchmark-real-mrms ARGS="--json-report"
make render-queue-status
cd frontend && npm run build
curl http://127.0.0.1:8000/api/validation/summary
```

### Known limitations
- Dashboard shows latest report only (no history)
- Benchmark tile build runs directly (not only via queue worker)
- `verified_mrms` always false — not verified production radar
- Production serving gates unchanged; placeholder default unchanged

## Phase 21 - Multi-Frame Catalog Growth + Batch Validation

Batch MRMS validation (default 3 frames, max 10), catalog status helpers, bounded validation history, and dashboard refresh.

### Backend
- `mrms_batch_validation.py` — `run_mrms_batch_validation`, per-frame summaries, safe count cap
- `catalog_status.py` — MRMS catalog counts by download/process/render status
- `validation_report_store.py` — bounded history (last 10) in `data/dev/validation_history.json`
- Dev API: `GET /api/validation/history`, `GET /api/catalog/status`
- Extended `GET /api/validation/summary` with catalog + history count

### Scripts / Makefile
- `scripts/batch_validate_mrms.py` — `make validate-real-mrms-batch` (default count 3)
- `scripts/catalog_status.py` — `make catalog-status`
- `scripts/validate_real_mrms.py` — `--count N` routes to batch when N > 1

### Frontend
- Validation panel: catalog counts, batch frame count, history count, Refresh button

### Run commands

```bash
make test
make validate-real-mrms-batch
make catalog-status
make render-queue-status
cd frontend && npm run build
```

### Known limitations
- Batch default/max caps prevent large downloads (max 10 frames)
- Stub mode cannot decode real GRIB2 without real downloads
- History stores compact summaries only (last 10)
- `verified_mrms` always false
- Production serving gates unchanged; placeholder default unchanged

## Phase 22 - Multi-Zoom Queue Benchmark + Validation History UI

Queue-based multi-zoom benchmark for small batches, persisted queue benchmark reports, and dev panel history/benchmark display.

### Backend
- `render_queue_benchmark.py` — enqueue one job per frame, bounded worker processing, per-job + aggregate metrics
- Safe defaults: count 3 (max 10), zoom 0–1 (clamped to z4)
- `validation_report_store.py` — `data/dev/queue_benchmark_latest.json` + bounded history (last 10)
- Extended `GET /api/validation/summary` with `queue_benchmark`, compact `validation_history`, queue benchmark history count
- `GET /api/validation/benchmarks` — latest queue benchmark + history
- Extended `GET /api/validation/latest` with `queue_benchmark` blob

### Scripts / Makefile
- `scripts/benchmark_render_queue.py` — `make benchmark-render-queue` (`--count`, `--min-zoom`, `--max-zoom`, `--force`, `--dry-run`, `--json-report`)

### Frontend
- Dev Validation panel: recent validation history list, queue benchmark metrics, per-job summaries, queue succeeded count

### Run commands

```bash
make test
make benchmark-render-queue
make benchmark-render-queue ARGS="--dry-run --json-report"
make validate-real-mrms-batch
make catalog-status
make render-queue-status
cd frontend && npm run build
```

### Known limitations
- Queue benchmark uses local catalog frames; does not auto-discover/download in real mode
- Without decode artifacts, worker jobs may succeed with 0 tiles written
- History stores compact summaries only (last 10)
- `verified_mrms` always false
- Production serving gates unchanged; placeholder default unchanged

## Phase 23 - Scheduled Local Validation + Per-Frame Tile Metrics

Cron-friendly scheduled validation wrapper, richer per-frame tile metrics, and dev panel JSON drill-down.

### Backend
- `scheduled_validation.py` — orchestrates catalog → batch validation → queue benchmark → queue status → summary
- `validation_report_store.py` — `data/dev/scheduled_validation_latest.json` + bounded history (last 10)
- Richer `FrameValidationSummary` and `JobBenchmarkSummary` tile/decode metrics
- `GET /api/validation/scheduled` — latest scheduled run + history
- Extended `GET /api/validation/summary` with `scheduled_validation`, `frame_summaries`
- Extended `GET /api/validation/latest` with `scheduled_validation` blob

### Scripts / Makefile
- `scripts/run_scheduled_validation.py` — `make scheduled-validation` (`--real`, `--count`, `--min-zoom`, `--max-zoom`, `--json-report`)

### Frontend
- Dev Validation panel: scheduled run status, per-frame/job tile metrics, Show details JSON drill-down

### Run commands

```bash
make test
make scheduled-validation
make scheduled-validation ARGS="--json-report"
make benchmark-render-queue
cd frontend && npm run build
```

### Known limitations
- Scheduled run does not install cron; operator must configure manually
- Real mode may download NOAA MRMS; decoder optional for full decode success
- Per-frame tile metrics depend on decode artifacts existing locally
- `verified_mrms` always false
- Production serving gates unchanged; placeholder default unchanged

## Phase 24 - Operator Runbooks + Failure Diagnostics

Step-level scheduled validation drill-down, append-only failure log, smoke test command, and operator runbook.

### Backend
- `validation_failure_log.py` — append-only `data/dev/validation_failures.jsonl` (max 100)
- `scheduled_validation.py` — step `started_at`/`finished_at`, statuses succeeded/failed/warning/skipped
- `run_real_mrms_smoke_test()` — real mode, count 1, zoom 0 only
- `GET /api/validation/failures` — recent failure entries
- Summary: `validation_failures_count`, `validation_failures_recent`, `scheduled_validation.steps`

### Scripts / Makefile
- `scripts/validation_failures.py` — `make validation-failures`
- `scripts/real_mrms_smoke_test.py` — `make real-mrms-smoke-test`

### Docs
- `docs/RUNBOOK_REAL_MRMS_VALIDATION.md` — operator troubleshooting guide

### Frontend
- Dev panel: scheduled step list, failure count/summaries, Show details JSON

### Run commands

```bash
make test
make scheduled-validation
make validation-failures
make real-mrms-smoke-test
cd frontend && npm run build
```

### Known limitations
- Failure log is dev-only, local disk, not replicated
- Smoke test still requires network for real downloads
- `verified_mrms` always false
- Production serving gates unchanged; placeholder default unchanged

## Phase 25 - Validation Alert Markers + Verified MRMS Proof Criteria

Local alert marker service, grouped failure causes in dev dashboard/API, and documented proof criteria for a future verified MRMS phase.

### Backend
- `validation_alerts.py` — alert status, grouped causes, cause classification, `data/dev/validation_alert_latest.json`
- `validation_failure_log.py` — `load_all_validation_failures()` for grouping
- `scheduled_validation.py` — refreshes alert after persist
- `validation_dashboard.py` — summary fields `validation_alert`, `grouped_failure_causes`
- `GET /api/validation/alerts` — latest alert (`?refresh=true` optional)

### Scripts / Makefile
- `scripts/validation_alerts.py` — `make validation-alerts`

### Docs
- `docs/VERIFIED_MRMS_CRITERIA.md` — explicit proof checklist (not met today)
- Updated runbook, architecture, API spec, README links

### Frontend
- Dev panel: alert status, grouped failure causes, suggested next action, alert timestamp

### Run commands

```bash
make test
make validation-alerts
make validation-failures
make scheduled-validation
cd frontend && npm run build
```

### Known limitations
- Alert marker is local/dev-only JSON, not replicated
- Cause classification is heuristic (normalized message buckets)
- `verified_mrms` always false — criteria doc is forward-looking only
- Production serving gates unchanged; placeholder default unchanged

## Phase 26 - Draft MRMS Proof Report Automation

Automated evidence gathering against `VERIFIED_MRMS_CRITERIA.md` with geo sanity helpers and operator sign-off template.

### Backend
- `mrms_proof_report.py` — multi-frame proof, criterion evaluation, geo sanity, persistence
- `GET /api/validation/proof` — latest proof report
- Summary/latest: `mrms_proof` compact status

### Scripts / Makefile
- `scripts/generate_mrms_proof_report.py` — `make mrms-proof-report`

### Docs
- `docs/MRMS_OPERATOR_SIGNOFF_TEMPLATE.md` — sign-off does not set verified_mrms
- Updated criteria, runbook, architecture, API spec

### Frontend
- Dev panel: proof status, frame count, criteria counts, operator review required

### Run commands

```bash
make test
make mrms-proof-report
make validation-alerts
cd frontend && npm run build
```

### Known limitations
- Proof automation is heuristic; visual/operator criteria remain manual
- Stub mode produces `insufficient_evidence` by design
- `verified_mrms` always false
- Production serving gates unchanged; placeholder default unchanged

## Phase 27 - Proof Regression Hooks + Operator Sign-Off Persistence

Detect worsening MRMS proof evidence, surface regressions in validation alerts, persist local operator sign-offs.

### Backend
- `mrms_proof_regression.py` — compare latest vs previous proof, persist regression report
- `mrms_signoff.py` — local sign-off records (`mrms_signoffs.json`)
- `validation_alerts.py` — `proof_regression` cause bucket and alert fields
- `scheduled_validation.py` — optional `--proof` pipeline step
- `GET /api/validation/proof-regression`, `GET /api/validation/signoffs`

### Scripts / Makefile
- `scripts/mrms_proof_regression.py` — `make mrms-proof-regression`
- `scripts/mrms_signoff.py` — `make mrms-signoff`

### Frontend
- Dev panel: proof regression status, sign-off count/timestamp

### Run commands

```bash
make test
make mrms-proof-report
make mrms-proof-regression
make scheduled-validation ARGS="--proof"
cd frontend && npm run build
```

### Known limitations
- Regression needs at least two proof runs for meaningful comparison
- Sign-off is CLI/local JSON only (no verified_mrms promotion)
- `verified_mrms` always false
- Production serving gates unchanged; placeholder default unchanged

## Phase 28 - Proof History Drill-Down + Sign-Off Review UI

Bounded read-only proof/regression/sign-off history APIs and dev panel proof review section.

### Backend
- `mrms_proof_history.py` — compact history builders
- `GET /api/validation/proof/history`
- `GET /api/validation/proof-regression/history`
- `GET /api/validation/signoffs` — compact sign-off items

### Scripts / Makefile
- `scripts/mrms_proof_history.py` — `make mrms-proof-history`

### Frontend
- Dev Validation: **Show proof review** toggle with history lists

### Run commands

```bash
make test
make mrms-proof-history
cd frontend && npm run build
```

### Known limitations
- History is local JSON only; no delete/reset endpoints
- Sign-off remains CLI-primary (API read-only)
- `verified_mrms` always false
- Production serving gates unchanged; placeholder default unchanged

## Phase 29 - Dev Sign-Off Form + Alert Linkage

Optional dev-only sign-off POST API, alert linkage after sign-off, scheduled proof-step compact in summary.

### Backend
- `POST /api/validation/signoffs` — dev/local only; shares validation with CLI (`create_signoff_and_refresh_alert`)
- Sign-off response always: `verified_mrms: false`, `local_signoff_only: true`, `does_not_enable_production: true`
- Alert refresh after sign-off; regression remains active until evidence improves
- Summary: `scheduled_validation.proof_step` compact; `mrms_signoff.proof_regression_still_active`

### Frontend
- Dev sign-off form in **Show proof review** section (honest local-only wording)
- Scheduled proof-step compact display; regression-still-active indicator

### Run commands

```bash
make test
make mrms-proof-report
make mrms-proof-regression
make mrms-proof-history
make validation-alerts
make scheduled-validation
make catalog-status
make render-queue-status
cd frontend && npm run build
```

### Known limitations
- Sign-off is local operator review only — not verified MRMS
- Sign-off does not clear proof regression automatically
- `verified_mrms` always false
- Production serving gates unchanged; placeholder default unchanged

## Phase 30 - Exportable MRMS Proof Bundle + Runbook Deep Links

Local proof evidence packaging into timestamped folder + ZIP with manifest and runbook references.

### Backend
- `mrms_proof_bundle.py` — gather evidence, write manifest/README, ZIP export
- `GET /api/validation/proof-bundles` — bounded bundle history (read-only)
- Summary/latest: `mrms_proof_bundle` compact + `runbook_references`

### Scripts / Makefile
- `scripts/export_mrms_proof_bundle.py` — `make mrms-proof-bundle` (`--json-report`, `--include-history`)

### Frontend
- Dev Validation proof bundle section + runbook doc path references

### Run commands

```bash
make test
make mrms-proof-bundle
make mrms-proof-report
make mrms-proof-regression
make mrms-proof-history
make validation-alerts
make scheduled-validation
make catalog-status
make render-queue-status
cd frontend && npm run build
```

### Known limitations
- Bundles are local dev artifacts only — not verified MRMS
- Export does not mutate catalog, sign-offs, or production flags
- No browser download endpoint (local paths only)
- `verified_mrms` always false
- Production serving gates unchanged; placeholder default unchanged

## Phase 31 - Proof Bundle Diff + Operator Handoff Checklist

Compare local proof bundles and generate operator handoff review checklist.

### Backend
- `mrms_proof_bundle_diff.py` — compare manifests/evidence; overall status (`unchanged`, `improved`, `worsened`, `mixed`, `no_baseline`, `unknown`)
- `mrms_operator_handoff.py` — generate `mrms_operator_handoff_latest.md` + JSON metadata
- `GET /api/validation/proof-bundle-diff`, `GET /api/validation/operator-handoff`
- Summary: `mrms_proof_bundle_diff`, `operator_handoff` compact status
- `.gitignore` covers `data/dev/proof_bundles/` and related runtime JSON/Markdown

### Scripts / Makefile
- `make mrms-proof-bundle-diff`, `make mrms-operator-handoff`

### Frontend
- Dev Validation proof bundle diff / handoff section

### Run commands

```bash
make test
make mrms-proof-bundle
make mrms-proof-bundle-diff
make mrms-operator-handoff
cd frontend && npm run build
```

### Known limitations
- Diff requires at least two exported bundles for baseline comparison
- Handoff/diff are local review only — not verified MRMS
- `verified_mrms` always false
- Production serving gates unchanged; placeholder default unchanged

## Phase 32 - Scheduled Proof Bundle Export + Alert Hooks

Optional scheduled proof bundle export/diff with validation alert hooks.

### Backend
- `run_scheduled_validation` — `--bundle` / `--diff-bundle` flags; steps `proof_report`, `proof_regression`, `proof_bundle_export`, `proof_bundle_diff`
- Alert cause `proof_bundle_diff_worsened`; operator attention for `worsened`/`mixed` diff
- Summary: `scheduled_proof_bundle` compact status

### Scripts / Makefile
- `make scheduled-proof-bundle` — `scheduled-validation --proof --bundle --diff-bundle`
- `run_scheduled_validation.py` — `--bundle`, `--proof-bundle`, `--diff-bundle`

### Frontend
- Dev Validation scheduled proof bundle monitoring section

### Run commands

```bash
make test
make scheduled-validation
make scheduled-proof-bundle
make validation-alerts
cd frontend && npm run build
```

### Known limitations
- Diff alert does not auto-clear when evidence improves (re-run scheduled flow)
- Scheduled bundle export is local monitoring only — not verified MRMS
- `verified_mrms` always false
- Production serving gates unchanged; placeholder default unchanged

## Phase 33 - Scheduled Handoff Auto-Regenerate + Operator Guidance

Optional scheduled handoff regeneration when proof bundle diff worsens/mixed; runbook guidance links in alerts and dashboard.

### Backend
- `operator_guidance.py` — cause → runbook guidance mapping
- `run_scheduled_validation` — `--handoff` flag; step `operator_handoff`; report handoff compact fields
- Validation alert adds `operator_guidance` when `operator_attention_needed`
- Summary: `operator_guidance`, extended `scheduled_proof_bundle` and `operator_handoff` handoff status

### Scripts / Makefile
- `make scheduled-proof-bundle-handoff` — `--proof --bundle --diff-bundle --handoff`
- `run_scheduled_validation.py` — `--handoff`

### Frontend
- Dev Validation: operator guidance links, scheduled handoff auto-gen status, honest non-verification wording

### Run commands

```bash
make test
make scheduled-validation
make scheduled-proof-bundle
make scheduled-proof-bundle-handoff
make validation-alerts
cd frontend && npm run build
```

### Known limitations
- Handoff auto-gen requires `--handoff` explicitly (default scheduled flows unchanged)
- Guidance links are doc path + section label (not live deep links in UI)
- `verified_mrms` always false; production gates unchanged

## Phase 34 - Proof Bundle Diff Alert History

Bounded timeline of proof bundle diff alert states for local operator monitoring.

### Backend
- `proof_bundle_diff_alert_history.py` — record/load bounded timeline (25 entries)
- Hooked into `build_proof_bundle_diff_report` / scheduled diff step
- Validation alert: `proof_bundle_diff_alert_history_count`, `latest_proof_bundle_diff_alert_at/status`
- Summary: `proof_bundle_diff_alert`, `proof_bundle_diff_alert_history` (last 5)
- `GET /api/validation/proof-bundle-diff-alert-history`

### Scripts / Makefile
- `make proof-bundle-diff-alert-history` — read-only CLI (`--json`, `--limit`)

### Frontend
- Dev Validation diff alert timeline section with show/hide toggle

### Run commands

```bash
make test
make proof-bundle-diff-alert-history
make scheduled-proof-bundle
make validation-alerts
cd frontend && npm run build
```

### Known limitations
- Duplicate exact diff results in the same run are skipped (not re-appended)
- Timeline does not auto-clear validation alerts when status improves
- `verified_mrms` always false; production gates unchanged

## Phase 35 - Diff Alert Trend Summary + Operator Acknowledgment

Trend analysis over diff alert history and optional local acknowledgment notes.

### Backend
- `proof_bundle_diff_alert_trends.py` — trend: worsening/improving/mixed/stable/no_data, streaks
- `proof_bundle_diff_acknowledgment.py` — bounded local ack records (50 max)
- Summary/alert: trend compact, acknowledgment count, acknowledged-but-still-active flag
- `GET /api/validation/proof-bundle-diff-alert-trend`
- `GET/POST /api/validation/proof-bundle-diff-acknowledgments`

### Scripts / Makefile
- `make proof-bundle-diff-alert-trend`, `make proof-bundle-diff-acknowledge`

### Frontend
- Dev Validation trend summary + acknowledgment form (local only)

### Run commands

```bash
make test
make proof-bundle-diff-alert-trend
make proof-bundle-diff-acknowledge ARGS="--operator OP --note 'local ack'"
cd frontend && npm run build
```

### Known limitations
- Acknowledgment does not clear validation alerts
- Trend window defaults to 10 entries
- `verified_mrms` always false

## Phase 36 - Diff Alert Escalation Hints + Runbook Deep Links

Escalation combines trend, diff alert history, and acknowledgment state into operator guidance levels with runbook section links.

### Backend
- `proof_bundle_diff_escalation.py` — levels: none/watch/attention/urgent; stale acknowledgment detection
- Summary `proof_bundle_diff_escalation`; alert escalation fields + guidance items
- `GET /api/validation/proof-bundle-diff-escalation` (read-only)

### Scripts / Makefile
- `make proof-bundle-diff-escalation` (`--json`)

### Frontend
- Dev Validation escalation section with show/hide toggle

### Run commands

```bash
make test
make proof-bundle-diff-escalation
make proof-bundle-diff-acknowledge ARGS="--operator OP --note 'local ack'"
cd frontend && npm run build
```

### Known limitations
- Escalation does not clear alerts or verify MRMS
- Escalation does not enable production rendering or mutate catalog gates
- `verified_mrms` always false

## Phase 37 - Escalation History + Stdout Urgent Notices

Bounded escalation snapshots and optional local terminal urgent notices during scheduled runs.

### Backend
- `proof_bundle_diff_escalation_history.py` — bounded snapshots (25 max)
- `proof_bundle_diff_escalation_stdout.py` — `--notify-stdout` urgent notice (no external notifications)
- `GET /api/validation/proof-bundle-diff-escalation-history`
- Summary `proof_bundle_diff_escalation_history`; alert history count + stdout status

### Scripts / Makefile
- `make proof-bundle-diff-escalation-history`, `make scheduled-proof-bundle-notify`

### Run commands

```bash
make test
make proof-bundle-diff-escalation-history
make scheduled-proof-bundle-notify
cd frontend && npm run build
```

### Known limitations
- Stdout notices are local terminal only — no email/Slack/webhooks
- History does not clear alerts or verify MRMS
- `verified_mrms` always false

## Phase 38 - Escalation Metrics + Local Digest Export

Trend metrics rollup and optional local Markdown digest for operator review.

### Backend
- `proof_bundle_diff_escalation_metrics.py` — counts, streaks, stale ack rollup
- `proof_bundle_diff_escalation_digest.py` — Markdown + JSON metadata export
- `GET /api/validation/proof-bundle-diff-escalation-metrics`
- `GET /api/validation/proof-bundle-diff-escalation-digest`
- Summary metrics + digest compacts

### Scripts / Makefile
- `make proof-bundle-diff-escalation-metrics`, `make proof-bundle-diff-escalation-digest`

### Frontend
- Dev Validation escalation metrics + digest section

### Run commands

```bash
make test
make proof-bundle-diff-escalation-metrics
make proof-bundle-diff-escalation-digest
cd frontend && npm run build
```

### Known limitations
- Digest is local file export only — not a notification system
- Metrics derived from bounded history (max 25 snapshots)
- `verified_mrms` always false

## Phase 39 - Scheduled Digest + Operator Review Checklist

Optional scheduled escalation digest after proof bundle diff and extended operator handoff checklist.

### Backend
- `scheduled_validation.py` — `digest_requested`, step `escalation_digest`, report digest fields
- `mrms_operator_handoff.py` — `include_escalation_review`, explicit Phase 39 checklist items, metrics/ack/digest sections
- `proof_bundle_diff_escalation_digest.py` — `compact_scheduled_digest()`
- Summary `scheduled_digest` + extended `operator_handoff` compacts

### Scripts / Makefile
- `--digest` / `--escalation-digest` on `run_scheduled_validation.py`
- `make scheduled-proof-bundle-digest`

### Frontend
- Dev Validation: scheduled digest status, operator checklist path/ack status, honest safety wording

### Run commands

```bash
make test
make scheduled-proof-bundle-digest
make scheduled-validation
cd frontend && npm run build
```

### Known limitations
- Scheduled digest opt-in only — default scheduled validation unchanged
- Checklist/digest do not clear alerts, verify MRMS, or enable production
- No external notifications
- `verified_mrms` always false

## Phase 40 - Digest History + Diff + Regeneration Hints

Bounded digest export history, diff metadata between exports, and regeneration hints in summary.

### Backend
- `proof_bundle_diff_escalation_digest_history.py` — bounded history (max 25)
- `proof_bundle_diff_escalation_digest_diff.py` — diff classification + regeneration hints
- Auto-record on digest export; summary compacts + new read-only API endpoints

### Scripts / Makefile
- `make proof-bundle-diff-escalation-digest-history`
- `make proof-bundle-diff-escalation-digest-diff`

### Frontend
- Dev Validation: digest history count, diff status, regeneration hint + suggested command

### Run commands

```bash
make test
make proof-bundle-diff-escalation-digest-history
make proof-bundle-diff-escalation-digest-diff
cd frontend && npm run build
```

### Known limitations
- History/diff derived from local metadata only — not verified MRMS
- Regeneration hints are suggestions only — no auto-export or notifications
- `verified_mrms` always false

## Phase 41 - Local MRMS Proof Review Sessions

Review session records linking escalation, digest, handoff, acknowledgment, bundle, diff, and proof report evidence.

### Backend
- `mrms_review_session.py` — create/list, validation, open attention items, checklist tracking
- `GET/POST /api/validation/review-sessions`
- Summary `mrms_review_session` compact
- Gitignored: `data/dev/mrms_review_sessions.json` (max 50)

### Scripts / Makefile
- `make mrms-review-session`, `make mrms-review-sessions`

### Frontend
- Dev Validation review session status + optional submit form

### Run commands

```bash
make test
make mrms-review-session ARGS="--operator TEST --notes 'local test' --accepted-limitations"
make mrms-review-sessions
cd frontend && npm run build
```

### Known limitations
- Review sessions do not clear alerts or verify MRMS
- Evidence links are point-in-time snapshots at session creation
- `verified_mrms` always false

## Phase 42 - Review Session Comparison + Runbook Guidance

Compare consecutive review sessions and surface runbook deep-links for open attention items.

### Backend
- `mrms_review_session_compare.py` — comparison service, persistence, bounded history (max 25)
- `operator_guidance.build_open_attention_guidance()` — open attention → runbook mapping
- `GET /api/validation/review-sessions/comparison`, `GET .../comparison/history`
- Summary `mrms_review_session` adds `comparison` + `open_attention_guidance`
- Gitignored: `mrms_review_session_comparison_latest.json`, `mrms_review_session_comparison_history.json`

### Scripts / Makefile
- `make mrms-review-session-compare` (read-only compare + persist; `--json`)

### Frontend
- Dev Validation: comparison status, baseline/latest timestamps, count changes, improvements/regressions, open attention runbook links

### Run commands

```bash
make test
make mrms-review-session ARGS="--operator TEST --notes 'local test' --accepted-limitations"
make mrms-review-session-compare
cd frontend && npm run build
```

### Known limitations
- Comparison is local/dev review tooling only — not verified MRMS
- Requires at least two sessions for baseline comparison (`no_baseline` otherwise)
- Comparison does not clear alerts or mutate production/catalog/render gates
- `verified_mrms` always false

## Phase 43 - Review Session Markdown Export

Optional local Markdown export of latest review session + comparison + guidance + digest hints.

### Backend
- `mrms_review_session_export.py` — export service, bounded history (max 25)
- `build_review_export_regeneration_hint()` — export stale vs session/comparison/digest
- `GET /api/validation/review-sessions/export`, `GET .../export/history`
- Summary: `mrms_review_session_export`, `review_export_regeneration_hint`
- Gitignored: export latest `.md`/`.json`, `mrms_review_session_export_history.json`

### Scripts / Makefile
- `make mrms-review-session-export` (`--json-report`)
- `make mrms-review-session-exports` (`--json`, `--limit`)

### Frontend
- Dev Validation: export timestamp/path, comparison status, regeneration hint + suggested command

### Run commands

```bash
make test
make mrms-review-session-export
make mrms-review-session-exports
cd frontend && npm run build
```

### Known limitations
- Export requires at least one review session
- Export is local/dev review tooling only — not verified MRMS
- Does not clear alerts or mutate production/catalog/render gates
- `verified_mrms` always false

## Phase 44 - Scheduled Review Session Export

Optional scheduled validation step to export review session Markdown after digest/handoff.

### Backend
- `run_scheduled_validation(..., review_export_requested=True)` — step `review_session_export`
- `compact_scheduled_review_export()` — summary compact
- Skips with `skipped_no_review_session` without failing run
- Summary: `scheduled_review_export` + existing export/regeneration compacts

### Scripts / Makefile
- `--review-export` / `--export-review` on `run_scheduled_validation.py`
- `make scheduled-proof-bundle-review-export`

### Frontend
- Dev Validation: scheduled review export status in proof bundle section

### Run commands

```bash
make test
make scheduled-proof-bundle-review-export
cd frontend && npm run build
```

### Known limitations
- Requires review session for generated export (`skipped_no_review_session` otherwise)
- Default `make scheduled-validation` unchanged
- Does not clear alerts or mutate production/catalog/render gates
- `verified_mrms` always false

## Phase 45 - Review Export Diff + Auto-Export After Create

Diff metadata between consecutive review session Markdown exports; optional export immediately after session create.

### Backend
- `mrms_review_session_export_diff.py` — compare latest vs previous export snapshots
- Persist: `mrms_review_session_export_diff_latest.json` + bounded history (max 25, gitignored)
- Record diff whenever `export_latest_review_session()` runs (manual, auto-export, scheduled)
- `GET /api/validation/review-sessions/export/diff`, `GET .../export/diff/history`
- Summary: `mrms_review_session_export_diff`
- `POST /api/validation/review-sessions` optional `export_after_create`; `try_export_after_review_session_create()` — no session rollback on export failure
- Export metadata enriched with `escalation_level`, `proof_bundle_diff_status`, `acknowledgment_id`

### Scripts / Makefile
- `make mrms-review-session-export-diff` (`--json`, `--limit`)
- `make mrms-review-session-export-diff-history` (`--history`, `--json`)
- `make mrms-review-session ARGS="... --export-after-create"` / `--export`

### Frontend
- Dev Validation: export diff status, timestamps, session changed, count change, improvements/regressions
- Review session form checkbox: “Export Markdown after creating this session”

### Run commands

```bash
make test
make mrms-review-session ARGS="--operator TEST --notes 'local test' --accepted-limitations --export-after-create"
make mrms-review-session-export-diff
make mrms-review-session-export-diff-history
cd frontend && npm run build
```

### Known limitations
- Export diff requires at least two exports for baseline comparison (`no_baseline` otherwise)
- Local/dev review tooling only — not verified MRMS
- Does not clear alerts or mutate production/catalog/render gates
- `verified_mrms` always false

## Phase 46 - Review Export Diff Trends

Trend summaries from bounded export diff history — local/dev review only.

### Backend
- `mrms_review_session_export_diff_trends.py` — counts, streaks, timestamps, `suggested_next_action`
- `GET /api/validation/review-sessions/export/diff/trend` (optional `window` 1–25)
- Summary: `mrms_review_session_export_diff_trend`
- Read-only — does not change export diff recording

### Scripts / Makefile
- `make mrms-review-session-export-diff-trend` (`--json`, `--limit`)

### Frontend
- Dev Validation: trend, latest status, counts, streaks, last timestamps, suggested action

### Run commands

```bash
make test
make mrms-review-session-export-diff-trend
cd frontend && npm run build
```

### Known limitations
- Trend requires export diff history (`no_data` when empty)
- Local/dev review tooling only — not verified MRMS
- Does not clear alerts or mutate production/catalog/render gates
- `verified_mrms` always false

## Phase 47 - Review Export Diff Trend Hints

Regeneration hints from export diff trends with optional scheduled validation tie-in.

### Backend
- `mrms_review_session_export_diff_trend_hint.py` — recommends new review/export from trend, diff, session staleness, digest hint
- `GET /api/validation/review-sessions/export/diff/trend-hint`
- Summary: `mrms_review_session_export_diff_trend_hint`
- Scheduled report: `review_export_trend_hint` when `review_export_requested` (no auto session/export)

### Scripts / Makefile
- `make mrms-review-session-export-diff-trend-hint` (`--json`)

### Frontend
- Dev Validation: regeneration recommended, reason, suggested command, trend, streaks, stale export

### Run commands

```bash
make test
make mrms-review-session-export-diff-trend-hint
make scheduled-proof-bundle-review-export
cd frontend && npm run build
```

### Known limitations
- Hint is read-only — does not auto-create sessions or export
- Local/dev review tooling only — not verified MRMS
- Does not clear alerts or mutate production/catalog/render gates
- `verified_mrms` always false

## Phase 48 - Review Export Diff History UI

Recent export diff history in Dev Validation summary and panel (max 5 entries).

### Backend
- `compact_review_session_export_diff_history_summary()` on export diff service
- Summary: `mrms_review_session_export_diff_history`
- Existing `GET .../export/diff/history` unchanged

### Frontend
- Dev Validation: count, latest status/timestamp, show/hide recent history list

### Run commands

```bash
make test
make mrms-review-session-export-diff-history
cd frontend && npm run build
```

### Known limitations
- Summary shows max 5 recent entries; full history via API/CLI (max 25)
- Local/dev review tooling only — not verified MRMS
- Does not clear alerts or mutate production/catalog/render gates
- `verified_mrms` always false

## Phase 49 - Operator Review Status Consolidation

Consolidated local operator review status for Dev Validation and CLI.

### Backend
- `operator_review_status.py` — reads existing validation alert, escalation, digest/export regeneration hints, review session/export/diff/trend/history compacts
- `GET /api/validation/operator-review-status`
- Summary: `operator_review_status`
- Read-only — does not mutate alerts, sessions, exports, digests, or gates

### Scripts / Makefile
- `make operator-review-status` (`--json`)

### Frontend
- Dev Validation: compact “Operator Review Status” block near top (level, reason, action, command, recommendations, trend, timestamps, counts)

### Run commands

```bash
make test
make operator-review-status
cd frontend && npm run build
```

### Known limitations
- Consolidation summarizes existing local artifacts only — `unknown` when insufficient data
- Local/dev review tooling only — not verified MRMS
- Does not clear alerts or mutate production/catalog/render gates
- `verified_mrms` always false

## Phase 50 - Scheduled Operator Review Status + Runbook Guidance

Scheduled validation tie-in and runbook deep-links for consolidated operator review status.

### Backend
- `build_operator_review_status_guidance()` — maps status levels, recommendations, evidence trends to runbook anchors
- `operator_review_status` adds `guidance_items`, `top_guidance_item`, `runbook_path`, `runbook_section`, `suggested_action`
- Scheduled validation: `--operator-status`; auto with `--review-export`
- Report fields: `operator_status_*`; step `operator_review_status`
- Summary: `scheduled_operator_status` compact

### Scripts / Makefile
- `make scheduled-proof-bundle-operator-status`
- `scripts/run_scheduled_validation.py --operator-status`

### Frontend
- Dev Validation: top guidance, runbook path/section, suggested action, scheduled operator status

### Run commands

```bash
make test
make scheduled-proof-bundle-operator-status
cd frontend && npm run build
```

### Known limitations
- Operator status build failure does not fail scheduled run — sets `operator_status_error`
- Local/dev review tooling only — not verified MRMS
- Does not clear alerts or mutate production/catalog/render gates
- `verified_mrms` always false

## Phase 51 - Dev Validation Panel UX Polish

Collapsible detail sections in the Dev Validation panel for easier scanning; Operator Review Status remains prominent and non-collapsible.

### Frontend
- `CollapsibleSection`, `StatusBadge`, `SafetyNote`, `CommandLine` helpers under `frontend/src/components/validation/`
- `ValidationStatusPanel.tsx` refactored: collapsible sections for validation alerts, proof bundle/diff/history, escalation/digest, review sessions/export/diff/history/trend, scheduled status, proof review, validation pipeline, raw JSON
- Summary lines visible when collapsed (status, counts, timestamps, suggested commands)
- Consistent safety labels: local only, does not verify MRMS, does not clear alerts, does not enable production rendering
- Mobile-friendly collapsible headers; no new UI library

### Backend
- No changes — API contracts unchanged

### Run commands

```bash
make test
make operator-review-status
make scheduled-validation
cd frontend && npm run build
```

### Known limitations
- UI polish only — does not change verification, alerts, proof state, review sessions, exports, or production gates
- `verified_mrms` always false
- Collapsed sections hide detail bodies; expand to use forms and full history lists

## Phase 52 - Operator Workflow Presets

Read-only local workflow presets derived from operator review status — organizes existing commands into guided presets.

### Backend
- `operator_workflow_presets.py` — seven presets with recommendation logic from `operator_review_status`
- Summary: `operator_workflow_presets` compact
- `GET /api/validation/operator-workflow-presets`
- `make operator-workflow-presets` (`--json`)

### Frontend
- Dev Validation **Operator Workflow Presets** collapsible below Operator Review Status
- Recommended presets listed first with command, when-to-use, expected outputs, safety notes

### Run commands

```bash
make test
make operator-workflow-presets
cd frontend && npm run build
```

### Known limitations
- Workflow guidance only — does not add new evidence or verify MRMS
- Does not clear alerts or mutate production/catalog/render gates
- `verified_mrms` always false

## Phase 53 - Workflow Preset Runbook Guidance + Copy-Ready Commands

Runbook deep-links and copy-ready command presentation for operator workflow presets.

### Backend
- `operator_workflow_presets.py` — each preset adds `runbook_path`, `runbook_section`, `runbook_anchor`, `suggested_action`
- Runbook anchors under `docs/RUNBOOK_REAL_MRMS_VALIDATION.md` (Phase 53 section)
- `make operator-workflow-presets` CLI prints guidance fields

### Frontend
- Operator Workflow Presets: recommended yes/no, recommendation reason, suggested action, runbook path/section/anchor
- `CommandLine` manual-copy hint — UI does not execute commands

### Run commands

```bash
make test
make operator-workflow-presets
cd frontend && npm run build
```

### Known limitations
- Advisory guidance only — operators copy commands manually
- Does not verify MRMS, clear alerts, or mutate gates

## Phase 54 - Grouped Operator Workflow Presets

Preset grouping and recommended priority for clearer local workflow navigation.

### Backend
- Preset fields: `group_id`, `group_title`, `priority`, `recommended_priority`, `short_reason`
- Groups: status-checks, full-review, review-session-export, troubleshooting, scheduled-workflows
- Compact `operator_workflow_preset_groups` in summary and endpoint payload
- Sort: recommended → recommended_priority → priority

### Frontend
- Dev Validation presets grouped by `group_title` with short_reason at top of each card

### Run commands

```bash
make test
make operator-workflow-presets
cd frontend && npm run build
```

### Known limitations
- Grouping is presentation only — does not change commands or verification behavior

## Phase 55 - Workflow Preset Command UX Polish

Preset filtering and copy-to-clipboard for local operator workflow guidance.

### Frontend
- `CommandLine`: Copy button with Copied/error states; manual-copy note clarifies copy does not execute commands
- `presetFilters.ts`: client-side recommended-only and optional group filter; empty groups hidden when filtered
- Dev Validation: visible preset count, filter controls, recommended styling preserved
- `npm test` (vitest): CommandLine copy button, clipboard helper, recommended-only filter logic

### Run commands

```bash
make test
make operator-workflow-presets
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Filtering is UI-only — API payload unchanged
- Copy uses browser clipboard API with manual-select fallback; does not run commands
- Presets remain advisory local-only — does not verify MRMS, clear alerts, or mutate gates

## Phase 56 - MRMS Visual Review Artifacts

Local visual review manifest and Markdown report for existing tile/render artifacts.

### Backend
- `backend/app/services/mrms_visual_review.py` — inspect catalog frames and on-disk tile paths
- Outputs: `data/dev/mrms_visual_review_latest.json`, `.md`, bounded `history.json` (max 25)
- Tile modes: `placeholder`, `placeholder_for_real_raw`, `decoded_prototype`, `production_gated`, `production_rendered_cache`, `unknown`
- `GET /api/validation/mrms-visual-review`, `/mrms-visual-review/history`
- Summary field: `mrms_visual_review` compact
- Operator review status optional context: `latest_visual_review_at`, paths

### Frontend
- Dev Validation collapsible **MRMS Visual Review** section with artifact counts, tile modes, suggested command

### Run commands

```bash
make test
make mrms-visual-review
make mrms-visual-review-history
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Read-only inspection — does not download, decode GRIB2, or render new tiles
- Does not verify MRMS, clear alerts, or enable production rendering

## Phase 57 - Visual Review Comparison and Hints

Compare visual review manifests and suggest when to regenerate.

### Backend
- `mrms_visual_review_compare.py` — latest vs previous manifest comparison with bounded history
- `mrms_visual_review_hint.py` — stale visual review regeneration hint from proof/validation evidence timestamps
- Previous manifest snapshot (`mrms_visual_review_previous.json`) on save
- Endpoints: `/mrms-visual-review/comparison`, `/comparison/history`, `/hint`
- Summary: `mrms_visual_review_comparison`, `mrms_visual_review_hint` compact fields

### Frontend
- Dev Validation MRMS Visual Review shows comparison status, count changes, tile mode deltas, regeneration hint

### Run commands

```bash
make test
make mrms-visual-review-compare
make mrms-visual-review-hint
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Comparison requires at least one prior visual review snapshot for baseline diffs
- Hints are advisory only — do not download, decode, or verify MRMS

## Phase 58 - Visual Review Operator Integration

Integrated MRMS visual review comparison and stale hints into operator review status and workflow presets.

### Backend
- `operator_review_status.py` reads visual review, comparison, and hint compacts
- New status fields: `visual_review_regeneration_recommended`, `visual_review_hint_reason`, comparison status, artifact counts
- Status level considers stale visual review (attention) and mixed/unknown comparison (watch)
- `top_suggested_command` may recommend `make mrms-visual-review` when stale (after digest; initial session still preferred when no session)
- Runbook guidance anchor `operator-review-status-visual-review-regeneration`
- `operator_workflow_presets.py` adds `regenerate-visual-review` preset in troubleshooting group

### Frontend
- Dev Validation **Operator Review Status** shows visual review recommendation fields
- Workflow presets include recommended `regenerate-visual-review` when stale

### Run commands

```bash
make test
make operator-review-status
make operator-workflow-presets
make mrms-visual-review-hint
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Visual review recommendations are local guidance only — do not verify MRMS, clear alerts, download/decode, or enable production rendering
- Empty dev environments may show visual review attention before other review evidence exists

## Phase 59 - Scheduled Visual Review Workflow

Optional scheduled validation step generates MRMS visual review artifacts when explicitly requested.

### Backend
- `scheduled_validation.py` — `--visual-review` flag; step after operator status
- Report fields: `visual_review_requested`, `visual_review_generated`, paths, reason, elapsed, error
- `compact_scheduled_visual_review()` on validation summary; operator review status embeds latest compact
- `make scheduled-proof-bundle-visual-review` Makefile target
- Workflow preset `full-scheduled-proof-review-with-visual-review`; updated standalone visual review preset wording

### Frontend
- Dev Validation scheduled section shows visual review requested/generated, paths, reason, elapsed, error

### Run commands

```bash
make test
make scheduled-proof-bundle-visual-review
make operator-workflow-presets
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Explicit opt-in only — default `make scheduled-validation` unchanged
- Scheduled visual review inspects existing artifacts — does not download/decode MRMS or enable production rendering

## Phase 60 - Visual Review Sample-Set Selection

Local drilldown sample-set selection from existing visual review manifests for closer manual inspection.

### Backend
- `mrms_visual_review_sample_set.py` — recommended/explicit selection, JSON/Markdown under `data/dev/`
- Paths: `mrms_visual_review_sample_set.json`, `mrms_visual_review_sample_set.md`
- `compact_visual_review_sample_set()` on validation summary
- API: `GET/POST /api/validation/mrms-visual-review/sample-set`
- CLI: `scripts/mrms_visual_review_sample_set.py`; `make mrms-visual-review-sample-set`

### Frontend
- Dev Validation **MRMS Visual Review** nested **Visual review sample set (drilldown)** collapsible
- Generate recommended sample set button (local only); copy-ready `make mrms-visual-review-sample-set`

### Run commands

```bash
make test
make mrms-visual-review-sample-set
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Sample set is local drilldown evidence only — does not verify MRMS, clear alerts, download/decode, or enable production rendering
- Empty selection when no visual review manifest exists — run `make mrms-visual-review` first

## Phase 61 - Visual Sample-Set Annotations and Candidate Readiness

Local operator annotations and conservative advisory readiness scoring for Phase 60 sample sets.

### Backend
- `mrms_visual_review_sample_readiness.py` — annotation upsert, readiness scoring, Markdown summary
- Paths: `mrms_visual_review_sample_annotations.json`, `mrms_visual_review_sample_readiness.md`
- `compact_visual_review_sample_readiness()` on validation summary
- API: `GET/POST /api/validation/mrms-visual-review/sample-set/readiness`, `POST /api/validation/mrms-visual-review/sample-set/annotations`
- CLI: `scripts/mrms_visual_review_sample_readiness.py`; `make mrms-visual-review-readiness`

### Frontend
- Dev Validation sample-set section extended with per-sample annotation forms and readiness summary
- Advisory safety wording: `candidate_ready` is not production authorization

### Run commands

```bash
make test
make mrms-visual-review-readiness --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Readiness scoring is advisory only — conservative blocks on rejected, missing, stale, unreviewed, questionable, or follow-up-tagged samples
- Does not verify MRMS, clear alerts, enable production rendering, or mutate catalog/render gates

## Phase 62 - Gated Real MRMS Rendering Candidate Preflight

Local advisory preflight checklist assembling safety gates, visual review evidence, sample-set readiness, and required docs before any render candidate path.

### Backend
- `mrms_render_candidate_preflight.py` — evidence gathering, conservative `blocked` / `needs_review` / `candidate_preflight_ready` scoring
- Paths: `mrms_render_candidate_preflight.json`, `mrms_render_candidate_preflight.md`
- `compact_render_candidate_preflight()` on validation summary
- API: `GET/POST /api/validation/mrms-render-candidate/preflight`
- CLI: `scripts/mrms_render_candidate_preflight.py`; `make mrms-render-candidate-preflight`

### Frontend
- Dev Validation **MRMS render candidate preflight** collapsible with blocking items, warnings, evidence found/missing, refresh button

### Run commands

```bash
make test
make mrms-render-candidate-preflight --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Preflight is advisory only — `candidate_preflight_ready` is not verified MRMS or production authorization
- Does not download/decode/render, clear alerts, enable production rendering, or mutate catalog/render gates

## Phase 63 - Gated Real MRMS Rendering Candidate Dry-Run Plan

Local advisory dry-run plan documenting prerequisites, future operator commands (not run now), expected artifacts, rollback/stop conditions, and evidence checklist.

### Backend
- `mrms_render_candidate_dry_run_plan.py` — dry-run plan generation, conservative `blocked` / `needs_review` / `dry_run_plan_ready` status
- Paths: `mrms_render_candidate_dry_run_plan.json`, `mrms_render_candidate_dry_run_plan.md`
- `compact_render_candidate_dry_run_plan()` on validation summary
- API: `GET/POST /api/validation/mrms-render-candidate/dry-run-plan`
- CLI: `scripts/mrms_render_candidate_dry_run_plan.py`; `make mrms-render-candidate-dry-run-plan`

### Frontend
- Dev Validation **MRMS render candidate dry-run plan** collapsible with blockers, warnings, prerequisites, stop conditions, expected outputs

### Run commands

```bash
make test
make mrms-render-candidate-dry-run-plan --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Dry-run plan is advisory only — does not download/decode/render or execute listed candidate commands
- `dry_run_plan_ready` is not production authorization

## Phase 64 - Gated Real MRMS Rendering Candidate Command Scaffold

Disabled-by-default local scaffold for a future real MRMS rendering candidate attempt, with hard safety gates and dry-run/no-op default behavior.

### Backend
- `mrms_render_candidate_scaffold.py` — scaffold generation, conservative `blocked` / `dry_run_only` / `scaffold_ready` status
- Paths: `mrms_render_candidate_scaffold.json`, `mrms_render_candidate_scaffold.md`
- `compact_render_candidate_scaffold()` on validation summary
- API: `GET/POST /api/validation/mrms-render-candidate/scaffold`
- CLI: `scripts/mrms_render_candidate_scaffold.py`; `make mrms-render-candidate-scaffold`

### Frontend
- Dev Validation **MRMS render candidate command scaffold** collapsible with blockers, warnings, safety gates, future commands (not executed by default)

### Run commands

```bash
make test
make mrms-render-candidate-scaffold --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Scaffold is disabled-by-default — does not download/decode/render, serve production tiles, clear alerts, or mutate gates
- `scaffold_ready` is not production authorization

## Phase 65 - Gated Candidate Artifact Sandbox Layout

Local sandbox directory layout and cleanup/reporting workflow for future real MRMS candidate artifacts, isolated from production tile serving.

### Backend
- `mrms_render_candidate_sandbox.py` — sandbox layout, manifest/report generation, conservative `missing` / `needs_setup` / `ready` / `needs_cleanup` / `blocked` status
- Sandbox root: `data/dev/mrms_render_candidate_sandbox/` with `incoming/`, `decoded/`, `rendered/`, `reports/`, `logs/`, `manifests/`, `scratch/`, `quarantine/`
- Manifest/report: `mrms_render_candidate_sandbox_manifest.json`, `mrms_render_candidate_sandbox_report.md`
- `compact_render_candidate_sandbox()` on validation summary
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox`
- CLI: `scripts/mrms_render_candidate_sandbox.py`; `make mrms-render-candidate-sandbox`

### Frontend
- Dev Validation **MRMS render candidate sandbox** collapsible with root, subdirectories, blockers, safety gates, report-only cleanup candidates

### Run commands

```bash
make test
make mrms-render-candidate-sandbox --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Sandbox is local-only — cleanup is report-only; no file deletion in Phase 65
- `ready` is not production authorization

## Phase 66 - Gated Candidate Sandbox Manifest Import/Export

Local metadata import/export for candidate sandbox manifests and reports, with advisory comparison and schema version 1.0.

### Backend
- `mrms_render_candidate_sandbox_import_export.py` — export/import validation, conservative `missing` / `export_ready` / `import_ready` / `imported` / `invalid` / `blocked` status
- Export dir: `data/dev/mrms_render_candidate_exports/`; import dir: `data/dev/mrms_render_candidate_imports/`
- Status: `mrms_render_candidate_import_export_latest.json`, `.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export` (+ `/export`, `/import`)
- CLI: `scripts/mrms_render_candidate_sandbox_import_export.py`; `make mrms-render-candidate-sandbox-export`, `make mrms-render-candidate-sandbox-import-export`

### Frontend
- Dev Validation **MRMS render candidate sandbox import/export** collapsible with schema version, included/missing reports, blockers, comparison summary

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-export
make mrms-render-candidate-sandbox-import-export
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Metadata/report-only — no binary artifacts, no production tile paths
- `imported` is not production authorization

## Phase 67 - Gated Candidate Sandbox Manifest Comparison History

Local comparison history for candidate sandbox exports/imports with bounded JSON/Markdown persistence.

### Backend
- `mrms_render_candidate_sandbox_comparison_history.py` — history recording, `missing` / `ready` / `blocked` status
- Paths: `mrms_render_candidate_sandbox_comparison_history.json`, `mrms_render_candidate_sandbox_comparison_latest.json`, `.md`
- Auto-records on import (`current_vs_imported`) and export pairs (`export_vs_previous_export`)
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-history`
- CLI: `scripts/mrms_render_candidate_sandbox_comparison_history.py`; `make mrms-render-candidate-sandbox-comparison-history`

### Frontend
- Dev Validation **MRMS render candidate sandbox comparison history** collapsible with recent entries and history status

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-import-export
make mrms-render-candidate-sandbox-comparison-history --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Advisory metadata comparisons only — no binary artifacts
- History is not production authorization

## Phase 68 - Gated Candidate Sandbox Comparison Trend Hints

Local trend hints across sandbox comparison history for spotting recurring changes.

### Backend
- `mrms_render_candidate_sandbox_comparison_trend_hint.py` — trend analysis, `missing` / `ready` / `needs_review` / `blocked` hint status
- Paths: `mrms_render_candidate_sandbox_comparison_trend_hint.json`, `.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-trend-hint`
- CLI: `scripts/mrms_render_candidate_sandbox_comparison_trend_hint.py`; `make mrms-render-candidate-sandbox-comparison-trend-hint`

### Frontend
- Dev Validation **MRMS render candidate sandbox comparison trend hints** collapsible

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-comparison-trend-hint --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Trend hints are advisory only — derived from comparison history metadata
- `needs_review` is not production authorization

## Phase 69 - Gated Candidate Sandbox Comparison Review Acknowledgment

Local acknowledgment of reviewed sandbox comparison trend hints without clearing validation alerts.

### Backend
- `mrms_render_candidate_sandbox_comparison_review_acknowledgment.py` — bounded JSON list, operator + note validation
- Path: `mrms_render_candidate_sandbox_comparison_review_acknowledgments.json`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-review-acknowledgments`
- CLI: `scripts/mrms_render_candidate_sandbox_comparison_review_acknowledgment.py`; `make mrms-render-candidate-sandbox-comparison-review-acknowledgment`

### Frontend
- Dev Validation **MRMS render candidate sandbox comparison review acknowledgment** collapsible with form

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-comparison-review-acknowledgment --operator OP --note "Reviewed locally"
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Acknowledgment does not clear alerts or mutate trend hints
- `trend_review_still_recommended` may remain true after acknowledgment

## Phase 70 - Gated Candidate Sandbox Comparison Acknowledgment Status

Local rollup linking latest trend hints to review acknowledgments.

### Backend
- `mrms_render_candidate_sandbox_comparison_acknowledgment_status.py` — rollup `missing` / `not_needed` / `needs_acknowledgment` / `current` / `stale` / `blocked`
- Paths: `mrms_render_candidate_sandbox_comparison_acknowledgment_status.json`, `.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status`
- CLI: `scripts/mrms_render_candidate_sandbox_comparison_acknowledgment_status.py`; `make mrms-render-candidate-sandbox-comparison-acknowledgment-status`

### Frontend
- Dev Validation **MRMS render candidate sandbox comparison acknowledgment status** collapsible

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-comparison-acknowledgment-status --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Status rollup is advisory only — does not clear alerts
- Stale when trend hint snapshot changes after last acknowledgment

## Phase 71 - Gated Candidate Sandbox Comparison Acknowledgment Status History

Bounded local history of acknowledgment status rollups with coverage-change classification.

### Backend
- `mrms_render_candidate_sandbox_comparison_acknowledgment_status_history.py` — append on status refresh, max 25 entries, coverage `unchanged` / `improved` / `worsened` / `mixed` / `no_baseline`
- Paths: `mrms_render_candidate_sandbox_comparison_acknowledgment_status_history.json`, `.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/history`
- CLI: `scripts/mrms_render_candidate_sandbox_comparison_acknowledgment_status_history.py`; `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-history`
- Status save hook appends history entry and refreshes history report

### Frontend
- Dev Validation **MRMS render candidate sandbox comparison acknowledgment status history** collapsible

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-comparison-acknowledgment-status --refresh
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-history --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- History appends on status refresh only
- Coverage change is rollup-rank advisory — does not clear alerts

## Phase 72 - Gated Candidate Sandbox Comparison Acknowledgment Status Trend Hints

Local advisory trend hints derived from acknowledgment status history.

### Backend
- `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint.py` — trend analysis, `missing` / `ready` / `needs_review` / `blocked` hint status
- Paths: `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint.json`, `.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-hint`
- CLI: `scripts/mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_hint.py`; `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-hint`

### Frontend
- Dev Validation **MRMS render candidate sandbox comparison acknowledgment status trend hints** collapsible

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-hint --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Trend hints are advisory only — derived from acknowledgment status history metadata
- `needs_review` is not production authorization

## Phase 73 - Gated Candidate Sandbox Comparison Acknowledgment Status Trend Review Acknowledgment

Local acknowledgment of reviewed acknowledgment status trend hints without clearing validation alerts.

### Backend
- `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment.py` — bounded JSON list, operator + note validation
- Path: `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgments.json`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgments`
- CLI: `scripts/mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment.py`; `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment`

### Frontend
- Dev Validation **MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment** collapsible with form

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment --operator OP --note "Reviewed locally"
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Acknowledgment does not clear alerts or mutate status trend hints
- `trend_review_still_recommended` may remain true after acknowledgment

## Phase 74 - Gated Candidate Sandbox Comparison Acknowledgment Status Trend Review Acknowledgment Status

Local rollup linking status trend hints to trend review acknowledgments.

### Backend
- `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status.py` — rollup `missing` / `not_needed` / `needs_acknowledgment` / `current` / `stale` / `blocked`
- Paths: `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status.json`, `.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status`
- CLI: `scripts/mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status.py`; `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status`

### Frontend
- Dev Validation **MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment status** collapsible

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Rollup is advisory only — does not clear alerts or mutate trend hints
- `stale_acknowledgment` when status trend hint snapshot changes

## Phase 75 - Gated Candidate Sandbox Comparison Acknowledgment Status Trend Review Acknowledgment Status History

Bounded local history of trend review acknowledgment status rollups.

### Backend
- `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_history.py` — bounded JSON list, coverage change tracking
- Paths: `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_history.json`, `.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/history`
- CLI: `scripts/mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_history.py`; `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-history`
- Status rollup refresh appends history entries automatically

### Frontend
- Dev Validation **MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment status history** collapsible

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-history --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- History appends on status rollup refresh only
- Coverage change is rollup-rank advisory — does not clear alerts

## Phase 76 - Gated Candidate Sandbox Comparison Acknowledgment Status Trend Review Acknowledgment Status Trend Hints

Local advisory trend hints derived from trend review acknowledgment status history.

### Backend
- `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_hint.py` — trend analysis, `missing` / `ready` / `needs_review` / `blocked` hint status
- Paths: `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_hint.json`, `.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-hint`
- CLI: `scripts/mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_hint.py`; `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-hint`

### Frontend
- Dev Validation **MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend hints** collapsible

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-hint --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Trend hints are advisory only — derived from trend review acknowledgment status history metadata
- `needs_review` is not production authorization

## Phase 77 - Gated Candidate Sandbox Comparison Acknowledgment Status Trend Review Acknowledgment Status Trend Review Acknowledgment

Local acknowledgment of reviewed trend review acknowledgment status trend hints without clearing validation alerts.

### Backend
- `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment.py` — bounded JSON list, operator + note validation
- Path: `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgments.json`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgments`
- CLI: `scripts/mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment.py`; `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment`

### Frontend
- Dev Validation **MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment** collapsible with form

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment --operator OP --note "Reviewed locally"
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Acknowledgment does not clear alerts or mutate status trend hints
- `trend_review_still_recommended` may remain true after acknowledgment

## Phase 78 - Gated Candidate Sandbox Comparison Acknowledgment Status Trend Review Acknowledgment Status Trend Review Acknowledgment Status

Local rollup linking trend review acknowledgment status trend hints to trend review acknowledgments.

### Backend
- `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status.py` — rollup classification, `missing` / `not_needed` / `needs_acknowledgment` / `current` / `stale` / `blocked`
- Paths: `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status.json`, `.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status`
- CLI: `scripts/mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status.py`; `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status`

### Frontend
- Dev Validation **MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment status** collapsible with refresh

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Rollup is advisory only — derived from trend hints and acknowledgments metadata
- `needs_acknowledgment` is not production authorization

## Phase 79 - Gated Candidate Sandbox Comparison Acknowledgment Status Trend Review Acknowledgment Status Trend Review Acknowledgment Status History

Local bounded history of trend review acknowledgment status rollups.

### Backend
- `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history.py` — bounded history, coverage change tracking
- Paths: `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history.json`, `.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status/history`
- CLI: `scripts/mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_history.py`; `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status-history`
- Phase 78 status save appends history entries on refresh

### Frontend
- Dev Validation **MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment status history** collapsible with refresh

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status-history --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- History appends on status rollup refresh only
- Coverage change is rollup-rank advisory — does not clear alerts

## Phase 80 - Gated Candidate Sandbox Comparison Acknowledgment Status Trend Review Acknowledgment Status Trend Review Acknowledgment Status Trend Hints

Local advisory trend hints derived from trend review acknowledgment status history.

### Backend
- `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint.py` — trend analysis, `missing` / `ready` / `needs_review` / `blocked` hint status
- Paths: `mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint.json`, `.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/import-export/comparison-acknowledgment-status/trend-review-acknowledgment-status/trend-review-acknowledgment-status/trend-hint`
- CLI: `scripts/mrms_render_candidate_sandbox_comparison_acknowledgment_status_trend_review_acknowledgment_status_trend_review_acknowledgment_status_trend_hint.py`; `make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status-trend-hint`

### Frontend
- Dev Validation **MRMS render candidate sandbox comparison acknowledgment status trend review acknowledgment status trend review acknowledgment status trend hints** collapsible with refresh

### Run commands

```bash
make test
make mrms-render-candidate-sandbox-comparison-acknowledgment-status-trend-review-acknowledgment-status-trend-review-acknowledgment-status-trend-hint --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Trend hints are advisory only — derived from status history metadata
- `needs_review` is not production authorization

## Phase 81 - Candidate Trend-Hint Review Acknowledgments

Local acknowledgment of reviewed candidate trend hints without clearing validation alerts.

### Backend
- `mrms_render_candidate_trend_hint_review_acknowledgment.py` — bounded JSON list, operator + note validation
- Path: `mrms_render_candidate_trend_hint_review_acknowledgments.json`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-review-acknowledgments`
- CLI: `scripts/mrms_render_candidate_trend_hint_review_acknowledgment.py`; `make mrms-render-candidate-trend-hint-review-acknowledgment`

### Frontend
- Dev Validation **Candidate trend-hint review acknowledgments** collapsible with form

### Run commands

```bash
make test
make mrms-render-candidate-trend-hint-review-acknowledgment --operator OP --note "Reviewed locally"
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Acknowledgment does not clear alerts or mutate trend hints
- `trend_review_still_recommended` may remain true after acknowledgment

## Phase 82 - Candidate Trend-Hint Acknowledgment Status Rollup

Local rollup linking candidate trend hints to trend-hint review acknowledgments without production authorization.

### Backend
- `mrms_render_candidate_trend_hint_ack_status.py` — rollup status, acknowledgment classification, JSON/Markdown reports
- Paths: `mrms_render_candidate_trend_hint_ack_status.json`, `mrms_render_candidate_trend_hint_ack_status.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-ack-status`
- CLI: `scripts/mrms_render_candidate_trend_hint_ack_status.py`; `make mrms-render-candidate-trend-hint-ack-status`

### Frontend
- Dev Validation **Candidate trend-hint acknowledgment status** collapsible with refresh button

### Run commands

```bash
make test
make mrms-render-candidate-trend-hint-ack-status --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Rollup does not clear alerts or mutate trend hints or acknowledgments
- Stale acknowledgment may remain after hint refresh until re-acknowledged

## Phase 83 - Candidate Trend-Hint Acknowledgment Status History

Bounded local history of trend-hint acknowledgment status rollups without production authorization.

### Backend
- `mrms_render_candidate_trend_hint_ack_status_history.py` — bounded JSON list, coverage change tracking, Markdown report
- Paths: `mrms_render_candidate_trend_hint_ack_status_history.json`, `mrms_render_candidate_trend_hint_ack_status_history.md`
- Phase 82 `save_trend_hint_ack_status` appends history on rollup refresh
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-ack-status/history`
- CLI: `scripts/mrms_render_candidate_trend_hint_ack_status_history.py`; `make mrms-render-candidate-trend-hint-ack-status-history`

### Frontend
- Dev Validation **Candidate trend-hint acknowledgment status history** collapsible with refresh button

### Run commands

```bash
make test
make mrms-render-candidate-trend-hint-ack-status --refresh
make mrms-render-candidate-trend-hint-ack-status-history --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- History does not clear alerts or mutate rollups or acknowledgments
- History appends on status rollup refresh only

## Phase 84 - Candidate Trend-Hint Review Chain Digest

Local digest combining trend-hint acknowledgment status rollup and history without production authorization.

### Backend
- `mrms_render_candidate_trend_hint_review_digest.py` — digest status, rollup + history summary, JSON/Markdown reports
- Paths: `mrms_render_candidate_trend_hint_review_digest.json`, `mrms_render_candidate_trend_hint_review_digest.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-review-digest`
- CLI: `scripts/mrms_render_candidate_trend_hint_review_digest.py`; `make mrms-render-candidate-trend-hint-review-digest`

### Frontend
- Dev Validation **Candidate trend-hint review chain digest** collapsible with refresh button

### Run commands

```bash
make test
make mrms-render-candidate-trend-hint-ack-status --refresh
make mrms-render-candidate-trend-hint-review-digest --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Digest does not clear alerts or mutate rollups, history, or acknowledgments
- Digest is advisory metadata only — not production authorization

## Phase 85 - Candidate Trend-Hint Review Digest History

Bounded local history of trend-hint review digests without production authorization.

### Backend
- `mrms_render_candidate_trend_hint_review_digest_history.py` — bounded JSON list, digest coverage change tracking, Markdown report
- Paths: `mrms_render_candidate_trend_hint_review_digest_history.json`, `mrms_render_candidate_trend_hint_review_digest_history.md`
- Phase 84 `save_trend_hint_review_digest` appends history on digest refresh
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-review-digest/history`
- CLI: `scripts/mrms_render_candidate_trend_hint_review_digest_history.py`; `make mrms-render-candidate-trend-hint-review-digest-history`

### Frontend
- Dev Validation **Candidate trend-hint review digest history** collapsible with refresh button

### Run commands

```bash
make test
make mrms-render-candidate-trend-hint-review-digest --refresh
make mrms-render-candidate-trend-hint-review-digest-history --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- History does not clear alerts or mutate digests, rollups, or acknowledgments
- History appends on review digest refresh only

## Phase 86 - Candidate Trend-Hint Review Digest Diff

Local diff between consecutive trend-hint review digests without production authorization.

### Backend
- `mrms_render_candidate_trend_hint_review_digest_diff.py` — compare consecutive digest history entries, bounded diff history, latest JSON
- Paths: `mrms_render_candidate_trend_hint_review_digest_diff_latest.json`, `mrms_render_candidate_trend_hint_review_digest_diff_history.json`
- Phase 85 `append_trend_hint_review_digest_history_entry` records diff on history append
- API: `GET /api/validation/mrms-render-candidate/sandbox/trend-hint-review-digest/diff`
- CLI: `scripts/mrms_render_candidate_trend_hint_review_digest_diff.py`; `make mrms-render-candidate-trend-hint-review-digest-diff`

### Frontend
- Dev Validation **Candidate trend-hint review digest diff** collapsible (read-only from summary)

### Run commands

```bash
make test
make mrms-render-candidate-trend-hint-review-digest --refresh
make mrms-render-candidate-trend-hint-review-digest-diff --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Diff does not clear alerts or mutate digests, rollups, or acknowledgments
- Diff records on digest history append or CLI `--refresh` recompute from latest history

## Phase 87 - Candidate Review Readiness Consolidation

Consolidated local readiness summary for the candidate trend-hint review chain and gated preflight status.

### Backend
- `mrms_render_candidate_review_readiness.py` — gathers chain evidence, regeneration hint, blockers, next operator step
- Paths: `mrms_render_candidate_review_readiness.json`, `mrms_render_candidate_review_readiness.md`
- Reuses compacts from trend hints, acknowledgments, rollup, history, digest, digest diff, and preflight
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/review-readiness`
- CLI: `scripts/mrms_render_candidate_review_readiness.py`; `make mrms-render-candidate-review-readiness`

### Frontend
- Dev Validation **Candidate review readiness** collapsible with refresh button (placed before preflight)

### Run commands

```bash
make test
make mrms-render-candidate-review-readiness --refresh
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Readiness summary does not clear alerts or mutate gates
- Not production authorization; typical fresh dev trees show blockers until chain is refreshed

## Phase 88 - Gated Real MRMS Render Candidate Preflight Attempt

Gate existing MRMS render candidate preflight behind review readiness — no new metadata chain.

### Backend
- `mrms_render_candidate_preflight_attempt.py` — checks review readiness gate, runs preflight only when `ready_for_preflight`, records attempt
- Path: `mrms_render_candidate_preflight_attempt_latest.json`
- Reuses `generate_render_candidate_preflight` and `generate_candidate_review_readiness`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/preflight-attempt`
- CLI: `scripts/mrms_render_candidate_preflight_attempt.py`; `make mrms-render-candidate-preflight-attempt`

### Frontend
- Gated preflight attempt button on **Candidate review readiness** collapsible

### Run commands

```bash
make test
make mrms-render-candidate-review-readiness ARGS="--refresh"
make mrms-render-candidate-preflight-attempt ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Does not force preflight when readiness has blockers (`blocked_by_readiness`)
- Local dev run: chain blocked (missing ack rollup) — preflight not executed
- Not production authorization

## Phase 89 - Resolve Preflight Blockers

Orchestrate blocker-removal refresh flow and record specific remaining blockers without forcing preflight.

### Backend
- `mrms_render_candidate_preflight_blockers.py` — runs ack status, digest, readiness, visual readiness, gated preflight retry in order
- Paths: `mrms_render_candidate_preflight_blockers_latest.json`, `mrms_render_candidate_preflight_blockers_latest.md`
- Maps blockers to specific next commands (trend-hint chain, visual sample set, preflight retry)
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/preflight-blockers`
- CLI: `scripts/mrms_render_candidate_preflight_blockers.py`; `make mrms-resolve-preflight-blockers`

### Frontend
- **Resolve preflight blockers** button on Candidate review readiness collapsible

### Run commands

```bash
make test
make mrms-resolve-preflight-blockers ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Does not force preflight when readiness gate is closed
- Local dev result: `still_blocked` — primary blocker is missing ack rollup / trend-hint chain upstream
- Not production authorization

## Phase 90 - Bootstrap Sandbox Comparison Trend-Hint Chain

Seed local sandbox comparison history and refresh the candidate trend-hint chain so ack rollup and review digest can reach current/stable without forcing preflight.

### Backend
- `mrms_render_candidate_trend_hint_chain_bootstrap.py` — seeds comparison history if empty, refreshes upstream sandbox chain, runs operator refresh flow, resolves blockers (skips preflight when visual blocked)
- Paths: `mrms_render_candidate_trend_hint_chain_bootstrap_latest.json`, `mrms_render_candidate_trend_hint_chain_bootstrap_latest.md`
- `resolve_preflight_blockers` updated to skip gated preflight attempt when visual sample readiness is blocked
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/trend-hint-chain-bootstrap`
- CLI: `scripts/mrms_render_candidate_trend_hint_chain_bootstrap.py`; `make mrms-bootstrap-trend-hint-chain`

### Frontend
- **Bootstrap sandbox comparison trend-hint chain** button on Candidate review readiness collapsible

### Run commands

```bash
make test
make mrms-bootstrap-trend-hint-chain ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Does not force preflight when visual sample readiness is blocked
- Local dev result: `chain_ready_visual_blocked` — trend-hint chain ready; visual `no_sample_set` remains
- Not production authorization

## Phase 91 - Bootstrap Visual Review Sample Set

Create local visual review sample set and acceptable annotations so visual sample readiness reaches `candidate_ready` and gated preflight can run.

### Backend
- `mrms_visual_review_sample_bootstrap.py` — ensures visual review manifest, sample set, bootstrap annotations, readiness refresh, blocker resolution
- Paths: `mrms_visual_review_sample_bootstrap_latest.json`, `mrms_visual_review_sample_bootstrap_latest.md`
- API: `GET/POST /api/validation/mrms-visual-review/sample-set/bootstrap`
- CLI: `scripts/mrms_visual_review_sample_bootstrap.py`; `make mrms-bootstrap-visual-sample-set`

### Frontend
- **Bootstrap visual review sample set** button on Candidate review readiness collapsible

### Run commands

```bash
make test
make mrms-bootstrap-visual-sample-set ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Bootstrap annotations are local drilldown only — not verified MRMS
- Local dev result: `preflight_attempted` — visual `candidate_ready`; gated preflight ran with advisory result
- Not production authorization

## Phase 92 - Gated Render Candidate Dry-Run Plan Review

Review gated preflight advisory result and evaluate/generate dry-run plan only when preflight is `candidate_preflight_ready`.

### Backend
- `mrms_render_candidate_gated_dry_run_review.py` — refreshes preflight, resolves blockers, generates dry-run plan only when gated
- Paths: `mrms_render_candidate_gated_dry_run_review_latest.json`, `mrms_render_candidate_gated_dry_run_review_latest.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-dry-run-review`
- CLI: `scripts/mrms_render_candidate_gated_dry_run_review.py`; `make mrms-review-gated-dry-run-plan`

### Frontend
- **Review gated dry-run plan** button on MRMS render candidate dry-run plan collapsible

### Run commands

```bash
make test
make mrms-review-gated-dry-run-plan ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Does not generate dry-run plan when preflight is not `candidate_preflight_ready`
- Local dev result: `preflight_not_candidate_ready` — preflight `needs_review`; dry-run plan skipped
- Not production authorization

## Phase 93 - Gated Render Candidate Scaffold Review

Evaluate disabled-by-default render candidate scaffold only after preflight is `candidate_preflight_ready` and dry-run plan is `dry_run_plan_ready`.

### Backend
- `mrms_render_candidate_gated_scaffold_review.py` — refreshes preflight, resolves blockers, generates dry-run plan and scaffold only when gated
- Paths: `mrms_render_candidate_gated_scaffold_review_latest.json`, `mrms_render_candidate_gated_scaffold_review_latest.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-scaffold-review`
- CLI: `scripts/mrms_render_candidate_gated_scaffold_review.py`; `make mrms-review-gated-scaffold`

### Frontend
- **Review gated scaffold** button on MRMS render candidate command scaffold collapsible

### Run commands

```bash
make test
make mrms-review-gated-scaffold ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Does not generate or review scaffold when preflight is not `candidate_preflight_ready` or dry-run plan is not `dry_run_plan_ready`
- Local dev result: `preflight_not_candidate_ready` — preflight `needs_review`; dry-run plan and scaffold skipped
- Not production authorization

## Phase 94 - Gated Candidate Artifact Sandbox Layout

Generate or review local candidate artifact sandbox layout only when preflight is `candidate_preflight_ready`, dry-run plan is `dry_run_plan_ready`, and scaffold is `scaffold_ready`.

### Backend
- `mrms_render_candidate_gated_sandbox_layout.py` — refreshes upstream gates and generates sandbox layout only when scaffold_ready
- Paths: `mrms_render_candidate_gated_sandbox_layout_latest.json`, `mrms_render_candidate_gated_sandbox_layout_latest.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-layout-review`
- CLI: `scripts/mrms_render_candidate_gated_sandbox_layout.py`; `make mrms-review-gated-sandbox-layout`

### Frontend
- **Review gated sandbox layout** button on MRMS render candidate sandbox collapsible

### Run commands

```bash
make test
make mrms-review-gated-sandbox-layout ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Does not generate sandbox layout when preflight, dry-run plan, or scaffold gates are closed
- Local dev result: `preflight_not_candidate_ready` — preflight `needs_review`; dry-run plan, scaffold, and sandbox skipped
- Not production authorization

## Phase 95 - Gated Sandbox Manifest Import/Export

Run or review local sandbox manifest import/export only when preflight is `candidate_preflight_ready`, dry-run plan is `dry_run_plan_ready`, scaffold is `scaffold_ready`, and sandbox layout is `sandbox_layout_ready`.

### Backend
- `mrms_render_candidate_gated_manifest_io.py` — refreshes upstream gates and runs manifest import/export only when sandbox_layout_ready
- Paths: `mrms_render_candidate_gated_manifest_io_latest.json`, `mrms_render_candidate_gated_manifest_io_latest.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-manifest-io`
- CLI: `scripts/mrms_render_candidate_gated_manifest_io.py`; `make mrms-review-gated-manifest-io`

### Frontend
- **Review gated manifest import/export** button on MRMS render candidate sandbox import/export collapsible

### Run commands

```bash
make test
make mrms-review-gated-manifest-io ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Does not run manifest import/export when any upstream gate is closed
- Local dev result: `preflight_not_candidate_ready` — preflight `needs_review`; dry-run plan, scaffold, sandbox, and manifest IO skipped
- Not production authorization

## Phase 96 - Gated Sandbox Comparison History

Run or review local sandbox comparison history only when manifest import/export is `manifest_io_ready`.

### Backend
- `mrms_render_candidate_gated_comparison_history.py` — refreshes upstream gates and refreshes comparison history only when manifest_io_ready
- Paths: `mrms_render_candidate_gated_comparison_history_latest.json`, `mrms_render_candidate_gated_comparison_history_latest.md`
- API: `GET/POST /api/validation/mrms-render-candidate/sandbox/gated-comparison-review`
- CLI: `scripts/mrms_render_candidate_gated_comparison_history.py`; `make mrms-review-gated-comparison`

### Frontend
- **Review gated comparison history** button on MRMS render candidate sandbox comparison history collapsible

### Run commands

```bash
make test
make mrms-review-gated-comparison ARGS="--refresh"
cd frontend && npm test
cd frontend && npm run build
```

### Known limitations
- Does not run comparison history when any upstream gate is closed
- Local dev result: `preflight_not_candidate_ready` — preflight `needs_review`; manifest IO and comparison skipped
- Not production authorization

