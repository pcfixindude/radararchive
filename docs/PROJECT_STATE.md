# Project State

Current phase: Phase 1 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- FastAPI backend serves health, layers, times, and latest endpoints from demo catalog data
- React PWA shell loads layers/timestamps from the backend and exposes map placeholder + controls
- Backend tests cover health, layers, times, latest, and demo labeling
- Frontend builds successfully; map tiles, auth, Stripe, and real collection are not started

Architecture decision:
- PWA first, native Android later
- Cloud collection, not phone/local collection
- MRMS first, HRRR/WPC/NWS layers later

## Local run

```bash
make setup
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
make seed
```
