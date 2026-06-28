# Next Steps

## Phase 23 - Scheduled Local Validation + Deeper Per-Frame Metrics

Goal: Add optional cron-friendly scheduled validation (no daemon), richer per-frame tile metrics in batch reports, and clearer operator docs for real-MRMS validation when decoder + network are available.

Suggested work:
1. Cron-friendly wrapper script for batch validation + queue benchmark (bounded, offline-safe defaults)
2. Per-frame tile metrics in batch validation reports (align with queue benchmark job summaries)
3. Optional notification hook (local log file only — no external services)
4. Dev panel drill-down for full validation/benchmark JSON (read-only)
5. Honest real-MRMS documentation when decoder + network available
6. Keep placeholder default for offline dev

Do not start yet:
- Stripe, real auth, HRRR, WPC, native Android
- Redis/Celery, cloud deployment
- Mandatory GDAL/rasterio/wgrib2

## Phase 22 verification commands

```bash
make test
make benchmark-render-queue
make validate-real-mrms-batch
make catalog-status
make render-queue-status
cd frontend && npm run build
```
