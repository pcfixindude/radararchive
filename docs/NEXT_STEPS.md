# Next Steps

## Phase 22 - Multi-Zoom Queue Benchmarks + Validation History UI

Goal: Run multi-zoom tile builds through the render queue for batched frames and add simple validation history browsing in the dev panel.

Suggested work:
1. Batch benchmark through queue worker with multi-zoom (`--min-zoom`/`--max-zoom`)
2. Validation history list in dev panel (from `/api/validation/history`)
3. Per-frame tile metrics in batch reports
4. Optional scheduled local validation script (cron-friendly, no daemon)
5. Honest real-MRMS documentation when decoder + network available
6. Keep placeholder default for offline dev

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment
- Mandatory GDAL/rasterio/wgrib2

## Phase 21 verification commands

```bash
make test
make validate-real-mrms
make validate-real-mrms-batch
make catalog-status
make render-queue-status
cd frontend && npm run build
```
