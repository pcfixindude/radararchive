# Project State

Current phase: Phase 17 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Default tile serving: placeholder** (`ENABLE_DECODED_TILES=false`, `ENABLE_PRODUCTION_RADAR_TILES=false`)
- Production warping prototype with multi-zoom build (Phase 16)
- **SQLite render job queue** + local worker (Phase 17)
- Production tiles served only when flag + catalog gate + cached tile all true
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
# Default — placeholder tiles only
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false
```

## Render queue (Phase 17)

```bash
# Enqueue a job
make enqueue-render-job
make enqueue-render-job ARGS="--min-zoom 0 --max-zoom 2"

# Process one queued job
make render-worker-once
make render-worker-once ARGS="--json-report"

# Or via API (dev)
curl -X POST http://127.0.0.1:8000/api/render/jobs -H 'Content-Type: application/json' -d '{"min_zoom":0,"max_zoom":0}'
curl http://127.0.0.1:8000/api/render/jobs
```

## Local test

```bash
make test
make enqueue-render-job
make render-worker-once
cd frontend && npm run build
```

## Pipeline

```bash
make decode-grib2
make enqueue-render-job ARGS="--min-zoom 0 --max-zoom 2"
make render-worker-once
ENABLE_PRODUCTION_RADAR_TILES=true make backend
```

See `docs/GRIB2_DECODE.md` for decode/warping/worker notes.

## Demo plans

| Plan | History window (demo) |
|------|------------------------|
| free | Latest frame only |
| basic | 7 days from catalog latest |
| pro | 90 days from catalog latest (default) |
| business | Unrestricted |

Reference timestamp for limits: latest frame in catalog, not wall-clock now.
