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

## Batch validation (Phase 21)

Multi-frame validation with safe defaults (count 3, max 10):

```bash
make validate-real-mrms-batch
make validate-real-mrms-batch ARGS="--count 5 --json-report"
make validate-real-mrms ARGS="--count 3"
MRMS_SOURCE_MODE=real make validate-real-mrms-batch ARGS="--real --count 3"
make catalog-status
```

Batch report includes per-frame summaries, aggregate tile metrics, `elapsed_seconds`, `verified_mrms: false`.

History: last 10 runs in `data/dev/validation_history.json`. API: `GET /api/validation/history`.

## Queue benchmark (Phase 22)

Multi-zoom tile builds through the render queue (default count 3, max 10; default zoom 0–1):

```bash
make benchmark-render-queue
make benchmark-render-queue ARGS="--count 3 --min-zoom 0 --max-zoom 1 --json-report"
make benchmark-render-queue ARGS="--dry-run"
```

Report includes per-job summaries (`job_id`, `status`, `tiles_written`/`tiles_skipped`, `output_bytes`, `elapsed_seconds`) and aggregate job/tile totals. `verified_mrms: false`.

Persisted to `data/dev/queue_benchmark_latest.json` with bounded history (last 10). Dev API: `GET /api/validation/benchmarks`, `GET /api/validation/summary` (`queue_benchmark`).

Limitations:
- Does not discover/download MRMS by default; uses local catalog frames
- Run `make validate-real-mrms-batch` first for decode artifacts when benchmarking tile output
- Higher zoom/count increases tile volume; caps apply

## Scheduled validation (Phase 23)

Cron-friendly local wrapper (default count 3, zoom 0–1; stub/offline by default):

```bash
make scheduled-validation
make scheduled-validation ARGS="--json-report"
make scheduled-validation ARGS="--real --count 3 --min-zoom 0 --max-zoom 1"
```

Runs: catalog status → batch validation → queue benchmark → render queue status → validation summary.

Persisted to `data/dev/scheduled_validation_latest.json`. API: `GET /api/validation/scheduled`, summary `scheduled_validation`.

Sample cron (not installed automatically):

```cron
0 */6 * * * cd /path/to/radararchive && make scheduled-validation >> data/dev/scheduled_validation.log 2>&1
```

Per-frame tile metrics in batch/queue reports: `decode_status`, `tiles_planned`/`tiles_written`/`tiles_skipped`, `render_job_id`, `elapsed_seconds`. `verified_mrms: false`.

## Failure logging + operator runbook (Phase 24)

Failure log: `data/dev/validation_failures.jsonl` (append-only, max 100 entries).

```bash
make validation-failures
make validation-failures ARGS="--json"
make real-mrms-smoke-test
```

Scheduled steps include `started_at`, `finished_at`, `status` (`succeeded`, `failed`, `warning`, `skipped`).

Operator runbook: [RUNBOOK_REAL_MRMS_VALIDATION.md](RUNBOOK_REAL_MRMS_VALIDATION.md)

Common interpretations:
- **warning** in stub mode: expected (no real GRIB2 decode)
- **failed** queue step: check `make validation-failures` and render queue status
- **zero tiles**: missing decode artifacts or production flag off — not necessarily a pipeline crash

## Verification criteria (Phase 25 — documentation only)

Decoded output and prototype tiles do **not** constitute verified MRMS. Before `verified_mrms` could ever become true, all criteria in [VERIFIED_MRMS_CRITERIA.md](VERIFIED_MRMS_CRITERIA.md) must pass with operator review.

Current project status: criteria **not met**. Decode artifacts alone are insufficient proof.

Local alert marker (`make validation-alerts`) summarizes validation health from failure log + scheduled runs — still prototype diagnostics only.

## Proof report automation (Phase 26)

```bash
make mrms-proof-report
make mrms-proof-report ARGS="--json-report"
make mrms-proof-report ARGS="--real --count 3"
```

Report: `data/dev/mrms_proof_latest.json` — per-criterion statuses, per-frame checksum/geo/tile evidence.

Interpretation:
- `insufficient_evidence` / `failed` in stub mode is **expected** — not verified MRMS
- `ready_for_operator_review` means automated checks passed enough for human review — still `verified_mrms: false`
- Visual sanity and operator review criteria remain manual (see [MRMS_OPERATOR_SIGNOFF_TEMPLATE.md](MRMS_OPERATOR_SIGNOFF_TEMPLATE.md))
- Proof regression compares consecutive proof runs — first run is `inconclusive`

