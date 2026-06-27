# Next Steps

## Phase 3 - Local Storage + Collector Stub

Goal: Wire the collector worker stub to write immutable raw file placeholders and register new frames in the catalog, still without real NOAA/MRMS S3 downloads.

Suggested work:
1. Implement `backend/app/services/storage.py` for local path layout under `data/raw/` and `data/processed/`
2. Implement `scripts/collect_once.py` to simulate a collection run and insert a new demo `RadarFile` row
3. Keep raw paths immutable; allow processed paths to be regenerated later
4. Add collector/storage tests; keep collection out of API request paths
5. Optionally expose a dev-only script endpoint or CLI only (not public API)

Do not start yet:
- Real MRMS S3/AWS downloads
- GRIB2 parsing or tile rendering
- Stripe billing
- Auth
- HRRR / WPC / native Android

## Phase 2 verification commands

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

Manual API checks:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/layers
curl "http://127.0.0.1:8000/api/times?layer=mrms_reflectivity"
curl "http://127.0.0.1:8000/api/latest?layer=mrms_reflectivity"
```

Database maintenance:

```bash
make seed
make db-reset
```
