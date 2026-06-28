# GRIB2 Decode Evaluation

Phase 11 evaluation notes for MRMS GRIB2.gz processing. **Not production rendering.**

## Intended future pipeline

```
MRMS GRIB2.gz (raw, immutable)
        ↓ decompress / stage
Decoded raster (float/int grid, native MRMS projection)
        ↓ normalize / QC
Normalized reflectivity values (dBZ or vendor units → standard dBZ)
        ↓ color table / legend
Styled raster (RGBA or indexed palette)
        ↓ COG or tile-ready raster
Cloud Optimized GeoTIFF and/or internal tile cache
        ↓ tile endpoint
GET /tiles/{layer}/{timestamp}/{z}/{x}/{y}.png  (real radar, not placeholder)
        ↓ PWA map
MapLibre raster overlay + playback
```

Current state (Phases 1–12):
- Discovery, download, and placeholder processing are implemented.
- Real `.grib2.gz` files get `placeholder_for_real_raw` preview tiles only.
- `make inspect-grib2` reports metadata when decoders are available.
- `make decode-grib2` writes prototype normalized raster artifacts under `data/staging/grib2_decode/` when optional decoders exist.
- **`/tiles` still serves placeholders** — decode output is not wired to the map.

## Decoder options and tradeoffs

| Backend | Pros | Cons | Phase 11 status |
|---------|------|------|-----------------|
| **wgrib2 (CLI)** | Widely used for GRIB2 inventory; no Python geospatial stack required; good for metadata spike | Subprocess overhead; not ideal for raster tile generation; must be installed separately | **Used when available** for `-s` inventory |
| **GDAL + rasterio** | Strong raster I/O; COG output; reprojection; tile warping | Heavy native dependencies; larger deploy image; install complexity | Detected only — not required |
| **pygrib** | Direct GRIB2 message access in Python | Can be difficult to build/install; less common in cloud images | Detected only — future path |
| **cfgrib + xarray** | Ergonomic for NetCDF-like GRIB access | Depends on ecCodes; memory use for large grids | Detected only — future path |

### Recommendation (for Phase 12+)

1. **Metadata spike:** wgrib2 CLI (already wired in `grib2_inspector.py`).
2. **Production decode prototype:** rasterio/GDAL reading decoded grid → normalized numpy array → PNG/COG tile pyramid.
3. **Keep stub path:** demo/collector/MRMS stub files remain on placeholder tiles for offline dev.

## Prototype decode CLI (Phase 12)

```bash
# Latest real MRMS file (friendly when none/decoders missing)
make decode-grib2

# Explicit file
PYTHONPATH=. python scripts/decode_grib2.py --file data/raw/mrms/reflectivity/example.grib2.gz
```

### Optional decoder install (not part of `make setup`)

**Preferred:** rasterio + GDAL (system package or wheels)

```bash
# Example only — install method varies by platform
pip install rasterio numpy
```

**Lightweight fallback:** wgrib2 CLI (binary grid export)

```bash
# macOS example
brew install wgrib2
```

When no decoder is installed, `make decode-grib2` exits 0 with a friendly message.

### Prototype output

For each input file, output goes to a deterministic folder:

```
data/staging/grib2_decode/{token}/
  decode_manifest.json   # prototype metadata (production_rendering: false)
  normalized.tif         # rasterio path (optional)
  normalized.raw         # wgrib2 bin path (float32 0..1 normalized)
```

The manifest explicitly states that catalog `processed_status` and `/tiles` were not changed.

### Before production rendering (future phase)

1. Decode grid → consistent CRS/bounds aligned with map layer metadata
2. Build tile pyramid or COG cache under `data/tiles/`
3. Add feature flag or processed status such as `real_raster_processed`
4. Update `/tiles` to serve real imagery only when explicitly enabled
5. Keep stub/demo paths on placeholder tiles for offline dev

The manifest explicitly states that catalog `processed_status` and default `/tiles` behavior were not changed.

## Tile cache prototype (Phase 13)

