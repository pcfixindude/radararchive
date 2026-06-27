# Next Steps

## Phase 10 - GRIB2 Processing Stub (metadata only or minimal decode planning)

Goal: Design the GRIB2 → raster processing path without committing to GDAL/rasterio yet — or add a minimal metadata-only GRIB2 header read if a lightweight stdlib-safe approach exists. Real radar rendering remains out of scope until a dedicated processing phase.

Suggested work:
1. Document GRIB2 processing architecture and tile pyramid strategy in `docs/ARCHITECTURE.md`
2. Evaluate processing libraries and memory constraints for CONUS MRMS grids
3. Wire processor to distinguish stub raw files (`.grib2.gz.stub`) from real downloads
4. Add catalog flags for processing readiness vs placeholder processing
5. Keep tile output as placeholders until real decode is approved

Do not start yet:
- Full GDAL/rasterio tile pyramid rendering
- Stripe billing integration
- Real auth / user accounts
- HRRR / WPC / native Android

## Phase 9 verification commands

```bash
make setup
make seed
make process-once
make test
make download-mrms -- --register-discovered --limit 3
make backend
```

In another terminal:

```bash
make frontend
```

MRMS download checks:

```bash
# Offline stub download (discover + register + download)
make download-mrms -- --register-discovered --limit 5

# Download already-registered rows
make discover-mrms -- --register --limit 5
make download-mrms -- --limit 5

# Force re-download
make download-mrms -- --limit 5 --force

# Live NOAA download (requires network)
MRMS_SOURCE_MODE=real make download-mrms -- --register-discovered --limit 3

curl "http://127.0.0.1:8000/api/sources/mrms/download-status"
```

Plan API checks (unchanged):

```bash
curl "http://127.0.0.1:8000/api/times?layer=mrms_reflectivity&plan=pro"
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:20:00Z/0/0/0.png?plan=pro"
```

In the UI:
1. Confirm banner: “MRMS discovery/download available; rendering still placeholder”
2. Demo playback and plan limits still work on processed demo timestamps
