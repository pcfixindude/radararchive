# Phase Log

## Phase 0 - Repo Setup

Created initial project structure, docs, and development rules. No app logic yet.

## Phase 1 - Thin Vertical Slice

Built and verified the local demo stack without real NOAA/MRMS downloads.

### Backend
- FastAPI app with typed routes under `backend/app/api/routes.py`
- Demo catalog in `backend/app/demo/catalog.py` (clearly labeled stub data)
- Pydantic schemas in `backend/app/schemas/catalog.py`
- Endpoints verified:
  - `GET /api/health`
  - `GET /api/layers`
  - `GET /api/times?layer=mrms_reflectivity`
  - `GET /api/latest?layer=mrms_reflectivity`

### Frontend
- Vite + React mobile-first shell
- Loads layers and timestamps from the backend API
- Map placeholder (no real radar tiles yet)
- Layer panel, time slider, playback controls
- PWA manifest at `frontend/public/manifest.webmanifest`
- Demo banner and NOAA/NWS attribution footer

### Run commands

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

### Test commands

```bash
make test
make lint
cd frontend && npm run build
make seed
```

### Known limitations
- Demo timestamps are hard-coded UTC values, not collected MRMS frames
- No tile endpoint implementation yet
- No database-backed catalog yet
- Empty worker/service/model stubs exist for later phases
