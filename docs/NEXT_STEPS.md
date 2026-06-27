# Next Steps

## Phase 12 - GRIB2 Raster Decode Prototype (single frame)

Goal: Decode one real downloaded MRMS GRIB2.gz frame into a normalized raster using rasterio/GDAL (or chosen backend), store as COG or tile-ready raster, and document memory/time — still behind a feature flag; do not replace all placeholder tiles yet.

Suggested work:
1. Add optional `decode-mrms` script behind dependency check (rasterio/GDAL)
2. Decode single CONUS reflectivity grid → numpy → GeoTIFF/COG under `data/processed/`
3. Update catalog with decode metadata (grid size, bounds, units) without changing tile endpoint yet
4. Benchmark one frame; document in `docs/GRIB2_DECODE.md`
5. Keep demo/stub paths on placeholder tiles

Do not start yet:
- Full tile pyramid replacement for all timestamps
- Stripe billing integration
- Real auth / user accounts
- HRRR / WPC / native Android

## Phase 11 verification commands

```bash
make setup
make test
make inspect-grib2
make backend
```

In another terminal:

```bash
make frontend
```

GRIB2 inspection:

```bash
make inspect-grib2
PYTHONPATH=. python scripts/inspect_grib2.py --file path/to/file.grib2.gz
MRMS_SOURCE_MODE=real make download-mrms -- --register-discovered --limit 1
make inspect-grib2
```

Placeholder pipeline (unchanged):

```bash
make process-once
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
```

In the UI:
1. Confirm banner mentions GRIB2 inspection spike; rendering still placeholder
2. Demo playback and plan limits still work
