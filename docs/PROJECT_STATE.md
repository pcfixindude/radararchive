# Project State

Current phase: Phase 5 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- FastAPI backend serves catalog API and placeholder tile endpoint (unchanged contracts)
- Collector/processor stubs populate SQLite catalog and processed PNG placeholders
- React PWA uses MapLibre GL JS with raster overlay from backend tile endpoint
- Time slider updates the active tile timestamp on the map
- Only `mrms_reflectivity` has tile support in the UI
- Real MRMS collection, GRIB2 parsing, georeferenced tiles, auth, and Stripe are not started

Architecture decision:
- PWA first, native Android later
- Cloud collection, not phone/local collection
- MRMS first, HRRR/WPC/NWS layers later
- SQLite catalog for local dev; Postgres later for production

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

## Pipeline (before viewing tiles on map)

```bash
make seed
make collect-once   # optional
make process-once   # required for tile overlay
```
