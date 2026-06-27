# Project State

Current phase: Phase 10 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- MRMS discovery + download pipeline (metadata → local GRIB2.gz or stub files)
- Processor distinguishes raw file kinds and records processing status cleanly
- Stub/demo raw files → `placeholder_processed` placeholder PNGs (tiles work)
- Real downloaded `.grib2.gz` → `placeholder_for_real_raw` preview only (GRIB2 decode not implemented)
- Dev APIs for discovery, download, and processing status
- MapLibre frontend with playback and demo plan selector
- No real auth, Stripe, GRIB2 parsing, or rendered radar tiles

## Local run

```bash
make setup
make seed
make download-mrms -- --register-discovered --limit 3
make process-once
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
make process-once
cd frontend && npm run build
```

## MRMS pipeline (discovery → download → process)

```bash
make download-mrms -- --register-discovered --limit 5
make process-once
```

Dev APIs:
- `GET /api/sources/mrms/latest?limit=5`
- `GET /api/sources/mrms/download-status`
- `GET /api/sources/mrms/processing-status`

## Processing statuses

| Status | Meaning |
|--------|---------|
| `pending` | Raw file present but not yet processed |
| `placeholder_processed` | Stub/demo raw → placeholder PNG (tiles available) |
| `placeholder_for_real_raw` | Real GRIB2.gz → labeled placeholder preview (decode not implemented) |
| `real_decode_not_implemented` | Real GRIB2 awaiting decode (no tiles unless preview created) |
| `failed` | Processing failed |

## Demo plans

| Plan | History window (demo) |
|------|------------------------|
| free | Latest frame only |
| basic | 7 days from catalog latest |
| pro | 90 days from catalog latest (default) |
| business | Unrestricted |

Reference timestamp for limits: latest frame in catalog, not wall-clock now.
