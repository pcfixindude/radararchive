# Next Steps

## Phase 19 - Real MRMS Validation + Worker Hardening

Goal: Validate one real MRMS frame end-to-end through the queue and harden local worker operations without cloud deployment.

Suggested work:
1. Run decode + enqueue + worker on one real downloaded MRMS frame; document results honestly (prototype, not verified production)
2. Worker daemon ergonomics: signal handling, structured logging, optional `--once` default safety docs
3. Dev dashboard polish: job detail view, filter by status in UI (optional)
4. Stale `running` job recovery (crash detection) if needed
5. Benchmark multi-zoom builds through queue with timing reports
6. Keep placeholder default for offline dev

Do not start yet:
- Stripe billing integration
- Real auth / user accounts
- HRRR / WPC / native Android
- Redis/Celery unless optional and clearly not required
- Mandatory GDAL/rasterio/wgrib2

## Phase 18 verification commands

```bash
make test
make enqueue-render-job
make render-queue-status
make render-worker-once
make render-worker ARGS="--max-jobs 1 --sleep 0.1"
make render-status
cd frontend && npm run build
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
