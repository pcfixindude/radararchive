# Next Steps

## Phase 13 - Tile Pyramid from Decoded Raster (feature-flagged)

Goal: Generate a tile cache or COG from Phase 12 decode artifacts and serve real imagery via `/tiles` behind an explicit feature flag — keep placeholder tiles as default for offline/stub paths.

Suggested work:
1. Warp decoded grid to layer bounds / Web Mercator tile scheme
2. Write tile pyramid under `data/tiles/mrms/reflectivity/{timestamp}/`
3. Add catalog status such as `real_raster_processed` (distinct from placeholder)
4. Gate `/tiles` on feature flag + status; default remains placeholder
5. Benchmark one CONUS frame end-to-end

Do not start yet:
- Stripe billing integration
- Real auth / user accounts
- HRRR / WPC / native Android

## Phase 12 verification commands

```bash
make test
make inspect-grib2
make decode-grib2
make process-once
cd frontend && npm run build
```

Decode prototype:

```bash
make decode-grib2
MRMS_SOURCE_MODE=real make download-mrms -- --register-discovered --limit 1
make decode-grib2
ls data/staging/grib2_decode/
```

Placeholder pipeline (must remain unchanged):

```bash
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
```
