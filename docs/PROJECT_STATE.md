# Project State

Current phase: Phase 6 complete

Project goal: Build a cloud-first historical weather replay app focused on radar history.

Current status:
- FastAPI backend serves catalog API with layer tile metadata and optional processed-only times filter
- Placeholder tile endpoint serves stub PNGs for processed timestamps
- MapLibre map with CONUS-bounded raster overlay and full playback controls
- Autoplay, speed control, UTC/local timestamp display, and mobile-friendly layout
- Real MRMS collection, GRIB2 parsing, auth, and Stripe are not started

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

## Pipeline (before tiles + autoplay)

```bash
make seed
make process-once
```
