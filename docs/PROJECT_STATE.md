# Project State

Current phase: Phase 20 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **End-to-end validation orchestrator** (`make validate-real-mrms`) — experimental, not verified MRMS
- **Validation dashboard** — dev API + frontend panel (`GET /api/validation/summary`)
- **Benchmark reporting** (`make benchmark-real-mrms`) — per-stage timing + tile metrics
- **Default tile serving: placeholder** (`ENABLE_DECODED_TILES=false`, `ENABLE_PRODUCTION_RADAR_TILES=false`)
- SQLite render job queue + worker with configurable stale threshold (`STALE_RUNNING_JOB_SECONDS`, default 3600)
- Production tiles served only when flag + catalog gate + cached tile all true
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
# Default — placeholder tiles only
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false

# Stale running job recovery threshold (seconds, default 3600)
STALE_RUNNING_JOB_SECONDS=3600
```

## Validation dashboard (Phase 20)

```bash
make validate-real-mrms
make benchmark-real-mrms
make benchmark-real-mrms ARGS="--json-report --min-zoom 0 --max-zoom 1"

# Dev API (prototype)
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/latest
```

Reports persist under `data/dev/validation_latest.json` and `data/dev/benchmark_latest.json`.

## MRMS validation (Phase 19)

```bash
make validate-real-mrms ARGS="--json-report"
MRMS_SOURCE_MODE=real make validate-real-mrms ARGS="--real --run-worker"
```

## Render queue (Phase 17–18)

```bash
make enqueue-render-job
make render-worker-once
make render-queue-status
make render-status
```

## Local test

```bash
make test
make validate-real-mrms
make benchmark-real-mrms
make render-queue-status
cd frontend && npm run build
```

See `docs/GRIB2_DECODE.md` for decode/warping/worker/validation/benchmark notes.

## Demo plans

| Plan | History window (demo) |
|------|------------------------|
| free | Latest frame only |
| basic | 7 days from catalog latest |
| pro | 90 days from catalog latest (default) |
| business | Unrestricted |

Reference timestamp for limits: latest frame in catalog, not wall-clock now.
