# Project State

Current phase: Phase 4 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- FastAPI backend serves health, layers, times, and latest endpoints from SQLite catalog
- Local storage service manages paths under `data/raw/`, `data/processed/`, and `data/tiles/`
- Collector stub (`make collect-once`) writes raw placeholders and registers new frames
- Processor stub (`make process-once`) writes processed PNG placeholders and marks frames processed
- Placeholder tile endpoint serves stub PNG tiles for processed frames
- React PWA shows tile availability/preview in the map placeholder
- Backend tests cover storage, collector, processor, tiles, catalog, API routes, and access plans
- Real MRMS collection, GRIB2 parsing, MapLibre tiles, auth, and Stripe are not started

Architecture decision:
- PWA first, native Android later
- Cloud collection, not phone/local collection
- MRMS first, HRRR/WPC/NWS layers later
- SQLite catalog for local dev; Postgres later for production

## Local run

```bash
make setup
make seed
make collect-once
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
make seed
make collect-once
make process-once
make db-reset
cd frontend && npm run build
```

## Pipeline commands

- Seed catalog + raw stubs: `make seed`
- Simulate collection: `make collect-once`
- Process pending frames: `make process-once`
- Reset catalog: `make db-reset`

## Tile endpoint

```bash
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
```

Returns PNG when the timestamp is processed; 404 otherwise.
