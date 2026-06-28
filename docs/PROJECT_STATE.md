# Project State

Current phase: Phase 22 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Batch validation** (`make validate-real-mrms-batch`, default 3 frames, max 10)
- **Queue benchmark** (`make benchmark-render-queue`, default 3 jobs, zoom 0–1)
- **Catalog status** (`make catalog-status`, `GET /api/catalog/status`)
- Validation dashboard + bounded history (last 10 reports) + queue benchmark history
- **Default tile serving: placeholder** (`ENABLE_DECODED_TILES=false`, `ENABLE_PRODUCTION_RADAR_TILES=false`)
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
STALE_RUNNING_JOB_SECONDS=3600
```

## Queue benchmark (Phase 22)

```bash
make benchmark-render-queue
make benchmark-render-queue ARGS="--count 3 --min-zoom 0 --max-zoom 1 --json-report"
make benchmark-render-queue ARGS="--dry-run"
```

## Batch validation (Phase 21)

```bash
make validate-real-mrms-batch
make validate-real-mrms-batch ARGS="--count 5 --json-report"
make validate-real-mrms ARGS="--count 3"
MRMS_SOURCE_MODE=real make validate-real-mrms-batch ARGS="--real --count 3"
make catalog-status
```

## Dev API

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/history
curl http://127.0.0.1:8000/api/validation/benchmarks
curl http://127.0.0.1:8000/api/catalog/status
```

## Local test

```bash
make test
make benchmark-render-queue
make validate-real-mrms-batch
make catalog-status
cd frontend && npm run build
```