Feature flag: `ENABLE_DECODED_TILES=false` (default).

When enabled and Phase 12 artifacts exist for a catalog frame:
- `/tiles` may return `decoded-prototype` PNG tiles (simple grid sampling)
- Pre-build cache: `make build-tile-cache` → `data/tiles/decoded_prototype/`
- Headers: `X-RadarArchive-Tile: decoded-prototype`, `X-RadarArchive-Production-Rendering: false`

When disabled or artifacts missing: placeholder tiles (unchanged Phase 4–12 behavior).

## Geo metadata + production gate (Phase 14)

Each successful Phase 12 decode writes `geo_metadata.json` alongside `decode_manifest.json`:

```json
{
  "product_name": "MRMS_ReflectivityAtLowestAltitude",
  "valid_timestamp": null,
  "source_crs": null,
  "output_crs": "EPSG:3857",
  "bounds": [-125.0, 24.0, -66.0, 50.0],
  "grid_width": 3500,
  "grid_height": 7000,
  "geo_accurate": false,
  "production_rendering": false,
  "notes": ["Prototype geo metadata — not geo-verified."]
}
```

Optional rasterio may enrich CRS/bounds when installed (not required for tests or `make setup`).

Catalog render fields (`render_status`, `render_mode`, `production_rendering`, paths) track placeholder vs decoded vs production states. **Real MRMS rows are not auto-marked `production_rendered`** unless `make build-production-tiles -- --mark-catalog` is used explicitly (fixture/test).

Production tile serving requires:
- `ENABLE_PRODUCTION_RADAR_TILES=true`
- Catalog `production_rendering=true` and `render_status=production_rendered`
- Cached tile at `data/tiles/production/{layer}/{timestamp}/{z}/{x}/{y}.png`

## Production warping prototype (Phase 15)

`make build-production-tiles` reads decode artifacts with valid `geo_metadata.json` and warps normalized `.raw` grids to EPSG:3857 XYZ tiles using stdlib math (no GDAL/rasterio).

Supported in prototype:
- `output_crs`: EPSG:3857
- `source_crs`: EPSG:4326 or missing (bounds treated as WGS84)
- `bounds`: [west, south, east, north] for geographic→grid mapping
- Bilinear sampling from small test fixtures

Not supported yet:
- Native projected source grids (e.g. EPSG:5070) without reprojection library
- Full multi-zoom CONUS pyramids
- Verified geo-accurate MRMS output

Output cache: `data/tiles/production/{layer}/{timestamp}/{z}/{x}/{y}.png`

Serving tile mode: `production-prototype` (not verified real radar).

Build CLI (Phase 16):

```bash
make build-production-tiles
PYTHONPATH=. python scripts/build_production_tiles.py --min-zoom 0 --max-zoom 2
PYTHONPATH=. python scripts/build_production_tiles.py --dry-run --json-report
PYTHONPATH=. python scripts/build_production_tiles.py --force
```

Benchmark JSON includes: `frames_considered`, `tiles_written`, `tiles_planned`, `elapsed_seconds`, `output_bytes`, `errors`, `prototype`, `verified_mrms`.

Report: `make render-status` (optional `--sync` to update catalog from artifacts).

## Render queue + worker (Phase 17–18)

SQLite-backed job queue for production tile builds (local dev — no Redis/Celery).

```bash
make enqueue-render-job
make enqueue-render-job ARGS="--min-zoom 0 --max-zoom 2"
make render-worker-once
make render-worker-once ARGS="--json-report"
make render-worker ARGS="--max-jobs 5 --sleep 0.5"
make render-queue-status
make render-status
```

Or via API:

```bash
curl -X POST http://127.0.0.1:8000/api/render/jobs \
  -H 'Content-Type: application/json' \
  -d '{"min_zoom":0,"max_zoom":2,"max_attempts":3}'
curl "http://127.0.0.1:8000/api/render/jobs?status=queued"
curl http://127.0.0.1:8000/api/render/jobs/summary
curl -X POST http://127.0.0.1:8000/api/render/jobs/1/retry
curl -X POST http://127.0.0.1:8000/api/render/jobs/1/cancel
```

