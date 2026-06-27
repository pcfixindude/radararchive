# Project State

Current phase: Phase 9 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- FastAPI backend enforces demo access plans on times, latest, and tile endpoints
- MRMS discovery lists public NOAA AWS object metadata (no GRIB2 parse)
- MRMS downloader stores GRIB2.gz (or stub placeholders) under `data/raw/mrms/reflectivity/`
- Catalog rows track `download_status`, `sha256`, `file_size_bytes`, `downloaded_at`
- `MRMS_SOURCE_MODE=stub|real` — stub works offline; real mode downloads from public URLs
- Processor stub can turn downloaded raw files into placeholder PNGs (not real radar)
- MapLibre frontend with playback controls and demo plan selector
- No real auth, Stripe, GRIB2 parsing, or rendered radar tiles

## Local run

```bash
make setup
make seed
make process-once
make discover-mrms -- --register --limit 5
make download-mrms -- --limit 5
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
make download-mrms -- --register-discovered --limit 3
cd frontend && npm run build
```

## MRMS pipeline (discovery → download)

```bash
# Discover + register metadata
make discover-mrms -- --register --limit 5

# Download stub placeholders (offline)
make download-mrms -- --limit 5

# One-shot discover + register + download
make download-mrms -- --register-discovered --limit 5

# Live NOAA download (requires network)
MRMS_SOURCE_MODE=real make download-mrms -- --register-discovered --limit 3
```

Dev APIs:
- `GET /api/sources/mrms/latest?limit=5`
- `GET /api/sources/mrms/download-status`

## Demo plans

| Plan | History window (demo) |
|------|------------------------|
| free | Latest frame only |
| basic | 7 days from catalog latest |
| pro | 90 days from catalog latest (default) |
| business | Unrestricted |

Reference timestamp for limits: latest frame in catalog, not wall-clock now.
