# Project State

Current phase: Phase 14 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Default tile serving: placeholder** (`ENABLE_DECODED_TILES=false`)
- Optional decoded prototype tiles when flag enabled + decode artifacts exist
- **Production geo-accurate rendering: disabled** (`ENABLE_PRODUCTION_RADAR_TILES=false`)
- Render status catalog fields + `geo_metadata.json` for future production tiles
- `make render-status` reports placeholder vs decoded vs production frames
- No production-rendered frames expected yet

## Feature flags

```bash
# Default — placeholder tiles only
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false

# Enable decoded prototype tiles (requires decode artifacts)
ENABLE_DECODED_TILES=true make backend

# Production gate (no renderer yet — still falls back to placeholder)
ENABLE_PRODUCTION_RADAR_TILES=true make backend
```

## Local test

```bash
make test
make render-status
make build-tile-cache
make inspect-grib2
cd frontend && npm run build
```

## Pipeline

```bash
make download-mrms -- --register-discovered --limit 1
make decode-grib2
make build-tile-cache
make render-status
ENABLE_DECODED_TILES=true make backend
```

See `docs/GRIB2_DECODE.md` for decode/tile-cache/geo-metadata notes.

## Demo plans

| Plan | History window (demo) |
|------|------------------------|
| free | Latest frame only |
| basic | 7 days from catalog latest |
| pro | 90 days from catalog latest (default) |
| business | Unrestricted |

Reference timestamp for limits: latest frame in catalog, not wall-clock now.