## Proof regression (Phase 27)

When a new proof report is worse than the previous snapshot, `make mrms-proof-regression` records findings and validation alerts may show `proof_regression`.

Sign-off via `make mrms-signoff` or dev-only `POST /api/validation/signoffs` is local audit only — `verified_mrms` stays false. Sign-off does not clear proof regression until evidence improves.

## Proof review history (Phase 28)

`make mrms-proof-history` lists bounded proof/regression/sign-off records for operator drill-down. Dev panel **Show proof review** includes history lists and a dev sign-off form.

## Proof bundle export (Phase 30)

`make mrms-proof-bundle` writes `data/dev/proof_bundles/mrms_proof_bundle_{timestamp}/` plus a ZIP. Includes proof/regression/sign-off/alert JSON, catalog/queue snapshots, runbook markdown copies, and `manifest.json` with `verified_mrms: false`. Bundles are supporting evidence only — not verified MRMS certification.

`make mrms-proof-bundle-diff` compares latest vs baseline bundle evidence (`unchanged`, `improved`, `worsened`, `mixed`, `no_baseline`). `make mrms-operator-handoff` generates a local Markdown checklist — review only, not verification.

`make scheduled-proof-bundle` runs scheduled validation with proof bundle export and diff; alerts may flag worsened/mixed diff for operator attention.

`make scheduled-proof-bundle-handoff` adds `--handoff` to auto-regenerate the operator handoff checklist when diff is worsened/mixed. Validation summary exposes `operator_guidance` runbook references when `decoder_unavailable` or other causes need attention — review aids only, not verification.

`make proof-bundle-diff-alert-history` prints the bounded diff alert timeline recorded on each diff evaluation — local evidence monitoring only; does not verify MRMS.

`make proof-bundle-diff-alert-trend` summarizes recent diff alert history into worsening/improving/mixed/stable trend with attention streaks. `make proof-bundle-diff-acknowledge` records a local operator note that does **not** clear alerts.

`make proof-bundle-diff-escalation` combines trend, history, and acknowledgment into escalation levels (`none`/`watch`/`attention`/`urgent`) with runbook section hints. Escalation is local guidance only — it does not verify MRMS output or clear alerts.

`make proof-bundle-diff-escalation-history` prints bounded escalation snapshots. `make scheduled-proof-bundle-notify` runs scheduled proof bundle with optional local stdout urgent notice when escalation is urgent — no external notifications.

`make proof-bundle-diff-escalation-metrics` prints rollup counts and streaks. `make proof-bundle-diff-escalation-digest` exports a local Markdown digest for operator review — not a notification system.

`make scheduled-proof-bundle-digest` runs proof → bundle → diff → handoff → escalation digest in one local sequence and refreshes the operator review checklist with escalation metrics, acknowledgment status, and explicit checklist items. This is local/dev operator tooling only — it does not verify MRMS or enable production rendering.

`make proof-bundle-diff-escalation-digest-history` shows bounded digest export history. `make proof-bundle-diff-escalation-digest-diff` compares consecutive digest exports and surfaces regeneration hints — local review only, not a notification system.

`make mrms-review-session` records a local MRMS proof review session linking escalation, digest, handoff, diff, and bundle evidence. `make mrms-review-sessions` lists bounded session history. `make mrms-review-session-compare` compares the latest session against the previous one. `make mrms-review-session-export` writes a local Markdown export with comparison, guidance, and digest hints. `make mrms-review-session-export-diff` compares consecutive exports; `make mrms-review-session-export-diff-history` lists bounded diff history. `make mrms-review-session-export-diff-trend` summarizes export diff trends (improving/worsening/mixed/stable). Optional `--export-after-create` on `make mrms-review-session` exports Markdown immediately after session create (session kept if export fails). `make scheduled-proof-bundle-review-export` runs proof → bundle → diff → handoff → digest → review export in one local sequence (skips export safely when no review session exists). Review sessions, comparison, export, export diff, auto-export, and scheduled export do not verify MRMS or enable production rendering.

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
- `scripts/batch_validate_mrms.py` — batch validation (Phase 21)
- `scripts/catalog_status.py` — catalog status CLI (Phase 21)
- `scripts/benchmark_render_queue.py` — queue benchmark CLI (Phase 22)
- `scripts/run_scheduled_validation.py` — scheduled validation CLI (Phase 23)

## Non-goals (Phases 11–12)

- Replace placeholder map tiles with real radar
- Add hard dependencies on GDAL/rasterio/wgrib2 to `make setup`
- Change processor statuses or `/tiles` behavior