Worker calls Phase 16 `build_production_tiles` with idempotent skip/force behavior. Jobs track `progress_current`, `tiles_written`, `output_bytes`, `error_message`, and retry fields (`attempt_count`, `max_attempts`, `next_retry_at`).

Failed jobs re-queue automatically when attempts remain (1s delay). Explicit retry via API for terminal failed jobs with attempts left. No delete endpoints.

Continuous worker: `make render-worker` loops until `--max-jobs` reached (default 100), sleeping when queue empty. Ctrl+C exits cleanly (Phase 19).

Stale job recovery: jobs stuck in `running` >1h are re-queued or failed per `max_attempts`.

`--mark-catalog` on enqueue shows a clear warning — prototype only, not verified MRMS.

## MRMS validation (Phase 19)

Experimental end-to-end validation (not verified production radar):

```bash
make validate-real-mrms
make validate-real-mrms ARGS="--json-report"
MRMS_SOURCE_MODE=real make validate-real-mrms ARGS="--real --run-worker"
```

Stub mode (default) is safe offline — explains that inspect/decode need a real `.grib2.gz`.
Real mode requires network for NOAA AWS download; output remains prototype (`verified_mrms: false`).

Service: `backend/app/services/mrms_validation.py`

## Benchmark (Phase 20)

Per-stage timing benchmark for one frame (not verified production radar):

```bash
make benchmark-real-mrms
make benchmark-real-mrms ARGS="--json-report --min-zoom 0 --max-zoom 1"
MRMS_SOURCE_MODE=real make benchmark-real-mrms ARGS="--real"
```

Report: `stage_timings`, `tile_build_elapsed_seconds`, `tiles_planned`/`tiles_written`/`tiles_skipped`, `output_bytes`, `decoder_used`, `verified_mrms: false`.

Persisted to `data/dev/benchmark_latest.json`. Dev API: `GET /api/validation/summary`.

## Inspection CLI

```bash
# Latest real downloaded MRMS file from catalog (safe when none exist)
make inspect-grib2

# Explicit file
PYTHONPATH=. python scripts/inspect_grib2.py --file data/raw/mrms/reflectivity/example.grib2.gz

# Fetch a real file first (network required)
MRMS_SOURCE_MODE=real make download-mrms -- --register-discovered --limit 1
make inspect-grib2
```

When no real file exists, the script prints a hint and exits 0.

When no decoder is installed, the script still reports gzip size and GRIB magic checks.

## Module layout

- `backend/app/services/grib2_inspector.py` — dependency detection, staging, wgrib2 spike
- `backend/app/services/grib2_inspect_catalog.py` — find latest real MRMS candidates
- `backend/app/services/grib2_decoder.py` — prototype raster decode (optional deps)
- `scripts/inspect_grib2.py` — inspection CLI
- `scripts/decode_grib2.py` — decode prototype CLI
- `backend/app/services/render_metadata.py` — geo metadata structures
- `backend/app/services/render_status.py` — render status report/sync
- `backend/app/services/tile_pyramid.py` — geo warping math (Phase 15)
- `backend/app/services/production_tile_builder.py` — production tile builder
- `scripts/build_production_tiles.py` — production tile CLI
- `backend/app/services/render_queue.py` — render job queue
- `backend/app/workers/render_worker.py` — local worker
- `scripts/enqueue_render_job.py`, `scripts/run_render_worker.py`, `scripts/render_queue_status.py`
- `scripts/validate_real_mrms.py` — MRMS validation orchestrator (Phase 19)
- `scripts/benchmark_real_mrms.py` — MRMS benchmark timing (Phase 20)

## Non-goals (Phases 11–12)

- Replace placeholder map tiles with real radar
- Add hard dependencies on GDAL/rasterio/wgrib2 to `make setup`
- Change processor statuses or `/tiles` behavior
