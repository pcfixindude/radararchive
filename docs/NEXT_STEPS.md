# Next Steps

## Phase 15 - Geo-Accurate Tile Warping + Production Render Pipeline

Goal: Implement actual CRS/bounds-aligned tile warping using geo metadata, produce production tile pyramids, and serve them only when `ENABLE_PRODUCTION_RADAR_TILES=true` and catalog `render_status=production_rendered`.

Suggested work:
1. Map MRMS grid to layer bounds / Web Mercator using `geo_metadata.json`
2. Build production tile pyramid under `data/tiles/production/`
3. Wire production renderer behind existing Phase 14 gates
4. Set catalog `render_status=production_rendered` only after verified geo-accurate output
5. Benchmark tile pyramid for one CONUS frame
6. Keep placeholder default for offline dev

Do not start yet:
- Stripe billing integration
- Real auth / user accounts
- HRRR / WPC / native Android

## Phase 14 verification commands

```bash
make test
make render-status
make build-tile-cache
make decode-grib2
cd frontend && npm run build
```

Render status report:

```bash
make render-status
make render-status -- --sync --dry-run
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
# X-RadarArchive-Render-Status: placeholder
```

Production gate (disabled by default):

```bash
# ENABLE_PRODUCTION_RADAR_TILES=true — no production renderer yet; still placeholder fallback
curl http://127.0.0.1:8000/tiles/config
```
