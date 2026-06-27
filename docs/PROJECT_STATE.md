# Project State

Current phase: Phase 7 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- FastAPI backend enforces demo access plans on times, latest, and tile endpoints
- Plan selection via `?plan=` or `X-Demo-Plan` header (default `pro` for local dev)
- Access plan metadata from SQLite (`free`, `basic`, `pro`, `business`)
- MapLibre frontend with playback controls and demo plan selector
- No real auth, Stripe, MRMS collection, or GRIB2 processing

## Local run

```bash
make setup
make seed
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
cd frontend && npm run build
```

## Demo plans

| Plan | History window (demo) |
|------|------------------------|
| free | Latest frame only |
| basic | 7 days from catalog latest |
| pro | 90 days from catalog latest (default) |
| business | Unrestricted |

Reference timestamp for limits: latest frame in catalog, not wall-clock now.
