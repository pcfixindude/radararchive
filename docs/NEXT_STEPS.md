# Next Steps

## Phase 20 - Validation Dashboard + Real Frame Benchmark

Goal: Surface validation results in dev UI and benchmark one real frame through multi-zoom queue builds without claiming verified production output.

Suggested work:
1. Optional dev validation status panel (last report summary from API or static hint)
2. Multi-zoom validation run through queue with timing JSON report
3. Document honest real-MRMS validation results when decoder + network available
4. Configurable stale-job threshold via env/CLI
5. Worker PID file or process supervisor notes for long-running local dev
6. Keep placeholder default for offline dev

Do not start yet:
- Stripe billing integration
- Real auth / user accounts
- HRRR / WPC / native Android
- Redis/Celery unless optional and clearly not required
- Mandatory GDAL/rasterio/wgrib2

## Phase 19 verification commands

```bash
make test
make validate-real-mrms
make validate-real-mrms ARGS="--json-report"
make render-worker-once
cd frontend && npm run build
```

Full experimental pipeline (real mode, network required):

```bash
MRMS_SOURCE_MODE=real make validate-real-mrms ARGS="--real --run-worker --json-report"
```

Render queue workflow:

```bash
make decode-grib2
make enqueue-render-job ARGS="--min-zoom 0 --max-zoom 2"
make render-worker-once
curl http://127.0.0.1:8000/api/render/jobs/summary
```

Production serving (unchanged gates):

```bash
ENABLE_PRODUCTION_RADAR_TILES=true make backend
# Still requires catalog gate + cached tiles
```

Placeholder default (unchanged):

```bash
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
```
