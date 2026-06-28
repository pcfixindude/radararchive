# Next Steps

## Phase 16 - Production Pipeline Hardening + Multi-Zoom Pyramids

Goal: Expand warping prototype to full zoom pyramids, improve CRS/transform handling, validate against known MRMS frames, and add worker-based batch rendering.

Suggested work:
1. Multi-zoom production pyramid (z0–z8) with CONUS bounds tuning
2. Use `transform` from geo metadata when present
3. Background worker job for `build-production-tiles` (not in API routes)
4. Benchmark one real MRMS frame end-to-end
5. Separate `production_rendered` from `production_prototype` status if needed
6. Keep placeholder default for offline dev

Do not start yet:
- Stripe billing integration
- Real auth / user accounts
- HRRR / WPC / native Android

## Phase 15 verification commands

```bash
make test
make build-production-tiles
make render-status
cd frontend && npm run build
```

Production warping prototype:

```bash
make decode-grib2
make build-production-tiles
make build-production-tiles -- --mark-catalog   # fixture/test catalog only
ENABLE_PRODUCTION_RADAR_TILES=true make backend
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/{timestamp}/0/0/0.png"
# X-RadarArchive-Tile: production-prototype
# X-RadarArchive-Production-Rendering: true
# X-RadarArchive-Render-Status: production_rendered
```

Placeholder default (unchanged):

```bash
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
# X-RadarArchive-Tile: placeholder
# X-RadarArchive-Production-Rendering: false
# X-RadarArchive-Render-Status: placeholder
```

Decoded prototype (unchanged):

```bash
ENABLE_DECODED_TILES=true make backend
```
