# Project State

Current phase: Phase 19 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **End-to-end validation orchestrator** (`make validate-real-mrms`) — experimental, not verified MRMS
- **Default tile serving: placeholder** (`ENABLE_DECODED_TILES=false`, `ENABLE_PRODUCTION_RADAR_TILES=false`)
- Production warping prototype with multi-zoom build (Phase 16)
- **SQLite render job queue** + one-shot and continuous local worker with retry policy (Phase 17–18)
- Stale `running` job recovery + worker signal handling (Phase 19)
- Queue observability: summary API, `make render-queue-status`, integrated into `make render-status`
- Production tiles served only when flag + catalog gate + cached tile all true
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
# Default — placeholder tiles only
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
```

## MRMS validation (Phase 19)

```bash
# Safe stub/offline default (no network required)
make validate-real-mrms
make validate-real-mrms ARGS="--json-report"

# Real NOAA AWS mode (network required; still prototype output)
MRMS_SOURCE_MODE=real make validate-real-mrms ARGS="--real"
make validate-real-mrms ARGS="--real --run-worker"
```

## Render queue (Phase 17–18)

```bash
# Enqueue a job
make enqueue-render-job
make enqueue-render-job ARGS="--min-zoom 0 --max-zoom 2"

# Process one queued job
make render-worker-once
make render-worker-once ARGS="--json-report"

# Continuous worker (default max 100 jobs, 1s sleep when empty; Ctrl+C to stop)
make render-worker
make render-worker ARGS="--max-jobs 5 --sleep 0.5 --verbose"

# Queue summary
make render-queue-status
make render-queue-status ARGS="--json-report"

# Full render status (includes queue summary)
make render-status
```

## Local test

```bash
make test
make validate-real-mrms
make render-worker-once
cd frontend && npm run build
```

## Pipeline

```bash
make validate-real-mrms ARGS="--run-worker"
# Or step by step:
make decode-grib2
make enqueue-render-job ARGS="--min-zoom 0 --max-zoom 2"
make render-worker-once
ENABLE_PRODUCTION_RADAR_TILES=true make backend
```

See `docs/GRIB2_DECODE.md` for decode/warping/worker/validation notes.

## Demo plans

| Plan | History window (demo) |
|------|------------------------|
| free | Latest frame only |
| basic | 7 days from catalog latest |
| pro | 90 days from catalog latest (default) |
| business | Unrestricted |

Reference timestamp for limits: latest frame in catalog, not wall-clock now.
