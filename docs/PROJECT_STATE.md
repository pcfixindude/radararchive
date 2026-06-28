# Project State

Current phase: Phase 13 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Default tile serving: placeholder** (`ENABLE_DECODED_TILES=false`)
- Optional decoded prototype tiles when flag enabled + decode artifacts exist
- `make build-tile-cache` pre-builds prototype tile cache
- No production rendering; catalog not marked as rendered

## Feature flag

```bash
# Default — placeholder tiles only
ENABLE_DECODED_TILES=false

# Enable decoded prototype tiles (requires decode artifacts)
ENABLE_DECODED_TILES=true make backend
```

## Local test

```bash
make test
make build-tile-cache
make inspect-grib2
cd frontend && npm run build
```

## Pipeline

```bash
make download-mrms -- --register-discovered --limit 1
make decode-grib2
make build-tile-cache
ENABLE_DECODED_TILES=true make backend
```

See `docs/GRIB2_DECODE.md` for full decode/tile-cache notes.

## Demo plans

| Plan | History window (demo) |
|------|------------------------|
| free | Latest frame only |
| basic | 7 days from catalog latest |
| pro | 90 days from catalog latest (default) |
| business | Unrestricted |

Reference timestamp for limits: latest frame in catalog, not wall-clock now.
