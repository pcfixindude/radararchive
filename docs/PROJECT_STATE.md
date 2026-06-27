# Project State

Current phase: Phase 11 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery + download pipeline (metadata → local GRIB2.gz or stub files)
- Processor distinguishes raw kinds; placeholder tiles unchanged
- GRIB2 inspection spike (`make inspect-grib2`) for metadata evaluation
- Optional decoder detection: wgrib2 CLI, GDAL, rasterio, pygrib, cfgrib (none required)
- MapLibre frontend with playback and demo plan selector
- No real auth, Stripe, production GRIB2 rendering, or real radar tiles

## Local run

```bash
make setup
make seed
make download-mrms -- --register-discovered --limit 3
make process-once
make inspect-grib2
make test
make backend
```

## Local test

```bash
make test
make lint
make inspect-grib2
cd frontend && npm run build
```

## MRMS pipeline

```bash
make download-mrms -- --register-discovered --limit 5
make process-once
make inspect-grib2
```

See `docs/GRIB2_DECODE.md` for future decode/render pipeline design.

Dev APIs (unchanged):
- `GET /api/sources/mrms/latest`
- `GET /api/sources/mrms/download-status`
- `GET /api/sources/mrms/processing-status`

## Demo plans

| Plan | History window (demo) |
|------|------------------------|
| free | Latest frame only |
| basic | 7 days from catalog latest |
| pro | 90 days from catalog latest (default) |
| business | Unrestricted |

Reference timestamp for limits: latest frame in catalog, not wall-clock now.
