# Next Steps

## Phase 4 - Processor Stub + Tile Placeholder

Goal: Add a processor worker stub that reads collector placeholder raw files and produces processed placeholders or simple tile metadata, still without real GRIB2 parsing or MapLibre tile rendering.

Suggested work:
1. Implement `backend/app/services/tile_service.py` stub and `scripts/process_once.py`
2. Wire `backend/app/workers/processor.py` to regenerate processed paths from raw catalog rows
3. Add a placeholder tile endpoint shape per `docs/API_SPEC.md` (static/404 stub acceptable)
4. Keep processing out of API request paths; use CLI/worker only
5. Add processor tests; preserve existing API response shapes

Do not start yet:
- Real MRMS S3/AWS downloads
- Real GRIB2 decoding
- MapLibre raster tile rendering
- Stripe billing
- Auth
- HRRR / WPC / native Android

## Phase 3 verification commands

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

Manual API checks:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/layers
curl "http://127.0.0.1:8000/api/times?layer=mrms_reflectivity"
curl "http://127.0.0.1:8000/api/latest?layer=mrms_reflectivity"
```

Database & collection maintenance:

```bash
make seed
make collect-once
make db-reset
```
