# Next Steps

## Phase 14 - Geo-Accurate Tile Warping + Production Render Gate

Goal: Replace simple grid sampling with proper CRS/bounds alignment, add explicit production render status separate from prototype, and gate real tile serving behind multiple checks (flag + status + artifact validity).

Suggested work:
1. Map MRMS grid to layer bounds / Web Mercator
2. Add `real_raster_processed` catalog status distinct from prototype
3. Separate `ENABLE_DECODED_TILES` from future `ENABLE_PRODUCTION_RENDERING`
4. Benchmark tile pyramid for one CONUS frame
5. Keep placeholder default for offline dev

Do not start yet:
- Stripe billing integration
- Real auth / user accounts
- HRRR / WPC / native Android

## Phase 13 verification commands

```bash
make test
make build-tile-cache
make decode-grib2
cd frontend && npm run build
```

Decoded tile prototype:

```bash
make decode-grib2
make build-tile-cache
curl http://127.0.0.1:8000/tiles/config
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
ENABLE_DECODED_TILES=true make backend
```

Placeholder default (unchanged):

```bash
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
# X-RadarArchive-Tile: placeholder
# X-RadarArchive-Production-Rendering: false
```
