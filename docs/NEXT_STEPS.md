# Next Steps

## Phase 11 - GRIB2 Decode Evaluation + Real Raster Pipeline Design

Goal: Evaluate and prototype GRIB2 decoding for MRMS reflectivity (likely GDAL/rasterio or equivalent), define tile pyramid generation, and replace placeholder tiles with real radar imagery for downloaded frames.

Suggested work:
1. Spike GRIB2 decode on a single downloaded CONUS MRMS file; document memory/time constraints
2. Choose processing library and document in `docs/ARCHITECTURE.md` and `docs/DATA_SOURCES.md`
3. Add worker step: `real_decode_pending` → decoded raster → tile pyramid
4. Update processor to transition `placeholder_for_real_raw` → real processed status when decode succeeds
5. Keep stub/demo paths on placeholder tiles for offline dev

Do not start yet:
- Stripe billing integration
- Real auth / user accounts
- HRRR / WPC / native Android

## Phase 10 verification commands

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

Processing checks:

```bash
make download-mrms -- --register-discovered --limit 3
make process-once
curl "http://127.0.0.1:8000/api/sources/mrms/processing-status"
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
```

Plan API checks (unchanged):

```bash
curl "http://127.0.0.1:8000/api/times?layer=mrms_reflectivity&processed_only=true&plan=pro"
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:20:00Z/0/0/0.png?plan=pro"
```

In the UI:
1. Confirm banner mentions placeholder tiles and GRIB2 rendering not implemented
2. Demo playback and plan limits still work on placeholder-processed timestamps
