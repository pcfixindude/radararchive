# Project State

Current phase: Phase 15 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Default tile serving: placeholder** (`ENABLE_DECODED_TILES=false`, `ENABLE_PRODUCTION_RADAR_TILES=false`)
- Optional decoded prototype tiles when `ENABLE_DECODED_TILES=true` + decode artifacts
- **Production warping prototype** builds geo-warped tiles via `make build-production-tiles`
- Production tiles served only when flag + catalog gate + cached tile all true
- Not verified real MRMS — warping prototype only

## Feature flags

```bash
# Default — placeholder tiles only
ENABLE_DECODED_TILES=false
ENABLE_PRODUCTION_RADAR_TILES=false

# Decoded prototype tiles (requires decode artifacts)
ENABLE_DECODED_TILES=true make backend

# Production warping prototype (requires built tiles + catalog gate)
ENABLE_PRODUCTION_RADAR_TILES=true make backend
make build-production-tiles -- --mark-catalog  # fixture/test only
```

## Local test

```bash
make test
make build-production-tiles
make render-status
cd frontend && npm run build
```

## Pipeline

```bash
make download-mrms -- --register-discovered --limit 1
make decode-grib2
make build-production-tiles
make build-tile-cache
make render-status
ENABLE_PRODUCTION_RADAR_TILES=true make backend
```

See `docs/GRIB2_DECODE.md` for decode/warping notes.

## Demo plans

| Plan | History window (demo) |
|------|------------------------|
| free | Latest frame only |
| basic | 7 days from catalog latest |
| pro | 90 days from catalog latest (default) |
| business | Unrestricted |

Reference timestamp for limits: latest frame in catalog, not wall-clock now.
