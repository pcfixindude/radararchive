# Next Steps

## Phase 5 - MapLibre Integration + Real Tile Grid

Goal: Replace the static placeholder map preview with a MapLibre map that requests placeholder tiles from the backend tile endpoint using the selected layer/timestamp.

Suggested work:
1. Wire MapLibre raster source to `/tiles/{layer}/{timestamp}/{z}/{x}/{y}.png`
2. Sync map timestamp with the time slider
3. Keep tiles as obvious placeholders until real GRIB2 processing lands
4. Add frontend tests or smoke checks for tile URL wiring
5. Preserve existing API contracts

Do not start yet:
- Real MRMS S3/AWS downloads
- Real GRIB2 decoding (GDAL/rasterio)
- Stripe billing
- Auth
- HRRR / WPC / native Android

## Phase 4 verification commands

```bash
make setup
make seed
make collect-once
make process-once
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
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
```

Pipeline maintenance:

```bash
make seed
make collect-once
make process-once
make db-reset
```
