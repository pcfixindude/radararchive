# Project State

Current phase: Phase 16 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery → download → decode prototype pipeline
- **Default tile serving: placeholder** (`ENABLE_DECODED_TILES=false`, `ENABLE_PRODUCTION_RADAR_TILES=false`)
- Optional decoded prototype tiles when `ENABLE_DECODED_TILES=true` + decode artifacts
- **Production warping prototype** with multi-zoom build (`--min-zoom` / `--max-zoom`, default z0 only)
- `make build-production-tiles` supports dry-run, force rebuild, JSON benchmark report
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
```

## Local test

```bash
make test
make build-production-tiles
PYTHONPATH=. python scripts/build_production_tiles.py --dry-run --json-report
cd frontend && npm run build
```

## Production tile build (Phase 16)

```bash
# Safe default — zoom 0 only
make build-production-tiles

# Plan without writing
PYTHONPATH=. python scripts/build_production_tiles.py --dry-run

# Limited multi-zoom (capped at z4, max 256 tiles)
PYTHONPATH=. python scripts/build_production_tiles.py --min-zoom 0 --max-zoom 2

# JSON benchmark report
PYTHONPATH=. python scripts/build_production_tiles.py --json-report

# Rebuild existing tiles
PYTHONPATH=. python scripts/build_production_tiles.py --force

# Fixture/test catalog mark (prototype only — NOT verified MRMS)
PYTHONPATH=. python scripts/build_production_tiles.py --mark-catalog
```

## Pipeline

```bash
make download-mrms -- --register-discovered --limit 1
make decode-grib2
make build-production-tiles
make render-status
ENABLE_PRODUCTION_RADAR_TILES=true make backend
```

See `docs/GRIB2_DECODE.md` for decode/warping/benchmark notes.

## Demo plans

| Plan | History window (demo) |
|------|------------------------|
| free | Latest frame only |
| basic | 7 days from catalog latest |
| pro | 90 days from catalog latest (default) |
| business | Unrestricted |

Reference timestamp for limits: latest frame in catalog, not wall-clock now.
