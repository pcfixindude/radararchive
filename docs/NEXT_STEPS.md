# Next Steps

## Phase 21 - Multi-Frame Catalog Growth + Honest Real-MRMS Docs

Goal: Expand local catalog with multiple MRMS frames through the validation pipeline and document honest real-frame results when decoder + network are available — without claiming verified production output.

Suggested work:
1. Batch validation for N frames with aggregated dashboard metrics
2. Catalog growth scripts (discover/register/download limits)
3. Multi-zoom benchmark reports through queue worker
4. Optional validation history (last N reports) without heavy storage
5. Dev panel polish: expand/collapse, refresh button
6. Keep placeholder default for offline dev

Do not start yet:
- Stripe billing integration
- Real auth / user accounts
- HRRR / WPC / native Android
- Redis/Celery unless optional and clearly not required
- Mandatory GDAL/rasterio/wgrib2
- Cloud deployment

## Phase 20 verification commands

```bash
make test
make validate-real-mrms
make benchmark-real-mrms
make benchmark-real-mrms ARGS="--json-report"
make render-queue-status
cd frontend && npm run build
```

Dev API:

```bash
curl http://127.0.0.1:8000/api/validation/summary
curl http://127.0.0.1:8000/api/validation/latest
```

Production serving (unchanged gates):

```bash
ENABLE_PRODUCTION_RADAR_TILES=true make backend
# Still requires catalog gate + cached tiles
```

Placeholder default (unchanged):

```bash
curl -I "http://127.0.0.1:8000/tiles/mrms_reflectivity/2026-06-27T20:00:00Z/0/0/0.png"
```
