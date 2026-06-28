# Next Steps

## Phase 18 - Render Job Observability + Continuous Worker

Goal: Add a long-running local worker loop, job retry policy, and richer dev observability without cloud deployment.

Suggested work:
1. `make render-worker` loop (poll queue, sleep between jobs)
2. Job retry for transient failures (max attempts)
3. Dev dashboard or expanded API filters (status, layer)
4. Wire render job status into `make render-status` report
5. Validate one real MRMS frame end-to-end through queue
6. Keep placeholder default for offline dev

Do not start yet:
- Stripe billing integration
- Real auth / user accounts
- HRRR / WPC / native Android
- Redis/Celery unless optional and clearly not required

## Phase 17 verification commands

```bash
make test
make enqueue-render-job
make enqueue-render-job ARGS="--min-zoom 0 --max-zoom 2"
make render-worker-once
make build-production-tiles ARGS="--dry-run --json-report"
cd frontend && npm run build
```

Render queue workflow:

```bash
make decode-grib2
make enqueue-render-job ARGS="--min-zoom 0 --max-zoom 2"
make render-worker-once
curl http://127.0.0.1:8000/api/render/jobs
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
