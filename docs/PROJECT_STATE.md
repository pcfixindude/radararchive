# Project State

Current phase: Phase 3 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- FastAPI backend serves health, layers, times, and latest endpoints from SQLite catalog
- Local storage service manages paths under `data/raw/`, `data/processed/`, and `data/tiles/`
- Collector stub (`make collect-once`) writes placeholder files and registers new demo frames
- React PWA shell loads layers/timestamps from the backend (unchanged API contract)
- Backend tests cover storage, collector, catalog, API routes, and access plans
- Map tiles, auth, Stripe, and real MRMS collection are not started

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
make db-reset
cd frontend && npm run build
```

## Database & storage

- Catalog DB: `data/radararchive.sqlite` (gitignored)
- Raw stubs: `data/raw/mrms/reflectivity/` (gitignored)
- Processed stubs: `data/processed/mrms/reflectivity/` (gitignored)
- Reset catalog: `make db-reset`
- Simulate collection: `make collect-once`
