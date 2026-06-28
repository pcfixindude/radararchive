# Project State

Current phase: Phase 23 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Batch validation** (`make validate-real-mrms-batch`, default 3 frames, max 10)
- **Queue benchmark** (`make benchmark-render-queue`, default 3 jobs, zoom 0–1)
- **Scheduled validation** (`make scheduled-validation`, cron-friendly wrapper)
- **Catalog status** (`make catalog-status`, `GET /api/catalog/status`)
- Validation dashboard + bounded histories (last 10) + per-frame tile metrics
- **Default tile serving: placeholder** (`ENABLE_DECODED_TILES=false`, `ENABLE_PRODUCTION_RADAR_TILES=false`)
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Scheduled validation (Phase 23)

```bash
make scheduled-validation
make scheduled-validation ARGS="--json-report"
make scheduled-validation ARGS="--real --count 3 --min-zoom 0 --max-zoom 1"
```

Sample cron (not installed automatically):

```cron
0 */6 * * * cd /path/to/radararchive && make scheduled-validation >> data/dev/scheduled_validation.log 2>&1
```

## Queue benchmark (Phase 22)

```bash
make benchmark-render-queue
make benchmark-render-queue ARGS="--dry-run --json-report"
```

## Batch validation (Phase 21)

```bash
make validate-real-mrms-batch
make catalog-status
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/scheduled
curl http://127.0.0.1:8000/api/validation/latest
curl http://127.0.0.1:8000/api/catalog/status
```

## Local test

```bash
make test
make scheduled-validation
make benchmark-render-queue
cd frontend && npm run build
```
