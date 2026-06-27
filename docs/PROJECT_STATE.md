# Project State

Current phase: Phase 8 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- FastAPI backend enforces demo access plans on times, latest, and tile endpoints
- Plan selection via `?plan=` or `X-Demo-Plan` header (default `pro` for local dev)
- MRMS discovery module lists public NOAA AWS object metadata (no GRIB2 download/parse)
- `MRMS_SOURCE_MODE=stub|real` — stub works offline; real mode uses anonymous S3 ListObjectsV2
- Optional catalog registration for discovered files (`source: mrms_discovered`)
- MapLibre frontend with playback controls and demo plan selector
- No real auth, Stripe, GRIB2 parsing, or rendered radar tiles

## Local run

```bash
make setup
make seed
make process-once
make discover-mrms
make test
make backend
```

In another terminal:

```bash
make frontend
```

Open http://127.0.0.1:5173

## Local test

```bash
make test
make lint
make discover-mrms
cd frontend && npm run build
```

## MRMS discovery

```bash
# Offline-safe stub listings (default)
make discover-mrms

# Register discovered metadata in catalog
make discover-mrms -- --register --limit 5

# Live NOAA AWS listing (requires network)
MRMS_SOURCE_MODE=real make discover-mrms -- --limit 5
```

Dev API: `GET /api/sources/mrms/latest?product=MRMS_ReflectivityAtLowestAltitude&limit=5`

## Demo plans

| Plan | History window (demo) |
|------|------------------------|
| free | Latest frame only |
| basic | 7 days from catalog latest |
| pro | 90 days from catalog latest (default) |
| business | Unrestricted |

Reference timestamp for limits: latest frame in catalog, not wall-clock now.
