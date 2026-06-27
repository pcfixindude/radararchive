# Project State

Current phase: Phase 2 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- FastAPI backend serves health, layers, times, and latest endpoints from SQLite catalog
- SQLAlchemy models cover layers, products, radar files, and access plans
- Demo catalog seeded via `make seed` or auto-seed on startup when empty
- React PWA shell loads layers/timestamps from the backend (unchanged API contract)
- Backend tests cover database creation, seeding, catalog service, API routes, and access plans
- Map tiles, auth, Stripe, and real collection are not started

Architecture decision:
- PWA first, native Android later
- Cloud collection, not phone/local collection
- MRMS first, HRRR/WPC/NWS layers later
- SQLite catalog for local dev; Postgres later for production

## Local run

```bash
make setup
make seed
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
make db-reset
cd frontend && npm run build
```

## Database

- Path: `data/radararchive.sqlite` (gitignored)
- Reset: `make db-reset`
